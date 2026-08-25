#!/usr/bin/env python3
"""Admit a Microsoft .NET Framework BCL assembly as a behaviour authority.

`pinned_assembly_audit.py` earns authority for an XNA assembly by
machine-comparing its public metadata against every entry it owns in the pinned
257-type / 2,964-member contract. A BCL assembly declares **zero** XNA contract
types, so that gate would pass with nothing compared -- it would calibrate
nothing at all. This tool is therefore a separate mechanism with its own,
non-vacuous calibration rule, and it deliberately shares no registry, no
counter and no scoreboard with the XNA audit.

Authority is earned here by five independent things, all of which must pass:

1. **Exact identity.** The AssemblyName, assembly version, public key and
   strong-name token, file size and full SHA-256 must equal the registered
   values. The token is *recomputed* from the assembly's own public key rather
   than read from a string, so a mismatched key cannot be asserted away.
2. **Microsoft provenance.** The PE version resource, the strong-name key file
   attribute, the required native module imports and the absence of every
   registered reimplementation marker are all checked against the binary.
3. **A pinned selected-shape manifest.** For every admitted family the full CLR
   identity, kind, base, generic arity, constructors, public members, relevant
   protected virtual members, static/instance, visibility, virtual/final/
   abstract flags, return and parameter CLR types and interface implementations
   are reconstructed from the binary and diffed against
   `reference/bcl40-selected-shape.json`. The manifest regenerates
   byte-identically from the admitted binary alone.
4. **Sentinel calibration.** Facts about the selected families that are stated
   here independently of the extractor -- arity, base, hook names, exact
   overridability, exact constructor count, the read-only asymmetry -- must
   hold. A parser that silently produced an empty or wrong shape fails these
   even if it agreed with a manifest it had itself written.
5. **Mutation self-tests.** Removing or altering a type, a member, a generic
   arity, a visibility, a virtual flag, a parameter type, a return type, a base
   or an interface must be *detected*. A comparison that always reported
   "exact" would pass steps 1-4 for the wrong reason.

Optionally, `--cross-check` re-reads the same binary with `monodis`, an
independent metadata reader, and requires it to agree about the critical shape
facts. The exact Microsoft binary remains the authority; the second tool only
validates this file's parsing of it.

    python3 tools/api_compat/bcl_authority_audit.py \
        --assembly mscorlib.dll=/path/to/mscorlib.dll \
        --cross-check \
        --output docs/generated/bcl-authority-audit.json

`--write-manifest` regenerates the pinned manifest from the admitted binaries.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pinned_assembly_audit import (  # noqa: E402
    Parser,
    finalize,
    split_call,
    split_generic_suffix,
    strip_directives,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools/api_compat/bcl-authorities.json"
MANIFEST = ROOT / "tools/api_compat/reference/bcl40-selected-shape.json"

# The method attribute tokens ikdasm emits. Kept identical to the set
# `pinned_assembly_audit.Parser.add_method` recognises, so that what this file
# treats as a flag and what that one treats as a non-return token agree. A
# self-test holds the two in step.
METHOD_ATTRIBUTES = {
    "public", "private", "family", "assembly", "famorassem", "famandassem",
    "static", "instance", "hidebysig", "specialname", "rtspecialname",
    "virtual", "abstract", "final", "newslot", "pinvokeimpl", "strict",
    "explicit", "reqsecobj", "unmanagedexp",
}

# Visibility is recorded for protected members too: a protected virtual hook is
# part of the derived type's contract, so dropping it would silently delete the
# override point an XNA subclass depends on. These are `Parser`'s already-mapped
# spellings, not the raw IL tokens (`family` arrives here as `protected`).
RECORDED_ACCESS = ("public", "protected", "protected-internal")


def public_key_token(public_key_hex: str) -> str:
    """The strong-name token of a public key: last 8 bytes of its SHA-1, reversed.

    Computed rather than read, so a binary whose key does not actually hash to
    the registered token cannot be admitted by asserting the token.
    """
    return hashlib.sha1(bytes.fromhex(public_key_hex)).digest()[-8:][::-1].hex()


def version_resource(data: bytes) -> dict[str, str]:
    """Read the PE VS_VERSION_INFO string table.

    Anchored at the VS_VERSION_INFO key so that an unrelated UTF-16 occurrence
    of a field name elsewhere in a five-megabyte image cannot be mistaken for
    the version resource.
    """
    anchor = data.find("VS_VERSION_INFO".encode("utf-16-le"))
    if anchor < 0:
        return {}
    window = data[anchor:anchor + 8192]
    found: dict[str, str] = {}
    for name in (
        "CompanyName", "FileDescription", "FileVersion", "ProductName",
        "ProductVersion", "OriginalFilename", "InternalName", "LegalCopyright",
    ):
        index = window.find(name.encode("utf-16-le"))
        if index < 0:
            continue
        tail = window[index + len(name) * 2:]
        start = 0
        while start + 1 < len(tail) and tail[start:start + 2] == b"\x00\x00":
            start += 2
        end = start
        while end + 1 < len(tail) and tail[end:end + 2] != b"\x00\x00":
            end += 2
        found[name] = tail[start:end].decode("utf-16-le", "replace")
    return found


def disassemble(path: Path, cache_dir: Path | None, digest: str) -> str:
    """Disassemble `path`, optionally through a shared on-disk cache.

    The cache is keyed by the binary's own SHA-256, never by its file name. Two
    different `mscorlib.dll` files -- Microsoft's and a reimplementation's --
    have the same stem, so a name-keyed cache would silently hand one binary's
    IL back for the other. That is not a hypothetical: it made this tool's own
    negative controls read the admitted assembly's disassembly.
    """
    cache = (cache_dir / f"{path.stem}-{digest[:16]}.il") if cache_dir else None
    if cache is not None and cache.exists():
        return cache.read_text(encoding="utf-8", errors="replace")
    completed = subprocess.run(
        ["ikdasm", str(path)], capture_output=True, text=True, errors="replace",
    )
    if completed.returncode != 0:
        raise SystemExit(f"ikdasm failed for {path}: {completed.stderr[:400]}")
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(completed.stdout, encoding="utf-8")
    return completed.stdout


# ----------------------------------------------------------------------------
# Extraction
# ----------------------------------------------------------------------------


def method_attributes(declaration: str) -> set[str]:
    """The CLR attribute tokens of one `.method` declaration."""
    body = strip_directives(declaration[len(".method"):].strip())
    split = split_call(body)
    if split is None:
        return set()
    head, _parameters, _tail = split
    head, _generics = split_generic_suffix(head)
    tokens = head.split()
    return {token for token in tokens[:-1] if token in METHOD_ATTRIBUTES}


class BclParser(Parser):
    """`Parser`, plus the CLR flags a BCL base-class contract depends on.

    The XNA contract never needed virtual/final/abstract, because an XNA type's
    overridability is recorded in the pinned contract itself. A BCL *base*
    class is different: whether `SetItem` is an overridable hook or a sealed
    implementation is the whole difference between a faithful projection and a
    broken one, so it is extracted rather than assumed.
    """

    def add_method(self, owner: dict[str, Any], declaration: str) -> None:
        before = len(owner["members"])
        super().add_method(owner, declaration)
        if len(owner["members"]) == before:
            return
        attributes = method_attributes(declaration)
        member = owner["members"][-1]
        member["virtual"] = "virtual" in attributes
        member["abstract"] = "abstract" in attributes
        member["final"] = "final" in attributes
        member["newslot"] = "newslot" in attributes
        # An overridable member is virtual and not sealed. `virtual final` is a
        # sealed interface implementation and is NOT an override point.
        member["overridable"] = member["virtual"] and not member["final"]
        owner.setdefault("_accessorFlags", {})[member["name"]] = {
            "virtual": member["virtual"],
            "abstract": member["abstract"],
            "final": member["final"],
            "overridable": member["overridable"],
        }

    def add_property(
        self, owner: dict[str, Any], declaration: str, index: int,
    ) -> int:
        before = len(owner["members"])
        result = super().add_property(owner, declaration, index)
        if len(owner["members"]) == before:
            return result
        member = owner["members"][-1]
        flags = owner.get("_accessorFlags", {})
        for role, accessor in (("get", f"get_{member['name']}"),
                               ("set", f"set_{member['name']}")):
            entry = flags.get(accessor)
            if entry is not None:
                member[f"{role}Overridable"] = entry["overridable"]
                member[f"{role}Abstract"] = entry["abstract"]
        return result


def visible_members(record: dict[str, Any]) -> list[dict[str, Any]]:
    """The members a derived type or a consumer can actually see.

    Explicit interface implementations are private in CLR metadata and carry a
    dotted name; they are neither callable nor overridable by name and are
    excluded. Everything public or protected is kept, including the protected
    hooks.
    """
    kept: list[dict[str, Any]] = []
    for member in record["members"]:
        if member["kind"] in ("method", "constructor"):
            if member.get("access") not in RECORDED_ACCESS:
                continue
        elif member["kind"] == "property":
            accesses = {member.get("getAccess"), member.get("setAccess")} - {None}
            if not accesses & set(RECORDED_ACCESS):
                continue
        elif member["kind"] == "field":
            if member.get("access") not in RECORDED_ACCESS:
                continue
        if "." in member["name"] and member["name"] not in (".ctor", ".cctor"):
            continue
        kept.append(member)
    return kept


def member_record(member: dict[str, Any]) -> dict[str, Any]:
    """One member of the selected-shape manifest, in a stable field order."""
    kind = member["kind"]
    record: dict[str, Any] = {"kind": kind, "name": member["name"]}
    if kind in ("method", "constructor"):
        record.update({
            "access": member.get("access"),
            "static": bool(member.get("static")),
            "virtual": bool(member.get("virtual")),
            "abstract": bool(member.get("abstract")),
            "final": bool(member.get("final")),
            "overridable": bool(member.get("overridable")),
            "returnType": member.get("returnType"),
            "genericParameters": [
                item["name"] for item in member.get("genericParameters", [])
            ],
            "parameters": [
                {
                    "name": item.get("name", ""),
                    "type": item.get("type"),
                    "ref": bool(item.get("ref")),
                    "out": bool(item.get("out")),
                }
                for item in member.get("parameters", [])
            ],
        })
    elif kind == "property":
        record.update({
            "type": member.get("type"),
            "static": bool(member.get("static")),
            "getAccess": member.get("getAccess"),
            "setAccess": member.get("setAccess"),
            "getOverridable": bool(member.get("getOverridable")),
            "setOverridable": bool(member.get("setOverridable")),
            "parameters": [
                {"name": item.get("name", ""), "type": item.get("type")}
                for item in member.get("parameters", [])
            ],
        })
    elif kind == "event":
        record.update({"type": member.get("type")})
    else:
        record.update({
            "type": member.get("type"),
            "access": member.get("access"),
            "static": bool(member.get("static")),
            "constant": bool(member.get("constant")),
            "value": member.get("value"),
        })
    return record


def member_sort_key(record: dict[str, Any]) -> tuple:
    return (
        record["kind"], record["name"],
        json.dumps(record.get("parameters", []), sort_keys=True),
        str(record.get("returnType")), str(record.get("type")),
    )


def type_record(
    assembly: str, name: str, record: dict[str, Any],
) -> dict[str, Any]:
    members = [member_record(item) for item in visible_members(record)]
    members.sort(key=member_sort_key)
    return {
        "assembly": assembly,
        "type": name,
        "kind": record["kind"],
        "sealed": bool(record.get("sealed")),
        "abstract": bool(record.get("abstract")),
        "baseType": record.get("baseType"),
        "genericArity": len(record.get("genericParameters") or []),
        "genericParameters": list(record.get("genericParameters") or []),
        "directInterfaces": sorted(record.get("directInterfaces") or []),
        "members": members,
    }


def extract(
    assembly: str, il: str, selected: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    types = BclParser(il).parse()
    # `finalize` drops the accessor methods a property already represents. It
    # is applied here through the same code path the XNA audit uses, so the BCL
    # manifest and that audit agree about what a property is.
    finalize(types)
    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for name in selected:
        found = types.get(name)
        if found is None:
            missing.append(name)
            continue
        records.append(type_record(assembly, name, found))
    return records, missing


# ----------------------------------------------------------------------------
# Comparison
# ----------------------------------------------------------------------------


def compare_records(
    expected: dict[str, Any], found: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    for field in ("kind", "sealed", "abstract", "baseType", "genericArity",
                  "genericParameters", "directInterfaces"):
        if expected.get(field) != found.get(field):
            issues.append(
                f"{field} {expected.get(field)!r} != {found.get(field)!r}")
    expected_members = {
        json.dumps(item, sort_keys=True) for item in expected["members"]}
    found_members = {
        json.dumps(item, sort_keys=True) for item in found["members"]}
    for item in sorted(expected_members - found_members):
        issues.append(f"pinned member absent from the assembly: {item}")
    for item in sorted(found_members - expected_members):
        issues.append(f"assembly declares a member absent from the manifest: {item}")
    return issues


# ----------------------------------------------------------------------------
# Sentinels: facts stated here, independently of the extractor
# ----------------------------------------------------------------------------

COLLECTION = "System.Collections.ObjectModel.Collection`1"
READONLY = "System.Collections.ObjectModel.ReadOnlyCollection`1"
LIST = "System.Collections.Generic.List`1"
ILIST = "System.Collections.Generic.IList`1"


def sentinel_checks(
    by_type: dict[str, dict[str, Any]],
) -> tuple[int, list[str]]:
    """Independently-expected facts about the selected families.

    These are written from the documented .NET Framework 4.0 contract, not read
    back from the extraction, so an extractor that produced an empty, truncated
    or systematically wrong shape fails here even though it would happily agree
    with a manifest it had itself generated. This is the check that stops the
    calibration being vacuous.
    """
    failures: list[str] = []
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(message)

    def members_of(type_name: str, kind: str, member_name: str) -> list[dict[str, Any]]:
        record = by_type.get(type_name)
        if record is None:
            return []
        return [
            item for item in record["members"]
            if item["kind"] == kind and item["name"] == member_name
        ]

    for name in (COLLECTION, READONLY, LIST, ILIST):
        require(name in by_type, f"{name} was not extracted at all")

    collection = by_type.get(COLLECTION)
    readonly = by_type.get(READONLY)
    if collection is None or readonly is None:
        return checks, failures

    # -- shape of the two base families ------------------------------------
    require(collection["kind"] == "class", "Collection<T> is not a class")
    require(not collection["sealed"], "Collection<T> is sealed")
    require(not collection["abstract"], "Collection<T> is abstract")
    require(collection["baseType"] == "System.Object",
            "Collection<T> does not derive directly from System.Object")
    require(collection["genericArity"] == 1,
            "Collection<T> is not of generic arity 1")
    require(readonly["kind"] == "class", "ReadOnlyCollection<T> is not a class")
    require(readonly["baseType"] == "System.Object",
            "ReadOnlyCollection<T> does not derive directly from System.Object")
    require(readonly["genericArity"] == 1,
            "ReadOnlyCollection<T> is not of generic arity 1")

    # The CLR hierarchy is two siblings, NOT an inheritance chain. Getting this
    # backwards would produce a Swift hierarchy in which a mutable collection
    # inherits a read-only one.
    require(collection["baseType"] != READONLY,
            "Collection<T> was extracted as deriving from ReadOnlyCollection<T>")
    require(readonly["baseType"] != COLLECTION,
            "ReadOnlyCollection<T> was extracted as deriving from Collection<T>")

    for name, record in ((COLLECTION, collection), (READONLY, readonly)):
        for interface in (
            "System.Collections.Generic.IList`1[!T]",
            "System.Collections.Generic.ICollection`1[!T]",
            "System.Collections.Generic.IEnumerable`1[!T]",
            "System.Collections.IList",
            "System.Collections.ICollection",
            "System.Collections.IEnumerable",
        ):
            require(interface in record["directInterfaces"],
                    f"{name} does not declare {interface}")

    # -- constructors -------------------------------------------------------
    collection_ctors = members_of(COLLECTION, "constructor", ".ctor")
    require(len(collection_ctors) == 2,
            f"Collection<T> should declare exactly 2 public constructors, "
            f"found {len(collection_ctors)}")
    require(any(not item["parameters"] for item in collection_ctors),
            "Collection<T> has no parameterless constructor")
    require(any(
        len(item["parameters"]) == 1 and
        item["parameters"][0]["type"] == "System.Collections.Generic.IList`1[!0]"
        for item in collection_ctors),
        "Collection<T> has no IList<T> wrapping constructor")

    readonly_ctors = members_of(READONLY, "constructor", ".ctor")
    require(len(readonly_ctors) == 1,
            f"ReadOnlyCollection<T> should declare exactly 1 public "
            f"constructor, found {len(readonly_ctors)}")
    require(bool(readonly_ctors) and
            len(readonly_ctors[0]["parameters"]) == 1 and
            readonly_ctors[0]["parameters"][0]["type"] ==
            "System.Collections.Generic.IList`1[!0]",
            "ReadOnlyCollection<T>'s only constructor does not take IList<T>")
    # There is deliberately no parameterless constructor: a read-only view must
    # always be a view OF something.
    require(all(item["parameters"] for item in readonly_ctors),
            "ReadOnlyCollection<T> declares a parameterless constructor")

    # -- the four protected virtual hooks ----------------------------------
    for hook, arity in (("ClearItems", 0), ("InsertItem", 2),
                        ("RemoveItem", 1), ("SetItem", 2)):
        candidates = members_of(COLLECTION, "method", hook)
        require(len(candidates) == 1,
                f"Collection<T>.{hook} should be declared exactly once, "
                f"found {len(candidates)}")
        if not candidates:
            continue
        member = candidates[0]
        require(member["access"] == "protected",
                f"Collection<T>.{hook} is not protected")
        require(member["overridable"],
                f"Collection<T>.{hook} is not an overridable virtual hook")
        require(not member["abstract"],
                f"Collection<T>.{hook} is abstract")
        require(len(member["parameters"]) == arity,
                f"Collection<T>.{hook} should take {arity} parameters")
        require(member["returnType"] == "System.Void",
                f"Collection<T>.{hook} does not return void")

    # ReadOnlyCollection<T> deliberately has none of them: it is not a
    # mutation point, so there is nothing to hook.
    for hook in ("ClearItems", "InsertItem", "RemoveItem", "SetItem"):
        require(not members_of(READONLY, "method", hook),
                f"ReadOnlyCollection<T> unexpectedly declares {hook}")

    # -- the public surface is sealed against overriding --------------------
    # Every public member of Collection<T> is `virtual final` -- a sealed
    # interface implementation. A subclass changes behaviour ONLY through the
    # four hooks, and a projection that made the public methods overridable
    # would invent an extension point the CLR does not have.
    for method in ("Add", "Clear", "Contains", "CopyTo", "GetEnumerator",
                   "IndexOf", "Insert", "Remove", "RemoveAt"):
        candidates = members_of(COLLECTION, "method", method)
        require(len(candidates) == 1,
                f"Collection<T>.{method} should be declared exactly once")
        for member in candidates:
            require(member["access"] == "public",
                    f"Collection<T>.{method} is not public")
            require(not member["overridable"],
                    f"Collection<T>.{method} is overridable; the CLR seals it")

    # ReadOnlyCollection<T> exposes no mutator at all.
    for method in ("Add", "Clear", "Insert", "Remove", "RemoveAt"):
        require(not members_of(READONLY, "method", method),
                f"ReadOnlyCollection<T> unexpectedly exposes the mutator {method}")
    for method in ("Contains", "CopyTo", "GetEnumerator", "IndexOf"):
        require(len(members_of(READONLY, "method", method)) == 1,
                f"ReadOnlyCollection<T>.{method} is missing")

    # -- Count, Item and the protected Items view --------------------------
    for name, record_name in ((COLLECTION, "Collection<T>"),
                              (READONLY, "ReadOnlyCollection<T>")):
        count = members_of(name, "property", "Count")
        require(len(count) == 1, f"{record_name}.Count is missing")
        for member in count:
            require(member["type"] == "System.Int32",
                    f"{record_name}.Count is not Int32")
            require(member["getAccess"] == "public" and
                    member["setAccess"] is None,
                    f"{record_name}.Count is not a public get-only property")
        items = members_of(name, "property", "Items")
        require(len(items) == 1, f"{record_name}.Items is missing")
        for member in items:
            require(member["getAccess"] == "protected",
                    f"{record_name}.Items is not a protected getter")
            require(member["setAccess"] is None,
                    f"{record_name}.Items has a setter")
            require(member["type"] == "System.Collections.Generic.IList`1[!0]",
                    f"{record_name}.Items is not IList<T>")

    # The read/write asymmetry between the two families is the whole point of
    # having two of them.
    collection_item = members_of(COLLECTION, "property", "Item")
    require(len(collection_item) == 1, "Collection<T>.Item is missing")
    for member in collection_item:
        require(member["getAccess"] == "public" and
                member["setAccess"] == "public",
                "Collection<T>.Item is not a public read/write indexer")
        require(len(member["parameters"]) == 1 and
                member["parameters"][0]["type"] == "System.Int32",
                "Collection<T>.Item is not indexed by Int32")
        require(member["type"] == "!0",
                "Collection<T>.Item is not typed by the generic parameter")
    readonly_item = members_of(READONLY, "property", "Item")
    require(len(readonly_item) == 1, "ReadOnlyCollection<T>.Item is missing")
    for member in readonly_item:
        require(member["getAccess"] == "public",
                "ReadOnlyCollection<T>.Item has no public getter")
        require(member["setAccess"] is None,
                "ReadOnlyCollection<T>.Item has a setter; it must be read-only")

    # -- the backing store --------------------------------------------------
    backing = by_type.get(LIST)
    if backing is not None:
        require(backing["kind"] == "class", "List<T> is not a class")
        require(backing["genericArity"] == 1, "List<T> is not of generic arity 1")
        require("System.Collections.Generic.IList`1[!T]" in
                backing["directInterfaces"],
                "List<T> does not implement IList<T>, so it cannot be the "
                "backing store Collection<T>..ctor() allocates")
        require(any(
            not item["parameters"]
            for item in members_of(LIST, "constructor", ".ctor")),
            "List<T> has no parameterless constructor")
    contract = by_type.get(ILIST)
    if contract is not None:
        require(contract["kind"] == "interface", "IList<T> is not an interface")
        for method in ("IndexOf", "Insert", "RemoveAt"):
            require(len(members_of(ILIST, "method", method)) == 1,
                    f"IList<T>.{method} is missing")
    return checks, failures


# ----------------------------------------------------------------------------
# Mutation self-tests
# ----------------------------------------------------------------------------


def mutation_self_tests(
    manifest: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """Prove the comparison and the sentinels are not vacuous.

    Every mutation below perturbs one already-matching record. A mutation that
    the comparison does not detect would mean the audit passes for the wrong
    reason.
    """
    failures: list[str] = []
    checks = 0
    by_name = {item["type"]: item for item in manifest}

    subjects = [name for name in (COLLECTION, READONLY, LIST, ILIST)
                if name in by_name]
    checks += 1
    if len(subjects) < 4:
        failures.append("mutation self-test subjects are missing")

    def first_of(record: dict[str, Any], kind: str) -> dict[str, Any] | None:
        for member in record["members"]:
            if member["kind"] == kind:
                return member
        return None

    def drop_member(kind: str) -> Any:
        def mutate(record: dict[str, Any]) -> bool:
            for index, member in enumerate(record["members"]):
                if member["kind"] == kind:
                    del record["members"][index]
                    return True
            return False
        return mutate

    def add_member(record: dict[str, Any]) -> bool:
        record["members"].append(member_record({
            "kind": "method", "name": "InventedMember", "access": "public",
            "static": False, "returnType": "System.Void",
            "genericParameters": [], "parameters": [],
        }))
        return True

    def change_arity(record: dict[str, Any]) -> bool:
        record["genericArity"] += 1
        return True

    def change_generic_parameters(record: dict[str, Any]) -> bool:
        record["genericParameters"] = ["TRenamed"]
        return True

    def change_base(record: dict[str, Any]) -> bool:
        record["baseType"] = "System.Collections.ObjectModel.ReadOnlyCollection`1"
        return True

    def drop_interface(record: dict[str, Any]) -> bool:
        if not record["directInterfaces"]:
            return False
        record["directInterfaces"] = record["directInterfaces"][1:]
        return True

    def drop_ilist_interface(record: dict[str, Any]) -> bool:
        target = "System.Collections.Generic.IList`1[!T]"
        if target not in record["directInterfaces"]:
            return False
        record["directInterfaces"] = [
            item for item in record["directInterfaces"] if item != target]
        return True

    def add_interface(record: dict[str, Any]) -> bool:
        record["directInterfaces"] = sorted(
            record["directInterfaces"] + ["System.ICloneable"])
        return True

    def change_kind(record: dict[str, Any]) -> bool:
        record["kind"] = "interface" if record["kind"] == "class" else "class"
        return True

    def flip_sealed(record: dict[str, Any]) -> bool:
        record["sealed"] = not record["sealed"]
        return True

    def change_visibility(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member.get("access") == "protected":
                member["access"] = "public"
                return True
            if member.get("getAccess") == "protected":
                member["getAccess"] = "public"
                return True
        return False

    def flip_virtual(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member.get("overridable"):
                member["overridable"] = False
                member["final"] = True
                return True
        return False

    def unseal_public_member(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] == "method" and member.get("final"):
                member["final"] = False
                member["overridable"] = True
                return True
        return False

    def change_parameter_type(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member.get("parameters"):
                member["parameters"][0]["type"] = "System.Object"
                return True
        return False

    def change_return_type(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] == "method" and member.get("returnType"):
                member["returnType"] = "System.Object"
                return True
        return False

    def change_property_type(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] == "property":
                member["type"] = "System.Object"
                return True
        return False

    def flip_static(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if "static" in member:
                member["static"] = not member["static"]
                return True
        return False

    def rename_member(record: dict[str, Any]) -> bool:
        member = first_of(record, "method")
        if member is None:
            return False
        member["name"] += "Renamed"
        return True

    def add_setter(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] == "property" and member.get("setAccess") is None:
                member["setAccess"] = "public"
                return True
        return False

    mutations = [
        ("dropped method", drop_member("method")),
        ("dropped constructor", drop_member("constructor")),
        ("dropped property", drop_member("property")),
        ("invented extra member", add_member),
        ("changed generic arity", change_arity),
        ("renamed generic parameter", change_generic_parameters),
        ("changed base type", change_base),
        ("dropped declared interface", drop_interface),
        ("invented declared interface", add_interface),
        ("changed type kind", change_kind),
        ("flipped sealed", flip_sealed),
        ("widened member visibility", change_visibility),
        ("removed a virtual flag", flip_virtual),
        ("unsealed a sealed public member", unseal_public_member),
        ("changed parameter type", change_parameter_type),
        ("changed return type", change_return_type),
        ("changed property type", change_property_type),
        ("flipped static identity", flip_static),
        ("renamed member", rename_member),
        ("invented a property setter", add_setter),
    ]

    for name in subjects:
        pinned = by_name[name]
        checks += 1
        if compare_records(pinned, pinned):
            failures.append(f"{name}: the unmutated comparison is not clean")
        for label, mutate in mutations:
            candidate = copy.deepcopy(pinned)
            if not mutate(candidate):
                continue
            checks += 1
            if not compare_records(pinned, candidate):
                failures.append(f"{name}: {label} was not detected")

    # A dropped type must be caught by the audit's own missing-type path, and a
    # sentinel set that survives an empty extraction would be worthless.
    checks += 1
    if not sentinel_checks({})[1]:
        failures.append("the sentinels pass against an empty extraction")

    # Each of these single mutations must break at least one sentinel.
    sentinel_mutations: list[tuple[str, str, Any]] = [
        ("Collection<T> made sealed", COLLECTION, flip_sealed),
        ("Collection<T> rebased on ReadOnlyCollection<T>", COLLECTION, change_base),
        ("Collection<T> arity changed", COLLECTION, change_arity),
        ("a Collection<T> hook made non-overridable", COLLECTION, flip_virtual),
        ("a Collection<T> hook made public", COLLECTION, change_visibility),
        ("a Collection<T> interface dropped", COLLECTION, drop_interface),
        ("a Collection<T> member dropped", COLLECTION, drop_member("method")),
        ("a Collection<T> constructor dropped", COLLECTION, drop_member("constructor")),
        ("ReadOnlyCollection<T> given a setter", READONLY, add_setter),
        ("ReadOnlyCollection<T> constructor dropped", READONLY,
         drop_member("constructor")),
        ("IList<T> turned into a class", ILIST, change_kind),
        ("List<T>'s IList<T> implementation dropped", LIST, drop_ilist_interface),
        ("Collection<T>'s IList<T> implementation dropped", COLLECTION,
         drop_ilist_interface),
        ("ReadOnlyCollection<T>'s IList<T> implementation dropped", READONLY,
         drop_ilist_interface),
    ]
    for label, subject, mutate in sentinel_mutations:
        if subject not in by_name:
            continue
        mutated = {item["type"]: copy.deepcopy(item) for item in manifest}
        checks += 1
        if not mutate(mutated[subject]):
            failures.append(f"sentinel mutation {label!r} did not apply")
            continue
        if not sentinel_checks(mutated)[1]:
            failures.append(f"sentinel mutation {label!r} was not detected")

    # Removing a whole selected family must break the sentinels too.
    for subject in (COLLECTION, READONLY, LIST, ILIST):
        if subject not in by_name:
            continue
        reduced = {
            item["type"]: copy.deepcopy(item)
            for item in manifest if item["type"] != subject
        }
        checks += 1
        if not sentinel_checks(reduced)[1]:
            failures.append(f"removing {subject} entirely was not detected")

    return checks, failures


# ----------------------------------------------------------------------------
# Independent metadata reader
# ----------------------------------------------------------------------------

# CLR TypeAttributes bits the independent reader is checked against.
TYPE_INTERFACE = 0x000020
TYPE_ABSTRACT = 0x000080
TYPE_SEALED = 0x000100


def monodis(path: Path, switch: str) -> str | None:
    try:
        completed = subprocess.run(
            ["monodis", switch, str(path)],
            capture_output=True, text=True, errors="replace", timeout=900,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


TYPEDEF_ROW = re.compile(
    r"^(\d+):\s+(\S+)\s+\(flist=(\d+),\s*mlist=(\d+),\s*flags=0x([0-9a-fA-F]+)")
METHOD_ROW = re.compile(r"^(\d+):\s+(.*?)\s*\(param:")


def monodis_method_name(signature: str) -> str | None:
    """The declared name in one `monodis --method` row.

    `instance default void ClearItems ()` -> `ClearItems`. A generic method is
    rendered by monodis with its parameter list attached to the name
    (`ConvertAll<TOutput>`), so the balanced suffix is removed before the name
    is taken -- a generic parameter list may itself contain spaces. A quoted
    name that contains a dot is an explicit interface implementation, which is
    private and unnameable, and is excluded exactly as the extraction excludes
    it.
    """
    head = signature.rsplit("(", 1)[0].strip()
    if not head:
        return None
    head, _generics = split_generic_suffix(head)
    if not head.split():
        return None
    name = head.split()[-1]
    quoted = name.startswith("'") and name.endswith("'")
    name = name.strip("'")
    if name in (".ctor", ".cctor"):
        return name
    if "." in name:
        return None
    if quoted and "." in name:
        return None
    return name


def cross_check(
    path: Path, records: list[dict[str, Any]],
) -> tuple[int, list[str], bool]:
    """Re-read the same binary with `monodis` and require agreement.

    `ikdasm` and `monodis` are separate implementations of a CLI metadata
    reader, so this is a genuine second opinion on the *parsing*, not a second
    opinion on the behaviour: the exact Microsoft binary remains the only
    authority for what the BCL does. If `monodis` is unavailable the check is
    reported as skipped, never silently passed.

    The comparison is index-sliced rather than name-grepped: `--typedef` gives
    each type's first method-table row, so the rows belonging to one type are
    exactly the half-open range up to the next type's first row. Property and
    event accessors are folded into properties by the extraction, so they are
    expanded back here -- which independently checks that the folding kept the
    accessors it claims to represent.
    """
    failures: list[str] = []
    checks = 0
    typedefs = monodis(path, "--typedef")
    methods = monodis(path, "--method")
    if typedefs is None or methods is None:
        return 0, [], False

    rows: list[tuple[int, str, int, int]] = []
    for line in typedefs.splitlines():
        found = TYPEDEF_ROW.match(line.strip())
        if found:
            rows.append((
                int(found.group(1)), found.group(2).replace("/", "+"),
                int(found.group(4)), int(found.group(5), 16),
            ))
    rows.sort()

    method_rows: dict[int, str] = {}
    for line in methods.splitlines():
        found = METHOD_ROW.match(line.strip())
        if found:
            method_rows[int(found.group(1))] = found.group(2)

    checks += 1
    if not rows or not method_rows:
        failures.append("monodis produced no type or method table")
        return checks, failures, True

    by_name = {name: (index, mlist, flags) for index, name, mlist, flags in rows}
    starts = sorted(item[2] for item in rows)

    for record in records:
        name = record["type"]
        checks += 1
        entry = by_name.get(name)
        if entry is None:
            failures.append(f"monodis does not declare {name}")
            continue
        _index, mlist, flags = entry

        checks += 1
        is_interface = bool(flags & TYPE_INTERFACE)
        if is_interface != (record["kind"] == "interface"):
            failures.append(
                f"{name}: monodis says interface={is_interface}, the "
                f"extraction says kind={record['kind']}")
        checks += 1
        if bool(flags & TYPE_SEALED) != record["sealed"]:
            failures.append(
                f"{name}: monodis says sealed={bool(flags & TYPE_SEALED)}, "
                f"the extraction says {record['sealed']}")
        checks += 1
        if bool(flags & TYPE_ABSTRACT) != record["abstract"]:
            failures.append(
                f"{name}: monodis says abstract={bool(flags & TYPE_ABSTRACT)}, "
                f"the extraction says {record['abstract']}")

        following = [item for item in starts if item > mlist]
        end = following[0] if following else max(method_rows) + 1
        observed: set[str] = set()
        for row in range(mlist, end):
            signature = method_rows.get(row)
            if signature is None:
                continue
            method_name = monodis_method_name(signature)
            if method_name is not None:
                observed.add(method_name)

        expected: set[str] = set()
        for member in record["members"]:
            if member["kind"] in ("method", "constructor"):
                expected.add(member["name"])
            elif member["kind"] == "property":
                if member.get("getAccess"):
                    expected.add(f"get_{member['name']}")
                if member.get("setAccess"):
                    expected.add(f"set_{member['name']}")
            elif member["kind"] == "event":
                expected.add(f"add_{member['name']}")
                expected.add(f"remove_{member['name']}")

        checks += 1
        unseen = sorted(expected - observed)
        if unseen:
            failures.append(
                f"{name}: the extraction claims members monodis's method table "
                f"does not carry: {unseen}")
    return checks, failures, True


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Identity and provenance
# ----------------------------------------------------------------------------


def verify_identity(
    name: str, entry: dict[str, Any], path: Path, il_cache: Path | None,
) -> tuple[int, list[str], str | None, dict[str, str], str, str]:
    """Check one candidate binary against its registered identity.

    Returns the number of independent checks made, the failures, the
    disassembly (None when the digest already disqualified the file, in which
    case nothing further is read from it), the PE version resource, the
    recomputed strong-name token and the digest.

    This is the same code path the negative controls use, so a check that has
    stopped being load-bearing shows up as a control that no longer rejects.
    """
    failures: list[str] = []
    checks = 0
    data = path.read_bytes()

    checks += 1
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry["sha256"]:
        failures.append(
            f"{name}: sha256 {digest} does not match the registered "
            f"{entry['sha256']}")

    checks += 1
    if len(data) != entry["fileSize"]:
        failures.append(
            f"{name}: size {len(data)} != registered {entry['fileSize']}")

    il = disassemble(path, il_cache, digest)

    checks += 1
    declared = re.search(r"^\.assembly\s+(?:extern\s+)?([\w.]+)\s*$", il, re.M)
    assembly_name = declared.group(1) if declared else None
    if assembly_name != entry["assemblyName"]:
        failures.append(
            f"{name}: declares assembly {assembly_name!r}, registered "
            f"{entry['assemblyName']!r}")

    checks += 1
    version = re.search(r"^\s*\.ver\s+(\d+):(\d+):(\d+):(\d+)\s*$", il, re.M)
    version_text = ".".join(version.groups()) if version else None
    if version_text != entry["assemblyVersion"]:
        failures.append(
            f"{name}: assembly version {version_text}, registered "
            f"{entry['assemblyVersion']}")

    checks += 1
    key = re.search(r"\.publickey\s*=\s*\(([0-9A-Fa-f\s]*?)\)", il, re.S)
    key_hex = re.sub(r"\s+", "", key.group(1)).lower() if key else ""
    if key_hex != entry["publicKey"]:
        failures.append(
            f"{name}: public key {key_hex!r} != registered "
            f"{entry['publicKey']!r}")

    checks += 1
    token = public_key_token(key_hex) if key_hex else ""
    if token != entry["publicKeyToken"]:
        failures.append(
            f"{name}: public key token {token!r} recomputed from the "
            f"assembly's own key != registered {entry['publicKeyToken']!r}")

    checks += 1
    module = re.search(r"^\.module\s+(\S+)\s*$", il, re.M)
    module_name = module.group(1) if module else None
    if module_name != entry["moduleName"]:
        failures.append(
            f"{name}: module {module_name!r} != registered "
            f"{entry['moduleName']!r}")

    resource = version_resource(data)
    for field, expected in entry["versionResource"].items():
        checks += 1
        if resource.get(field) != expected:
            failures.append(
                f"{name}: version resource {field}={resource.get(field)!r} "
                f"!= registered {expected!r}")

    checks += 1
    if entry["strongNameKeyFile"].encode("ascii") not in data:
        failures.append(
            f"{name}: the registered strong-name key file "
            f"{entry['strongNameKeyFile']!r} is not present in the binary")

    for module_import in entry["requiredModuleImports"]:
        checks += 1
        if not re.search(
            rf"^\.module\s+extern\s+{re.escape(module_import)}\s*$", il, re.M,
        ):
            failures.append(
                f"{name}: required module import {module_import} is absent")

    for marker in entry["forbiddenProvenanceMarkers"]:
        checks += 1
        if marker in il:
            failures.append(
                f"{name}: reimplementation marker {marker!r} is present")

    return checks, failures, il, resource, token, digest


def negative_controls(
    authorities: dict[str, dict[str, Any]],
    controls: list[str],
    il_cache: Path | None,
) -> tuple[int, list[str], list[dict[str, Any]]]:
    """Prove the identity and provenance checks actually reject.

    A gate that admits everything would pass every positive test in this file.
    Each control names a binary that must NOT be admitted, and it is run
    through exactly the checks a real admission runs through; a control that
    produces no failure is itself a failure.
    """
    failures: list[str] = []
    checks = 0
    results: list[dict[str, Any]] = []
    for control in controls:
        name, _, raw = control.partition("=")
        entry = authorities.get(name)
        if entry is None or not raw:
            failures.append(f"negative control {control!r} names no authority")
            checks += 1
            continue
        path = Path(raw).expanduser()
        if not path.is_file():
            failures.append(f"negative control {path} is not a file")
            checks += 1
            continue
        # Deliberately NOT cached: a control is read once and its
        # disassembly is tens of megabytes. Caching it would trade real disk
        # wear for a saving no later run collects.
        made, rejected, _il, _resource, _token, _digest = verify_identity(
            name, entry, path, None)
        checks += 1
        if not rejected:
            failures.append(
                f"negative control {path} was NOT rejected as {name}")
        results.append({
            "control": str(path),
            "offeredAs": name,
            "checksRun": made,
            "rejectedBy": len(rejected),
            "reasons": rejected,
        })
    return checks, failures, results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--assembly", action="append", default=[], metavar="NAME=PATH",
        help="a registered BCL assembly and the binary to admit for it")
    parser.add_argument("--il-cache", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--cross-check", action="store_true")
    parser.add_argument(
        "--negative-control", action="append", default=[], metavar="NAME=PATH",
        help="a binary that must NOT be admitted as NAME; proves the "
             "identity and provenance checks still reject")
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    authorities = {item["assembly"]: item for item in registry["authorities"]}

    supplied: dict[str, Path] = {}
    for entry in args.assembly:
        name, _, raw = entry.partition("=")
        if not raw:
            raise SystemExit(f"--assembly expects NAME=PATH, got {entry!r}")
        supplied[name] = Path(raw).expanduser()

    identity_failures: list[str] = []
    identity_checks = 0
    admitted: list[dict[str, Any]] = []
    manifest_records: list[dict[str, Any]] = []
    cross_check_checks = 0
    cross_check_failures: list[str] = []
    cross_check_ran = False

    for name, entry in authorities.items():
        path = supplied.get(name)
        if path is None:
            identity_failures.append(f"{name}: no binary supplied")
            identity_checks += 1
            continue
        if not path.is_file():
            identity_failures.append(f"{name}: {path} is not a file")
            identity_checks += 1
            continue

        identity_made, identity_issues, il, resource, token, digest = (
            verify_identity(name, entry, path, args.il_cache))
        identity_checks += identity_made
        identity_failures.extend(identity_issues)
        if identity_issues:
            continue

        selected = [item["type"] for item in entry["selectedFamilies"]]
        records, missing = extract(name, il, selected)
        for absent in missing:
            identity_checks += 1
            identity_failures.append(
                f"{name}: selected family {absent} is not declared")
        manifest_records.extend(records)

        admitted.append({
            "assembly": name,
            "assemblyName": entry["assemblyName"],
            "assemblyVersion": entry["assemblyVersion"],
            "publicKeyToken": entry["publicKeyToken"],
            "publicKeyTokenRecomputed": token,
            "sha256": digest,
            "fileVersion": resource.get("FileVersion"),
            "selectedTypes": len(records),
            "selectedMembers": sum(len(item["members"]) for item in records),
        })

        if args.cross_check:
            checks, failures, ran = cross_check(path, records)
            cross_check_checks += checks
            cross_check_failures.extend(f"{name}: {item}" for item in failures)
            cross_check_ran = cross_check_ran or ran

    manifest_records.sort(key=lambda item: (item["assembly"], item["type"]))
    document = {
        "schemaVersion": 1,
        "profile": registry["profile"],
        "note": (
            "The selected BCL shape this binding's support classes are derived "
            "from, reconstructed mechanically from the hash-registered "
            "Microsoft binaries named in bcl-authorities.json. It records CLR "
            "facts only -- no Swift spelling, no mapping rule and no "
            "machine-local path -- so it is a function of those binaries "
            "alone and regenerates byte-identically. No Microsoft binary is "
            "stored in the repository."),
        "types": manifest_records,
    }

    if args.write_manifest:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(
            json.dumps(document, indent=2, sort_keys=False) + "\n",
            encoding="utf-8")

    manifest_failures: list[str] = []
    manifest_checks = 0
    if MANIFEST.exists():
        pinned = json.loads(MANIFEST.read_text(encoding="utf-8"))
        pinned_by_name = {
            (item["assembly"], item["type"]): item for item in pinned["types"]}
        found_by_name = {
            (item["assembly"], item["type"]): item for item in manifest_records}
        for key in sorted(set(pinned_by_name) | set(found_by_name)):
            manifest_checks += 1
            if key not in found_by_name:
                manifest_failures.append(
                    f"{key[1]}: pinned in the manifest but not extracted")
                continue
            if key not in pinned_by_name:
                manifest_failures.append(
                    f"{key[1]}: extracted but absent from the pinned manifest")
                continue
            for issue in compare_records(pinned_by_name[key], found_by_name[key]):
                manifest_failures.append(f"{key[1]}: {issue}")
    elif not args.write_manifest:
        manifest_failures.append(f"{MANIFEST} does not exist")

    control_checks, control_failures, controls = negative_controls(
        authorities, args.negative_control, args.il_cache)

    by_type = {item["type"]: item for item in manifest_records}
    sentinel_count, sentinel_failures = sentinel_checks(by_type)
    mutation_count, mutation_failures = mutation_self_tests(manifest_records)

    failed = bool(
        identity_failures or manifest_failures or sentinel_failures or
        mutation_failures or cross_check_failures or control_failures)

    report = {
        "schemaVersion": 1,
        "registrySha256": hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
        "manifestSha256": (
            hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
            if MANIFEST.exists() else None),
        "BCL_AUTHORITY_STATUS": "FAIL" if failed else "PASS",
        "BCL_AUTHORITY_ASSEMBLIES": len(admitted),
        "BCL_AUTHORITY_TYPES": len(manifest_records),
        "BCL_AUTHORITY_MEMBERS": sum(
            len(item["members"]) for item in manifest_records),
        "BCL_IDENTITY_CHECKS": identity_checks,
        "BCL_SENTINEL_CHECKS": sentinel_count,
        "BCL_MANIFEST_CHECKS": manifest_checks,
        "BCL_MUTATION_SELF_TESTS": mutation_count,
        "BCL_CROSS_CHECKS": cross_check_checks,
        "BCL_NEGATIVE_CONTROLS": control_checks,
        "BCL_CROSS_CHECK_TOOL": "monodis" if cross_check_ran else "not run",
        "identityFailures": identity_failures,
        "manifestFailures": manifest_failures,
        "sentinelFailures": sentinel_failures,
        "mutationFailures": mutation_failures,
        "crossCheckFailures": cross_check_failures,
        "controlFailures": control_failures,
        "negativeControls": controls,
        "assemblies": admitted,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for record in admitted:
        print(
            f"{record['assembly']:20s} v{record['assemblyVersion']} "
            f"token={record['publicKeyTokenRecomputed']} "
            f"types={record['selectedTypes']:2d} "
            f"members={record['selectedMembers']:4d}")
    print(
        f"BCL_AUTHORITY_ASSEMBLIES={report['BCL_AUTHORITY_ASSEMBLIES']} "
        f"BCL_AUTHORITY_TYPES={report['BCL_AUTHORITY_TYPES']} "
        f"BCL_AUTHORITY_MEMBERS={report['BCL_AUTHORITY_MEMBERS']}")
    print(
        f"BCL_IDENTITY_CHECKS={identity_checks} "
        f"BCL_SENTINEL_CHECKS={sentinel_count} "
        f"BCL_MANIFEST_CHECKS={manifest_checks} "
        f"BCL_MUTATION_SELF_TESTS={mutation_count} "
        f"BCL_CROSS_CHECKS={cross_check_checks} "
        f"({report['BCL_CROSS_CHECK_TOOL']}) "
        f"BCL_NEGATIVE_CONTROLS={control_checks}")
    for record in controls:
        print(
            f"  rejected {Path(record['control']).name} offered as "
            f"{record['offeredAs']}: {record['rejectedBy']}/"
            f"{record['checksRun']} checks failed")
    print(f"BCL_AUTHORITY_STATUS={report['BCL_AUTHORITY_STATUS']}")
    for line in (identity_failures + manifest_failures + sentinel_failures +
                 mutation_failures + cross_check_failures + control_failures):
        print(f"  {line}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
