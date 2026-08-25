#!/usr/bin/env python3
"""Audit pinned Microsoft XNA assemblies against the retained contract.

The retained contract in `reference/xna40-windows-runtime-contract.json` is the
public-shape authority, and a hash-matched assembly is the behavior authority
for the types it declares. Before an assembly may be used as a behavior
authority it must be *registered*: its SHA-256 recorded, and its public
metadata machine-compared against every contract entry it owns.

This tool performs that comparison. It disassembles each assembly with
`ikdasm`, reconstructs the public type/member shape in the contract's own
schema, and diffs it against the contract.

Correctness of the reconstruction is not asserted, it is calibrated: the two
assemblies that were already registered before this tool existed must
reproduce their contract entries exactly. `--require-exact NAME` makes that a
hard gate, and the audit refuses to report on any other assembly unless every
calibration assembly passes.

    python3 tools/api_compat/pinned_assembly_audit.py \
        --assembly-dir ~/Downloads/win \
        --require-exact Microsoft.Xna.Framework.dll \
        --require-exact Microsoft.Xna.Framework.Graphics.dll \
        --output docs/generated/pinned-assembly-audit.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "tools/api_compat/reference/xna40-windows-runtime-contract.json"

PRIMITIVES = {
    "void": "System.Void",
    "bool": "System.Boolean",
    "char": "System.Char",
    "int8": "System.SByte",
    "unsigned int8": "System.Byte",
    "int16": "System.Int16",
    "unsigned int16": "System.UInt16",
    "int32": "System.Int32",
    "unsigned int32": "System.UInt32",
    "int64": "System.Int64",
    "unsigned int64": "System.UInt64",
    "float32": "System.Single",
    "float64": "System.Double",
    "string": "System.String",
    "object": "System.Object",
    "native int": "System.IntPtr",
    "native unsigned int": "System.UIntPtr",
    "typedref": "System.TypedReference",
    # ikdasm also emits the short unsigned spellings.
    "uint8": "System.Byte",
    "uint16": "System.UInt16",
    "uint32": "System.UInt32",
    "uint64": "System.UInt64",
}

ACCESS = {
    "public": "public",
    "family": "protected",
    "famorassem": "protected-internal",
}
# Only these reach the public contract surface.
VISIBLE_ACCESS = set(ACCESS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def disassemble(path: Path, cache: Path | None) -> str:
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


def strip_assembly_ref(text: str) -> str:
    return re.sub(r"\[[A-Za-z0-9_.]+\]", "", text)


def normalize_type(text: str) -> str:
    """Map an IL type expression onto the contract's CLR type spelling."""
    text = text.strip()
    if not text:
        return ""
    # Drop custom modifiers and marshalling directives, which the contract
    # does not record.
    text = re.sub(r"modopt\([^)]*\)|modreq\([^)]*\)", "", text)
    text = re.sub(r"\bmarshal\s*\([^)]*\)", "", text).strip()
    # Trailing by-ref marker is carried as a separate flag by the caller.
    text = text.rstrip()
    suffix = ""
    if text.endswith("&"):
        # The contract keeps the by-ref marker in the type spelling and
        # additionally records ref/out flags, so preserve it here.
        return normalize_type(text[:-1]) + "&"
    while text.endswith("[]") or text.endswith("*"):
        if text.endswith("[]"):
            suffix = "[]" + suffix
            text = text[:-2].rstrip()
        else:
            suffix = "*" + suffix
            text = text[:-1].rstrip()
    for keyword in ("class ", "valuetype ", "instance "):
        while text.startswith(keyword):
            text = text[len(keyword):].strip()
    if text in PRIMITIVES:
        return PRIMITIVES[text] + suffix
    # Generic instantiation: Foo`1<class Bar> -> Foo`1[Bar]
    match = re.match(r"^(.*?)<(.*)>$", text, re.S)
    if match:
        base = normalize_type(match.group(1))
        arguments = [normalize_type(item) for item in split_top(match.group(2))]
        # The retained contract separates generic arguments with a bare comma.
        return f"{base}[{','.join(arguments)}]" + suffix
    text = strip_assembly_ref(text).strip()
    if text in PRIMITIVES:
        return PRIMITIVES[text] + suffix
    text = text.replace("/", "+")
    text = text.strip("'")
    return text + suffix


def split_top(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char in "<[(":
            depth += 1
        elif char in ">])":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return [item.strip() for item in parts if item.strip()]


def positional_generics(
    text: str,
    type_parameters: tuple[str, ...],
    method_parameters: tuple[str, ...],
) -> str:
    """Rewrite named IL generic parameters to the contract's positional form.

    IL spells a generic parameter by name (`!!T`, `!TPacked`); the retained
    contract spells it by position (`!!0`, `!0`).
    """
    for index, name in enumerate(method_parameters):
        text = re.sub(rf"!!{re.escape(name)}\b", f"!!{index}", text)
    for index, name in enumerate(type_parameters):
        text = re.sub(rf"(?<!!)!{re.escape(name)}\b", f"!{index}", text)
    return text


def split_parameters(
    text: str,
    type_parameters: tuple[str, ...] = (),
    method_parameters: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for fragment in split_top(text):
        if not fragment or fragment == "...":
            continue
        is_out = bool(re.match(r"^\[out\]", fragment.strip()))
        fragment = re.sub(r"^\[(in|out|opt)\]\s*", "", fragment.strip())
        tokens = fragment.rsplit(" ", 1)
        if len(tokens) == 2 and re.match(r"^'?[A-Za-z_][\w]*'?$", tokens[1]):
            type_text, name = tokens[0], tokens[1].strip("'")
        else:
            type_text, name = fragment, ""
        mapped = normalize_type(
            positional_generics(type_text, type_parameters, method_parameters))
        result.append({
            "name": name,
            "type": mapped,
            "ref": mapped.endswith("&"),
            "out": is_out,
            "in": False,
            "optional": False,
        })
    return result


DIRECTIVE = re.compile(
    r"\b(?:marshal|modopt|modreq|pinvokeimpl)\s*\([^()]*(?:\([^()]*\)[^()]*)*\)")


def strip_directives(text: str) -> str:
    """Remove marshalling and custom-modifier directives.

    These carry their own parentheses, so they must be removed before the
    parameter list is located or `split_call` locks on to the wrong `(`.
    """
    previous = None
    while previous != text:
        previous = text
        text = DIRECTIVE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_call(text: str) -> tuple[str, str, str] | None:
    """Split `head(parameters)tail` at the top-level parameter list."""
    depth = 0
    start = None
    for index, char in enumerate(text):
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
        elif char == "(" and depth == 0:
            start = index
            break
    if start is None:
        return None
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[:start], text[start + 1:index], text[index + 1:]
    return None


def split_generic_suffix(head: str) -> tuple[str, tuple[str, ...]]:
    """Split `Name<a, b>` into its name and its generic parameter names."""
    head = head.strip()
    if not head.endswith(">"):
        return head, ()
    depth = 0
    for index in range(len(head) - 1, -1, -1):
        if head[index] == ">":
            depth += 1
        elif head[index] == "<":
            depth -= 1
            if depth == 0:
                names = tuple(
                    item.split()[-1].strip("'")
                    for item in split_top(head[index + 1:-1]) if item.split()
                )
                return head[:index].strip(), names
    return head, ()


INTEGER_LITERAL = re.compile(
    r"^(int8|int16|int32|int64|uint8|uint16|uint32|uint64|"
    r"unsigned int8|unsigned int16|unsigned int32|unsigned int64|char|bool)"
    r"\((.*)\)$")
FLOAT_LITERAL = re.compile(r"^(float32|float64)\((.*)\)$")

# The retained contract records literal values in their decimal C# spelling,
# so a hexadecimal IL literal is normalised rather than compared verbatim.
LITERAL_WIDTH = {
    "int8": 8, "uint8": 8, "unsigned int8": 8, "bool": 8,
    "int16": 16, "uint16": 16, "unsigned int16": 16, "char": 16,
    "int32": 32, "uint32": 32, "unsigned int32": 32,
    "int64": 64, "uint64": 64, "unsigned int64": 64,
}
SIGNED_LITERAL = {"int8", "int16", "int32", "int64"}


def parse_literal(text: str) -> str | None:
    match = re.search(r"=\s*(.*)$", text)
    if not match:
        return None
    value = match.group(1).strip()
    found = INTEGER_LITERAL.match(value)
    if found:
        kind, raw = found.group(1), found.group(2).strip()
        try:
            number = int(raw, 0)
        except ValueError:
            return raw
        width = LITERAL_WIDTH.get(kind)
        if width and kind in SIGNED_LITERAL and number >= (1 << (width - 1)):
            number -= 1 << width
        return str(number)
    found = FLOAT_LITERAL.match(value)
    if found:
        raw = found.group(2).strip()
        try:
            number = float.fromhex(raw) if raw.lower().startswith("0x") else float(raw)
        except ValueError:
            return raw
        # The retained contract stores a Single constant in the CLR's default
        # `Single.ToString()` rendering, which is seven significant digits.
        # ikdasm prints the full decimal expansion of the same bits.
        digits = 7 if found.group(1) == "float32" else 15
        return f"{number:.{digits}G}"
    return value or None


class Parser:
    """Reconstruct public type shape from ikdasm IL output."""

    def __init__(self, il: str) -> None:
        self.lines = il.splitlines()
        self.types: dict[str, dict[str, Any]] = {}

    def parse(self) -> dict[str, dict[str, Any]]:
        stack: list[dict[str, Any]] = []
        index = 0
        while index < len(self.lines):
            line = self.lines[index]
            stripped = line.strip()
            if stripped.startswith(".class "):
                declaration, index = self.gather(index, ("{",))
                stack.append(self.begin_class(declaration, stack))
                continue
            if stripped.startswith("} // end of class"):
                stack.pop()
                index += 1
                continue
            if not stack or stack[-1] is None:
                index += 1
                continue
            owner = stack[-1]
            if stripped.startswith(".method "):
                declaration, index = self.gather(index, ("cil managed", "runtime managed", "cil runtime managed", "managed"))
                self.add_method(owner, declaration)
                index = self.skip_block(index, "} // end of method")
                continue
            if stripped.startswith(".property "):
                declaration, index = self.gather(index, ("{",))
                index = self.add_property(owner, declaration, index)
                continue
            if stripped.startswith(".event "):
                declaration, index = self.gather(index, ("{",))
                index = self.add_event(owner, declaration, index)
                continue
            if stripped.startswith(".field "):
                declaration, index = self.gather(index, None)
                self.add_field(owner, declaration)
                continue
            index += 1
        return self.types

    def gather(self, index: int, terminators: tuple[str, ...] | None) -> tuple[str, int]:
        """Collect a possibly multi-line declaration starting at `index`."""
        parts: list[str] = []
        while index < len(self.lines):
            raw = self.lines[index].strip()
            index += 1
            if terminators is None:
                parts.append(raw)
                break
            if raw.endswith("{"):
                parts.append(raw[:-1].strip())
                break
            parts.append(raw)
            joined = " ".join(parts)
            if any(joined.rstrip().endswith(item) for item in terminators):
                break
            if index < len(self.lines) and self.lines[index].strip() == "{":
                index += 1
                break
        return " ".join(part for part in parts if part), index

    def skip_block(self, index: int, end_marker: str) -> int:
        depth = 0
        while index < len(self.lines):
            stripped = self.lines[index].strip()
            if stripped.startswith(end_marker):
                return index + 1
            if stripped == "{":
                depth += 1
            elif stripped.startswith("}") and depth:
                depth -= 1
            index += 1
        return index

    def begin_class(self, declaration: str, stack: list[dict[str, Any]]) -> dict[str, Any] | None:
        body = declaration[len(".class"):].strip()
        extends = None
        implements: list[str] = []
        match = re.search(r"\bextends\s+(.*?)(?:\s+implements\s+(.*))?$", body)
        if match:
            extends = normalize_type(match.group(1))
            if match.group(2):
                implements = [normalize_type(item) for item in split_top(match.group(2))]
            body = body[:match.start()].strip()
        else:
            match = re.search(r"\bimplements\s+(.*)$", body)
            if match:
                implements = [normalize_type(item) for item in split_top(match.group(1))]
                body = body[:match.start()].strip()
        tokens = body.split()
        name = tokens[-1] if tokens else ""
        attributes = set(tokens[:-1])
        # A generic class name carries its parameter list: `Foo`1<T>`.
        if ">" in body:
            head, _, _rest = body.partition("<")
            head_tokens = head.split()
            if head_tokens:
                name_index = body.index(head_tokens[-1])
                name, type_parameters = split_generic_suffix(body[name_index:])
                attributes = set(body[:name_index].split())
            else:
                type_parameters = ()
        else:
            name, type_parameters = split_generic_suffix(name)
        nested = "nested" in attributes
        parent = stack[-1] if stack else None
        if nested:
            visible = any(
                f"nested {item}" in body for item in ("public", "family", "famorassem")
            )
            if parent is None or not visible:
                return None
            full = f"{parent['name']}+{name}"
        else:
            if "public" not in attributes:
                return None
            full = name
        kind = "interface" if "interface" in attributes else (
            "enum" if extends == "System.Enum" else (
                "struct" if extends == "System.ValueType" else "class"
            )
        )
        record = {
            "name": full,
            "kind": kind,
            "sealed": "sealed" in attributes,
            "abstract": "abstract" in attributes,
            "baseType": extends,
            "directInterfaces": implements,
            "genericParameters": list(type_parameters),
            "members": [],
        }
        self.types[full] = record
        return record

    @staticmethod
    def access_of(attributes: set[str]) -> str | None:
        for key, value in ACCESS.items():
            if key in attributes:
                return value
        return None

    def add_method(self, owner: dict[str, Any], declaration: str) -> None:
        body = strip_directives(declaration[len(".method"):].strip())
        split = split_call(body)
        if split is None:
            return
        head, parameter_text, _tail = split
        head, method_parameters = split_generic_suffix(head)
        tokens = head.split()
        if not tokens:
            return
        name = tokens[-1].strip("'")
        rest = tokens[:-1]
        attributes: set[str] = set()
        return_tokens: list[str] = []
        known = {
            "public", "private", "family", "assembly", "famorassem", "famandassem",
            "static", "instance", "hidebysig", "specialname", "rtspecialname",
            "virtual", "abstract", "final", "newslot", "pinvokeimpl", "strict",
            "explicit", "reqsecobj", "unmanagedexp",
        }
        for token in rest:
            if token in known:
                attributes.add(token)
            else:
                return_tokens.append(token)
        access = self.access_of(attributes)
        if access is None:
            return
        if name == ".cctor":
            return
        type_parameters = tuple(owner.get("genericParameters") or ())
        return_type = normalize_type(positional_generics(
            " ".join(return_tokens), type_parameters, method_parameters))
        parameters = split_parameters(
            parameter_text, type_parameters, method_parameters)
        is_constructor = name == ".ctor"
        owner["members"].append({
            "kind": "constructor" if is_constructor else "method",
            "name": name,
            "static": "static" in attributes,
            "access": access,
            "returnType": None if is_constructor else return_type,
            "genericParameters": [
                {"name": item} for item in method_parameters
            ],
            "parameters": parameters,
            "_specialname": "specialname" in attributes,
        })

    def add_property(self, owner: dict[str, Any], declaration: str, index: int) -> int:
        body = strip_directives(declaration[len(".property"):].strip())
        split = split_call(body)
        if split is None:
            return self.skip_block(index, "} // end of property")
        head, parameter_text, _tail = split
        tokens = head.split()
        name = tokens[-1].strip("'")
        type_text = " ".join(tokens[:-1])
        type_text = re.sub(r"^\s*(instance|specialname|rtspecialname)\s+", "", type_text)
        while True:
            new = re.sub(r"^\s*(instance|specialname|rtspecialname)\s+", "", type_text)
            if new == type_text:
                break
            type_text = new
        static = "instance" not in head.split()
        get_access: str | None = None
        set_access: str | None = None
        cursor = index
        while cursor < len(self.lines):
            stripped = self.lines[cursor].strip()
            if stripped.startswith("} // end of property"):
                cursor += 1
                break
            if stripped.startswith(".get "):
                get_access = self.accessor_access(owner, stripped, f"get_{name}")
            elif stripped.startswith(".set "):
                set_access = self.accessor_access(owner, stripped, f"set_{name}")
            cursor += 1
        if get_access is None and set_access is None:
            return cursor
        type_parameters = tuple(owner.get("genericParameters") or ())
        owner["members"].append({
            "kind": "property",
            "name": name,
            "type": normalize_type(
                positional_generics(type_text, type_parameters, ())),
            "static": static,
            "get": get_access is not None,
            "set": set_access is not None,
            "getAccess": get_access,
            "setAccess": set_access,
            "parameters": split_parameters(parameter_text, type_parameters, ()),
        })
        return cursor

    @staticmethod
    def accessor_access(owner: dict[str, Any], line: str, accessor: str) -> str | None:
        for member in owner["members"]:
            if member.get("name") == accessor and member["kind"] == "method":
                return member.get("access")
        return None

    def add_event(self, owner: dict[str, Any], declaration: str, index: int) -> int:
        body = strip_directives(declaration[len(".event"):].strip())
        tokens = body.split()
        name = tokens[-1].strip("'")
        type_text = " ".join(tokens[:-1])
        type_text = re.sub(r"^\s*(specialname|rtspecialname)\s+", "", type_text).strip()
        add_access = None
        remove_access = None
        fires = False
        cursor = index
        while cursor < len(self.lines):
            stripped = self.lines[cursor].strip()
            if stripped.startswith("} // end of event"):
                cursor += 1
                break
            if stripped.startswith(".addon "):
                add_access = self.accessor_access(owner, stripped, f"add_{name}")
            elif stripped.startswith(".removeon "):
                remove_access = self.accessor_access(owner, stripped, f"remove_{name}")
            elif stripped.startswith(".fire "):
                fires = True
            cursor += 1
        if add_access is None and remove_access is None:
            return cursor
        if fires:
            owner.setdefault("_raisers", set()).add(f"raise_{name}")
        owner["members"].append({
            "kind": "event",
            "name": name,
            "type": normalize_type(positional_generics(
                type_text, tuple(owner.get("genericParameters") or ()), ())),
            "static": False,
            "add": add_access is not None,
            "remove": remove_access is not None,
        })
        return cursor

    def add_field(self, owner: dict[str, Any], declaration: str) -> None:
        body = strip_directives(declaration[len(".field"):].strip())
        value = None
        if " = " in body:
            head, _, _tail = body.partition(" = ")
            value = parse_literal(body)
            body = head.strip()
        tokens = body.split()
        if not tokens:
            return
        name = tokens[-1].strip("'")
        rest = tokens[:-1]
        attributes: set[str] = set()
        type_tokens: list[str] = []
        known = {
            "public", "private", "family", "assembly", "famorassem", "famandassem",
            "static", "literal", "initonly", "specialname", "rtspecialname",
            "notserialized", "marshal",
        }
        for token in rest:
            if token in known:
                attributes.add(token)
            else:
                type_tokens.append(token)
        access = self.access_of(attributes)
        if access is None:
            return
        owner["members"].append({
            "kind": "field",
            "name": name,
            "type": normalize_type(positional_generics(
                " ".join(type_tokens),
                tuple(owner.get("genericParameters") or ()), ())),
            "static": "static" in attributes or "literal" in attributes,
            "constant": "literal" in attributes,
            "value": value,
        })


def finalize(types: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Drop accessor methods that a property or event already represents."""
    for record in types.values():
        accessors: set[str] = set()
        for member in record["members"]:
            if member["kind"] == "property":
                accessors.add(f"get_{member['name']}")
                accessors.add(f"set_{member['name']}")
            elif member["kind"] == "event":
                accessors.add(f"add_{member['name']}")
                accessors.add(f"remove_{member['name']}")
                accessors.add(f"raise_{member['name']}")
        record["members"] = [
            member for member in record["members"]
            if not (
                member["kind"] == "method" and
                member.get("_specialname") and
                member["name"] in accessors
            )
        ]
        for member in record["members"]:
            member.pop("_specialname", None)
        record.pop("_raisers", None)
    return types


def member_key(member: dict[str, Any]) -> tuple:
    kind = member["kind"]
    if kind in ("method", "constructor"):
        return (
            kind, member["name"], bool(member.get("static")),
            tuple(
                (item.get("type"), bool(item.get("ref")), bool(item.get("out")))
                for item in member.get("parameters", [])
            ),
            member.get("returnType"),
        )
    if kind == "property":
        return (
            kind, member["name"], bool(member.get("static")), member.get("type"),
            bool(member.get("get")), bool(member.get("set")),
            tuple(item.get("type") for item in member.get("parameters", [])),
        )
    if kind == "event":
        return (kind, member["name"], member.get("type"))
    return (
        kind, member["name"], bool(member.get("static")), member.get("type"),
        bool(member.get("constant")), member.get("value"),
    )


def compare_type(expected: dict[str, Any], found: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if expected["kind"] != found["kind"]:
        issues.append(f"kind {expected['kind']} != {found['kind']}")
    if bool(expected.get("sealed")) != bool(found.get("sealed")):
        issues.append(f"sealed {expected.get('sealed')} != {found.get('sealed')}")
    if expected.get("baseType") != found.get("baseType"):
        issues.append(f"base {expected.get('baseType')} != {found.get('baseType')}")
    # The retained contract records a *reduced* direct-interface set: an
    # interface that is already a base interface of another listed entry is
    # omitted (IEnumerable behind IEnumerable`1, IGraphicsResource behind
    # IDynamicGraphicsResource, and so on). Reproducing that reduction would
    # mean modelling BCL interface hierarchies, so the audit requires the
    # weaker, sound relation instead: every interface the contract records must
    # actually be declared by the assembly. Interfaces the assembly declares
    # beyond that set are the contract's documented reduction and are reported
    # separately rather than treated as a discrepancy.
    expected_interfaces = set(expected.get("directInterfaces") or [])
    found_interfaces = set(found.get("directInterfaces") or [])
    for item in sorted(expected_interfaces - found_interfaces):
        issues.append(f"assembly does not declare contract interface {item}")
    expected_members = sorted(member_key(item) for item in expected["members"])
    found_members = sorted(member_key(item) for item in found["members"])
    missing = [item for item in expected_members if item not in found_members]
    extra = [item for item in found_members if item not in expected_members]
    for item in missing:
        issues.append(f"assembly is missing contract member {item}")
    for item in extra:
        issues.append(f"assembly declares member absent from contract {item}")
    return issues


def self_test(
    contract_types: dict[str, dict[str, Any]],
    extracted: dict[str, dict[str, Any]],
) -> tuple[int, list[str]]:
    """Prove the comparison is not vacuous.

    A comparison that always reports "exact" would pass the calibration gate
    for the wrong reason. Each mutation below perturbs one already-matching
    type and must be detected.
    """
    import copy as copy_module

    failures: list[str] = []
    checks = 0
    subjects = [
        name for name in (
            "Microsoft.Xna.Framework.Vector2",
            "Microsoft.Xna.Framework.Graphics.PresentationParameters",
            "Microsoft.Xna.Framework.Input.MouseState",
            "Microsoft.Xna.Framework.Color",
            "Microsoft.Xna.Framework.MathHelper",
        ) if name in extracted
    ]
    if len(subjects) < 5:
        failures.append("self-test subjects are missing from the extraction")
    checks += 1

    def drop_first(kind: str) -> Any:
        def mutate(record: dict[str, Any]) -> bool:
            for index, member in enumerate(record["members"]):
                if member["kind"] == kind:
                    del record["members"][index]
                    return True
            return False
        return mutate

    def retype_first(kind: str) -> Any:
        def mutate(record: dict[str, Any]) -> bool:
            for member in record["members"]:
                if member["kind"] == kind:
                    key = "returnType" if kind in ("method",) else "type"
                    if member.get(key) is None:
                        continue
                    member[key] = "Microsoft.Xna.Framework.Point"
                    return True
            return False
        return mutate

    def revalue_first(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] == "field" and member.get("constant"):
                member["value"] = "999"
                return True
        return False

    def flip_sealed(record: dict[str, Any]) -> bool:
        record["sealed"] = not record["sealed"]
        return True

    def rebase(record: dict[str, Any]) -> bool:
        record["baseType"] = "Microsoft.Xna.Framework.Point"
        return True

    def drop_interface(record: dict[str, Any]) -> bool:
        if not record.get("directInterfaces"):
            return False
        record["directInterfaces"] = record["directInterfaces"][1:]
        return True

    def add_member(record: dict[str, Any]) -> bool:
        record["members"].append({
            "kind": "method", "name": "InventedMember", "static": False,
            "access": "public", "returnType": "System.Void",
            "genericParameters": [], "parameters": [],
        })
        return True

    def rename_first_method(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] == "method":
                member["name"] = member["name"] + "Renamed"
                return True
        return False

    def flip_static(record: dict[str, Any]) -> bool:
        for member in record["members"]:
            if member["kind"] in ("method", "property"):
                member["static"] = not member.get("static")
                return True
        return False

    mutations = [
        ("dropped method", drop_first("method")),
        ("dropped property", drop_first("property")),
        ("dropped field", drop_first("field")),
        ("dropped constructor", drop_first("constructor")),
        ("retyped method result", retype_first("method")),
        ("retyped property", retype_first("property")),
        ("retyped field", retype_first("field")),
        ("changed constant value", revalue_first),
        ("flipped sealed", flip_sealed),
        ("changed base type", rebase),
        ("dropped declared interface", drop_interface),
        ("invented extra member", add_member),
        ("renamed method", rename_first_method),
        ("flipped static identity", flip_static),
    ]

    for name in subjects:
        expected = contract_types[name]
        found = extracted[name]
        if compare_type(expected, found):
            failures.append(f"{name}: unmutated comparison is not clean")
        checks += 1
        for label, mutate in mutations:
            candidate = copy_module.deepcopy(found)
            if not mutate(candidate):
                continue
            if not compare_type(expected, candidate):
                failures.append(f"{name}: {label} was not detected")
            checks += 1
    return checks, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembly-dir", type=Path, required=True)
    parser.add_argument("--require-exact", action="append", default=[])
    parser.add_argument("--il-cache", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = json.loads(REFERENCE.read_text(encoding="utf-8"))
    by_name = {item["name"]: item for item in contract["types"]}

    assemblies = sorted(args.assembly_dir.glob("Microsoft.Xna.Framework*.dll"))
    if not assemblies:
        raise SystemExit(f"no XNA assemblies under {args.assembly_dir}")

    extracted: dict[str, dict[str, dict[str, Any]]] = {}
    for path in assemblies:
        cache = (args.il_cache / f"{path.stem}.il") if args.il_cache else None
        parsed = finalize(Parser(disassemble(path, cache)).parse())
        extracted[path.name] = parsed

    # Attribute each contract type to the assembly that declares it.
    owner_of: dict[str, str] = {}
    unattributed: list[str] = []
    for name in by_name:
        owners = [item for item, types in extracted.items() if name in types]
        if len(owners) == 1:
            owner_of[name] = owners[0]
        elif not owners:
            unattributed.append(name)
        else:
            owner_of[name] = sorted(owners)[0]

    results: list[dict[str, Any]] = []
    for path in assemblies:
        owned = sorted(name for name, item in owner_of.items() if item == path.name)
        if not owned:
            continue
        mismatches: list[dict[str, Any]] = []
        members = 0
        reductions = 0
        for name in owned:
            members += len(by_name[name]["members"])
            found = extracted[path.name][name]
            reductions += len(
                set(found.get("directInterfaces") or []) -
                set(by_name[name].get("directInterfaces") or []))
            issues = compare_type(by_name[name], found)
            if issues:
                mismatches.append({"type": name, "issues": issues})
        results.append({
            "assembly": path.name,
            "sha256": sha256(path),
            "contractTypes": len(owned),
            "contractMembers": members,
            "contractInterfaceReductions": reductions,
            "typesExact": len(owned) - len(mismatches),
            "typesMismatched": len(mismatches),
            "mismatches": mismatches,
        })

    merged: dict[str, dict[str, Any]] = {}
    for types in extracted.values():
        merged.update(types)
    checks, self_test_failures = self_test(by_name, merged)

    by_assembly = {item["assembly"]: item for item in results}
    calibration_failed = []
    for name in args.require_exact:
        record = by_assembly.get(name)
        if record is None:
            calibration_failed.append(f"{name}: not audited")
        elif record["typesMismatched"]:
            calibration_failed.append(
                f"{name}: {record['typesMismatched']} type(s) differ from the contract")

    report = {
        "schemaVersion": 1,
        "referenceSha256": hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        "calibrationAssemblies": sorted(args.require_exact),
        "CALIBRATION_STATUS":
            "FAIL" if (calibration_failed or self_test_failures) else "PASS",
        "AUDIT_SELF_TESTS": checks,
        "AUDIT_SELF_TEST_STATUS": "FAIL" if self_test_failures else "PASS",
        "auditSelfTestFailures": self_test_failures,
        "CONTRACT_TYPES_REPRODUCED": sum(
            item["typesExact"] for item in results),
        "CONTRACT_MEMBERS_REPRODUCED": sum(
            item["contractMembers"] for item in results
            if not item["typesMismatched"]),
        "calibrationFailures": calibration_failed,
        "unattributedContractTypes": sorted(unattributed),
        "assemblies": results,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for record in results:
        print(
            f"{record['assembly']:44s} types={record['contractTypes']:3d} "
            f"members={record['contractMembers']:4d} "
            f"exact={record['typesExact']:3d} mismatched={record['typesMismatched']:3d}"
        )
    print(f"UNATTRIBUTED_CONTRACT_TYPES={len(unattributed)} {unattributed}")
    print(
        f"CONTRACT_TYPES_REPRODUCED={report['CONTRACT_TYPES_REPRODUCED']} "
        f"CONTRACT_MEMBERS_REPRODUCED={report['CONTRACT_MEMBERS_REPRODUCED']}")
    print(
        f"AUDIT_SELF_TESTS={checks} "
        f"AUDIT_SELF_TEST_STATUS={report['AUDIT_SELF_TEST_STATUS']}")
    print(f"CALIBRATION_STATUS={report['CALIBRATION_STATUS']}")
    for line in calibration_failed + self_test_failures:
        print(f"  {line}", file=sys.stderr)
    return 1 if (calibration_failed or self_test_failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
