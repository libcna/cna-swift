#!/usr/bin/env python3
"""Compiler-Symbol-Graph verifier for the strict CNA-Swift XNA projection."""

from __future__ import annotations

import argparse
import collections
import copy
import dataclasses
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "tools/api_compat/reference/xna40-windows-runtime-contract.json"
RULES = ROOT / "tools/api_compat/mapping-rules.json"
ACCESSOR_FALLIBILITY = ROOT / "tools/api_compat/reference/xna40-accessor-fallibility.json"

# The general CLR-property-accessor projection. Swift property and subscript
# syntax is used for exactly the accessors Swift can express: a getter always
# keeps it, gaining `get throws` when the accessor is fallible, and a writer
# keeps `set` only when Swift permits one -- which the compiler refuses beside
# a throwing getter, and which cannot throw at all. Every other writer becomes
# a `Set<Name>` method carrying the setter's own fallibility. An indexed
# property whose writer is a method spells its reader `Item(...)` beside
# `SetItem(...)`, the established rule this generalises, so the two halves of
# one CLR member stay one named pair.
WRITER_ABSENT = "absent"
WRITER_PROPERTY = "set"
WRITER_METHOD = "method"

CATEGORIES = (
    "MISSING_TYPE", "MISSING_MEMBER", "UNEXPECTED_TYPE", "UNEXPECTED_MEMBER",
    "TYPE_KIND_MISMATCH", "BASE_MAPPING_MISMATCH", "INTERFACE_MAPPING_MISMATCH",
    "FIELD_MAPPING_MISMATCH", "PROPERTY_MAPPING_MISMATCH",
    "METHOD_SIGNATURE_MAPPING_MISMATCH", "PARAMETER_MAPPING_MISMATCH",
    "RETURN_MAPPING_MISMATCH", "OVERLOAD_MAPPING_MISMATCH", "GENERIC_MAPPING_MISMATCH",
    "ENUM_VALUE_MISMATCH", "FLAGS_MAPPING_MISMATCH", "EVENT_MAPPING_MISMATCH",
    "OPERATOR_MAPPING_MISMATCH", "REF_OUT_MAPPING_MISMATCH", "LANGUAGE_MAPPING_MISMATCH",
    "INTERNAL_TYPE_LEAK", "RAW_HANDLE_LEAK", "PUBLIC_NATIVE_FFI_LEAK",
    "UNMEASURED_STRUCTURAL_CATEGORY",
)

TYPE_KINDS = {
    "swift.class": "class",
    "swift.struct": "struct",
    "swift.protocol": "protocol",
    "swift.enum": "enum",
}

# CLR encodes an event as add_/remove_/raise_ accessor methods. Zero reference
# members in the pinned contract carry these prefixes, so any such name in the
# strict XNA surface is a leaked CLR accessor, never an XNA identity. Kept in
# step with `eventAccessorPrefixes` by a self-test.
EVENT_ACCESSOR_PREFIXES = ("add_", "remove_", "raise_")

# A CopyTo destination array is caller-owned storage. `IList<T>` inherits
# `ICollection<T>`, so a type whose pinned direct interface is either one has
# the same caller-owned destination and the same inout projection. Kept in step
# with `collectionCopyToArrayMutationMapping` by a self-test.
COLLECTION_COPY_INTERFACES = (
    "System.Collections.Generic.ICollection`1[",
    "System.Collections.Generic.IList`1[",
)

OPERATOR_FROM_SWIFT = {
    "==": "op_Equality", "!=": "op_Inequality", "+": "op_Addition",
    "*": "op_Multiply", "/": "op_Division",
}


@dataclasses.dataclass
class Member:
    owner: str
    kind: str
    name: str
    static: bool
    parameters: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()
    directions: tuple[str, ...] = ()
    return_type: str = "Void"
    mutable: bool | None = None
    self_mutating: bool | None = None
    raw_value: int | None = None
    declaration: str = ""
    identifier: str = ""
    parameter_names: tuple[str, ...] = ()
    verify_parameter_order: bool = False
    getter_throws: bool | None = None
    writer_kind: str | None = None
    writer_name: str | None = None
    writer_throws: bool | None = None
    writer_self_mutating: bool | None = None
    writer_member: Any = None

    @property
    def display(self) -> str:
        params = ",".join(
            f"{direction + ' ' if direction else ''}{label}:{kind}"
            for label, kind, direction in zip(self.labels, self.parameters, self.directions)
        )
        return f"{self.owner}.{self.name}({params})"


@dataclasses.dataclass
class TypeModel:
    name: str
    kind: str
    flags: bool = False
    base: str | None = None
    interfaces: tuple[str, ...] = ()
    generic_count: int = 0
    generic_parameters: tuple[str, ...] = ()
    declaration: str = ""
    identifier: str = ""
    members: list[Member] = dataclasses.field(default_factory=list)
    raw_type: str | None = None
    verify_raw_type: bool = False
    access: str = ""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def map_type_name(name: str, rules: dict[str, Any]) -> str:
    collision = rules["genericCollisionTypeNames"].get(name)
    if collision:
        return collision
    name = name.replace("+", ".")
    return re.sub(r"`\d+", "", name)


def split_generic_arguments(text: str) -> list[str]:
    result: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "[<":
            depth += 1
        elif char in "]>":
            depth -= 1
        elif char == "," and depth == 0:
            result.append(text[start:index])
            start = index + 1
    result.append(text[start:])
    return [item.strip() for item in result if item.strip()]


def map_clr_type(
    clr: str | None,
    rules: dict[str, Any],
    generic_parameters: tuple[str, ...] = (),
) -> str:
    if clr is None:
        return "Void"
    text = clr.rstrip("&")
    placeholder = re.fullmatch(r"!(\d+)", text)
    if placeholder and int(placeholder.group(1)) < len(generic_parameters):
        return generic_parameters[int(placeholder.group(1))]
    if text.endswith("[]"):
        return f"[{map_clr_type(text[:-2], rules, generic_parameters)}]"
    direct = rules["typeMappings"].get(text)
    if direct:
        return direct
    nullable = re.fullmatch(r"System\.Nullable`1\[(.+)]", text)
    if nullable:
        return f"{map_clr_type(nullable.group(1), rules, generic_parameters)}?"
    enumerable = re.fullmatch(r"System\.Collections\.Generic\.IEnumerable`1\[(.+)]", text)
    if enumerable:
        return f"[{map_clr_type(enumerable.group(1), rules, generic_parameters)}]"
    enumerator = re.fullmatch(r"System\.Collections\.Generic\.IEnumerator`1\[(.+)]", text)
    if enumerator:
        return f"CNAEnumerator<{map_clr_type(enumerator.group(1), rules, generic_parameters)}>"
    # Every public event in the pinned contract is System.EventHandler<TArgs>.
    # The delegate is not projected; the event is one get-only property of the
    # consumer view type. See `eventMapping`.
    handler = re.fullmatch(r"System\.EventHandler`1\[(.+)]", text)
    if handler:
        return f"CNAEvent<{map_clr_type(handler.group(1), rules, generic_parameters)}>"
    generic = re.fullmatch(r"(.+)`(\d+)\[(.*)]", text)
    if generic:
        base = map_type_name(f"{generic.group(1)}`{generic.group(2)}", rules)
        args = ", ".join(
            map_clr_type(item, rules, generic_parameters)
            for item in split_generic_arguments(generic.group(3))
        )
        return f"{base}<{args}>"
    return map_type_name(text, rules)


def load_accessor_fallibility(rules: dict[str, Any]) -> dict[tuple[str, str], dict[str, bool]]:
    """The pinned per-accessor fallibility verdicts, keyed by CLR identity.

    Regenerated by `tools/api_compat/accessor_fallibility.py` from the CIL of
    the hash-registered assemblies and pinned here so the verifier runs without
    any Microsoft binary. The digest is checked exactly as the contract's is.
    """
    raw = ACCESSOR_FALLIBILITY.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    pinned = rules.get("accessorFallibilitySha256")
    if pinned and digest != pinned:
        raise SystemExit(
            f"accessor fallibility reference digest {digest} does not match the "
            f"pinned {pinned}")
    document = json.loads(raw.decode("utf-8"))
    return {
        (item["type"], item["property"]): {
            "getter": bool(item["getter"]["fallible"]),
            "setter": bool(item["setter"]["fallible"]),
        }
        for item in document["entries"]
    }


def accessor_projection(
    source: dict[str, Any], verdict: dict[str, bool] | None,
) -> tuple[bool, str, bool]:
    """(getter throws, writer kind, writer throws) for one CLR property."""
    getter_throws = bool(verdict and verdict["getter"])
    if not source.get("set"):
        return getter_throws, WRITER_ABSENT, False
    setter_throws = bool(verdict and verdict["setter"])
    if setter_throws or getter_throws:
        return getter_throws, WRITER_METHOD, setter_throws
    return getter_throws, WRITER_PROPERTY, False


def writer_method_name(property_name: str, indexed: bool) -> str:
    return "SetItem" if indexed else f"Set{property_name}"


def member_is_omitted(member: dict[str, Any]) -> bool:
    return (member["kind"] == "field" and member["name"] == "value__") or member["name"] == "Finalize"


def expected_member(
    owner: str,
    source: dict[str, Any],
    rules: dict[str, Any],
    owner_kind: str,
    owner_generic_parameters: tuple[str, ...] = (),
    owner_direct_interfaces: tuple[str, ...] = (),
    accessor_verdict: dict[str, bool] | None = None,
) -> Member:
    kind = source["kind"]
    name = source["name"]
    if kind == "constructor":
        mapped_name = ".ctor"
    elif kind == "property" and source.get("parameters"):
        mapped_name = "Item"
    else:
        mapped_name = name

    parameters = source.get("parameters", [])
    labels: list[str] = []
    directions: list[str] = []
    types: list[str] = []
    for index, parameter in enumerate(parameters):
        if kind == "constructor":
            labels.append(parameter["name"] if owner_kind == "class" else "_")
        else:
            labels.append("_" if index == 0 or name.startswith("op_") else parameter["name"])
        collection_copy_destination = (
            name == "CopyTo" and parameter.get("name") == "array" and
            parameter.get("type", "").endswith("[]") and
            any(
                item.startswith(COLLECTION_COPY_INTERFACES)
                for item in owner_direct_interfaces
            )
        )
        direction = "inout" if (
            parameter.get("ref") or parameter.get("out") or
            (
                parameter.get("name") in rules.get("arrayMutationParameterNames", ["destinationArray"])
                and parameter.get("type", "").endswith("[]")
            ) or collection_copy_destination
        ) else ""
        directions.append(direction)
        mapped_parameter_type = map_clr_type(
            parameter["type"], rules, owner_generic_parameters,
        )
        optional_reference = any(
            item.get("owner") == owner and
            item.get("member") == mapped_name and
            item.get("parameter") == parameter.get("name")
            for item in rules.get("optionalReferenceParameters", [])
        )
        if optional_reference and not mapped_parameter_type.endswith("?"):
            mapped_parameter_type += "?"
        types.append(mapped_parameter_type)

    mutable: bool | None = None
    getter_throws: bool | None = None
    writer_kind: str | None = None
    writer_name: str | None = None
    writer_throws: bool | None = None
    writer_self_mutating: bool | None = None
    if kind == "property":
        getter_throws, writer_kind, writer_throws = accessor_projection(
            source, accessor_verdict,
        )
        mutable = writer_kind == WRITER_PROPERTY
        if writer_kind == WRITER_METHOD:
            writer_name = writer_method_name(name, bool(source.get("parameters")))
            if owner_kind == "interface":
                writer_self_mutating = (
                    f"{owner}.{writer_name}" in
                    rules.get("mutatingProtocolRequirements", [])
                )
    elif kind == "field":
        mutable = not bool(source.get("constant"))
    elif kind == "event":
        # A CLR event has add/remove accessors and no setter. The projected
        # Swift property is therefore get-only, and a writable one is an
        # EVENT_MAPPING_MISMATCH rather than a silent difference.
        mutable = False

    raw: int | None = None
    if kind == "field" and source.get("value") is not None:
        try:
            raw = int(source["value"], 0)
        except (TypeError, ValueError):
            try:
                raw = int(source["value"])
            except (TypeError, ValueError):
                raw = None

    return Member(
        owner=owner,
        kind=kind,
        name=mapped_name,
        static=bool(source.get("static")),
        parameters=tuple(types),
        labels=tuple(labels),
        directions=tuple(directions),
        return_type=map_clr_type(
            source.get("returnType") or source.get("type"), rules,
            owner_generic_parameters,
        ),
        mutable=mutable,
        self_mutating=(
            f"{owner}.{mapped_name}" in rules.get("mutatingProtocolRequirements", [])
            if kind == "method" and owner_kind == "interface" else None
        ),
        raw_value=raw,
        parameter_names=tuple(
            parameter.get("name", "") for parameter in parameters
        ),
        verify_parameter_order=(
            f"{owner}.{mapped_name.lstrip('.')}" in
            rules.get("internalParameterOrderChecks", [])
        ),
        getter_throws=getter_throws,
        writer_kind=writer_kind,
        writer_name=writer_name,
        writer_throws=writer_throws,
        writer_self_mutating=writer_self_mutating,
    )


def build_expected(
    contract: dict[str, Any],
    rules: dict[str, Any],
    fallibility: dict[tuple[str, str], dict[str, bool]] | None = None,
) -> dict[str, TypeModel]:
    fallibility = fallibility or {}
    models: dict[str, TypeModel] = {}
    for source_type in contract["types"]:
        name = map_type_name(source_type["name"], rules)
        kind = source_type["kind"]
        flags = bool(source_type.get("flags"))
        swift_kind = "struct" if kind == "enum" and flags else rules["typeKinds"][kind]
        generic_parameters = tuple(
            item["name"] for item in source_type.get("genericParameters", [])
        )
        clr_base = source_type.get("baseType")
        mapped_base = map_clr_type(clr_base, rules) if clr_base else None
        model = TypeModel(
            name=name,
            kind=swift_kind,
            flags=flags,
            base=mapped_base,
            interfaces=tuple(map_clr_type(value, rules) for value in source_type.get("directInterfaces", [])),
            generic_count=len(generic_parameters),
            generic_parameters=generic_parameters,
            raw_type=(
                map_clr_type(source_type.get("underlyingType"), rules)
                if source_type.get("underlyingType") else None
            ),
            verify_raw_type=name in rules.get("rawTypeChecks", []),
        )
        model.members = [
            expected_member(
                name, member, rules, source_type["kind"], generic_parameters,
                tuple(source_type.get("directInterfaces", [])),
                fallibility.get((source_type["name"], member["name"])),
            )
            for member in source_type["members"] if not member_is_omitted(member)
        ]
        models[name] = model
    return models


def declaration(symbol: dict[str, Any]) -> str:
    return "".join(part.get("spelling", "") for part in symbol.get("declarationFragments", []))


def normalize_swift_type(text: str) -> str:
    value = re.sub(r"\s+", " ", text.strip())
    value = value.replace("Swift.", "").replace("CNA.", "")
    value = value.replace("Self.", "")
    # `any P` is the Swift 5.7+ spelling of the existential `P`, and the
    # compiler emits it whether or not the source wrote it. It is the same
    # type, so it normalizes away. `some P` is deliberately NOT normalized: an
    # opaque result type is a different type from the existential a CLR
    # interface-typed member requires, and must still be diagnosed.
    value = re.sub(r"\bany\s+", "", value)
    if value == "InputStream":
        value = "Foundation.InputStream"
    value = value.replace("()", "Void") if value == "()" else value
    return value


def parse_parameter(fragment: str) -> tuple[str, str]:
    if ":" not in fragment:
        return "", normalize_swift_type(fragment)
    _, value = fragment.split(":", 1)
    value = normalize_swift_type(value)
    if value.startswith("inout "):
        return "inout", value[6:]
    return "", value


def actual_member(owner: str, symbol: dict[str, Any], raw_values: dict[tuple[str, str], int]) -> Member:
    swift_kind = symbol["kind"]["identifier"]
    title = symbol["names"]["title"]
    decl = declaration(symbol)
    if swift_kind == "swift.init":
        kind, name = "constructor", ".ctor"
    elif swift_kind == "swift.subscript":
        kind, name = "property", "Item"
    elif swift_kind == "swift.enum.case":
        kind, name = "field", symbol["pathComponents"][-1]
    elif swift_kind == "swift.func.op":
        kind = "method"
        operator = title.split("(", 1)[0]
        if operator == "-":
            count = len(symbol.get("functionSignature", {}).get("parameters", []))
            name = "op_UnaryNegation" if count == 1 else "op_Subtraction"
        else:
            name = OPERATOR_FROM_SWIFT.get(operator, operator)
    elif swift_kind in ("swift.method", "swift.type.method"):
        kind, name = "method", title.split("(", 1)[0]
    elif swift_kind in ("swift.property", "swift.type.property"):
        kind, name = "property", title
    else:
        kind, name = "unknown", title

    signature = symbol.get("functionSignature", {})
    parameter_types: list[str] = []
    directions: list[str] = []
    for parameter in signature.get("parameters", []):
        text = "".join(item.get("spelling", "") for item in parameter.get("declarationFragments", []))
        direction, mapped = parse_parameter(text)
        parameter_name = parameter.get("name", "")
        if "inout" in text or re.search(rf"(?:_\s+)?{re.escape(parameter_name)}:\s*inout\b", decl):
            direction = "inout"
        directions.append(direction)
        parameter_types.append(mapped)
    labels = tuple(
        item["spelling"] for item in symbol.get("declarationFragments", [])
        if item.get("kind") == "externalParam"
    )
    if swift_kind == "swift.func.op":
        labels = tuple("_" for _ in parameter_types)
    elif len(labels) != len(parameter_types):
        labels = tuple("_" if index == 0 else parameter.get("name", "_") for index, parameter in enumerate(signature.get("parameters", [])))

    returns = normalize_swift_type("".join(item.get("spelling", "") for item in signature.get("returns", [])))
    if not returns:
        if kind in ("property", "field") and ":" in decl:
            returns = normalize_swift_type(decl.split(":", 1)[1].split("{", 1)[0])
        else:
            returns = "Void"
    mutable: bool | None = None
    getter_throws: bool | None = None
    writer_kind: str | None = None
    if kind == "property":
        mutable = not ("let " in decl or ("{ get" in decl and " set" not in decl))
        getter_throws = getter_declaration_throws(decl)
        writer_kind = WRITER_PROPERTY if mutable else WRITER_ABSENT
    elif kind == "field":
        mutable = False
        returns = owner

    return Member(
        owner=owner,
        kind=kind,
        name=name,
        static=swift_kind.startswith("swift.type.") or swift_kind == "swift.enum.case" or swift_kind == "swift.func.op" or "static " in decl,
        parameters=tuple(parameter_types),
        labels=labels,
        directions=tuple(directions),
        return_type=returns,
        mutable=mutable,
        self_mutating=("mutating func " in decl if kind == "method" else None),
        raw_value=raw_values.get((owner.rsplit(".", 1)[-1], name)),
        declaration=decl,
        identifier=symbol["identifier"]["precise"],
        parameter_names=tuple(
            item.get("name", "") for item in signature.get("parameters", [])
        ),
        getter_throws=getter_throws,
        writer_kind=writer_kind,
    )


def source_constant_values(source_root: Path) -> dict[tuple[str, str], int]:
    values: dict[tuple[str, str], int] = {}
    container_name: str | None = None
    container_kind: str | None = None
    brace_depth = 0
    for path in source_root.rglob("*.swift"):
        container_name = None
        container_kind = None
        brace_depth = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            declaration_match = re.search(
                r"(?:public|open)\s+(?:final\s+)?(enum|struct|class)\s+(\w+)(?:\s*:\s*([^\{]+))?", line)
            if declaration_match:
                container_kind = declaration_match.group(1)
                container_name = declaration_match.group(2)
                brace_depth = line.count("{") - line.count("}")
                continue
            if container_name:
                brace_depth += line.count("{") - line.count("}")
                if container_kind == "enum":
                    case = re.search(r"\bcase\s+(\w+)\s*=\s*(-?(?:0x[0-9A-Fa-f_]+|\d[\d_]*))", line)
                    if case:
                        values[(container_name, case.group(1))] = int(case.group(2).replace("_", ""), 0)
                option = re.search(r"static let\s+(\w+)\s*=\s*\w+\(rawValue:\s*(-?(?:0x[0-9A-Fa-f_]+|\d[\d_]*))\)", line)
                if option:
                    values[(container_name, option.group(1))] = int(option.group(2).replace("_", ""), 0)
                empty_option = re.search(r"static let\s+(\w+)\s*=\s*\w+\(\[\]\)", line)
                if empty_option:
                    values[(container_name, empty_option.group(1))] = 0
                integer_constant = re.search(
                    r"public\s+static\s+let\s+(\w+)\s*:\s*U?Int\d+\s*=\s*"
                    r"(-?(?:0x[0-9A-Fa-f_]+|\d[\d_]*))", line)
                if integer_constant:
                    values[(container_name, integer_constant.group(1))] = int(
                        integer_constant.group(2).replace("_", ""), 0)
                if brace_depth <= 0:
                    container_name = None
                    container_kind = None
    return values


def source_raw_types(source_root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in source_root.rglob("*.swift"):
        container_name: str | None = None
        option_set = False
        brace_depth = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            declaration_match = re.search(
                r"(?:public|open)\s+(?:final\s+)?(enum|struct)\s+(\w+)"
                r"(?:\s*:\s*([^\{]+))?", line,
            )
            if declaration_match:
                container_name = declaration_match.group(2)
                inheritance = (declaration_match.group(3) or "").strip()
                option_set = "OptionSet" in inheritance
                brace_depth = line.count("{") - line.count("}")
                if declaration_match.group(1) == "enum" and inheritance:
                    values[container_name] = normalize_swift_type(
                        inheritance.split(",", 1)[0].strip()
                    )
                continue
            if container_name:
                brace_depth += line.count("{") - line.count("}")
                if option_set:
                    raw = re.search(
                        r"public\s+let\s+rawValue\s*:\s*([A-Za-z0-9_.]+)", line,
                    )
                    if raw:
                        values[container_name] = normalize_swift_type(raw.group(1))
                if brace_depth <= 0:
                    container_name = None
                    option_set = False
    return values


def relationship_name(relationship: dict[str, Any], symbols: dict[str, dict[str, Any]]) -> str | None:
    target = symbols.get(relationship.get("target", ""))
    if target:
        return ".".join(target["pathComponents"])
    fallback = relationship.get("targetFallback")
    return fallback.replace("Swift.", "") if fallback else None


def is_synthesized_language_member(owner: TypeModel, member: Member) -> bool:
    if "::SYNTHESIZED::" in member.identifier:
        return True
    if owner.kind in ("enum", "struct") and member.name in {"rawValue", "hashValue", "hash", ".ctor", "op_Equality", "op_Inequality"}:
        if owner.kind == "enum" or owner.flags:
            return True
    return False


def protocol_witness_shape_diagnostic(
    witness: Member,
    requirement: Member,
) -> dict[str, str] | None:
    subject = witness.display
    if witness.kind != requirement.kind or witness.static != requirement.static:
        return diagnostic(
            "METHOD_SIGNATURE_MAPPING_MISMATCH", subject,
            "projected protocol witness does not match the interface requirement kind/static identity",
        )
    if witness.parameters != requirement.parameters or witness.labels != requirement.labels:
        return diagnostic(
            "PARAMETER_MAPPING_MISMATCH", subject,
            "projected protocol witness parameters do not match the interface requirement",
        )
    if witness.directions != requirement.directions:
        return diagnostic(
            "REF_OUT_MAPPING_MISMATCH", subject,
            "projected protocol witness parameter direction does not match the interface requirement",
        )
    if witness.return_type != requirement.return_type:
        return diagnostic(
            "RETURN_MAPPING_MISMATCH", subject,
            f"projected protocol witness returns {witness.return_type}, expected {requirement.return_type}",
        )
    if witness.self_mutating != requirement.self_mutating:
        return diagnostic(
            "METHOD_SIGNATURE_MAPPING_MISMATCH", subject,
            "projected protocol witness mutating identity does not match the interface requirement",
        )
    return None


def writer_method_shape_diagnostics(
    owner_name: str,
    writer: Member,
    expected_property: Member,
) -> list[dict[str, str]]:
    """Measure a projected `Set<Name>` writer against its CLR setter accessor.

    The writer takes the property's index parameters, if any, then the value.
    Its static identity, parameter types, labels, directions, return type and
    `throws` are each measured; nothing about it is assumed from the getter.
    """
    result: list[dict[str, str]] = []
    expected_parameters = expected_property.parameters + (
        expected_property.return_type,
    )
    expected_labels = expected_property.labels + ("_",)
    expected_directions = expected_property.directions + ("",)
    subject = f"{owner_name}.{expected_property.writer_name}"
    if writer.static != expected_property.static or writer.kind != "method":
        result.append(diagnostic(
            "METHOD_SIGNATURE_MAPPING_MISMATCH", subject,
            "property writer kind/static identity differs",
        ))
    if writer.parameters != expected_parameters or writer.labels != expected_labels:
        result.append(diagnostic(
            "PARAMETER_MAPPING_MISMATCH", subject,
            f"property writer expects labels/types "
            f"{list(zip(expected_labels, expected_parameters))}, found "
            f"{list(zip(writer.labels, writer.parameters))}",
        ))
    if writer.directions != expected_directions:
        result.append(diagnostic(
            "REF_OUT_MAPPING_MISMATCH", subject,
            "property writer parameter direction differs",
        ))
    if writer.return_type != "Void":
        result.append(diagnostic(
            "RETURN_MAPPING_MISMATCH", subject,
            f"property writer returns {writer.return_type}, expected Void",
        ))
    if (
        expected_property.writer_self_mutating is not None and
        writer.self_mutating is not None and
        expected_property.writer_self_mutating != writer.self_mutating
    ):
        result.append(diagnostic(
            "METHOD_SIGNATURE_MAPPING_MISMATCH", subject,
            f"expected mutating={expected_property.writer_self_mutating}, "
            f"found mutating={writer.self_mutating}",
        ))
    observed_throws = declaration_throws(writer.declaration)
    if bool(expected_property.writer_throws) != observed_throws:
        result.append(diagnostic(
            "PROPERTY_MAPPING_MISMATCH", subject,
            f"CLR setter is {'fallible' if expected_property.writer_throws else 'infallible'}, "
            f"so the writer must {'throw' if expected_property.writer_throws else 'not throw'}; "
            f"found throws={observed_throws}",
        ))
    return result


def declaration_throws(text: str) -> bool:
    """Whether a Symbol-Graph declaration carries the Swift `throws` effect."""
    return bool(re.search(r"\bthrows\b", text))


def getter_declaration_throws(text: str) -> bool:
    """Whether a property/subscript declaration spells `get throws`."""
    return bool(re.search(r"\bget\s+(?:async\s+)?throws\b", text))


def parse_symbol_graph(
    path: Path,
    rules: dict[str, Any],
    source_root: Path,
    expected: dict[str, TypeModel],
    graph: dict[str, Any] | None = None,
) -> tuple[
    dict[str, TypeModel], list[dict[str, Any]], int,
    list[dict[str, str]], list[dict[str, Any]],
]:
    graph = load_json(path) if graph is None else graph
    symbols = {item["identifier"]["precise"]: item for item in graph["symbols"]}
    markers = set(rules["namespaceMarkers"])
    support_names = set(rules.get("eventSupportContract", {}))
    raw_values = source_constant_values(source_root)
    raw_types = source_raw_types(source_root)
    types: dict[str, TypeModel] = {}
    strict_symbols = 0
    for symbol in graph["symbols"]:
        path_name = ".".join(symbol["pathComponents"])
        if symbol.get("accessLevel") not in ("public", "open"):
            continue
        if path_name.startswith("Microsoft.Xna.Framework"):
            strict_symbols += 1
        swift_kind = symbol["kind"]["identifier"]
        selected = (
            path_name.startswith("Microsoft.Xna.Framework") or
            path_name in support_names
        )
        if swift_kind not in TYPE_KINDS or not selected or path_name in markers:
            continue
        decl = declaration(symbol)
        generic_match = re.search(
            r"\b(?:class|struct|enum|protocol)\s+\w+\s*<([^>]+)>", decl,
        )
        generic_parameters = tuple(
            item.split(":", 1)[0].strip()
            for item in split_generic_arguments(generic_match.group(1))
        ) if generic_match else ()
        types[path_name] = TypeModel(
            name=path_name,
            kind=TYPE_KINDS[swift_kind],
            flags="OptionSet" in declaration(symbol),
            generic_count=len(generic_parameters),
            generic_parameters=generic_parameters,
            declaration=decl,
            identifier=symbol["identifier"]["precise"],
            raw_type=raw_types.get(path_name.rsplit(".", 1)[-1]),
            access=symbol.get("accessLevel", ""),
        )

    member_relationships: dict[str, str] = {}
    source_origins: dict[str, dict[str, str]] = {}
    associated_type_witnesses: dict[str, dict[str, str]] = collections.defaultdict(dict)
    for relation in graph.get("relationships", []):
        if relation["kind"] != "memberOf" or relation.get("target") not in symbols:
            continue
        source = symbols.get(relation.get("source", ""))
        if not source or source["kind"]["identifier"] != "swift.typealias":
            continue
        parent = ".".join(symbols[relation["target"]]["pathComponents"])
        match = re.fullmatch(r"typealias\s+(\w+)\s*=\s*(.+)", declaration(source))
        if match:
            associated_type_witnesses[parent][match.group(1)] = normalize_swift_type(match.group(2))

    diagnostics_context: list[dict[str, Any]] = []
    for relation in graph.get("relationships", []):
        if relation["kind"] in ("memberOf", "requirementOf") and relation.get("target") in symbols:
            parent = ".".join(symbols[relation["target"]]["pathComponents"])
            member_relationships[relation["source"]] = parent
            if relation.get("sourceOrigin"):
                source_origins[relation["source"]] = relation["sourceOrigin"]
        elif relation["kind"] in ("inheritsFrom", "conformsTo") and relation.get("source") in symbols:
            source_name = ".".join(symbols[relation["source"]]["pathComponents"])
            if source_name in types:
                target_name = relationship_name(relation, symbols)
                if relation["kind"] == "inheritsFrom":
                    types[source_name].base = target_name
                elif target_name:
                    target_model = types.get(target_name)
                    witnesses = associated_type_witnesses.get(source_name, {})
                    if (
                        target_model and target_model.generic_parameters and
                        all(parameter in witnesses for parameter in target_model.generic_parameters)
                    ):
                        arguments = ", ".join(
                            witnesses[parameter]
                            for parameter in target_model.generic_parameters
                        )
                        target_name = f"{target_name}<{arguments}>"
                    types[source_name].interfaces += (target_name,)
                    if target_name in ("OptionSet", "Swift.OptionSet"):
                        types[source_name].flags = True

    # Every CLR property whose writer cannot be a Swift `set`. An indexed one
    # also moves its reader out of subscript syntax, so both halves arrive as
    # methods; a plain one keeps `var P` and adds only the writer method.
    method_writer_properties = {
        (owner_name, member.name): member
        for owner_name, model in expected.items()
        for member in model.members
        if member.kind == "property" and member.writer_kind == WRITER_METHOD
    }
    indexed_method_readers = {
        key for key, member in method_writer_properties.items() if member.parameters
    }
    writer_identities = {
        (owner_name, member.writer_name): (owner_name, property_name)
        for (owner_name, property_name), member in method_writer_properties.items()
    }
    accessor_candidates: dict[tuple[str, str, str], Member] = {}
    witness_candidates: list[tuple[str, Member, dict[str, str]]] = []
    for precise, parent in member_relationships.items():
        if parent not in types or precise not in symbols:
            continue
        symbol = symbols[precise]
        if symbol.get("accessLevel") not in ("public", "open"):
            continue
        if symbol["kind"]["identifier"] not in {
            "swift.init", "swift.subscript", "swift.enum.case", "swift.func.op",
            "swift.method", "swift.type.method", "swift.property", "swift.type.property",
        }:
            continue
        member = actual_member(parent, symbol, raw_values)
        if (
            (parent, member.name) in indexed_method_readers and
            symbol["kind"]["identifier"] in ("swift.method", "swift.type.method")
        ):
            accessor_candidates[(parent, member.name, "reader")] = member
            continue
        if (parent, member.name) in writer_identities:
            owner_key = writer_identities[(parent, member.name)]
            accessor_candidates[(owner_key[0], owner_key[1], "writer")] = member
            continue
        witness_identity = f"{parent}.{member.name}"
        if (
            precise in source_origins and
            witness_identity in rules.get("protocolWitnessMemberProjections", [])
        ):
            witness_candidates.append((parent, member, source_origins[precise]))
            continue
        if not is_synthesized_language_member(types[parent], member):
            types[parent].members.append(member)

    # Swift has no throwing setter, and the compiler additionally refuses any
    # `set` beside a throwing getter. A CLR property in either situation is
    # emitted as a reader plus a `Set<Name>` writer, and both compiler symbols
    # are recombined here into the one source property identity the strict
    # scoreboard counts.
    accessor_evidence: list[dict[str, Any]] = []
    for (owner_name, property_name), expected_property in method_writer_properties.items():
        if owner_name not in types:
            continue
        indexed = bool(expected_property.parameters)
        writer = accessor_candidates.get((owner_name, property_name, "writer"))
        if indexed:
            reader = accessor_candidates.get((owner_name, property_name, "reader"))
            if reader is not None:
                types[owner_name].members.append(dataclasses.replace(
                    reader,
                    kind="property",
                    name=property_name,
                    mutable=False,
                    getter_throws=declaration_throws(reader.declaration),
                    writer_kind=WRITER_METHOD if writer else WRITER_ABSENT,
                    writer_name=expected_property.writer_name,
                    writer_throws=(
                        declaration_throws(writer.declaration) if writer else None
                    ),
                    writer_member=writer,
                ))
        else:
            reader = next(
                (
                    item for item in types[owner_name].members
                    if item.kind == "property" and item.name == property_name
                ),
                None,
            )
            if reader is not None:
                reader.writer_kind = WRITER_METHOD if writer else WRITER_ABSENT
                reader.writer_name = expected_property.writer_name
                reader.writer_throws = (
                    declaration_throws(writer.declaration) if writer else None
                )
                reader.writer_member = writer
        accessor_evidence.append({
            "ownerType": owner_name,
            "sourceProperty": property_name,
            "indexed": indexed,
            "readerSymbol": reader.display if reader else None,
            "readerForm": (
                "method" if indexed else "property"
            ),
            "readerThrows": bool(expected_property.getter_throws),
            "writerSymbol": writer.display if writer else None,
            "writerName": expected_property.writer_name,
            "writerThrows": bool(expected_property.writer_throws),
            "readerObserved": reader is not None,
            "writerObserved": writer is not None,
            "reason":
                "Swift has no throwing property setter and forbids `set` beside "
                "a throwing getter, so this CLR setter accessor projects to a "
                "named writer method measured as part of one property identity",
        })

    # Optional-reference operators cannot be declared as type members in
    # Swift because neither operand has the non-Optional owner type. Assign
    # only the explicitly configured global symbols back to their XNA owner.
    owned_precise = set(member_relationships)
    for identity in rules.get("globalOperatorProjections", []):
        owner_name, member_name = identity.rsplit(".", 1)
        for symbol in graph["symbols"]:
            if (
                symbol["identifier"]["precise"] in owned_precise or
                symbol.get("accessLevel") not in ("public", "open") or
                symbol["kind"]["identifier"] != "swift.func.op"
            ):
                continue
            member = actual_member(owner_name, symbol, raw_values)
            if member.name != member_name:
                continue
            if not all(
                parameter.rstrip("?") == owner_name
                for parameter in member.parameters
            ):
                continue
            types[owner_name].members.append(member)
            break

    observed_projections: list[dict[str, str]] = []
    for parent, witness, origin in witness_candidates:
        display_name = origin.get("displayName", "")
        requirement_owner = display_name.rsplit(".", 1)[0] if "." in display_name else ""
        requirement = next(
            (
                item for item in types.get(requirement_owner, TypeModel("", "")).members
                if item.name == witness.name
            ),
            None,
        )
        identity = f"{parent}.{witness.name}"
        if requirement is None:
            diagnostics_context.append(diagnostic(
                "UNMEASURED_STRUCTURAL_CATEGORY", identity,
                f"protocol witness sourceOrigin does not resolve to a compiler-emitted requirement: {display_name}",
            ))
            continue
        mismatch = protocol_witness_shape_diagnostic(witness, requirement)
        if mismatch:
            diagnostics_context.append(mismatch)
            continue
        observed_projections.append({
            "ownerType": parent,
            "swiftMember": witness.name,
            "sourceOrigin": display_name,
        })

    support = {name: types.pop(name) for name in support_names if name in types}

    return (
        types, diagnostics_context, strict_symbols, observed_projections,
        accessor_evidence, support,
    )


def comparable_kind(expected: Member, actual: Member) -> bool:
    if expected.kind == actual.kind:
        return True
    if expected.kind == "field" and actual.kind == "property":
        return "{ get" not in actual.declaration
    if expected.kind == "event" and actual.kind == "property":
        return True
    return False


# An XNA base has always been measured. A non-XNA CLR base is measured exactly
# when the project has decided its support projection: `System.EventArgs` maps
# to `CNAEventArgs` and is checked, while `System.Object`, `System.ValueType`
# and the still-undecided BCL bases stay unmeasured rather than silently
# asserted. Kept in step with `measuredSupportBaseProjections` by a self-test.
MEASURED_SUPPORT_BASES = ("CNAEventArgs",)

# The three CLR roots carry no projected members, so a type sitting directly on
# one of them has nothing to inherit and needs no base decision. Every other
# non-XNA base is a real BCL mapping question.
CLR_ROOT_BASES = ("Any?", "System.ValueType", "System.Enum")


def base_is_measured(mapped_base: str | None) -> bool:
    if not mapped_base:
        return False
    return (
        mapped_base.startswith("Microsoft.Xna.Framework") or
        mapped_base in MEASURED_SUPPORT_BASES
    )


def base_is_undecided(mapped_base: str | None) -> bool:
    """A non-XNA base whose support projection this project has not decided.

    Implementing such a type would drop its CLR base silently -- exactly the
    failure the `System.EventArgs` decision was made to avoid. Reporting it as
    unmeasured keeps the deferral honest: `System.Exception`,
    `System.Attribute`, `Collection<T>`, `ReadOnlyCollection<T>` and
    `Dictionary<K,V>` cannot be quietly projected as base-less Swift classes to
    improve the scoreboard, and a future decision plugs into the same measured
    machinery `CNAEventArgs` uses.
    """
    if not mapped_base or base_is_measured(mapped_base):
        return False
    return mapped_base not in CLR_ROOT_BASES


def system_interface_is_language_mapped(name: str) -> bool:
    return name.startswith("System.")


def diagnostic(category: str, subject: str, detail: str) -> dict[str, str]:
    return {"category": category, "subject": subject, "detail": detail}


def apply_manual_suppressions(
    diagnostics: list[dict[str, str]],
    suppressions: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    remaining = list(diagnostics)
    applied = 0
    for suppression in suppressions:
        category = suppression.get("category")
        subject = suppression.get("subject")
        for index, item in enumerate(remaining):
            if item["category"] == category and item["subject"] == subject:
                remaining.pop(index)
                applied += 1
                break
    return remaining, applied


def same_callable_identity(expected: Member, actual: Member) -> bool:
    return (
        expected.name == actual.name and
        comparable_kind(expected, actual) and
        expected.static == actual.static and
        expected.parameters == actual.parameters and
        expected.labels == actual.labels and
        expected.directions == actual.directions
    )


def is_inherited_language_projection(
    owner: TypeModel,
    member: Member,
    expected: dict[str, TypeModel],
) -> bool:
    if any(same_callable_identity(item, member) for item in owner.members):
        return False
    if "System.IDisposable" in owner.interfaces and member.name == "Dispose" and not member.parameters:
        return True
    visited: set[str] = set()
    base = owner.base
    while base and base not in visited:
        visited.add(base)
        ancestor = expected.get(base)
        if ancestor is None:
            break
        if any(same_callable_identity(item, member) for item in ancestor.members):
            return True
        base = ancestor.base
    return False


def compare(expected: dict[str, TypeModel], actual: dict[str, TypeModel]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    consumed: dict[str, set[str]] = collections.defaultdict(set)

    for name, expected_type in expected.items():
        actual_type = actual.get(name)
        if actual_type is None:
            result.append(diagnostic("MISSING_TYPE", name, "mapped XNA type is absent from the Swift Symbol Graph"))
            continue
        if actual_type.kind != expected_type.kind:
            result.append(diagnostic("TYPE_KIND_MISMATCH", name, f"expected {expected_type.kind}, found {actual_type.kind}"))
        if expected_type.flags and not actual_type.flags:
            result.append(diagnostic("FLAGS_MAPPING_MISMATCH", name, "CLR [Flags] enum is not a Swift OptionSet"))
        if expected_type.kind == "enum" and not expected_type.flags and actual_type.flags:
            result.append(diagnostic("FLAGS_MAPPING_MISMATCH", name, "ordinary CLR enum unexpectedly maps as a Swift OptionSet"))
        if (
            expected_type.verify_raw_type and expected_type.raw_type and
            actual_type.raw_type != expected_type.raw_type
        ):
            category = "FLAGS_MAPPING_MISMATCH" if expected_type.flags else "TYPE_KIND_MISMATCH"
            result.append(diagnostic(
                category, name,
                f"expected raw type {expected_type.raw_type}, found {actual_type.raw_type}",
            ))
        if expected_type.generic_count != actual_type.generic_count:
            result.append(diagnostic("GENERIC_MAPPING_MISMATCH", name, f"expected {expected_type.generic_count} generic parameters, found {actual_type.generic_count}"))
        elif expected_type.generic_parameters != actual_type.generic_parameters:
            result.append(diagnostic(
                "GENERIC_MAPPING_MISMATCH", name,
                f"expected generic parameters {expected_type.generic_parameters}, "
                f"found {actual_type.generic_parameters}",
            ))

        expected_base = expected_type.base
        if base_is_measured(expected_base) and actual_type.base != expected_base:
            result.append(diagnostic("BASE_MAPPING_MISMATCH", name, f"expected base {expected_base}, found {actual_type.base}"))
        elif base_is_undecided(expected_base):
            result.append(diagnostic(
                "UNMEASURED_STRUCTURAL_CATEGORY", name,
                f"CLR base {expected_base} has no decided Swift support "
                "projection, so this implemented type's base is unmeasured",
            ))
        expected_interfaces = {
            item for item in expected_type.interfaces
            if not system_interface_is_language_mapped(item) and item.split("<", 1)[0] in expected
        }
        actual_interfaces = set(actual_type.interfaces)
        if not expected_interfaces.issubset(actual_interfaces):
            result.append(diagnostic("INTERFACE_MAPPING_MISMATCH", name, f"missing protocols {sorted(expected_interfaces - actual_interfaces)}"))

        def exact_shape_exists(member: Member) -> bool:
            return any(
                item.name == member.name and
                comparable_kind(member, item) and
                item.static == member.static and
                item.parameters == member.parameters and
                item.labels == member.labels and
                item.directions == member.directions
                for item in actual_type.members
            )

        # Reserve exact overload identities before considering malformed or
        # absent overloads. A greedy name-only walk can otherwise consume the
        # one real nine-parameter Draw while diagnosing an absent four-
        # parameter Draw, and then falsely call the real overload missing.
        ordered_expected_members = sorted(
            enumerate(expected_type.members),
            key=lambda pair: (not exact_shape_exists(pair[1]), pair[0]),
        )
        for _, expected_member_model in ordered_expected_members:
            candidates = [item for item in actual_type.members if item.name == expected_member_model.name and item.identifier not in consumed[name]]
            if not candidates:
                result.append(diagnostic("MISSING_MEMBER", expected_member_model.display, "mapped member is absent"))
                if any(item.name == expected_member_model.name for item in actual_type.members):
                    result.append(diagnostic("OVERLOAD_MAPPING_MISMATCH", expected_member_model.display, "required overload is absent"))
                continue

            arity_candidates = [
                item for item in candidates
                if len(item.parameters) == len(expected_member_model.parameters)
            ]
            if not arity_candidates:
                result.append(diagnostic("MISSING_MEMBER", expected_member_model.display, "mapped overload is absent"))
                result.append(diagnostic("OVERLOAD_MAPPING_MISMATCH", expected_member_model.display, "required overload is absent"))
                continue

            def distance(item: Member) -> int:
                return (
                    (0 if comparable_kind(expected_member_model, item) else 8) +
                    (0 if expected_member_model.static == item.static else 4) +
                    abs(len(expected_member_model.parameters) - len(item.parameters)) * 3 +
                    sum(a != b for a, b in zip(expected_member_model.parameters, item.parameters)) +
                    sum(a != b for a, b in zip(expected_member_model.labels, item.labels))
                )

            candidate = min(arity_candidates, key=distance)
            consumed[name].add(candidate.identifier)
            subject = expected_member_model.display
            if not comparable_kind(expected_member_model, candidate):
                category = {
                    "field": "FIELD_MAPPING_MISMATCH", "property": "PROPERTY_MAPPING_MISMATCH",
                    "event": "EVENT_MAPPING_MISMATCH",
                }.get(expected_member_model.kind, "METHOD_SIGNATURE_MAPPING_MISMATCH")
                result.append(diagnostic(category, subject, f"expected {expected_member_model.kind}, found {candidate.kind}"))
            if expected_member_model.static != candidate.static:
                category = {
                    "property": "PROPERTY_MAPPING_MISMATCH",
                    "field": "PROPERTY_MAPPING_MISMATCH",
                    "event": "EVENT_MAPPING_MISMATCH",
                }.get(expected_member_model.kind, "METHOD_SIGNATURE_MAPPING_MISMATCH")
                result.append(diagnostic(category, subject, "static/instance identity differs"))
            if len(expected_member_model.parameters) != len(candidate.parameters):
                result.append(diagnostic("OVERLOAD_MAPPING_MISMATCH", subject, f"expected {len(expected_member_model.parameters)} parameters, found {len(candidate.parameters)}"))
            else:
                if expected_member_model.labels != candidate.labels or expected_member_model.parameters != candidate.parameters:
                    result.append(diagnostic("PARAMETER_MAPPING_MISMATCH", subject, f"expected labels/types {list(zip(expected_member_model.labels, expected_member_model.parameters))}, found {list(zip(candidate.labels, candidate.parameters))}"))
                if expected_member_model.directions != candidate.directions:
                    result.append(diagnostic("REF_OUT_MAPPING_MISMATCH", subject, f"expected {expected_member_model.directions}, found {candidate.directions}"))
                if (
                    expected_member_model.verify_parameter_order and
                    expected_member_model.parameter_names != candidate.parameter_names
                ):
                    result.append(diagnostic(
                        "PARAMETER_MAPPING_MISMATCH", subject,
                        f"expected internal parameter order {expected_member_model.parameter_names}, "
                        f"found {candidate.parameter_names}",
                    ))
            if expected_member_model.kind in ("method", "property", "field", "event") and expected_member_model.return_type != candidate.return_type:
                category = {
                    "method": "RETURN_MAPPING_MISMATCH",
                    "field": "FIELD_MAPPING_MISMATCH",
                    "event": "EVENT_MAPPING_MISMATCH",
                }.get(expected_member_model.kind, "PROPERTY_MAPPING_MISMATCH")
                result.append(diagnostic(category, subject, f"expected {expected_member_model.return_type}, found {candidate.return_type}"))
            # A property whose CLR setter projects to a writer method is
            # measured accessor by accessor where the two compiler symbols are
            # recombined; reporting its mutability here as well would count one
            # defect twice.
            writer_owned_elsewhere = (
                expected_member_model.kind == "property" and
                expected_member_model.writer_kind == WRITER_METHOD
            )
            if (
                not writer_owned_elsewhere and
                expected_member_model.mutable is not None and
                candidate.mutable is not None and
                expected_member_model.mutable != candidate.mutable
            ):
                category = {
                    "field": "FIELD_MAPPING_MISMATCH",
                    "event": "EVENT_MAPPING_MISMATCH",
                }.get(expected_member_model.kind, "PROPERTY_MAPPING_MISMATCH")
                result.append(diagnostic(category, subject, f"expected mutable={expected_member_model.mutable}, found mutable={candidate.mutable}"))
            if (
                expected_member_model.kind == "property" and
                expected_member_model.getter_throws is not None and
                candidate.getter_throws is not None and
                expected_member_model.getter_throws != candidate.getter_throws
            ):
                result.append(diagnostic(
                    "PROPERTY_MAPPING_MISMATCH", subject,
                    "CLR getter is "
                    f"{'fallible' if expected_member_model.getter_throws else 'infallible'}, "
                    f"so the Swift reader must "
                    f"{'be `get throws`' if expected_member_model.getter_throws else 'not throw'}; "
                    f"found throws={candidate.getter_throws}",
                ))
            if writer_owned_elsewhere:
                if candidate.writer_kind != WRITER_METHOD:
                    result.append(diagnostic(
                        "PROPERTY_MAPPING_MISMATCH", subject,
                        "the CLR setter cannot be a Swift `set`, so the "
                        f"projection requires a {expected_member_model.writer_name} "
                        "writer method; it is absent",
                    ))
                else:
                    if candidate.writer_member is not None:
                        result.extend(writer_method_shape_diagnostics(
                            expected_member_model.owner, candidate.writer_member,
                            expected_member_model,
                        ))
                    elif candidate.writer_throws is not None and bool(
                        expected_member_model.writer_throws
                    ) != bool(candidate.writer_throws):
                        result.append(diagnostic(
                            "PROPERTY_MAPPING_MISMATCH",
                            f"{expected_member_model.owner}.{expected_member_model.writer_name}",
                            "writer method fallibility differs from the CLR setter",
                        ))
                    if candidate.mutable:
                        result.append(diagnostic(
                            "PROPERTY_MAPPING_MISMATCH", subject,
                            "an ordinary Swift setter is retained beside "
                            f"{expected_member_model.writer_name}, so the "
                            "unchecked write path still exists",
                        ))
            if (
                expected_member_model.self_mutating is not None and
                candidate.self_mutating is not None and
                expected_member_model.self_mutating != candidate.self_mutating
            ):
                result.append(diagnostic(
                    "METHOD_SIGNATURE_MAPPING_MISMATCH", subject,
                    f"expected mutating={expected_member_model.self_mutating}, "
                    f"found mutating={candidate.self_mutating}",
                ))
            if expected_member_model.raw_value is not None:
                if candidate.raw_value is None:
                    result.append(diagnostic("UNMEASURED_STRUCTURAL_CATEGORY", subject, "constant/enum raw value unavailable from source supplement"))
                elif expected_member_model.raw_value != candidate.raw_value:
                    result.append(diagnostic("ENUM_VALUE_MISMATCH", subject, f"expected {expected_member_model.raw_value}, found {candidate.raw_value}"))
            if expected_member_model.name.startswith("op_") and candidate.kind != "method":
                result.append(diagnostic("OPERATOR_MAPPING_MISMATCH", subject, "operator did not map to a Swift operator function"))
            if ("<" in expected_member_model.return_type or any("<" in item for item in expected_member_model.parameters)) != ("<" in candidate.declaration):
                result.append(diagnostic("GENERIC_MAPPING_MISMATCH", subject, "generic member shape differs"))

        for member in actual_type.members:
            if member.identifier not in consumed[name]:
                if is_inherited_language_projection(expected_type, member, expected):
                    continue
                result.append(diagnostic("UNEXPECTED_MEMBER", member.display, "public XNA-namespace member has no mapped reference identity"))

    for name, actual_type in actual.items():
        if name not in expected:
            result.append(diagnostic("UNEXPECTED_TYPE", name, "public XNA-namespace type has no mapped reference identity"))
            if any(part.startswith("_") or part in {"Runtime", "Native", "Internal"} for part in name.split(".")):
                result.append(diagnostic("INTERNAL_TYPE_LEAK", name, "implementation type leaked into strict XNA namespace"))

    for model in actual.values():
        for member in model.members:
            if member.name.startswith(EVENT_ACCESSOR_PREFIXES):
                result.append(diagnostic(
                    "EVENT_MAPPING_MISMATCH", member.display,
                    "CLR event accessor leaked as an XNA identity; a CLR event "
                    "maps to one get-only CNAEvent property and no accessor",
                ))

    pointer_pattern = re.compile(r"Unsafe(?:Mutable)?(?:Raw)?Pointer|OpaquePointer|nativeHandle|CNASwift_|CNA_Handle")
    raw_pattern = re.compile(r"Unsafe(?:Mutable)?(?:Raw)?Pointer|OpaquePointer|nativeHandle")
    for model in actual.values():
        for member in model.members:
            if raw_pattern.search(member.declaration):
                result.append(diagnostic("RAW_HANDLE_LEAK", member.display, member.declaration))
            if pointer_pattern.search(member.declaration):
                result.append(diagnostic("PUBLIC_NATIVE_FFI_LEAK", member.display, member.declaration))
    return result


def self_test() -> None:
    base_member = Member("Microsoft.Xna.Framework.Foo", "method", "Bar", False, ("Int32",), ("_",), ("",), "Bool", identifier="bar")
    expected = {
        "Microsoft.Xna.Framework.Foo": TypeModel("Microsoft.Xna.Framework.Foo", "class", base="Microsoft.Xna.Framework.Base", interfaces=("Microsoft.Xna.Framework.IFoo",), members=[base_member]),
        "Microsoft.Xna.Framework.Base": TypeModel("Microsoft.Xna.Framework.Base", "class"),
        "Microsoft.Xna.Framework.IFoo": TypeModel("Microsoft.Xna.Framework.IFoo", "protocol"),
    }
    good = {
        "Microsoft.Xna.Framework.Foo": TypeModel("Microsoft.Xna.Framework.Foo", "class", base="Microsoft.Xna.Framework.Base", interfaces=("Microsoft.Xna.Framework.IFoo",), members=[dataclasses.replace(base_member)]),
        "Microsoft.Xna.Framework.Base": TypeModel("Microsoft.Xna.Framework.Base", "class"),
        "Microsoft.Xna.Framework.IFoo": TypeModel("Microsoft.Xna.Framework.IFoo", "protocol"),
    }

    def categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(expected, models)}

    mutations: list[tuple[str, str, Any]] = []
    mutations.append(("missing type", "MISSING_TYPE", lambda m: m.pop("Microsoft.Xna.Framework.Foo")))
    mutations.append(("missing method", "MISSING_MEMBER", lambda m: m["Microsoft.Xna.Framework.Foo"].members.clear()))
    mutations.append(("wrong kind", "TYPE_KIND_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"], "kind", "struct")))
    mutations.append(("wrong namespace", "MISSING_TYPE", lambda m: m.__setitem__("Microsoft.Xna.Wrong.Foo", m.pop("Microsoft.Xna.Framework.Foo"))))
    mutations.append(("wrong base", "BASE_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"], "base", None)))
    mutations.append(("wrong protocol", "INTERFACE_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"], "interfaces", ())))
    mutations.append(("wrong constructor", "MISSING_MEMBER", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "name", ".ctor")))
    mutations.append(("missing overload", "OVERLOAD_MAPPING_MISMATCH", lambda m: m["Microsoft.Xna.Framework.Foo"].members[0].parameters.__class__))
    mutations.append(("wrong label", "PARAMETER_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "labels", ("value",))))
    mutations.append(("wrong parameter", "PARAMETER_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "parameters", ("Float",))))
    mutations.append(("wrong return", "RETURN_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "return_type", "Int32")))
    mutations.append(("wrong static", "METHOD_SIGNATURE_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "static", True)))
    mutations.append(("ref mismatch", "REF_OUT_MAPPING_MISMATCH", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "directions", ("inout",))))
    mutations.append(("unexpected type", "UNEXPECTED_TYPE", lambda m: m.__setitem__("Microsoft.Xna.Framework.Extra", TypeModel("Microsoft.Xna.Framework.Extra", "class"))))
    mutations.append(("unexpected member", "UNEXPECTED_MEMBER", lambda m: m["Microsoft.Xna.Framework.Foo"].members.append(Member("Microsoft.Xna.Framework.Foo", "method", "Extra", False, identifier="extra"))))
    mutations.append(("raw pointer", "RAW_HANDLE_LEAK", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "declaration", "func Bar(_ value: UnsafeRawPointer)")))
    mutations.append(("native handle", "PUBLIC_NATIVE_FFI_LEAK", lambda m: setattr(m["Microsoft.Xna.Framework.Foo"].members[0], "declaration", "func Bar(_ value: CNA_Handle)")))
    mutations.append(("internal helper", "INTERNAL_TYPE_LEAK", lambda m: m.__setitem__("Microsoft.Xna.Framework.Internal.Helper", TypeModel("Microsoft.Xna.Framework.Internal.Helper", "class"))))

    failures: list[str] = []
    import copy
    for label, wanted, mutate in mutations:
        models = copy.deepcopy(good)
        if label == "missing overload":
            models["Microsoft.Xna.Framework.Foo"].members.append(Member("Microsoft.Xna.Framework.Foo", "method", "Bar", False, (), (), (), "Bool", identifier="other"))
            models["Microsoft.Xna.Framework.Foo"].members.pop(0)
        else:
            mutate(models)
        if wanted not in categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    enum_expected = {"Microsoft.Xna.Framework.E": TypeModel("Microsoft.Xna.Framework.E", "enum", members=[Member("Microsoft.Xna.Framework.E", "field", "A", True, return_type="Microsoft.Xna.Framework.E", mutable=False, raw_value=1)])}
    enum_actual = {"Microsoft.Xna.Framework.E": TypeModel("Microsoft.Xna.Framework.E", "enum", members=[Member("Microsoft.Xna.Framework.E", "field", "A", True, return_type="Microsoft.Xna.Framework.E", mutable=False, raw_value=2, identifier="a")])}
    if "ENUM_VALUE_MISMATCH" not in {item["category"] for item in compare(enum_expected, enum_actual)}:
        failures.append("enum raw value mutation")
    flags_expected = {"Microsoft.Xna.Framework.F": TypeModel("Microsoft.Xna.Framework.F", "struct", flags=True)}
    flags_actual = {"Microsoft.Xna.Framework.F": TypeModel("Microsoft.Xna.Framework.F", "struct", flags=False)}
    if "FLAGS_MAPPING_MISMATCH" not in {item["category"] for item in compare(flags_expected, flags_actual)}:
        failures.append("flags mutation")
    generic_expected = {"Microsoft.Xna.Framework.GOfT": TypeModel("Microsoft.Xna.Framework.GOfT", "class", generic_count=1)}
    generic_actual = {"Microsoft.Xna.Framework.GOfT": TypeModel("Microsoft.Xna.Framework.GOfT", "class", generic_count=0)}
    if "GENERIC_MAPPING_MISMATCH" not in {item["category"] for item in compare(generic_expected, generic_actual)}:
        failures.append("generic collision mutation")
    property_expected = {"Microsoft.Xna.Framework.P": TypeModel("Microsoft.Xna.Framework.P", "struct", members=[Member("Microsoft.Xna.Framework.P", "property", "Value", False, return_type="Int32", mutable=True)])}
    property_actual = {"Microsoft.Xna.Framework.P": TypeModel("Microsoft.Xna.Framework.P", "struct", members=[Member("Microsoft.Xna.Framework.P", "property", "Value", False, return_type="Int32", mutable=False, identifier="value")])}
    if "PROPERTY_MAPPING_MISMATCH" not in {item["category"] for item in compare(property_expected, property_actual)}:
        failures.append("property mutability mutation")
    unmeasured_actual = {"Microsoft.Xna.Framework.E": TypeModel("Microsoft.Xna.Framework.E", "enum", members=[Member("Microsoft.Xna.Framework.E", "field", "A", True, return_type="Microsoft.Xna.Framework.E", mutable=False, raw_value=None, identifier="a")])}
    if "UNMEASURED_STRUCTURAL_CATEGORY" not in {item["category"] for item in compare(enum_expected, unmeasured_actual)}:
        failures.append("unmeasured category mutation")

    rules = load_json(RULES)
    array_source = {
        "kind": "method", "name": "Transform", "static": True,
        "returnType": "System.Void", "parameters": [
            {"name": "sourceArray", "type": "Microsoft.Xna.Framework.Vector3[]"},
            {"name": "destinationArray", "type": "Microsoft.Xna.Framework.Vector3[]"},
        ],
    }
    array_member = expected_member("Microsoft.Xna.Framework.Vector3", array_source, rules, "struct")
    if array_member.directions != ("", "inout"):
        failures.append("array mutation language projection")

    corners_source = {
        "kind": "method", "name": "GetCorners", "static": False,
        "returnType": "System.Void", "parameters": [
            {"name": "corners", "type": "Microsoft.Xna.Framework.Vector3[]"},
        ],
    }
    corners_member = expected_member("Microsoft.Xna.Framework.BoundingBox", corners_source, rules, "struct")
    if corners_member.directions != ("inout",):
        failures.append("caller-owned corners array mutation projection")

    if map_clr_type("System.Nullable`1[System.Single]", rules) != "Float?":
        failures.append("nullable value projection")
    nullable_out_source = {
        "kind": "method", "name": "Intersects", "static": False,
        "returnType": "System.Void", "parameters": [
            {"name": "result", "type": "System.Nullable`1[System.Single]&", "out": True},
        ],
    }
    nullable_out_member = expected_member("Microsoft.Xna.Framework.Ray", nullable_out_source, rules, "struct")
    if nullable_out_member.parameters != ("Float?",) or nullable_out_member.directions != ("inout",):
        failures.append("nullable out projection")

    enumerable_type = "System.Collections.Generic.IEnumerable`1[Microsoft.Xna.Framework.Vector3]"
    if map_clr_type(enumerable_type, rules) != "[Microsoft.Xna.Framework.Vector3]":
        failures.append("generic enumerable array projection")

    suppressible = [diagnostic("MISSING_MEMBER", "Microsoft.Xna.Framework.Foo.Bar()", "mapped member is absent")]
    filtered, applied = apply_manual_suppressions(suppressible, [{
        "category": "MISSING_MEMBER", "subject": "Microsoft.Xna.Framework.Foo.Bar()",
    }])
    if filtered or applied != 1:
        failures.append("manual diagnostic suppression accounting")

    geometry_expected = {
        "Microsoft.Xna.Framework.Plane": TypeModel(
            "Microsoft.Xna.Framework.Plane", "struct",
            members=[Member("Microsoft.Xna.Framework.Plane", "method", "Intersects", False,
                            ("Microsoft.Xna.Framework.BoundingBox",), ("_",), ("",),
                            "Microsoft.Xna.Framework.PlaneIntersectionType")],
        ),
    }
    geometry_actual = {"Microsoft.Xna.Framework.Plane": TypeModel("Microsoft.Xna.Framework.Plane", "struct")}
    geometry_categories = {item["category"] for item in compare(geometry_expected, geometry_actual)}
    if "MISSING_MEMBER" not in geometry_categories:
        failures.append("geometry member hidden by language projection")

    packed = "Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVector"
    packed_generic = "Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVectorOfT"
    color = "Microsoft.Xna.Framework.Color"
    vector4 = "Microsoft.Xna.Framework.Vector4"
    packed_members = [
        Member(
            packed, "method", "ToVector4", False, return_type=vector4,
            self_mutating=False, identifier="to-vector4",
        ),
        Member(
            packed, "method", "PackFromVector4", False,
            (vector4,), ("_",), ("",), "Void", self_mutating=True,
            identifier="pack-from-vector4",
        ),
    ]
    packed_value = Member(
        packed_generic, "property", "PackedValue", False,
        return_type="TPacked", mutable=True, identifier="packed-value",
    )
    protocol_expected = {
        packed: TypeModel(packed, "protocol", members=copy.deepcopy(packed_members)),
        packed_generic: TypeModel(
            packed_generic, "protocol", interfaces=(packed,), generic_count=1,
            generic_parameters=("TPacked",), members=[copy.deepcopy(packed_value)],
        ),
        color: TypeModel(
            color, "struct", interfaces=(f"{packed_generic}<UInt32>",),
        ),
        vector4: TypeModel(vector4, "struct"),
    }
    protocol_good = copy.deepcopy(protocol_expected)

    def protocol_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(protocol_expected, models)}

    protocol_mutations: list[tuple[str, str, Any]] = [
        ("missing IPackedVector", "MISSING_TYPE", lambda m: m.pop(packed)),
        ("missing IPackedVectorOfT", "MISSING_TYPE", lambda m: m.pop(packed_generic)),
        ("wrong packed protocol kind", "TYPE_KIND_MISMATCH", lambda m: setattr(m[packed], "kind", "struct")),
        ("missing packed protocol inheritance", "INTERFACE_MAPPING_MISMATCH", lambda m: setattr(m[packed_generic], "interfaces", ())),
        ("wrong packed generic parameter", "GENERIC_MAPPING_MISMATCH", lambda m: setattr(m[packed_generic], "generic_parameters", ("TValue",))),
        ("wrong PackedValue type", "PROPERTY_MAPPING_MISMATCH", lambda m: setattr(m[packed_generic].members[0], "return_type", "UInt32")),
        ("read-only PackedValue", "PROPERTY_MAPPING_MISMATCH", lambda m: setattr(m[packed_generic].members[0], "mutable", False)),
        ("wrong PackFromVector4 argument", "PARAMETER_MAPPING_MISMATCH", lambda m: setattr(m[packed].members[1], "parameters", ("Float",))),
        ("nonmutating PackFromVector4", "METHOD_SIGNATURE_MAPPING_MISMATCH", lambda m: setattr(m[packed].members[1], "self_mutating", False)),
        ("wrong ToVector4 return", "RETURN_MAPPING_MISMATCH", lambda m: setattr(m[packed].members[0], "return_type", "Microsoft.Xna.Framework.Vector3")),
        ("Color missing packed conformance", "INTERFACE_MAPPING_MISMATCH", lambda m: setattr(m[color], "interfaces", ())),
        ("Color wrong packed type", "INTERFACE_MAPPING_MISMATCH", lambda m: setattr(m[color], "interfaces", (f"{packed_generic}<UInt16>",))),
    ]
    for label, wanted, mutate in protocol_mutations:
        models = copy.deepcopy(protocol_good)
        mutate(models)
        if wanted not in protocol_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    witness_requirement = Member(
        packed, "method", "PackFromVector4", False,
        (vector4,), ("_",), ("",), "Void", self_mutating=True,
        identifier="packed-requirement",
    )
    witness = dataclasses.replace(
        witness_requirement,
        owner="Microsoft.Xna.Framework.Graphics.PackedVector.Alpha8",
        identifier="alpha-witness",
    )
    if protocol_witness_shape_diagnostic(witness, witness_requirement) is not None:
        failures.append("valid concrete packed witness rejected")
    wrong_witness_return = dataclasses.replace(witness, return_type=vector4)
    wrong_return = protocol_witness_shape_diagnostic(
        wrong_witness_return, witness_requirement,
    )
    if wrong_return is None or wrong_return["category"] != "RETURN_MAPPING_MISMATCH":
        failures.append("wrong projected witness return not detected")
    nonmutating_witness = dataclasses.replace(witness, self_mutating=False)
    wrong_mutation = protocol_witness_shape_diagnostic(
        nonmutating_witness, witness_requirement,
    )
    if wrong_mutation is None or wrong_mutation["category"] != "METHOD_SIGNATURE_MAPPING_MISMATCH":
        failures.append("nonmutating projected witness not detected")

    contract = load_json(REFERENCE)
    configured_witnesses = [
        {
            "ownerType": identity.rsplit(".", 1)[0],
            "swiftMember": identity.rsplit(".", 1)[1],
        }
        for identity in rules["protocolWitnessMemberProjections"]
    ]
    _, complete_witness_diagnostics = protocol_witness_projection_evidence(
        contract, rules, configured_witnesses,
    )
    if complete_witness_diagnostics:
        failures.append("configured protocol-witness evidence is not contract-complete")
    _, missing_witness_diagnostics = protocol_witness_projection_evidence(
        contract, rules, configured_witnesses[1:],
    )
    if "LANGUAGE_MAPPING_MISMATCH" not in {
        item["category"] for item in missing_witness_diagnostics
    }:
        failures.append("removed required witness not detected")

    packed_extra_expected = {
        "Microsoft.Xna.Framework.Graphics.PackedVector.Alpha8": TypeModel(
            "Microsoft.Xna.Framework.Graphics.PackedVector.Alpha8", "struct",
        ),
    }
    packed_extra_actual = copy.deepcopy(packed_extra_expected)
    packed_extra_actual[next(iter(packed_extra_actual))].members.append(Member(
        next(iter(packed_extra_actual)), "method", "Unrelated", False,
        identifier="unrelated-packed-member",
    ))
    if "UNEXPECTED_MEMBER" not in {
        item["category"] for item in compare(packed_extra_expected, packed_extra_actual)
    }:
        failures.append("unrelated packed member hidden by witness projection")

    curve_key_name = "Microsoft.Xna.Framework.CurveKey"
    curve_collection_name = "Microsoft.Xna.Framework.CurveKeyCollection"
    curve_loop_name = "Microsoft.Xna.Framework.CurveLoopType"
    curve_key_compare = Member(
        curve_key_name, "method", "CompareTo", False,
        (f"{curve_key_name}?",), ("_",), ("",), "Int32",
        identifier="curve-compare",
    )
    curve_item = Member(
        curve_collection_name, "property", "Item", False,
        ("Int32",), ("_",), ("",), curve_key_name, mutable=False,
        identifier="curve-item", getter_throws=True,
        writer_kind=WRITER_METHOD, writer_name="SetItem", writer_throws=True,
    )
    curve_copy = Member(
        curve_collection_name, "method", "CopyTo", False,
        (f"[{curve_key_name}]", "Int32"), ("_", "arrayIndex"),
        ("inout", ""), "Void", identifier="curve-copy",
    )
    curve_enumerator = Member(
        curve_collection_name, "method", "GetEnumerator", False,
        return_type=f"CNAEnumerator<{curve_key_name}>",
        identifier="curve-enumerator",
        declaration=f"func GetEnumerator() -> CNAEnumerator<{curve_key_name}>",
    )
    curve_count = Member(
        curve_collection_name, "property", "Count", False,
        return_type="Int32", mutable=False, identifier="curve-count",
    )
    curve_read_only = Member(
        curve_collection_name, "property", "IsReadOnly", False,
        return_type="Bool", mutable=False, identifier="curve-read-only",
    )
    curve_expected = {
        curve_key_name: TypeModel(
            curve_key_name, "class", members=[copy.deepcopy(curve_key_compare)],
        ),
        curve_collection_name: TypeModel(
            curve_collection_name, "class", members=[
                copy.deepcopy(curve_item), copy.deepcopy(curve_copy),
                copy.deepcopy(curve_enumerator), copy.deepcopy(curve_count),
                copy.deepcopy(curve_read_only),
            ],
        ),
        curve_loop_name: TypeModel(
            curve_loop_name, "enum", members=[Member(
                curve_loop_name, "field", "CycleOffset", True,
                return_type=curve_loop_name, mutable=False, raw_value=2,
                identifier="curve-loop-cycle-offset",
            )],
        ),
    }
    curve_good = copy.deepcopy(curve_expected)

    def curve_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(curve_expected, models)}

    curve_mutations: list[tuple[str, str, Any]] = [
        ("CurveKeyCollection wrong kind", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[curve_collection_name], "kind", "struct")),
        ("missing collection member", "MISSING_MEMBER",
         lambda m: m[curve_collection_name].members.pop()),
        ("unwanted Swift Collection witness", "UNEXPECTED_MEMBER",
         lambda m: m[curve_collection_name].members.append(Member(
             curve_collection_name, "property", "startIndex", False,
             return_type="Int", mutable=False, identifier="start-index",
         ))),
        ("wrong enumerator element", "RETURN_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[2], "return_type",
                           "CNAEnumerator<Float>")),
        ("missing Item getter", "MISSING_MEMBER",
         lambda m: m[curve_collection_name].members.pop(0)),
        ("missing Item writer method", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "writer_kind",
                           WRITER_ABSENT)),
        ("Item writer drops throws", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "writer_throws", False)),
        ("ordinary setter retained beside SetItem", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "mutable", True)),
        ("Item reader drops get throws", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "getter_throws", False)),
        ("Item wrong index type", "PARAMETER_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "parameters", ("Int",))),
        ("Item wrong element type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "return_type", "Float")),
        ("CopyTo wrong mutation direction", "REF_OUT_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[1], "directions", ("", ""))),
        ("Count wrong type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[3], "return_type", "Int")),
        ("IsReadOnly writable", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[4], "mutable", True)),
        ("CompareTo wrong parameter", "PARAMETER_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_key_name].members[0], "parameters", ("Float",))),
        ("CompareTo wrong return", "RETURN_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_key_name].members[0], "return_type", "Bool")),
        ("CurveLoopType wrong raw value", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(m[curve_loop_name].members[0], "raw_value", 3)),
    ]
    curve_baseline_self_tests = 1
    if curve_categories(curve_good):
        failures.append("clean curve model is not diagnostic-free")
    for label, wanted, mutate in curve_mutations:
        models = copy.deepcopy(curve_good)
        mutate(models)
        if wanted not in curve_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    setter_good = Member(
        curve_collection_name, "method", "SetItem", False,
        ("Int32", curve_key_name), ("_", "_"), ("", ""), "Void",
        identifier="curve-set-item",
        declaration="func SetItem(_ index: Int32, _ value: CurveKey) throws",
    )
    accessor_writer_self_tests = 1
    if writer_method_shape_diagnostics(
        curve_collection_name, setter_good, curve_item,
    ):
        failures.append("valid indexed-property writer rejected")
    writer_mutations = [
        ("wrong writer index type", "PARAMETER_MAPPING_MISMATCH",
         dict(parameters=("Int", curve_key_name))),
        ("wrong writer element type", "PARAMETER_MAPPING_MISMATCH",
         dict(parameters=("Int32", "Float"))),
        ("writer returns a value", "RETURN_MAPPING_MISMATCH",
         dict(return_type="Bool")),
        ("writer static identity flipped", "METHOD_SIGNATURE_MAPPING_MISMATCH",
         dict(static=True)),
        ("writer parameter direction differs", "REF_OUT_MAPPING_MISMATCH",
         dict(directions=("inout", ""))),
        ("writer drops throws", "PROPERTY_MAPPING_MISMATCH",
         dict(declaration="func SetItem(_ index: Int32, _ value: CurveKey)")),
    ]
    for label, wanted, overrides in writer_mutations:
        broken = dataclasses.replace(setter_good, **overrides)
        if wanted not in {
            item["category"] for item in writer_method_shape_diagnostics(
                curve_collection_name, broken, curve_item,
            )
        }:
            failures.append(f"{label}: did not produce {wanted}")
        accessor_writer_self_tests += 1
    accessor_writer_self_tests += 2
    # Every branch of the general accessor rule, including the four the pinned
    # contract never exercises. An unexercised branch that no test touches is
    # an unmeasured category; these make all twelve a measured number.
    accessor_rule_cases = [
        # (indexed, getter fallible, setter declared, setter fallible)
        #     -> (expected get throws, writer kind, writer throws, writer name)
        ((False, False, False, False), (False, WRITER_ABSENT, False, None)),
        ((False, False, True, False), (False, WRITER_PROPERTY, False, None)),
        ((False, False, True, True), (False, WRITER_METHOD, True, "SetP")),
        ((False, True, False, False), (True, WRITER_ABSENT, False, None)),
        ((False, True, True, True), (True, WRITER_METHOD, True, "SetP")),
        ((False, True, True, False), (True, WRITER_METHOD, False, "SetP")),
        ((True, False, False, False), (False, WRITER_ABSENT, False, None)),
        ((True, False, True, False), (False, WRITER_PROPERTY, False, None)),
        ((True, False, True, True), (False, WRITER_METHOD, True, "SetItem")),
        ((True, True, False, False), (True, WRITER_ABSENT, False, None)),
        ((True, True, True, True), (True, WRITER_METHOD, True, "SetItem")),
        ((True, True, True, False), (True, WRITER_METHOD, False, "SetItem")),
    ]
    for (indexed, get_fallible, has_set, set_fallible), wanted in accessor_rule_cases:
        source = {
            "kind": "property", "name": "P", "type": "System.Single",
            "static": False, "get": True, "set": has_set,
            "parameters": [{"name": "index", "type": "System.Int32"}] if indexed else [],
        }
        verdict = {"getter": get_fallible, "setter": set_fallible}
        observed = accessor_projection(source, verdict)
        if observed != wanted[:3]:
            failures.append(
                f"accessor rule {(indexed, get_fallible, has_set, set_fallible)}: "
                f"expected {wanted[:3]}, produced {observed}")
        accessor_writer_self_tests += 1
        member = expected_member(
            "Microsoft.Xna.Framework.Foo", source, rules, "class",
            accessor_verdict=verdict,
        )
        if (member.getter_throws, member.writer_kind, member.writer_throws,
                member.writer_name) != wanted:
            failures.append(
                f"expected_member {(indexed, get_fallible, has_set, set_fallible)}: "
                f"expected {wanted}, produced "
                f"{(member.getter_throws, member.writer_kind, member.writer_throws, member.writer_name)}")
        if member.mutable != (member.writer_kind == WRITER_PROPERTY):
            failures.append(
                "a property whose writer is a method must not be Swift-mutable")
        accessor_writer_self_tests += 2

    # A write-only CLR property projects only its writer; no getter is invented.
    for set_fallible in (False, True):
        write_only = {
            "kind": "property", "name": "P", "type": "System.Single",
            "static": True, "get": False, "set": True, "parameters": [],
        }
        member = expected_member(
            "Microsoft.Xna.Framework.Foo", write_only, rules, "class",
            accessor_verdict={"getter": False, "setter": set_fallible},
        )
        if member.writer_kind != (WRITER_METHOD if set_fallible else WRITER_PROPERTY):
            failures.append("write-only projection ignored its setter fallibility")
        if member.getter_throws:
            failures.append("a write-only property must not invent a throwing getter")
        if not member.static:
            failures.append("a static CLR setter must project to a static writer")
        accessor_writer_self_tests += 3

    # The writer name preserves XNA capitalisation and is never invented.
    for name, indexed, wanted_name in (
        ("Viewport", False, "SetViewport"), ("DopplerScale", False, "SetDopplerScale"),
        ("Item", True, "SetItem"), ("foo", False, "Setfoo"),
    ):
        if writer_method_name(name, indexed) != wanted_name:
            failures.append(f"writer name for {name} is not {wanted_name}")
        accessor_writer_self_tests += 1

    mutating_requirement = dataclasses.replace(curve_item, writer_self_mutating=True)
    if "METHOD_SIGNATURE_MAPPING_MISMATCH" not in {
        item["category"] for item in writer_method_shape_diagnostics(
            curve_collection_name,
            dataclasses.replace(setter_good, self_mutating=False),
            mutating_requirement,
        )
    }:
        failures.append("a nonmutating writer for a mutating requirement is not detected")
    infallible_item = dataclasses.replace(curve_item, writer_throws=False)
    if "PROPERTY_MAPPING_MISMATCH" not in {
        item["category"] for item in writer_method_shape_diagnostics(
            curve_collection_name, setter_good, infallible_item,
        )
    }:
        failures.append("a writer that throws for an infallible setter is not detected")

    comparable_contract = {"types": [{
        "name": curve_key_name,
        "directInterfaces": [f"System.IComparable`1[{curve_key_name}]"],
        "members": [{"name": "CompareTo"}],
    }]}
    missing_comparable_rules = copy.deepcopy(rules)
    missing_comparable_rules["requiredSystemInterfaceProjections"] = [
        "System.IComparable`1",
    ]
    missing_comparable_rules["systemInterfaceMappings"].pop("System.IComparable`1")
    _, missing_comparable_diagnostics = system_interface_projection_evidence(
        comparable_contract, missing_comparable_rules,
    )
    if "LANGUAGE_MAPPING_MISMATCH" not in {
        item["category"] for item in missing_comparable_diagnostics
    }:
        failures.append("missing IComparable<T> projection not detected")

    collection_contract = {"types": [{
        "name": curve_collection_name,
        "directInterfaces": [
            f"System.Collections.Generic.ICollection`1[{curve_key_name}]",
        ],
        "members": [
            {"name": name} for name in (
                "Add", "Clear", "Contains", "CopyTo", "Remove", "Count",
                "IsReadOnly",
            )
        ],
    }]}
    missing_collection_rules = copy.deepcopy(rules)
    missing_collection_rules["requiredSystemInterfaceProjections"] = [
        "System.Collections.Generic.ICollection`1",
    ]
    missing_collection_rules["systemInterfaceMappings"].pop(
        "System.Collections.Generic.ICollection`1",
    )
    _, missing_collection_diagnostics = system_interface_projection_evidence(
        collection_contract, missing_collection_rules,
    )
    if "LANGUAGE_MAPPING_MISMATCH" not in {
        item["category"] for item in missing_collection_diagnostics
    }:
        failures.append("missing ICollection<T> projection not detected")

    gamepad_type_names = {
        "Microsoft.Xna.Framework.Input.ButtonState",
        "Microsoft.Xna.Framework.Input.Buttons",
        "Microsoft.Xna.Framework.Input.GamePad",
        "Microsoft.Xna.Framework.Input.GamePadButtons",
        "Microsoft.Xna.Framework.Input.GamePadCapabilities",
        "Microsoft.Xna.Framework.Input.GamePadDPad",
        "Microsoft.Xna.Framework.Input.GamePadDeadZone",
        "Microsoft.Xna.Framework.Input.GamePadState",
        "Microsoft.Xna.Framework.Input.GamePadThumbSticks",
        "Microsoft.Xna.Framework.Input.GamePadTriggers",
        "Microsoft.Xna.Framework.Input.GamePadType",
    }
    all_expected = build_expected(contract, rules)
    gamepad_expected = {
        name: copy.deepcopy(model) for name, model in all_expected.items()
        if name in gamepad_type_names
    }
    gamepad_good = copy.deepcopy(gamepad_expected)
    buttons_name = "Microsoft.Xna.Framework.Input.Buttons"
    gamepad_name = "Microsoft.Xna.Framework.Input.GamePad"
    gamepad_buttons_name = "Microsoft.Xna.Framework.Input.GamePadButtons"
    capabilities_name = "Microsoft.Xna.Framework.Input.GamePadCapabilities"
    dpad_name = "Microsoft.Xna.Framework.Input.GamePadDPad"
    state_name = "Microsoft.Xna.Framework.Input.GamePadState"
    sticks_name = "Microsoft.Xna.Framework.Input.GamePadThumbSticks"
    triggers_name = "Microsoft.Xna.Framework.Input.GamePadTriggers"

    for model in gamepad_good.values():
        model.identifier = model.name
        for index, member in enumerate(model.members):
            member.identifier = f"{model.name}:{index}"

    def gamepad_member(
        models: dict[str, TypeModel], owner: str, name: str,
        arity: int | None = None,
    ) -> Member:
        return next(
            member for member in models[owner].members
            if member.name == name and (arity is None or len(member.parameters) == arity)
        )

    def gamepad_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(gamepad_expected, models)}

    gamepad_mutations: list[tuple[str, str, Any]] = [
        ("Buttons normal enum", "FLAGS_MAPPING_MISMATCH",
         lambda m: (setattr(m[buttons_name], "kind", "enum"), setattr(m[buttons_name], "flags", False))),
        ("Buttons wrong raw type", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[buttons_name], "raw_type", "UInt32")),
        ("Buttons wrong A constant", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(gamepad_member(m, buttons_name, "A"), "raw_value", 4097)),
        ("Buttons missing BigButton", "MISSING_MEMBER",
         lambda m: m[buttons_name].members.remove(gamepad_member(m, buttons_name, "BigButton"))),
        ("Buttons wrong high-bit constant", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(gamepad_member(m, buttons_name, "LeftThumbstickRight"), "raw_value", 1)),
        ("Buttons flags metadata absent", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[buttons_name], "flags", False)),
        ("GamePadButtons invented virtual property", "UNEXPECTED_MEMBER",
         lambda m: m[gamepad_buttons_name].members.append(Member(
             gamepad_buttons_name, "property", "LeftTrigger", False,
             return_type="ButtonState", mutable=False, identifier="invented-virtual",
         ))),
        ("GamePadDPad constructor order", "PARAMETER_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, dpad_name, ".ctor"), "parameter_names",
                           ("upValue", "downValue", "rightValue", "leftValue"))),
        ("GamePadTriggers writable property", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, triggers_name, "Left"), "mutable", True)),
        ("GamePadThumbSticks wrong Vector2", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, sticks_name, "Left"), "return_type", "Vector3")),
        ("GamePadCapabilities public constructor", "UNEXPECTED_MEMBER",
         lambda m: m[capabilities_name].members.append(Member(
             capabilities_name, "constructor", ".ctor", False,
             identifier="public-capabilities-constructor",
         ))),
        ("GamePadCapabilities missing property", "MISSING_MEMBER",
         lambda m: m[capabilities_name].members.remove(
             gamepad_member(m, capabilities_name, "HasVoiceSupport")
         )),
        ("GamePadState missing second constructor", "MISSING_MEMBER",
         lambda m: m[state_name].members.remove(gamepad_member(m, state_name, ".ctor", 5))),
        ("GamePadState Buttons array projected scalar", "PARAMETER_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, state_name, ".ctor", 5), "parameters",
                           ("Microsoft.Xna.Framework.Vector2", "Microsoft.Xna.Framework.Vector2",
                            "Float", "Float", buttons_name))),
        ("GamePadState invented typed Equals", "UNEXPECTED_MEMBER",
         lambda m: m[state_name].members.append(Member(
             state_name, "method", "Equals", False, (state_name,), ("_",), ("",),
             "Bool", identifier="typed-state-equals",
         ))),
        ("GamePadState wrong PacketNumber type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, state_name, "PacketNumber"), "return_type", "UInt32")),
        ("GamePad constructible", "UNEXPECTED_MEMBER",
         lambda m: m[gamepad_name].members.append(Member(
             gamepad_name, "constructor", ".ctor", False, identifier="gamepad-constructor",
         ))),
        ("GamePad GetState not static", "METHOD_SIGNATURE_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, gamepad_name, "GetState", 1), "static", False)),
        ("GamePad missing GetState overload", "MISSING_MEMBER",
         lambda m: m[gamepad_name].members.remove(gamepad_member(m, gamepad_name, "GetState", 2))),
        ("GamePad wrong dead-zone argument", "PARAMETER_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, gamepad_name, "GetState", 2), "parameters",
                           ("Microsoft.Xna.Framework.PlayerIndex", "Int32"))),
        ("GamePad GetCapabilities wrong return", "RETURN_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, gamepad_name, "GetCapabilities"), "return_type", state_name)),
        ("GamePad SetVibration wrong return", "RETURN_MAPPING_MISMATCH",
         lambda m: setattr(gamepad_member(m, gamepad_name, "SetVibration"), "return_type", "Void")),
        ("GamePad public native handle", "RAW_HANDLE_LEAK",
         lambda m: m[gamepad_name].members.append(Member(
             gamepad_name, "property", "nativeHandle", True,
             return_type="UInt64", mutable=False,
             declaration="static let nativeHandle: UInt64", identifier="native-handle",
         ))),
        ("GamePad raw native state return", "PUBLIC_NATIVE_FFI_LEAK",
         lambda m: (
             setattr(gamepad_member(m, gamepad_name, "GetState", 1),
                     "return_type", "CNASwift_GamePadState"),
             setattr(gamepad_member(m, gamepad_name, "GetState", 1),
                     "declaration", "func GetState(_ playerIndex: PlayerIndex) -> CNASwift_GamePadState")
         )),
    ]
    for label, wanted, mutate in gamepad_mutations:
        models = copy.deepcopy(gamepad_good)
        mutate(models)
        if wanted not in gamepad_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    display_name = "Microsoft.Xna.Framework.DisplayOrientation"
    display_expected = {
        display_name: copy.deepcopy(all_expected[display_name]),
    }
    display_good = copy.deepcopy(display_expected)
    display_good[display_name].identifier = display_name
    for index, member in enumerate(display_good[display_name].members):
        member.identifier = f"{display_name}:{index}"

    def display_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(member for member in models[display_name].members if member.name == name)

    def display_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(display_expected, models)}

    display_mutations: list[tuple[str, str, Any]] = [
        ("DisplayOrientation missing type", "MISSING_TYPE",
         lambda m: m.pop(display_name)),
        ("DisplayOrientation normal enum", "FLAGS_MAPPING_MISMATCH",
         lambda m: (setattr(m[display_name], "kind", "enum"),
                    setattr(m[display_name], "flags", False))),
        ("DisplayOrientation wrong raw type", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[display_name], "raw_type", "UInt32")),
        ("DisplayOrientation wrong Default", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(display_member(m, "Default"), "raw_value", 1)),
        ("DisplayOrientation wrong LandscapeLeft", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(display_member(m, "LandscapeLeft"), "raw_value", 2)),
        ("DisplayOrientation wrong LandscapeRight", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(display_member(m, "LandscapeRight"), "raw_value", 4)),
        ("DisplayOrientation wrong Portrait", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(display_member(m, "Portrait"), "raw_value", 8)),
        ("DisplayOrientation missing Portrait", "MISSING_MEMBER",
         lambda m: m[display_name].members.remove(display_member(m, "Portrait"))),
        ("DisplayOrientation wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.Graphics.DisplayOrientation",
             m.pop(display_name),
         )),
        ("DisplayOrientation flags metadata absent", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[display_name], "flags", False)),
        ("DisplayOrientation unexpected declared member", "UNEXPECTED_MEMBER",
         lambda m: m[display_name].members.append(Member(
             display_name, "method", "IsLandscape", False,
             identifier="invented-display-orientation-member",
         ))),
    ]
    for label, wanted, mutate in display_mutations:
        models = copy.deepcopy(display_good)
        mutate(models)
        if wanted not in display_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if any(member.name == "value__" for member in display_expected[display_name].members):
        failures.append("DisplayOrientation value__ was not excluded from the Swift contract")
    display_value_storage_expected = copy.deepcopy(display_expected)
    display_value_storage_expected[display_name].members.append(Member(
        display_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-required-enum-storage",
    ))
    if "MISSING_MEMBER" not in {
        item["category"] for item in compare(
            display_value_storage_expected, display_good,
        )
    }:
        failures.append("DisplayOrientation value__ treated as required did not fail")

    buffer_name = "Microsoft.Xna.Framework.Graphics.BufferUsage"
    buffer_expected = {
        buffer_name: copy.deepcopy(all_expected[buffer_name]),
    }
    buffer_good = copy.deepcopy(buffer_expected)
    buffer_good[buffer_name].identifier = buffer_name
    for index, member in enumerate(buffer_good[buffer_name].members):
        member.identifier = f"{buffer_name}:{index}"

    def buffer_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(member for member in models[buffer_name].members if member.name == name)

    def buffer_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(buffer_expected, models)}

    buffer_mutations: list[tuple[str, str, Any]] = [
        ("BufferUsage missing type", "MISSING_TYPE",
         lambda m: m.pop(buffer_name)),
        ("BufferUsage wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.BufferUsage",
             m.pop(buffer_name),
         )),
        ("BufferUsage normal enum", "TYPE_KIND_MISMATCH",
         lambda m: (setattr(m[buffer_name], "kind", "enum"),
                    setattr(m[buffer_name], "flags", False))),
        ("BufferUsage wrong raw type", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[buffer_name], "raw_type", "UInt32")),
        ("BufferUsage flags metadata absent", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[buffer_name], "flags", False)),
        ("BufferUsage wrong None", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(buffer_member(m, "None"), "raw_value", 1)),
        ("BufferUsage wrong WriteOnly", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(buffer_member(m, "WriteOnly"), "raw_value", 2)),
        ("BufferUsage missing WriteOnly", "MISSING_MEMBER",
         lambda m: m[buffer_name].members.remove(buffer_member(m, "WriteOnly"))),
        ("BufferUsage unexpected declared field", "UNEXPECTED_MEMBER",
         lambda m: m[buffer_name].members.append(Member(
             buffer_name, "field", "ReadOnly", True,
             return_type=buffer_name, mutable=False, raw_value=2,
             identifier="invented-buffer-usage-field",
         ))),
        ("BufferUsage public description helper", "UNEXPECTED_MEMBER",
         lambda m: m[buffer_name].members.append(Member(
             buffer_name, "property", "description", False,
             return_type="String", mutable=False,
             identifier="invented-buffer-usage-description",
         ))),
        ("BufferUsage malformed OptionSet conformance", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[buffer_name], "flags", False)),
    ]
    for label, wanted, mutate in buffer_mutations:
        models = copy.deepcopy(buffer_good)
        mutate(models)
        if wanted not in buffer_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if any(member.name == "value__" for member in buffer_expected[buffer_name].members):
        failures.append("BufferUsage value__ was not excluded from the Swift contract")
    buffer_value_storage_expected = copy.deepcopy(buffer_expected)
    buffer_value_storage_expected[buffer_name].members.append(Member(
        buffer_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-required-buffer-usage-storage",
    ))
    if "MISSING_MEMBER" not in {
        item["category"] for item in compare(
            buffer_value_storage_expected, buffer_good,
        )
    }:
        failures.append("BufferUsage value__ treated as required did not fail")

    fill_name = "Microsoft.Xna.Framework.Graphics.FillMode"
    fill_expected = {
        fill_name: copy.deepcopy(all_expected[fill_name]),
    }
    fill_good = copy.deepcopy(fill_expected)
    fill_good[fill_name].identifier = fill_name
    for index, member in enumerate(fill_good[fill_name].members):
        member.identifier = f"{fill_name}:{index}"

    def fill_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(member for member in models[fill_name].members if member.name == name)

    def fill_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(fill_expected, models)}

    fill_mutations: list[tuple[str, str, Any]] = [
        ("FillMode missing type", "MISSING_TYPE",
         lambda m: m.pop(fill_name)),
        ("FillMode wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.FillMode",
             m.pop(fill_name),
         )),
        ("FillMode struct instead of enum", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[fill_name], "kind", "struct")),
        ("FillMode OptionSet instead of ordinary enum", "FLAGS_MAPPING_MISMATCH",
         lambda m: (setattr(m[fill_name], "kind", "struct"),
                    setattr(m[fill_name], "flags", True))),
        ("FillMode wrong raw type", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[fill_name], "raw_type", "UInt32")),
        ("FillMode flags metadata present", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[fill_name], "flags", True)),
        ("FillMode wrong Solid", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(fill_member(m, "Solid"), "raw_value", 1)),
        ("FillMode wrong WireFrame", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(fill_member(m, "WireFrame"), "raw_value", 2)),
        ("FillMode missing WireFrame", "MISSING_MEMBER",
         lambda m: m[fill_name].members.remove(fill_member(m, "WireFrame"))),
        ("FillMode unexpected third enum case", "UNEXPECTED_MEMBER",
         lambda m: m[fill_name].members.append(Member(
             fill_name, "field", "Point", True,
             return_type=fill_name, mutable=False, raw_value=2,
             identifier="invented-fill-mode-case",
         ))),
        ("FillMode public description helper", "UNEXPECTED_MEMBER",
         lambda m: m[fill_name].members.append(Member(
             fill_name, "property", "description", False,
             return_type="String", mutable=False,
             identifier="invented-fill-mode-description",
         ))),
    ]
    for label, wanted, mutate in fill_mutations:
        models = copy.deepcopy(fill_good)
        mutate(models)
        if wanted not in fill_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if any(member.name == "value__" for member in fill_expected[fill_name].members):
        failures.append("FillMode value__ was not excluded from the Swift contract")
    fill_value_storage_expected = copy.deepcopy(fill_expected)
    fill_value_storage_expected[fill_name].members.append(Member(
        fill_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-required-fill-mode-storage",
    ))
    if "MISSING_MEMBER" not in {
        item["category"] for item in compare(
            fill_value_storage_expected, fill_good,
        )
    }:
        failures.append("FillMode value__ treated as required did not fail")

    surface_name = "Microsoft.Xna.Framework.Graphics.SurfaceFormat"
    surface_expected = {
        surface_name: copy.deepcopy(all_expected[surface_name]),
    }
    surface_good = copy.deepcopy(surface_expected)
    surface_good[surface_name].identifier = surface_name
    for index, member in enumerate(surface_good[surface_name].members):
        member.identifier = f"{surface_name}:{index}"

    def surface_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(
            member for member in models[surface_name].members
            if member.name == name
        )

    def surface_categories(models: dict[str, TypeModel]) -> set[str]:
        return {
            item["category"] for item in compare(surface_expected, models)
        }

    surface_mutations: list[tuple[str, str, Any]] = [
        ("SurfaceFormat missing type", "MISSING_TYPE",
         lambda m: m.pop(surface_name)),
        ("SurfaceFormat wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.SurfaceFormat",
             m.pop(surface_name),
         )),
        ("SurfaceFormat struct instead of enum", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[surface_name], "kind", "struct")),
        ("SurfaceFormat OptionSet instead of ordinary enum", "FLAGS_MAPPING_MISMATCH",
         lambda m: (setattr(m[surface_name], "kind", "struct"),
                    setattr(m[surface_name], "flags", True))),
        ("SurfaceFormat wrong raw type", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[surface_name], "raw_type", "UInt32")),
        ("SurfaceFormat flags metadata present", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[surface_name], "flags", True)),
        ("SurfaceFormat wrong Color", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "Color"), "raw_value", 1)),
        ("SurfaceFormat wrong Bgr565", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "Bgr565"), "raw_value", 2)),
        ("SurfaceFormat wrong Dxt1", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "Dxt1"), "raw_value", 5)),
        ("SurfaceFormat wrong NormalizedByte4", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "NormalizedByte4"), "raw_value", 9)),
        ("SurfaceFormat wrong Rgba1010102", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "Rgba1010102"), "raw_value", 10)),
        ("SurfaceFormat wrong Alpha8", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "Alpha8"), "raw_value", 13)),
        ("SurfaceFormat wrong HalfVector4", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "HalfVector4"), "raw_value", 19)),
        ("SurfaceFormat wrong HdrBlendable", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(surface_member(m, "HdrBlendable"), "raw_value", 20)),
        ("SurfaceFormat missing middle case", "MISSING_MEMBER",
         lambda m: m[surface_name].members.remove(surface_member(m, "Rg32"))),
        ("SurfaceFormat missing HdrBlendable", "MISSING_MEMBER",
         lambda m: m[surface_name].members.remove(surface_member(m, "HdrBlendable"))),
        ("SurfaceFormat unexpected extra enum case", "UNEXPECTED_MEMBER",
         lambda m: m[surface_name].members.append(Member(
             surface_name, "field", "Unknown", True,
             return_type=surface_name, mutable=False, raw_value=20,
             identifier="invented-surface-format-case",
         ))),
        ("SurfaceFormat public description helper", "UNEXPECTED_MEMBER",
         lambda m: m[surface_name].members.append(Member(
             surface_name, "property", "description", False,
             return_type="String", mutable=False,
             identifier="invented-surface-format-description",
         ))),
    ]
    for label, wanted, mutate in surface_mutations:
        models = copy.deepcopy(surface_good)
        mutate(models)
        if wanted not in surface_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if any(
        member.name == "value__"
        for member in surface_expected[surface_name].members
    ):
        failures.append("SurfaceFormat value__ was not excluded from the Swift contract")
    surface_value_storage_expected = copy.deepcopy(surface_expected)
    surface_value_storage_expected[surface_name].members.append(Member(
        surface_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-required-surface-format-storage",
    ))
    if "MISSING_MEMBER" not in {
        item["category"] for item in compare(
            surface_value_storage_expected, surface_good,
        )
    }:
        failures.append("SurfaceFormat value__ treated as required did not fail")

    depth_name = "Microsoft.Xna.Framework.Graphics.DepthFormat"
    depth_expected = {
        depth_name: copy.deepcopy(all_expected[depth_name]),
    }
    depth_good = copy.deepcopy(depth_expected)
    depth_good[depth_name].identifier = depth_name
    for index, member in enumerate(depth_good[depth_name].members):
        member.identifier = f"{depth_name}:{index}"

    def depth_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(
            member for member in models[depth_name].members
            if member.name == name
        )

    def depth_categories(models: dict[str, TypeModel]) -> set[str]:
        return {
            item["category"] for item in compare(depth_expected, models)
        }

    depth_mutations: list[tuple[str, str, Any]] = [
        ("DepthFormat missing type", "MISSING_TYPE",
         lambda m: m.pop(depth_name)),
        ("DepthFormat wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.DepthFormat",
             m.pop(depth_name),
         )),
        ("DepthFormat struct instead of enum", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[depth_name], "kind", "struct")),
        ("DepthFormat OptionSet instead of ordinary enum", "FLAGS_MAPPING_MISMATCH",
         lambda m: (setattr(m[depth_name], "kind", "struct"),
                    setattr(m[depth_name], "flags", True))),
        ("DepthFormat wrong raw type", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[depth_name], "raw_type", "UInt32")),
        ("DepthFormat flags metadata present", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[depth_name], "flags", True)),
        ("DepthFormat wrong None", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(depth_member(m, "None"), "raw_value", 1)),
        ("DepthFormat wrong Depth16", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(depth_member(m, "Depth16"), "raw_value", 2)),
        ("DepthFormat wrong Depth24", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(depth_member(m, "Depth24"), "raw_value", 3)),
        ("DepthFormat wrong Depth24Stencil8", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(depth_member(m, "Depth24Stencil8"), "raw_value", 4)),
        ("DepthFormat missing Depth24", "MISSING_MEMBER",
         lambda m: m[depth_name].members.remove(depth_member(m, "Depth24"))),
        ("DepthFormat missing Depth24Stencil8", "MISSING_MEMBER",
         lambda m: m[depth_name].members.remove(depth_member(m, "Depth24Stencil8"))),
        ("DepthFormat renamed Depth24Stencil8", "MISSING_MEMBER",
         lambda m: setattr(depth_member(m, "Depth24Stencil8"), "name", "Depth24Stencil")),
        ("DepthFormat unexpected extra enum case", "UNEXPECTED_MEMBER",
         lambda m: m[depth_name].members.append(Member(
             depth_name, "field", "Depth32", True,
             return_type=depth_name, mutable=False, raw_value=4,
             identifier="invented-depth-format-case",
         ))),
        ("DepthFormat public description helper", "UNEXPECTED_MEMBER",
         lambda m: m[depth_name].members.append(Member(
             depth_name, "property", "description", False,
             return_type="String", mutable=False,
             identifier="invented-depth-format-description",
         ))),
    ]
    for label, wanted, mutate in depth_mutations:
        models = copy.deepcopy(depth_good)
        mutate(models)
        if wanted not in depth_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if any(
        member.name == "value__"
        for member in depth_expected[depth_name].members
    ):
        failures.append("DepthFormat value__ was not excluded from the Swift contract")
    depth_value_storage_expected = copy.deepcopy(depth_expected)
    depth_value_storage_expected[depth_name].members.append(Member(
        depth_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-required-depth-format-storage",
    ))
    if "MISSING_MEMBER" not in {
        item["category"] for item in compare(
            depth_value_storage_expected, depth_good,
        )
    }:
        failures.append("DepthFormat value__ treated as required did not fail")

    mode_name = "Microsoft.Xna.Framework.Graphics.DisplayMode"
    mode_expected = {
        mode_name: copy.deepcopy(all_expected[mode_name]),
    }
    mode_good = copy.deepcopy(mode_expected)
    mode_good[mode_name].identifier = mode_name
    for index, member in enumerate(mode_good[mode_name].members):
        member.identifier = f"{mode_name}:{index}"

    def mode_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(
            member for member in models[mode_name].members
            if member.name == name
        )

    def mode_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(mode_expected, models)}

    def mode_extra(name: str, **overrides: Any) -> Any:
        defaults: dict[str, Any] = {
            "kind": "method", "static": False, "return_type": "Void",
            "identifier": f"invented-display-mode-{name}",
        }
        defaults.update(overrides)
        return lambda m: m[mode_name].members.append(Member(
            mode_name, defaults["kind"], name, defaults["static"],
            parameters=defaults.get("parameters", ()),
            labels=defaults.get("labels", ()),
            directions=defaults.get("directions", ()),
            return_type=defaults["return_type"],
            mutable=defaults.get("mutable"),
            identifier=defaults["identifier"],
        ))

    mode_mutations: list[tuple[str, str, Any]] = [
        ("DisplayMode missing type", "MISSING_TYPE",
         lambda m: m.pop(mode_name)),
        ("DisplayMode wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.DisplayMode", m.pop(mode_name),
         )),
        ("DisplayMode struct instead of class", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[mode_name], "kind", "struct")),
        ("DisplayMode protocol instead of class", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[mode_name], "kind", "protocol")),
        ("DisplayMode enum instead of class", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[mode_name], "kind", "enum")),
        ("DisplayMode missing ToString", "MISSING_MEMBER",
         lambda m: m[mode_name].members.remove(mode_member(m, "ToString"))),
        ("DisplayMode ToString wrong return type", "RETURN_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "ToString"), "return_type", "Int32")),
        ("DisplayMode ToString wrong arity", "OVERLOAD_MAPPING_MISMATCH",
         lambda m: (setattr(mode_member(m, "ToString"), "parameters", ("Int32",)),
                    setattr(mode_member(m, "ToString"), "labels", ("_",)),
                    setattr(mode_member(m, "ToString"), "directions", ("",)))),
        ("DisplayMode ToString as property", "METHOD_SIGNATURE_MAPPING_MISMATCH",
         lambda m: (setattr(mode_member(m, "ToString"), "kind", "property"),
                    setattr(mode_member(m, "ToString"), "mutable", False))),
        ("DisplayMode ToString static", "METHOD_SIGNATURE_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "ToString"), "static", True)),
        ("DisplayMode missing Format", "MISSING_MEMBER",
         lambda m: m[mode_name].members.remove(mode_member(m, "Format"))),
        ("DisplayMode missing Width", "MISSING_MEMBER",
         lambda m: m[mode_name].members.remove(mode_member(m, "Width"))),
        ("DisplayMode missing Height", "MISSING_MEMBER",
         lambda m: m[mode_name].members.remove(mode_member(m, "Height"))),
        ("DisplayMode missing AspectRatio", "MISSING_MEMBER",
         lambda m: m[mode_name].members.remove(mode_member(m, "AspectRatio"))),
        ("DisplayMode missing TitleSafeArea", "MISSING_MEMBER",
         lambda m: m[mode_name].members.remove(mode_member(m, "TitleSafeArea"))),
        ("DisplayMode Format wrong type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "Format"), "return_type", "Int32")),
        ("DisplayMode Width wrong type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "Width"), "return_type", "Int64")),
        ("DisplayMode Height wrong type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "Height"), "return_type", "Float")),
        ("DisplayMode AspectRatio wrong type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "AspectRatio"), "return_type", "Double")),
        ("DisplayMode TitleSafeArea wrong type", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(
             mode_member(m, "TitleSafeArea"), "return_type",
             "Microsoft.Xna.Framework.Graphics.Viewport",
         )),
        ("DisplayMode Format as method", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "Format"), "kind", "method")),
        ("DisplayMode Width static", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(mode_member(m, "Width"), "static", True)),
        ("DisplayMode public initializer exposed", "UNEXPECTED_MEMBER",
         mode_extra(
             ".ctor", kind="constructor", return_type=mode_name,
             parameters=("Int32", "Int32",
                         "Microsoft.Xna.Framework.Graphics.SurfaceFormat"),
             labels=("width", "height", "format"), directions=("", "", ""),
             identifier="invented-display-mode-public-init",
         )),
        ("DisplayMode extra public Equals", "UNEXPECTED_MEMBER",
         mode_extra(
             "Equals", parameters=(mode_name,), labels=("_",),
             directions=("",), return_type="Bool",
         )),
        ("DisplayMode extra public GetHashCode", "UNEXPECTED_MEMBER",
         mode_extra("GetHashCode", return_type="Int32")),
        ("DisplayMode extra public op_Equality", "UNEXPECTED_MEMBER",
         mode_extra(
             "op_Equality", static=True, parameters=(mode_name, mode_name),
             labels=("_", "_"), directions=("", ""), return_type="Bool",
         )),
        ("DisplayMode extra public op_Inequality", "UNEXPECTED_MEMBER",
         mode_extra(
             "op_Inequality", static=True, parameters=(mode_name, mode_name),
             labels=("_", "_"), directions=("", ""), return_type="Bool",
         )),
        ("DisplayMode extra public description helper", "UNEXPECTED_MEMBER",
         mode_extra(
             "description", kind="property", return_type="String", mutable=False,
         )),
        ("DisplayMode extra public convenience helper", "UNEXPECTED_MEMBER",
         mode_extra(
             "WithFormat", parameters=(
                 "Microsoft.Xna.Framework.Graphics.SurfaceFormat",
             ),
             labels=("_",), directions=("",), return_type=mode_name,
         )),
    ]
    # Every declared DisplayMode property is get-only in the pinned contract;
    # this is validated generically rather than for a hand-picked subset.
    mode_read_only = ("Format", "Height", "Width", "AspectRatio", "TitleSafeArea")
    for property_name in mode_read_only:
        mode_mutations.append((
            f"DisplayMode {property_name} writable", "PROPERTY_MAPPING_MISMATCH",
            (lambda name: lambda m: setattr(
                mode_member(m, name), "mutable", True,
            ))(property_name),
        ))
    for label, wanted, mutate in mode_mutations:
        models = copy.deepcopy(mode_good)
        mutate(models)
        if wanted not in mode_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if mode_categories(mode_good):
        failures.append("DisplayMode reference model is not diagnostic-free")
    if len(mode_expected[mode_name].members) != 6:
        failures.append("DisplayMode expected Swift member count is not exactly 6")
    if {member.name for member in mode_expected[mode_name].members} != {
        "ToString", "Format", "Height", "Width", "AspectRatio", "TitleSafeArea",
    }:
        failures.append("DisplayMode expected Swift identities are not the pinned six")
    if any(
        member.mutable for member in mode_expected[mode_name].members
        if member.kind == "property"
    ):
        failures.append("DisplayMode expected a writable property")
    if any(
        member.kind == "constructor"
        for member in mode_expected[mode_name].members
    ):
        failures.append("DisplayMode expected a public constructor identity")

    # The System.Object base is a language mapping and is not required, but a
    # genuinely mapped XNA base must still be measured on this type.
    mode_base_expected = copy.deepcopy(mode_expected)
    mode_base_expected[mode_name].base = "Microsoft.Xna.Framework.Graphics.Texture2D"
    if "BASE_MAPPING_MISMATCH" not in {
        item["category"] for item in compare(mode_base_expected, mode_good)
    }:
        failures.append("DisplayMode wrong mapped base did not fail")

    usage_name = "Microsoft.Xna.Framework.Graphics.RenderTargetUsage"
    usage_expected = {
        usage_name: copy.deepcopy(all_expected[usage_name]),
    }
    usage_good = copy.deepcopy(usage_expected)
    usage_good[usage_name].identifier = usage_name
    for index, member in enumerate(usage_good[usage_name].members):
        member.identifier = f"{usage_name}:{index}"

    def usage_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(
            member for member in models[usage_name].members
            if member.name == name
        )

    def usage_categories(models: dict[str, TypeModel]) -> set[str]:
        return {
            item["category"] for item in compare(usage_expected, models)
        }

    usage_mutations: list[tuple[str, str, Any]] = [
        ("RenderTargetUsage missing type", "MISSING_TYPE",
         lambda m: m.pop(usage_name)),
        ("RenderTargetUsage wrong namespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.RenderTargetUsage",
             m.pop(usage_name),
         )),
        ("RenderTargetUsage RenderTarget subnamespace", "MISSING_TYPE",
         lambda m: m.__setitem__(
             "Microsoft.Xna.Framework.Graphics.RenderTarget.RenderTargetUsage",
             m.pop(usage_name),
         )),
        ("RenderTargetUsage struct instead of enum", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[usage_name], "kind", "struct")),
        ("RenderTargetUsage OptionSet instead of ordinary enum",
         "FLAGS_MAPPING_MISMATCH",
         lambda m: (setattr(m[usage_name], "kind", "struct"),
                    setattr(m[usage_name], "flags", True))),
        ("RenderTargetUsage wrong raw type", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[usage_name], "raw_type", "UInt32")),
        ("RenderTargetUsage Int raw type", "TYPE_KIND_MISMATCH",
         lambda m: setattr(m[usage_name], "raw_type", "Int")),
        ("RenderTargetUsage flags metadata present", "FLAGS_MAPPING_MISMATCH",
         lambda m: setattr(m[usage_name], "flags", True)),
        ("RenderTargetUsage wrong DiscardContents", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(usage_member(m, "DiscardContents"), "raw_value", 1)),
        ("RenderTargetUsage wrong PreserveContents", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(usage_member(m, "PreserveContents"), "raw_value", 2)),
        ("RenderTargetUsage wrong PlatformContents", "ENUM_VALUE_MISMATCH",
         lambda m: setattr(usage_member(m, "PlatformContents"), "raw_value", 3)),
        ("RenderTargetUsage missing DiscardContents", "MISSING_MEMBER",
         lambda m: m[usage_name].members.remove(
             usage_member(m, "DiscardContents"))),
        ("RenderTargetUsage missing middle PreserveContents", "MISSING_MEMBER",
         lambda m: m[usage_name].members.remove(
             usage_member(m, "PreserveContents"))),
        ("RenderTargetUsage missing final PlatformContents", "MISSING_MEMBER",
         lambda m: m[usage_name].members.remove(
             usage_member(m, "PlatformContents"))),
        ("RenderTargetUsage renamed DiscardContents", "MISSING_MEMBER",
         lambda m: setattr(usage_member(m, "DiscardContents"), "name", "Discard")),
        ("RenderTargetUsage renamed PreserveContents", "MISSING_MEMBER",
         lambda m: setattr(
             usage_member(m, "PreserveContents"), "name", "KeepContents")),
        ("RenderTargetUsage unexpected extra enum case", "UNEXPECTED_MEMBER",
         lambda m: m[usage_name].members.append(Member(
             usage_name, "field", "Default", True,
             return_type=usage_name, mutable=False, raw_value=3,
             identifier="invented-render-target-usage-case",
         ))),
        ("RenderTargetUsage public description helper", "UNEXPECTED_MEMBER",
         lambda m: m[usage_name].members.append(Member(
             usage_name, "property", "description", False,
             return_type="String", mutable=False,
             identifier="invented-render-target-usage-description",
         ))),
        ("RenderTargetUsage public ToString helper", "UNEXPECTED_MEMBER",
         lambda m: m[usage_name].members.append(Member(
             usage_name, "method", "ToString", False, return_type="String",
             identifier="invented-render-target-usage-to-string",
         ))),
        ("RenderTargetUsage public predicate helper", "UNEXPECTED_MEMBER",
         lambda m: m[usage_name].members.append(Member(
             usage_name, "property", "preservesContents", False,
             return_type="Bool", mutable=False,
             identifier="invented-render-target-usage-predicate",
         ))),
        ("RenderTargetUsage public consumer helper", "UNEXPECTED_MEMBER",
         lambda m: m[usage_name].members.append(Member(
             usage_name, "method", "Apply", False,
             parameters=("Microsoft.Xna.Framework.Graphics.RenderTarget2D",),
             labels=("_",), directions=("",), return_type="Void",
             identifier="invented-render-target-usage-consumer",
         ))),
        ("RenderTargetUsage public native mapping helper", "UNEXPECTED_MEMBER",
         lambda m: m[usage_name].members.append(Member(
             usage_name, "property", "nativeUsage", False,
             return_type="Int32", mutable=False,
             identifier="invented-render-target-usage-native",
         ))),
    ]
    for label, wanted, mutate in usage_mutations:
        models = copy.deepcopy(usage_good)
        mutate(models)
        if wanted not in usage_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    if usage_categories(usage_good):
        failures.append("RenderTargetUsage reference model is not diagnostic-free")
    if usage_expected[usage_name].kind != "enum":
        failures.append("RenderTargetUsage expected Swift kind is not enum")
    if usage_expected[usage_name].flags:
        failures.append("RenderTargetUsage expected flags is not false")
    if usage_expected[usage_name].raw_type != "Int32":
        failures.append("RenderTargetUsage expected raw type is not Int32")
    if not usage_expected[usage_name].verify_raw_type:
        failures.append("RenderTargetUsage raw type is not verified")
    if len(usage_expected[usage_name].members) != 3:
        failures.append(
            "RenderTargetUsage expected Swift member count is not exactly 3")
    if {
        member.name: member.raw_value
        for member in usage_expected[usage_name].members
    } != {"DiscardContents": 0, "PreserveContents": 1, "PlatformContents": 2}:
        failures.append("RenderTargetUsage expected raw table is not the pinned table")
    if any(
        member.kind != "field" or not member.static
        for member in usage_expected[usage_name].members
    ):
        failures.append(
            "RenderTargetUsage expected identity is not a static enum literal")
    if any(
        member.kind == "constructor"
        for member in usage_expected[usage_name].members
    ):
        failures.append("RenderTargetUsage expected a public constructor identity")

    if any(
        member.name == "value__"
        for member in usage_expected[usage_name].members
    ):
        failures.append(
            "RenderTargetUsage value__ was not excluded from the Swift contract")
    usage_value_storage_expected = copy.deepcopy(usage_expected)
    usage_value_storage_expected[usage_name].members.append(Member(
        usage_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-required-render-target-usage-storage",
    ))
    if "MISSING_MEMBER" not in {
        item["category"] for item in compare(
            usage_value_storage_expected, usage_good,
        )
    }:
        failures.append(
            "RenderTargetUsage value__ treated as required did not fail")
    usage_value_storage_actual = copy.deepcopy(usage_good)
    usage_value_storage_actual[usage_name].members.append(Member(
        usage_name, "field", "value__", False,
        return_type="Int32", mutable=True,
        identifier="incorrectly-exposed-render-target-usage-storage",
    ))
    if "UNEXPECTED_MEMBER" not in {
        item["category"] for item in compare(
            usage_expected, usage_value_storage_actual,
        )
    }:
        failures.append(
            "RenderTargetUsage publicly exposed value__ did not fail")

    # Foundation 14, 16 and 17 pure managed batches. Every batch enum is
    # driven through the same structural mutation matrix, built from its own
    # pinned reference model rather than from a transcribed table, so a batch
    # type cannot be registered without negative coverage for its exact
    # literals.
    batch_enum_names = [
        "Microsoft.Xna.Framework.Audio.AudioStopOptions",
        "Microsoft.Xna.Framework.Audio.MicrophoneState",
        "Microsoft.Xna.Framework.Input.Touch.GestureType",
        "Microsoft.Xna.Framework.Input.Touch.TouchLocationState",
        "Microsoft.Xna.Framework.Media.VideoSoundtrackType",
        "Microsoft.Xna.Framework.Media.MediaSourceType",
        "Microsoft.Xna.Framework.Media.MediaState",
        "Microsoft.Xna.Framework.Graphics.Blend",
        "Microsoft.Xna.Framework.Graphics.BlendFunction",
        "Microsoft.Xna.Framework.Graphics.ClearOptions",
        "Microsoft.Xna.Framework.Graphics.ColorWriteChannels",
        "Microsoft.Xna.Framework.Graphics.CompareFunction",
        "Microsoft.Xna.Framework.Graphics.CubeMapFace",
        "Microsoft.Xna.Framework.Graphics.CullMode",
        "Microsoft.Xna.Framework.Graphics.EffectParameterClass",
        "Microsoft.Xna.Framework.Graphics.EffectParameterType",
        "Microsoft.Xna.Framework.Graphics.GraphicsDeviceStatus",
        "Microsoft.Xna.Framework.Graphics.GraphicsProfile",
        "Microsoft.Xna.Framework.Graphics.IndexElementSize",
        "Microsoft.Xna.Framework.Graphics.PresentInterval",
        "Microsoft.Xna.Framework.Graphics.PrimitiveType",
        "Microsoft.Xna.Framework.Graphics.SetDataOptions",
        "Microsoft.Xna.Framework.Graphics.StencilOperation",
        "Microsoft.Xna.Framework.Graphics.TextureAddressMode",
        "Microsoft.Xna.Framework.Graphics.TextureFilter",
        "Microsoft.Xna.Framework.Graphics.VertexElementFormat",
        "Microsoft.Xna.Framework.Graphics.VertexElementUsage",
        "Microsoft.Xna.Framework.Audio.AudioChannels",
        "Microsoft.Xna.Framework.Audio.SoundState",
    ]
    source_types_by_name = {item["name"]: item for item in contract["types"]}
    batch_self_tests = 0
    for batch_name in batch_enum_names:
        batch_expected = {batch_name: copy.deepcopy(all_expected[batch_name])}
        batch_good = copy.deepcopy(batch_expected)
        batch_good[batch_name].identifier = batch_name
        for index, member in enumerate(batch_good[batch_name].members):
            member.identifier = f"{batch_name}:{index}"
        batch_model = batch_expected[batch_name]
        batch_flags = batch_model.flags
        batch_simple = batch_name.rsplit(".", 1)[-1]
        batch_slug = re.sub(r"(?<!^)(?=[A-Z])", "-", batch_simple).lower()
        pinned_table = {
            member.name: member.raw_value for member in batch_model.members
        }

        def batch_member(models: dict[str, TypeModel], name: str, owner: str) -> Member:
            return next(
                member for member in models[owner].members if member.name == name
            )

        def batch_categories(
            models: dict[str, TypeModel], reference: dict[str, TypeModel] = batch_expected,
        ) -> set[str]:
            return {item["category"] for item in compare(reference, models)}

        raw_type_category = (
            "FLAGS_MAPPING_MISMATCH" if batch_flags else "TYPE_KIND_MISMATCH"
        )
        batch_mutations: list[tuple[str, str, Any]] = [
            (f"{batch_simple} missing type", "MISSING_TYPE",
             lambda m, n=batch_name: m.pop(n)),
            (f"{batch_simple} wrong namespace", "MISSING_TYPE",
             lambda m, n=batch_name, s=batch_simple: m.__setitem__(
                 f"Microsoft.Xna.Framework.{s}", m.pop(n))),
            (f"{batch_simple} wrong raw type", raw_type_category,
             lambda m, n=batch_name: setattr(m[n], "raw_type", "UInt32")),
            (f"{batch_simple} Int raw type", raw_type_category,
             lambda m, n=batch_name: setattr(m[n], "raw_type", "Int")),
            (f"{batch_simple} inverted flags metadata", "FLAGS_MAPPING_MISMATCH",
             lambda m, n=batch_name, f=batch_flags: setattr(m[n], "flags", not f)),
            (f"{batch_simple} unexpected invented literal", "UNEXPECTED_MEMBER",
             lambda m, n=batch_name, s=batch_slug, v=max(pinned_table.values()) + 1:
                 m[n].members.append(Member(
                     n, "field", "Invented", True, return_type=n, mutable=False,
                     raw_value=v, identifier=f"invented-{s}-literal"))),
            (f"{batch_simple} public description helper", "UNEXPECTED_MEMBER",
             lambda m, n=batch_name, s=batch_slug: m[n].members.append(Member(
                 n, "property", "description", False, return_type="String",
                 mutable=False, identifier=f"invented-{s}-description"))),
            (f"{batch_simple} public ToString helper", "UNEXPECTED_MEMBER",
             lambda m, n=batch_name, s=batch_slug: m[n].members.append(Member(
                 n, "method", "ToString", False, return_type="String",
                 identifier=f"invented-{s}-to-string"))),
            (f"{batch_simple} public predicate helper", "UNEXPECTED_MEMBER",
             lambda m, n=batch_name, s=batch_slug: m[n].members.append(Member(
                 n, "property", "isDefault", False, return_type="Bool",
                 mutable=False, identifier=f"invented-{s}-predicate"))),
            (f"{batch_simple} public native mapping helper", "UNEXPECTED_MEMBER",
             lambda m, n=batch_name, s=batch_slug: m[n].members.append(Member(
                 n, "property", "nativeValue", False, return_type="Int32",
                 mutable=False, identifier=f"invented-{s}-native"))),
        ]
        if batch_flags:
            batch_mutations.append((
                f"{batch_simple} ordinary enum instead of OptionSet",
                "TYPE_KIND_MISMATCH",
                lambda m, n=batch_name: (setattr(m[n], "kind", "enum"),
                                         setattr(m[n], "flags", False))))
        else:
            batch_mutations.append((
                f"{batch_simple} struct instead of enum", "TYPE_KIND_MISMATCH",
                lambda m, n=batch_name: setattr(m[n], "kind", "struct")))
            batch_mutations.append((
                f"{batch_simple} OptionSet instead of ordinary enum",
                "FLAGS_MAPPING_MISMATCH",
                lambda m, n=batch_name: (setattr(m[n], "kind", "struct"),
                                         setattr(m[n], "flags", True))))
        for literal, literal_value in pinned_table.items():
            batch_mutations.append((
                f"{batch_simple} wrong {literal}", "ENUM_VALUE_MISMATCH",
                lambda m, n=batch_name, k=literal, v=literal_value: setattr(
                    batch_member(m, k, n), "raw_value", v + 1)))
            batch_mutations.append((
                f"{batch_simple} missing {literal}", "MISSING_MEMBER",
                lambda m, n=batch_name, k=literal: m[n].members.remove(
                    batch_member(m, k, n))))
            batch_mutations.append((
                f"{batch_simple} renamed {literal}", "MISSING_MEMBER",
                lambda m, n=batch_name, k=literal: setattr(
                    batch_member(m, k, n), "name", f"{k}Renamed")))
        for label, wanted, mutate in batch_mutations:
            models = copy.deepcopy(batch_good)
            mutate(models)
            if wanted not in batch_categories(models):
                failures.append(f"{label}: did not produce {wanted}")
        batch_self_tests += len(batch_mutations)

        if batch_categories(batch_good):
            failures.append(f"{batch_simple} reference model is not diagnostic-free")
        if batch_model.kind != ("struct" if batch_flags else "enum"):
            failures.append(f"{batch_simple} expected Swift kind is wrong")
        if batch_model.raw_type != "Int32":
            failures.append(f"{batch_simple} expected raw type is not Int32")
        if not batch_model.verify_raw_type:
            failures.append(f"{batch_simple} raw type is not verified")
        if any(member.name == "value__" for member in batch_model.members):
            failures.append(
                f"{batch_simple} value__ was not excluded from the Swift contract")
        if any(
            member.kind != "field" or not member.static
            for member in batch_model.members
        ):
            failures.append(
                f"{batch_simple} expected identity is not a static enum literal")
        if any(member.kind == "constructor" for member in batch_model.members):
            failures.append(f"{batch_simple} expected a public constructor identity")
        source_literals = {
            member["name"]: int(member["value"])
            for member in source_types_by_name[batch_name]["members"]
            if member["kind"] == "field" and member["name"] != "value__"
        }
        if pinned_table != source_literals:
            failures.append(f"{batch_simple} expected raw table is not the pinned table")
        if len(batch_model.members) != len(source_literals):
            failures.append(
                f"{batch_simple} expected Swift member count is not the pinned count")
        batch_storage_expected = copy.deepcopy(batch_expected)
        batch_storage_expected[batch_name].members.append(Member(
            batch_name, "field", "value__", False, return_type="Int32",
            mutable=True, identifier=f"incorrectly-required-{batch_slug}-storage",
        ))
        if "MISSING_MEMBER" not in {
            item["category"]
            for item in compare(batch_storage_expected, batch_good)
        }:
            failures.append(f"{batch_simple} value__ treated as required did not fail")
        batch_storage_actual = copy.deepcopy(batch_good)
        batch_storage_actual[batch_name].members.append(Member(
            batch_name, "field", "value__", False, return_type="Int32",
            mutable=True, identifier=f"incorrectly-exposed-{batch_slug}-storage",
        ))
        if "UNEXPECTED_MEMBER" not in {
            item["category"]
            for item in compare(batch_expected, batch_storage_actual)
        }:
            failures.append(f"{batch_simple} publicly exposed value__ did not fail")
        batch_self_tests += 11

    # Foundation 14 and 15 pure managed closures, non-enum. The pinned value
    # struct, the two pinned effect interfaces, and the pinned descriptor class
    # are driven through a per-member structural mutation matrix built from
    # their own reference models, so no member can be renamed, retyped, made
    # read-only, made static, or dropped without a diagnostic.
    batch_managed_names = [
        "Microsoft.Xna.Framework.Graphics.IEffectFog",
        "Microsoft.Xna.Framework.Graphics.IEffectMatrices",
        "Microsoft.Xna.Framework.Graphics.VertexElement",
        "Microsoft.Xna.Framework.Graphics.PresentationParameters",
        "Microsoft.Xna.Framework.Input.MouseState",
        "Microsoft.Xna.Framework.IGameComponent",
        "Microsoft.Xna.Framework.IGraphicsDeviceManager",
        "Microsoft.Xna.Framework.Input.Touch.TouchPanelCapabilities",
        "Microsoft.Xna.Framework.Input.Touch.GestureSample",
        "Microsoft.Xna.Framework.Input.Touch.TouchLocation",
        "Microsoft.Xna.Framework.Graphics.DisplayModeCollection",
    ]
    def synthesized_declaration(member: Member) -> str:
        """A representative Swift declaration for a fixture member.

        The generic-shape check reads the candidate's declaration text, so a
        fixture whose members carry no declaration silently reports a
        generic mismatch for any member whose mapped type is generic. Building
        the declaration from the member's own mapped types keeps the fixture
        faithful to what the compiler Symbol Graph emits.
        """
        parameters = ", ".join(
            f"{label} value: {'inout ' if direction else ''}{kind}"
            for label, kind, direction in zip(
                member.labels, member.parameters, member.directions)
        )
        if member.kind == "constructor":
            return f"public init({parameters})"
        if member.kind in ("property", "field"):
            suffix = " { get set }" if member.mutable else " { get }"
            return f"public var {member.name}: {member.return_type}{suffix}"
        if member.kind == "event":
            return f"public var {member.name}: {member.return_type}"
        return f"public func {member.name}({parameters}) -> {member.return_type}"

    for managed_name in batch_managed_names:
        managed_expected = {managed_name: copy.deepcopy(all_expected[managed_name])}
        managed_good = copy.deepcopy(managed_expected)
        managed_good[managed_name].identifier = managed_name
        for index, member in enumerate(managed_good[managed_name].members):
            member.identifier = f"{managed_name}:{index}"
            member.declaration = synthesized_declaration(member)
        managed_model = managed_expected[managed_name]
        managed_simple = managed_name.rsplit(".", 1)[-1]
        managed_slug = re.sub(r"(?<!^)(?=[A-Z])", "-", managed_simple).lower()

        def managed_member(
            models: dict[str, TypeModel], owner: str, name: str, arity: int,
        ) -> Member:
            return next(
                member for member in models[owner].members
                if member.name == name and len(member.parameters) == arity
            )

        def managed_categories(
            models: dict[str, TypeModel],
            reference: dict[str, TypeModel] = managed_expected,
        ) -> set[str]:
            return {item["category"] for item in compare(reference, models)}

        other_kind = "class" if managed_model.kind != "class" else "struct"
        managed_mutations: list[tuple[str, str, Any]] = [
            (f"{managed_simple} missing type", "MISSING_TYPE",
             lambda m, n=managed_name: m.pop(n)),
            # The relocation target must differ from the type's own
            # namespace, otherwise the mutation is a no-op for a type that
            # already lives at the namespace root.
            (f"{managed_simple} wrong namespace", "MISSING_TYPE",
             lambda m, n=managed_name, s=managed_simple: m.__setitem__(
                 f"Microsoft.Xna.Framework.Relocated.{s}", m.pop(n))),
            (f"{managed_simple} wrong Swift kind", "TYPE_KIND_MISMATCH",
             lambda m, n=managed_name, k=other_kind: setattr(m[n], "kind", k)),
            (f"{managed_simple} unexpected description helper", "UNEXPECTED_MEMBER",
             lambda m, n=managed_name, s=managed_slug: m[n].members.append(Member(
                 n, "property", "description", False, return_type="String",
                 mutable=False, identifier=f"invented-{s}-description"))),
            (f"{managed_simple} unexpected native mapping helper", "UNEXPECTED_MEMBER",
             lambda m, n=managed_name, s=managed_slug: m[n].members.append(Member(
                 n, "property", "nativeValue", False, return_type="Int32",
                 mutable=False, identifier=f"invented-{s}-native"))),
            (f"{managed_simple} unexpected invented method", "UNEXPECTED_MEMBER",
             lambda m, n=managed_name, s=managed_slug: m[n].members.append(Member(
                 n, "method", "Apply", False, return_type="Void",
                 identifier=f"invented-{s}-method"))),
        ]
        for member in managed_model.members:
            key = (member.name, len(member.parameters))
            is_property = member.kind == "property"
            kind_category = (
                "PROPERTY_MAPPING_MISMATCH" if is_property
                else "METHOD_SIGNATURE_MAPPING_MISMATCH"
            )
            return_category = (
                "PROPERTY_MAPPING_MISMATCH" if is_property
                else "RETURN_MAPPING_MISMATCH"
            )
            managed_mutations.append((
                f"{managed_simple} missing {member.name}/{key[1]}", "MISSING_MEMBER",
                lambda m, n=managed_name, k=key: m[n].members.remove(
                    managed_member(m, n, k[0], k[1]))))
            managed_mutations.append((
                f"{managed_simple} renamed {member.name}/{key[1]}", "MISSING_MEMBER",
                lambda m, n=managed_name, k=key: setattr(
                    managed_member(m, n, k[0], k[1]), "name", f"{k[0]}Renamed")))
            managed_mutations.append((
                f"{managed_simple} {member.name}/{key[1]} wrong Swift kind",
                kind_category,
                lambda m, n=managed_name, k=key, p=is_property: setattr(
                    managed_member(m, n, k[0], k[1]), "kind",
                    "method" if p else "property")))
            managed_mutations.append((
                f"{managed_simple} {member.name}/{key[1]} static identity flipped",
                kind_category,
                lambda m, n=managed_name, k=key: setattr(
                    managed_member(m, n, k[0], k[1]), "static",
                    not managed_member(m, n, k[0], k[1]).static)))
            if member.kind in ("method", "property"):
                managed_mutations.append((
                    f"{managed_simple} {member.name}/{key[1]} wrong result type",
                    return_category,
                    lambda m, n=managed_name, k=key: setattr(
                        managed_member(m, n, k[0], k[1]), "return_type",
                        "Microsoft.Xna.Framework.Point")))
            if member.mutable is not None:
                managed_mutations.append((
                    f"{managed_simple} {member.name}/{key[1]} mutability flipped",
                    "PROPERTY_MAPPING_MISMATCH",
                    lambda m, n=managed_name, k=key: setattr(
                        managed_member(m, n, k[0], k[1]), "mutable",
                        not managed_member(m, n, k[0], k[1]).mutable)))
            if member.parameters:
                managed_mutations.append((
                    f"{managed_simple} {member.name}/{key[1]} wrong parameter type",
                    "PARAMETER_MAPPING_MISMATCH",
                    lambda m, n=managed_name, k=key: setattr(
                        managed_member(m, n, k[0], k[1]), "parameters",
                        ("Microsoft.Xna.Framework.Point",) +
                        managed_member(m, n, k[0], k[1]).parameters[1:])))
                managed_mutations.append((
                    f"{managed_simple} {member.name}/{key[1]} wrong external label",
                    "PARAMETER_MAPPING_MISMATCH",
                    lambda m, n=managed_name, k=key: setattr(
                        managed_member(m, n, k[0], k[1]), "labels",
                        ("invented",) +
                        managed_member(m, n, k[0], k[1]).labels[1:])))
                managed_mutations.append((
                    f"{managed_simple} {member.name}/{key[1]} dropped parameter",
                    "OVERLOAD_MAPPING_MISMATCH",
                    lambda m, n=managed_name, k=key: (lambda found: [
                        setattr(found, field, getattr(found, field)[1:])
                        for field in ("parameters", "labels", "directions")
                    ])(managed_member(m, n, k[0], k[1]))))
        for label, wanted, mutate in managed_mutations:
            models = copy.deepcopy(managed_good)
            mutate(models)
            if wanted not in managed_categories(models):
                failures.append(f"{label}: did not produce {wanted}")
        batch_self_tests += len(managed_mutations)

        if managed_categories(managed_good):
            failures.append(f"{managed_simple} reference model is not diagnostic-free")
        source_managed = source_types_by_name[managed_name]
        expected_kind = {
            "interface": "protocol", "struct": "struct", "class": "class",
        }[source_managed["kind"]]
        if managed_model.kind != expected_kind:
            failures.append(f"{managed_simple} expected Swift kind is not {expected_kind}")
        if managed_model.flags or managed_model.raw_type is not None:
            failures.append(f"{managed_simple} is not an enum and must carry no raw type")
        if len(managed_model.members) != len(source_managed["members"]):
            failures.append(
                f"{managed_simple} expected identity count is not the pinned count")
        if {member.name for member in managed_model.members} != {
            member["name"] for member in source_managed["members"]
        }:
            failures.append(f"{managed_simple} expected identity names are not the pinned names")
        batch_self_tests += 5

    # ------------------------------------------------------------------
    # General `System.IntPtr` -> Swift `Int` language projection.
    #
    # `System.IntPtr` maps to Swift `Int`: the opaque pointer-width signed
    # numeric value of the CLR IntPtr. It is a LANGUAGE PROJECTION and is not a
    # Swift pointer, a dereferenceable address, a CNA native handle, an SDL
    # window, or any proof that the value is valid. The expected projection
    # must therefore never be counted as RAW_HANDLE_LEAK, while every
    # accidental pointer, native-handle, or fixed-width substitute must still
    # be a diagnostic. The rule is proved twice: generically against a
    # synthetic owner, and then against the one real selected XNA identity that
    # uses it.
    # ------------------------------------------------------------------
    intptr_self_tests = 0
    if map_clr_type("System.IntPtr", rules) != "Int":
        failures.append("System.IntPtr does not map to Swift Int")
    intptr_self_tests += 1

    intptr_owner = "Microsoft.Xna.Framework.Graphics.IntPtrProjectionProbe"
    intptr_source = {
        "kind": "property", "name": "Handle", "type": "System.IntPtr",
        "static": False, "get": True, "set": True, "parameters": [],
    }
    intptr_reference_member = expected_member(
        intptr_owner, intptr_source, rules, "class",
    )
    if intptr_reference_member.return_type != "Int":
        failures.append("mapped System.IntPtr property is not Swift Int")
    intptr_self_tests += 1
    intptr_expected = {
        intptr_owner: TypeModel(
            intptr_owner, "class", members=[intptr_reference_member],
        ),
    }

    def intptr_models(swift_type: str) -> dict[str, TypeModel]:
        model = TypeModel(intptr_owner, "class", identifier=intptr_owner)
        model.members = [Member(
            intptr_owner, "property", "Handle", False,
            return_type=swift_type, mutable=True,
            declaration=f"public var Handle: {swift_type} {{ get set }}",
            identifier=f"{intptr_owner}:Handle",
        )]
        return {intptr_owner: model}

    def intptr_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(intptr_expected, models)}

    leak = "RAW_HANDLE_LEAK"
    ffi = "PUBLIC_NATIVE_FFI_LEAK"
    mismatch = "PROPERTY_MAPPING_MISMATCH"
    # (label, Swift type, categories required, categories forbidden)
    intptr_cases: list[tuple[str, str, set[str], set[str]]] = [
        # 1. The expected CLR-language projection. It is clean: not a leak, and
        #    not a mapping mismatch.
        ("expected IntPtr -> Int projection", "Int", set(), {leak, ffi, mismatch}),
        # 2-4. Accidental public pointer projections.
        ("accidental UnsafeRawPointer", "UnsafeRawPointer", {leak, ffi}, set()),
        ("accidental UnsafeMutableRawPointer", "UnsafeMutableRawPointer",
         {leak, ffi}, set()),
        ("accidental OpaquePointer", "OpaquePointer", {leak, ffi}, set()),
        # 5. A fixed-width substitute is not the pointer-width projection.
        ("incorrect fixed-width Int64 projection", "Int64", {mismatch}, {leak}),
        # 6. CLR IntPtr is signed, so an unsigned projection is wrong.
        ("incorrect unsigned UInt projection", "UInt", {mismatch}, {leak}),
        # 7. Native-handle wrapper leakage, both under the CNA FFI naming that
        #    the encapsulation gate recognises and under an unrelated platform
        #    wrapper name that it does not; neither can pass the mapping check.
        ("CNA native handle wrapper", "CNA_Handle", {ffi, mismatch}, set()),
        ("CNA shim handle wrapper", "CNASwift_WindowHandle", {ffi, mismatch}, set()),
        ("native handle property projection", "nativeHandle", {leak, ffi, mismatch}, set()),
        ("SDL window wrapper", "SDL_Window", {mismatch}, set()),
    ]
    for label, swift_type, required, forbidden in intptr_cases:
        observed = intptr_categories(intptr_models(swift_type))
        for category in sorted(required):
            if category not in observed:
                failures.append(f"IntPtr {label}: did not produce {category}")
            intptr_self_tests += 1
        for category in sorted(forbidden):
            if category in observed:
                failures.append(f"IntPtr {label}: unexpectedly produced {category}")
            intptr_self_tests += 1

    # The same rule proved on the one real selected XNA identity that carries a
    # `System.IntPtr`, so the general policy is anchored to real pinned
    # metadata rather than only to a synthetic probe.
    parameters_name = "Microsoft.Xna.Framework.Graphics.PresentationParameters"
    handle_source = next(
        item for item in source_types_by_name[parameters_name]["members"]
        if item["name"] == "DeviceWindowHandle"
    )
    if handle_source["type"] != "System.IntPtr":
        failures.append("DeviceWindowHandle is not a pinned System.IntPtr")
    intptr_self_tests += 1
    handle_expected = next(
        member for member in all_expected[parameters_name].members
        if member.name == "DeviceWindowHandle"
    )
    if handle_expected.return_type != "Int":
        failures.append("DeviceWindowHandle does not map to Swift Int")
    if not handle_expected.mutable:
        failures.append("DeviceWindowHandle is not a read/write mapping")
    intptr_self_tests += 2

    parameters_expected = {
        parameters_name: copy.deepcopy(all_expected[parameters_name]),
    }
    parameters_good = copy.deepcopy(parameters_expected)
    parameters_good[parameters_name].identifier = parameters_name
    for index, member in enumerate(parameters_good[parameters_name].members):
        member.identifier = f"{parameters_name}:{index}"
        member.declaration = (
            f"public var {member.name}: {member.return_type}"
            if member.kind == "property"
            else f"public func {member.name}() -> {member.return_type}"
        )

    def parameters_handle(models: dict[str, TypeModel]) -> Member:
        return next(
            member for member in models[parameters_name].members
            if member.name == "DeviceWindowHandle"
        )

    def parameters_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(parameters_expected, models)}

    if parameters_categories(parameters_good):
        failures.append(
            "PresentationParameters IntPtr reference model is not diagnostic-free")
    intptr_self_tests += 1

    for label, swift_type, required, forbidden in intptr_cases:
        models = copy.deepcopy(parameters_good)
        handle = parameters_handle(models)
        handle.return_type = swift_type
        handle.declaration = f"public var DeviceWindowHandle: {swift_type}"
        observed = parameters_categories(models)
        for category in sorted(required):
            if category not in observed:
                failures.append(
                    f"DeviceWindowHandle {label}: did not produce {category}")
            intptr_self_tests += 1
        for category in sorted(forbidden):
            if category in observed:
                failures.append(
                    f"DeviceWindowHandle {label}: unexpectedly produced {category}")
            intptr_self_tests += 1

    # The descriptor must stay a descriptor: a public member that would
    # dereference, resolve, or hand the handle to the native layer is not part
    # of the pinned contract and must be rejected as an unexpected member.
    for invented, invented_kind, invented_return in (
        ("GetWindow", "method", "Int"),
        ("ResolveDeviceWindow", "method", "Void"),
        ("NativeWindowHandle", "property", "Int"),
    ):
        models = copy.deepcopy(parameters_good)
        models[parameters_name].members.append(Member(
            parameters_name, invented_kind, invented, False,
            return_type=invented_return,
            mutable=False if invented_kind == "property" else None,
            declaration=f"public func {invented}()",
            identifier=f"invented-presentation-parameters-{invented}",
        ))
        if "UNEXPECTED_MEMBER" not in parameters_categories(models):
            failures.append(
                f"PresentationParameters invented {invented} did not fail")
        intptr_self_tests += 1

    # ------------------------------------------------------------------
    # Foundation 16: the MouseState constructor's pinned parameter order.
    #
    # The pinned metadata order is
    # (x, y, scrollWheel, leftButton, middleButton, rightButton,
    #  xButton1, xButton2)
    # — middleButton precedes rightButton, which is not the order the property
    # list suggests. Both parameters have the same mapped type and the same
    # `_` external label, so a transposition is invisible to the type, label,
    # and arity checks. It is caught only because the constructor is
    # registered in `internalParameterOrderChecks` and the internal names are
    # compared positionally.
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # CLR event projection, the System.EventArgs base, and the event support
    # types. All 49 events in the pinned contract are the single shape
    # System.EventHandler<TArgs>; each maps to exactly one get-only property of
    # type CNAEvent<TArgs> that keeps the XNA event name. The CLR add_/remove_/
    # raise_ accessors are the encoding of an event, never XNA identities.
    # ------------------------------------------------------------------
    event_self_tests = 0

    if EVENT_ACCESSOR_PREFIXES != tuple(rules.get("eventAccessorPrefixes", [])):
        failures.append("event accessor prefixes drifted from mapping-rules.json")
    event_self_tests += 1
    if sorted(MEASURED_SUPPORT_BASES) != sorted(
        rules.get("measuredSupportBaseProjections", {}).values()
    ):
        failures.append("measured support bases drifted from mapping-rules.json")
    event_self_tests += 1

    # Every event in the pinned contract really is EventHandler<TArgs>, so the
    # single projection rule is complete rather than merely convenient.
    contract_events = [
        (item["name"], member)
        for item in contract["types"] for member in item["members"]
        if member["kind"] == "event"
    ]
    if len(contract_events) != 49:
        failures.append(f"expected 49 pinned events, found {len(contract_events)}")
    event_self_tests += 1
    for owner_name, member in contract_events:
        if not member["type"].startswith("System.EventHandler`1["):
            failures.append(f"{owner_name}.{member['name']} is not EventHandler<TArgs>")
        event_self_tests += 1

    updateable_name = "Microsoft.Xna.Framework.IUpdateable"
    event_expected = {updateable_name: copy.deepcopy(all_expected[updateable_name])}
    enabled_changed = next(
        member for member in event_expected[updateable_name].members
        if member.name == "EnabledChanged"
    )
    if enabled_changed.kind != "event":
        failures.append("IUpdateable.EnabledChanged is not a pinned event")
    event_self_tests += 1
    if enabled_changed.return_type != "CNAEvent<CNAEventArgs>":
        failures.append(
            "IUpdateable.EnabledChanged does not map to CNAEvent<CNAEventArgs>")
    event_self_tests += 1
    if enabled_changed.mutable is not False:
        failures.append("a pinned CLR event does not map to a get-only property")
    event_self_tests += 1

    def event_member(models: dict[str, TypeModel], name: str) -> Member:
        return next(
            member for member in models[updateable_name].members
            if member.name == name
        )

    def event_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(event_expected, models)}

    event_good = copy.deepcopy(event_expected)
    event_good[updateable_name].identifier = updateable_name
    for index, member in enumerate(event_good[updateable_name].members):
        member.identifier = f"{updateable_name}:{index}"
        if member.kind == "event":
            # What the compiler actually emits for the projection: a get-only
            # property whose type is the consumer view.
            member.kind = "property"
            member.declaration = (
                f"var {member.name}: CNAEvent<CNAEventArgs> {{ get }}"
            )
    if event_categories(event_good):
        failures.append("the IUpdateable event reference model is not diagnostic-free")
    event_self_tests += 1

    def event_leak(name: str) -> dict[str, TypeModel]:
        models = copy.deepcopy(event_good)
        models[updateable_name].members.append(Member(
            updateable_name, "method", name, False, ("CNAEvent<CNAEventArgs>",),
            ("_",), ("",), "Void",
            declaration=f"func {name}(_ handler: CNAEvent<CNAEventArgs>)",
            identifier=f"{updateable_name}:{name}",
        ))
        return models

    event_mutations: list[tuple[str, str, Any]] = [
        ("event missing", "MISSING_MEMBER",
         lambda m: m[updateable_name].members.remove(
             event_member(m, "EnabledChanged"))),
        ("event renamed", "MISSING_MEMBER",
         lambda m: setattr(event_member(m, "EnabledChanged"), "name", "OnEnabledChanged")),
        ("event projected as a bare closure", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "EnabledChanged"), "return_type",
                           "(Any?, CNAEventArgs) throws -> Void")),
        ("event projected as an array of closures", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "EnabledChanged"), "return_type",
                           "[(Any?, CNAEventArgs) throws -> Void]")),
        ("event projected as CNAEventSource", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "EnabledChanged"), "return_type",
                           "CNAEventSource<CNAEventArgs>")),
        ("support source leaked as the event property", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "UpdateOrderChanged"), "return_type",
                           "CNAEventSource<CNAEventArgs>")),
        ("event property writable", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "EnabledChanged"), "mutable", True)),
        ("wrong TArgs", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "EnabledChanged"), "return_type",
                           "CNAEvent<Microsoft.Xna.Framework.GameComponentCollectionEventArgs>")),
        ("event static/instance identity", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(event_member(m, "EnabledChanged"), "static", True)),
        ("event projected as a callback pointer", "RAW_HANDLE_LEAK",
         lambda m: setattr(event_member(m, "EnabledChanged"), "declaration",
                           "var EnabledChanged: UnsafeRawPointer { get }")),
    ]
    for label, wanted, mutate in event_mutations:
        models = copy.deepcopy(event_good)
        mutate(models)
        if wanted not in event_categories(models):
            failures.append(f"event {label}: did not produce {wanted}")
        event_self_tests += 1

    for prefix in EVENT_ACCESSOR_PREFIXES:
        observed = event_categories(event_leak(f"{prefix}EnabledChanged"))
        if "EVENT_MAPPING_MISMATCH" not in observed:
            failures.append(f"{prefix}EnabledChanged leak was not diagnosed")
        event_self_tests += 1
        if "UNEXPECTED_MEMBER" not in observed:
            failures.append(f"{prefix}EnabledChanged has no reference identity")
        event_self_tests += 1

    # ------------------------------------------------------------------
    # System.EventArgs is a MEASURED base, not a dropped one.
    # ------------------------------------------------------------------
    args_name = "Microsoft.Xna.Framework.Graphics.ResourceCreatedEventArgs"
    args_expected = {args_name: copy.deepcopy(all_expected[args_name])}
    if args_expected[args_name].base != "CNAEventArgs":
        failures.append("ResourceCreatedEventArgs does not map its base to CNAEventArgs")
    event_self_tests += 1
    if not base_is_measured(args_expected[args_name].base):
        failures.append("the CNAEventArgs base projection is not measured")
    event_self_tests += 1
    if base_is_measured("System.ValueType") or base_is_measured("Any?"):
        failures.append("an undecided BCL base is being asserted as measured")
    event_self_tests += 1

    # A CLR root carries no projected members, so it needs no base decision.
    for root in CLR_ROOT_BASES:
        if base_is_undecided(root):
            failures.append(f"CLR root base {root} was reported undecided")
        event_self_tests += 1
    if base_is_undecided("Microsoft.Xna.Framework.Graphics.Texture") or \
            base_is_undecided("CNAEventArgs") or base_is_undecided(None):
        failures.append("a decided base was reported undecided")
    event_self_tests += 1

    # Every other non-XNA base is a real BCL mapping question, and implementing
    # such a type without deciding it must be caught rather than silently
    # accepted. These are the still-deferred bases named in the handoff.
    undecided_bases = [
        "System.Exception",
        "System.Attribute",
        "System.Runtime.InteropServices.ExternalException",
        "System.ComponentModel.ExpandableObjectConverter",
        "System.IO.BinaryReader",
        "System.Collections.Generic.Dictionary<String, String>",
        "System.Collections.ObjectModel.Collection<Microsoft.Xna.Framework.IGameComponent>",
        "System.Collections.ObjectModel.ReadOnlyCollection<Microsoft.Xna.Framework.Graphics.ModelBone>",
    ]
    for undecided in undecided_bases:
        if not base_is_undecided(undecided):
            failures.append(f"undecided BCL base {undecided} was treated as decided")
        event_self_tests += 1

    # GameComponentCollection is the live case: its XNA dependencies are all
    # complete, so only the base guard stops it being projected as a base-less
    # Swift class whose entire collection surface would be invented rather than
    # derived.
    collection_name = "Microsoft.Xna.Framework.GameComponentCollection"
    collection_expected = {collection_name: copy.deepcopy(all_expected[collection_name])}
    if not base_is_undecided(collection_expected[collection_name].base):
        failures.append("GameComponentCollection's Collection<T> base is not guarded")
    event_self_tests += 1
    collection_actual = {collection_name: TypeModel(
        collection_name, "class", identifier=collection_name,
        declaration=f"class {collection_name}",
    )}
    if "UNMEASURED_STRUCTURAL_CATEGORY" not in {
        item["category"] for item in compare(collection_expected, collection_actual)
    }:
        failures.append(
            "implementing GameComponentCollection without deciding its base "
            "was not reported unmeasured")
    event_self_tests += 1

    args_good = copy.deepcopy(args_expected)
    args_good[args_name].identifier = args_name
    for index, member in enumerate(args_good[args_name].members):
        member.identifier = f"{args_name}:{index}"

    def args_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(args_expected, models)}

    if args_categories(args_good):
        failures.append("the ResourceCreatedEventArgs reference model is not clean")
    event_self_tests += 1

    base_mutations: list[tuple[str, Any]] = [
        ("missing CNAEventArgs base", lambda m: setattr(m[args_name], "base", None)),
        ("AnyObject in place of the base", lambda m: setattr(m[args_name], "base", "AnyObject")),
        ("Object in place of the base", lambda m: setattr(m[args_name], "base", "Any?")),
        ("wrong support base", lambda m: setattr(m[args_name], "base", "CNAEventSubscription")),
        ("extra incompatible base projection",
         lambda m: setattr(m[args_name], "base", "CNAEnumerator<CNAEventArgs>")),
    ]
    for label, mutate in base_mutations:
        models = copy.deepcopy(args_good)
        mutate(models)
        if "BASE_MAPPING_MISMATCH" not in args_categories(models):
            failures.append(f"EventArgs base: {label} did not fail")
        event_self_tests += 1

    # A struct cannot carry the CLR class base, so it is caught twice.
    models = copy.deepcopy(args_good)
    models[args_name].kind = "struct"
    models[args_name].base = None
    observed = args_categories(models)
    for category in ("TYPE_KIND_MISMATCH", "BASE_MAPPING_MISMATCH"):
        if category not in observed:
            failures.append(
                f"EventArgs base: struct where a CLR class is required did not "
                f"produce {category}")
        event_self_tests += 1

    # ------------------------------------------------------------------
    # The support types themselves.
    # ------------------------------------------------------------------
    def support_member(
        owner: str, name: str, kind: str, parameters: tuple[str, ...],
        labels: tuple[str, ...], returns: str, static: bool = False,
        mutable: bool | None = None, declaration: str = "",
    ) -> Member:
        return Member(
            owner=owner, kind=kind, name=name, static=static,
            parameters=parameters, labels=labels,
            directions=tuple("" for _ in parameters), return_type=returns,
            mutable=mutable, declaration=declaration or f"func {name}()",
            identifier=f"{owner}:{name}",
        )

    def support_models() -> dict[str, TypeModel]:
        models = {
            "CNAEventArgs": TypeModel(
                "CNAEventArgs", "class", declaration="class CNAEventArgs",
                identifier="CNAEventArgs", access="open",
            ),
            "CNAEvent": TypeModel(
                "CNAEvent", "class", generic_count=1,
                generic_parameters=("TArgs",),
                declaration="final class CNAEvent<TArgs>",
                identifier="CNAEvent", access="public",
            ),
            "CNAEventSource": TypeModel(
                "CNAEventSource", "class", generic_count=1,
                generic_parameters=("TArgs",),
                declaration="final class CNAEventSource<TArgs>",
                identifier="CNAEventSource", access="public",
            ),
            "CNAEventSubscription": TypeModel(
                "CNAEventSubscription", "class",
                declaration="final class CNAEventSubscription",
                identifier="CNAEventSubscription", access="public",
            ),
        }
        models["CNAEventArgs"].members = [
            support_member("CNAEventArgs", ".ctor", "constructor", (), (), "Void",
                           declaration="init()"),
            support_member("CNAEventArgs", "Empty", "property", (), (),
                           "CNAEventArgs", static=True, mutable=False,
                           declaration="static let Empty: CNAEventArgs"),
        ]
        models["CNAEvent"].members = [
            support_member(
                "CNAEvent", "Add", "method",
                ("(Any?, TArgs) throws -> Void",), ("_",), "CNAEventSubscription",
                declaration="func Add(_ handler: @escaping (Any?, TArgs) throws -> Void) -> CNAEventSubscription"),
            support_member(
                "CNAEvent", "Remove", "method", ("CNAEventSubscription",), ("_",),
                "Void",
                declaration="func Remove(_ subscription: CNAEventSubscription)"),
        ]
        models["CNAEventSource"].members = [
            support_member("CNAEventSource", ".ctor", "constructor", (), (), "Void",
                           declaration="init()"),
            support_member("CNAEventSource", "Event", "property", (), (),
                           "CNAEvent<TArgs>", mutable=False,
                           declaration="var Event: CNAEvent<TArgs> { get }"),
            support_member("CNAEventSource", "Raise", "method",
                           ("Any?", "TArgs"), ("_", "args"), "Void",
                           declaration="func Raise(_ sender: Any?, args: TArgs) throws"),
        ]
        return models

    def support_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in event_support_evidence(models, rules)[1]}

    if support_categories(support_models()):
        failures.append("the event support reference model is not diagnostic-free")
    event_self_tests += 1
    if len(event_support_evidence(support_models(), rules)[0]) != 4:
        failures.append("the event support evidence does not cover four types")
    event_self_tests += 1

    raise_member = support_member(
        "CNAEvent", "Raise", "method", ("Any?", "TArgs"), ("_", "args"), "Void",
        declaration="func Raise(_ sender: Any?, args: TArgs) throws")

    support_mutations: list[tuple[str, str, Any]] = [
        # The two rules that carry the whole architecture.
        ("CNAEvent exposing Raise", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEvent"].members.append(raise_member)),
        ("CNAEventSource subclassing CNAEvent", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEventSource"], "base", "CNAEvent")),
        # Removal identity.
        ("wrong token type returned by Add", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEvent"].members[0], "return_type", "Int")),
        ("wrong token type accepted by Remove", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEvent"].members[1], "parameters",
                           ("(Any?, TArgs) throws -> Void",))),
        ("token carrying a public native handle", "PUBLIC_NATIVE_FFI_LEAK",
         lambda m: m["CNAEventSubscription"].members.append(support_member(
             "CNAEventSubscription", "Handle", "property", (), (), "Int",
             mutable=False,
             declaration="var Handle: CNA_Handle { get }"))),
        ("token carrying a public raw pointer", "RAW_HANDLE_LEAK",
         lambda m: m["CNAEventSubscription"].members.append(support_member(
             "CNAEventSubscription", "Storage", "property", (), (), "Int",
             mutable=False,
             declaration="var Storage: UnsafeMutableRawPointer { get }"))),
        # Construction and capability boundaries.
        ("publicly constructible token", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEventSubscription"].members.append(support_member(
             "CNAEventSubscription", ".ctor", "constructor", (), (), "Void",
             declaration="init()"))),
        ("consumer view publicly constructible", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEvent"].members.append(support_member(
             "CNAEvent", ".ctor", "constructor", (), (), "Void",
             declaration="init()"))),
        ("event source is not publicly constructible", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEventSource"].members.pop(0)),
        ("Raise missing from the event source", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEventSource"].members.pop(2)),
        ("Event view missing from the event source", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEventSource"].members.pop(1)),
        ("writable Event view", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEventSource"].members[1], "mutable", True)),
        ("Add missing from the consumer view", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEvent"].members.pop(0)),
        ("Remove missing from the consumer view", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEvent"].members.pop(1)),
        # Shape of the support types.
        ("CNAEventArgs projected as a struct", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEventArgs"], "kind", "struct")),
        ("CNAEventArgs not open", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEventArgs"], "access", "public")),
        ("CNAEventArgs missing Empty", "EVENT_MAPPING_MISMATCH",
         lambda m: m["CNAEventArgs"].members.pop(1)),
        ("CNAEventArgs.Empty made an instance member", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEventArgs"].members[1], "static", False)),
        ("consumer view not final", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEvent"], "declaration", "class CNAEvent<TArgs>")),
        ("consumer view loses its generic parameter", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEvent"], "generic_parameters", ())),
        ("handler signature drops the sender", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEvent"].members[0], "parameters",
                           ("(TArgs) throws -> Void",))),
        ("Raise drops the sender", "EVENT_MAPPING_MISMATCH",
         lambda m: setattr(m["CNAEventSource"].members[2], "parameters", ("TArgs",))),
    ]
    for label, wanted, mutate in support_mutations:
        models = support_models()
        mutate(models)
        if wanted not in support_categories(models):
            failures.append(f"event support {label}: did not produce {wanted}")
        event_self_tests += 1

    # Omitting any support type from measurement is itself a finding.
    for name in sorted(rules.get("eventSupportContract", {})):
        models = support_models()
        models.pop(name, None)
        if "UNMEASURED_STRUCTURAL_CATEGORY" not in support_categories(models):
            failures.append(f"event support omitted: {name} was not reported unmeasured")
        event_self_tests += 1

    # ------------------------------------------------------------------
    # IList<T> as a measured direct interface, and its CopyTo destination.
    # `TouchCollection` is the pinned owner: its declared direct interface is
    # IList<TouchLocation>, and its CopyTo writes into the caller's array. The
    # rule that makes that array `inout` used to key on ICollection<T> alone,
    # which would have silently turned a destination into a value copy here.
    # ------------------------------------------------------------------
    list_self_tests = 0
    if sorted(COLLECTION_COPY_INTERFACES) != sorted(
        item + "[" for item in [
            "System.Collections.Generic.ICollection`1",
            "System.Collections.Generic.IList`1",
        ]
    ):
        failures.append("CopyTo destination interfaces drifted from the rule text")
    list_self_tests += 1
    if "System.Collections.Generic.IList`1" not in rules.get(
        "requiredSystemInterfaceProjections", []
    ):
        failures.append("IList<T> is not a required system-interface projection")
    list_self_tests += 1
    if "System.Collections.Generic.IList`1" not in rules.get(
        "systemInterfaceMappings", {}
    ):
        failures.append("IList<T> has no configured Swift projection")
    list_self_tests += 1

    touch_name = "Microsoft.Xna.Framework.Input.Touch.TouchCollection"
    touch_expected = {touch_name: copy.deepcopy(all_expected[touch_name])}
    touch_copy_to = next(
        member for member in touch_expected[touch_name].members
        if member.name == "CopyTo"
    )
    if touch_copy_to.directions != ("inout", ""):
        failures.append(
            "TouchCollection.CopyTo destination array is not caller-owned inout")
    list_self_tests += 1

    touch_good = copy.deepcopy(touch_expected)
    touch_good[touch_name].identifier = touch_name
    for index, member in enumerate(touch_good[touch_name].members):
        member.identifier = f"{touch_name}:{index}"

    def touch_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(touch_expected, models)}

    if touch_categories(touch_good):
        failures.append("the TouchCollection reference model is not diagnostic-free")
    list_self_tests += 1

    # A value-copy destination loses every written element, so it must fail.
    models = copy.deepcopy(touch_good)
    next(
        member for member in models[touch_name].members if member.name == "CopyTo"
    ).directions = ("", "")
    if "REF_OUT_MAPPING_MISMATCH" not in touch_categories(models):
        failures.append("TouchCollection.CopyTo value-copy destination did not fail")
    list_self_tests += 1

    # The read/write indexed Item must expand to the throwing Item/SetItem
    # pair, not to a plain subscript, because set_Item throws.
    touch_item = next(
        member for member in touch_expected[touch_name].members
        if member.name == "Item"
    )
    if not (touch_item.kind == "property" and touch_item.parameters and touch_item.mutable):
        failures.append("TouchCollection.Item is not a read/write indexed property")
    list_self_tests += 1

    order_self_tests = 0
    mouse_name = "Microsoft.Xna.Framework.Input.MouseState"
    if f"{mouse_name}.ctor" not in rules.get("internalParameterOrderChecks", []):
        failures.append("MouseState constructor order is not verified")
    order_self_tests += 1

    mouse_expected = {mouse_name: copy.deepcopy(all_expected[mouse_name])}
    mouse_good = copy.deepcopy(mouse_expected)
    mouse_good[mouse_name].identifier = mouse_name
    for index, member in enumerate(mouse_good[mouse_name].members):
        member.identifier = f"{mouse_name}:{index}"

    def mouse_ctor(models: dict[str, TypeModel]) -> Member:
        return next(
            member for member in models[mouse_name].members
            if member.name == ".ctor"
        )

    def mouse_categories(models: dict[str, TypeModel]) -> set[str]:
        return {item["category"] for item in compare(mouse_expected, models)}

    pinned_order = mouse_ctor(mouse_expected).parameter_names
    if pinned_order != (
        "x", "y", "scrollWheel", "leftButton", "middleButton", "rightButton",
        "xButton1", "xButton2",
    ):
        failures.append("MouseState pinned constructor order is not the pinned order")
    order_self_tests += 1
    if mouse_categories(mouse_good):
        failures.append("MouseState reference model is not diagnostic-free")
    order_self_tests += 1

    def swapped(names: tuple[str, ...], first: int, second: int) -> tuple[str, ...]:
        items = list(names)
        items[first], items[second] = items[second], items[first]
        return tuple(items)

    # Every adjacent transposition must be caught, not only the middle/right
    # pair, so the rule is positional rather than a single hand-picked case.
    for index in range(len(pinned_order) - 1):
        models = copy.deepcopy(mouse_good)
        setattr(
            mouse_ctor(models), "parameter_names",
            swapped(pinned_order, index, index + 1),
        )
        if "PARAMETER_MAPPING_MISMATCH" not in mouse_categories(models):
            failures.append(
                f"MouseState constructor order swap {index}/{index + 1} did not fail")
        order_self_tests += 1

    # A renamed internal parameter is equally a mismatch.
    models = copy.deepcopy(mouse_good)
    setattr(mouse_ctor(models), "parameter_names", ("a",) + pinned_order[1:])
    if "PARAMETER_MAPPING_MISMATCH" not in mouse_categories(models):
        failures.append("MouseState renamed constructor parameter did not fail")
    order_self_tests += 1

    # The eight declared properties are all get-only in the pinned contract.
    mouse_properties = [
        member for member in mouse_expected[mouse_name].members
        if member.kind == "property"
    ]
    if len(mouse_properties) != 8:
        failures.append("MouseState expected property count is not eight")
    order_self_tests += 1
    for member in mouse_properties:
        if member.mutable:
            failures.append(f"MouseState {member.name} is not get-only")
        order_self_tests += 1

    if failures:
        raise SystemExit("self-test failures:\n" + "\n".join(failures))
    print(
        "API_COMPAT_SELF_TESTS="
        f"{len(mutations) + 17 + len(protocol_mutations) + len(curve_mutations) + curve_baseline_self_tests + accessor_writer_self_tests + 2 + len(gamepad_mutations) + len(display_mutations) + 1 + len(buffer_mutations) + 1 + len(fill_mutations) + 1 + len(surface_mutations) + 1 + len(depth_mutations) + 1 + len(mode_mutations) + 6 + len(usage_mutations) + 12 + batch_self_tests + intptr_self_tests + event_self_tests + list_self_tests + order_self_tests}"
    )
    print("API_COMPAT_SELF_TEST_STATUS=PASS")


def symbol_graph_self_test(path: Path) -> None:
    """Negative fixtures cut from the Symbol Graph the compiler actually emitted.

    The synthetic model self-tests prove the comparison rules bite. These prove
    the *reader* does too: every mutation below edits the real emitted graph the
    way a wrong Swift declaration would, and the accessor projection must
    report it. A source regex could not do this -- the throws effect and the
    presence of a setter are compiler facts here, not spellings in a file.
    """
    contract = load_json(REFERENCE)
    rules = load_json(RULES)
    fallibility = load_accessor_fallibility(rules)
    expected = build_expected(contract, rules, fallibility)
    base = load_json(path)

    def find(graph: dict[str, Any], suffix: str) -> dict[str, Any]:
        for symbol in graph["symbols"]:
            name = ".".join(symbol["pathComponents"])
            if name == suffix or name.startswith(f"{suffix}("):
                return symbol
        raise SystemExit(f"symbol-graph self-test could not find {suffix}")

    def observed(graph: dict[str, Any]) -> set[tuple[str, str, str]]:
        actual, parser_diagnostics, _, _, _, _ = parse_symbol_graph(
            path, rules, ROOT / "Sources/CNA", expected, graph,
        )
        return {
            (item["category"], item["subject"], item["detail"])
            for item in compare(expected, actual) + parser_diagnostics
        }

    emitter = "Microsoft.Xna.Framework.Audio.AudioEmitter"
    fog = "Microsoft.Xna.Framework.Graphics.IEffectFog"
    enumerator = "Microsoft.Xna.Framework.Input.Touch.TouchCollection.Enumerator"

    def drop_symbol(suffix: str):
        def mutate(graph: dict[str, Any]) -> None:
            target = find(graph, suffix)
            graph["symbols"].remove(target)
        return mutate

    def edit_fragments(suffix: str, before: str, after: str | None):
        def mutate(graph: dict[str, Any]) -> None:
            target = find(graph, suffix)
            fragments = target["declarationFragments"]
            for index, fragment in enumerate(fragments):
                if fragment.get("spelling") == before:
                    if after is None:
                        fragments.pop(index)
                    else:
                        fragment["spelling"] = after
                    return
            raise SystemExit(
                f"symbol-graph self-test could not edit {suffix}: no {before!r}")
        return mutate

    def rename(suffix: str, title: str):
        def mutate(graph: dict[str, Any]) -> None:
            target = find(graph, suffix)
            old = target["pathComponents"][-1]
            target["pathComponents"][-1] = old.replace(
                old.split("(")[0], title, 1)
            target["names"]["title"] = target["names"]["title"].replace(
                target["names"]["title"].split("(")[0], title, 1)
        return mutate

    def retype_parameter(suffix: str, before: str, after: str):
        def mutate(graph: dict[str, Any]) -> None:
            target = find(graph, suffix)
            for parameter in target["functionSignature"]["parameters"]:
                for fragment in parameter["declarationFragments"]:
                    if fragment.get("spelling") == before:
                        fragment["spelling"] = after
                        return
            raise SystemExit(f"symbol-graph self-test could not retype {suffix}")
        return mutate

    mutations: list[tuple[str, str, Any]] = [
        ("writer method deleted", "PROPERTY_MAPPING_MISMATCH",
         drop_symbol(f"{emitter}.SetDopplerScale")),
        ("writer method loses throws", "PROPERTY_MAPPING_MISMATCH",
         edit_fragments(f"{emitter}.SetDopplerScale", "throws", None)),
        ("writer method renamed to lowercase", "PROPERTY_MAPPING_MISMATCH",
         rename(f"{emitter}.SetDopplerScale", "setDopplerScale")),
        ("writer method renamed to TrySet", "PROPERTY_MAPPING_MISMATCH",
         rename(f"{emitter}.SetDopplerScale", "TrySetDopplerScale")),
        ("writer method wrong value type", "PARAMETER_MAPPING_MISMATCH",
         retype_parameter(f"{emitter}.SetDopplerScale", "Float", "Double")),
        ("ordinary setter retained beside the writer", "PROPERTY_MAPPING_MISMATCH",
         edit_fragments(f"{emitter}.DopplerScale", " }", " set }")),
        ("infallible getter made throwing", "PROPERTY_MAPPING_MISMATCH",
         edit_fragments(f"{emitter}.DopplerScale", " }", " throws }")),
        ("infallible read/write property made get-only", "PROPERTY_MAPPING_MISMATCH",
         edit_fragments(f"{emitter}.Position", "set", None)),
        ("fallible getter made infallible", "PROPERTY_MAPPING_MISMATCH",
         edit_fragments(f"{fog}.FogColor", "throws", None)),
        ("interface writer deleted", "PROPERTY_MAPPING_MISMATCH",
         drop_symbol(f"{fog}.SetFogColor")),
        ("throwing indexed reader loses throws", "PROPERTY_MAPPING_MISMATCH",
         edit_fragments(f"{enumerator}.Current", "throws", None)),
    ]

    baseline = observed(copy.deepcopy(base))
    failures: list[str] = []
    if any(
        item[1].startswith((emitter, fog, enumerator)) for item in baseline
    ):
        failures.append(
            "unmutated Symbol Graph already reports a diagnostic on a fixture type")
    for label, wanted, mutate in mutations:
        graph = copy.deepcopy(base)
        mutate(graph)
        # Only diagnostics the mutation *introduced* count. Comparing whole
        # categories would let a pre-existing PROPERTY_MAPPING_MISMATCH on an
        # unrelated partial pass every fixture without detecting anything.
        introduced = observed(graph) - baseline
        if not introduced:
            failures.append(f"{label}: produced no new diagnostic at all")
        elif wanted not in {item[0] for item in introduced}:
            failures.append(
                f"{label}: did not produce {wanted}; introduced "
                f"{sorted({item[0] for item in introduced})}")
    if failures:
        raise SystemExit("symbol-graph self-test failures:\n" + "\n".join(failures))
    print(f"SYMBOL_GRAPH_SELF_TESTS={len(mutations) + 1}")
    print("SYMBOL_GRAPH_SELF_TEST_STATUS=PASS")


def event_support_evidence(
    support: dict[str, TypeModel],
    rules: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Measure the event support types against their pinned shape.

    These types live outside `Microsoft.Xna.Framework`, so they are counted in
    no XNA scoreboard, but they are the public machinery every projected event
    is expressed through and they are measured, not assumed. The two rules that
    carry the architecture are checked here and nowhere else: `CNAEvent` must
    not expose `Raise`, and `CNAEventSource` must not inherit from `CNAEvent` --
    if it did, a consumer handed the read-only view could downcast its way to
    the raise capability that CLR reserves for the declaring type.
    """
    contract = rules.get("eventSupportContract", {})
    evidence: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    pointer_pattern = re.compile(
        r"Unsafe(?:Mutable)?(?:Raw)?Pointer|OpaquePointer|nativeHandle|CNASwift_|CNA_Handle"
    )
    raw_pattern = re.compile(
        r"Unsafe(?:Mutable)?(?:Raw)?Pointer|OpaquePointer|nativeHandle"
    )

    for name in sorted(contract):
        specification = contract[name]
        model = support.get(name)
        if model is None:
            # Omitting a support type from measurement is itself a finding: the
            # projection every event depends on would otherwise go unchecked.
            diagnostics.append(diagnostic(
                "UNMEASURED_STRUCTURAL_CATEGORY", name,
                "event support type is absent from the Swift Symbol Graph, so "
                "the event projection it carries is unmeasured",
            ))
            continue

        if model.kind != specification["kind"]:
            diagnostics.append(diagnostic(
                "EVENT_MAPPING_MISMATCH", name,
                f"expected support kind {specification['kind']}, found {model.kind}",
            ))
        expected_generics = tuple(specification.get("generics", []))
        if model.generic_parameters != expected_generics:
            diagnostics.append(diagnostic(
                "EVENT_MAPPING_MISMATCH", name,
                f"expected generic parameters {expected_generics}, "
                f"found {model.generic_parameters}",
            ))
        if model.base != specification.get("base"):
            diagnostics.append(diagnostic(
                "EVENT_MAPPING_MISMATCH", name,
                f"expected base {specification.get('base')}, found {model.base}; "
                "the consumer view and the event source are composed over "
                "private storage and neither derives from the other",
            ))
        inheritance = specification.get("inheritance")
        if inheritance == "final" and "final class" not in model.declaration:
            diagnostics.append(diagnostic(
                "EVENT_MAPPING_MISMATCH", name,
                f"expected a final support class, found {model.declaration!r}",
            ))
        if inheritance == "open" and model.access != "open":
            diagnostics.append(diagnostic(
                "EVENT_MAPPING_MISMATCH", name,
                f"expected an open support class, found access {model.access!r}",
            ))

        observed = {member.name: member for member in model.members}
        for member_name, shape in sorted(specification.get("members", {}).items()):
            member = observed.get(member_name)
            if member is None:
                diagnostics.append(diagnostic(
                    "EVENT_MAPPING_MISMATCH", f"{name}.{member_name}",
                    "required event support member is absent",
                ))
                continue
            expected_shape = (
                shape["kind"], bool(shape.get("static")),
                tuple(shape.get("parameters", [])),
                tuple(shape.get("labels", [])), shape["returns"],
            )
            observed_shape = (
                member.kind, member.static, member.parameters,
                member.labels, member.return_type,
            )
            if expected_shape != observed_shape:
                diagnostics.append(diagnostic(
                    "EVENT_MAPPING_MISMATCH", f"{name}.{member_name}",
                    f"expected {expected_shape}, found {observed_shape}",
                ))
            if (
                "mutable" in shape and member.mutable is not None and
                bool(shape["mutable"]) != member.mutable
            ):
                diagnostics.append(diagnostic(
                    "EVENT_MAPPING_MISMATCH", f"{name}.{member_name}",
                    f"expected mutable={shape['mutable']}, found mutable={member.mutable}",
                ))

        for member_name in specification.get("forbiddenMembers", []):
            if member_name in observed:
                diagnostics.append(diagnostic(
                    "EVENT_MAPPING_MISMATCH", f"{name}.{member_name}",
                    "event support member is forbidden on this type; it would "
                    "hand a consumer a capability the CLR event model reserves",
                ))

        for member in model.members:
            if raw_pattern.search(member.declaration):
                diagnostics.append(diagnostic(
                    "RAW_HANDLE_LEAK", member.display, member.declaration,
                ))
            if pointer_pattern.search(member.declaration):
                diagnostics.append(diagnostic(
                    "PUBLIC_NATIVE_FFI_LEAK", member.display, member.declaration,
                ))

        evidence.append({
            "supportType": name,
            "kind": model.kind,
            "inheritance": inheritance,
            "genericParameters": list(model.generic_parameters),
            "base": model.base,
            "publicMembers": sorted(observed),
            "forbiddenMembersAbsent": [
                item for item in specification.get("forbiddenMembers", [])
                if item not in observed
            ],
            "reason": rules.get("eventSupportMapping", ""),
        })

    return evidence, diagnostics


def protocol_witness_projection_evidence(
    contract: dict[str, Any],
    rules: dict[str, Any],
    observed: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    source_types = {
        map_type_name(item["name"], rules): item for item in contract["types"]
    }
    interface_name = "Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVector"
    interface = source_types[interface_name]
    observed_identities = {
        f"{item['ownerType']}.{item['swiftMember']}" for item in observed
    }
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for identity in rules.get("protocolWitnessMemberProjections", []):
        owner_name, member_name = identity.rsplit(".", 1)
        owner = source_types.get(owner_name)
        requirement = next(
            (item for item in interface["members"] if item["name"] == member_name),
            None,
        )
        forcing_interfaces = [] if owner is None else [
            item for item in owner.get("directInterfaces", [])
            if item.startswith(
                "Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVector`1["
            )
        ]
        declared = [] if owner is None else [
            item for item in owner["members"] if item["name"] == member_name
        ]
        if owner is None or requirement is None or len(forcing_interfaces) != 1 or declared:
            failures.append(diagnostic(
                "UNMEASURED_STRUCTURAL_CATEGORY", identity,
                "protocol-witness rule lacks a unique concrete owner/direct generic CLR interface, "
                "a matching IPackedVector requirement, or absence from public declared CLR members",
            ))
            continue
        compiler_observed = identity in observed_identities
        if not compiler_observed:
            failures.append(diagnostic(
                "LANGUAGE_MAPPING_MISMATCH", identity,
                "configured protocol-witness projection has no matching compiler sourceOrigin witness",
            ))
        records.append({
            "ownerType": owner_name,
            "swiftMember": member_name,
            "forcingClrInterface": forcing_interfaces[0],
            "interfaceRequirement": f"{interface_name}.{member_name}",
            "absentFromPublicDeclaredClrMembers": True,
            "compilerSourceOriginObserved": compiler_observed,
            "reason": "Swift requires a public conformance witness for XNA's private explicit-interface implementation",
        })
    return records, failures


def system_interface_projection_evidence(
    contract: dict[str, Any],
    rules: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    mappings = rules.get("systemInterfaceMappings", {})
    for interface_prefix in rules.get("requiredSystemInterfaceProjections", []):
        if interface_prefix not in mappings:
            failures.append(diagnostic(
                "LANGUAGE_MAPPING_MISMATCH", interface_prefix,
                "required CLR system-interface projection is not configured",
            ))
            continue
        owners = [
            item for item in contract["types"]
            if any(
                direct == interface_prefix or direct.startswith(interface_prefix + "[")
                for direct in item.get("directInterfaces", [])
            )
        ]
        if not owners:
            failures.append(diagnostic(
                "UNMEASURED_STRUCTURAL_CATEGORY", interface_prefix,
                "configured system-interface projection has no pinned direct-interface owner",
            ))
            continue
        for owner in owners:
            if interface_prefix == "System.IComparable`1":
                required_members = {"CompareTo"}
            elif interface_prefix == "System.Collections.Generic.ICollection`1":
                required_members = {
                    "Add", "Clear", "Contains", "CopyTo", "Remove",
                    "Count", "IsReadOnly",
                }
            elif interface_prefix == "System.Collections.Generic.IList`1":
                # IList<T> inherits ICollection<T>, so its concrete surface is
                # the seven ICollection members plus the three IList ones and
                # the indexed Item.
                required_members = {
                    "Add", "Clear", "Contains", "CopyTo", "Remove",
                    "Count", "IsReadOnly",
                    "IndexOf", "Insert", "RemoveAt", "Item",
                }
            else:
                required_members = set()
            declared_members = {member["name"] for member in owner["members"]}
            missing = sorted(required_members - declared_members)
            if missing:
                failures.append(diagnostic(
                    "UNMEASURED_STRUCTURAL_CATEGORY", owner["name"],
                    f"direct {interface_prefix} owner lacks mapped contract members {missing}",
                ))
            records.append({
                "ownerType": owner["name"],
                "clrInterface": next(
                    direct for direct in owner["directInterfaces"]
                    if direct == interface_prefix or direct.startswith(interface_prefix + "[")
                ),
                "swiftProjection": mappings[interface_prefix],
                "requiredConcreteMembers": sorted(required_members),
            })
    return records, failures


def make_report(
    contract: dict[str, Any],
    rules: dict[str, Any],
    expected: dict[str, TypeModel],
    actual: dict[str, TypeModel],
    diagnostics: list[dict[str, str]],
    graph_path: Path,
    applied_suppressions: int,
    witness_evidence: list[dict[str, Any]],
    accessor_evidence: list[dict[str, Any]],
    system_interface_evidence: list[dict[str, Any]],
    support_evidence: list[dict[str, Any]],
    accessor_fallibility: dict[tuple[str, str], dict[str, bool]],
) -> dict[str, Any]:
    counts = collections.Counter(item["category"] for item in diagnostics)
    type_diagnostics: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for item in diagnostics:
        owner = item["subject"]
        while owner not in expected and "." in owner:
            owner = owner.rsplit(".", 1)[0]
        if owner in expected:
            type_diagnostics[owner].append(item)
    missing_types = sorted(name for name in expected if name not in actual)
    complete_types = sorted(name for name in expected if name in actual and not type_diagnostics[name])
    partial_types = sorted(name for name in expected if name in actual and type_diagnostics[name])
    expected_members = sum(len(model.members) for model in expected.values())
    target_members = sum(len(model.members) for model in actual.values())
    summary: dict[str, Any] = {
        "REFERENCE_TYPES": len(contract["types"]),
        "REFERENCE_MEMBERS": sum(len(item["members"]) for item in contract["types"]),
        "EXPECTED_SWIFT_TYPES": len(expected),
        "EXPECTED_SWIFT_MEMBERS": expected_members,
        "TARGET_TYPES": len(actual),
        "TARGET_MEMBERS": target_members,
        "TOTAL_DIAGNOSTICS": len(diagnostics),
        "COMPLETE_TYPES": len(complete_types),
        "PARTIAL_TYPES": len(partial_types),
        "MISSING_TYPES": len(missing_types),
    }
    summary.update({category: counts[category] for category in CATEGORIES})
    inherited_projections = sum(
        is_inherited_language_projection(expected[name], member, expected)
        for name, model in actual.items() if name in expected
        for member in model.members
    )
    enum_storage_exclusions = sum(
        member["kind"] == "field" and member["name"] == "value__"
        for item in contract["types"] for member in item["members"]
    )
    finalizer_mappings = sum(
        member["name"] == "Finalize"
        for item in contract["types"] for member in item["members"]
    )
    namespace_markers = len(rules["namespaceMarkers"])
    protocol_witness_projections = sum(
        item["compilerSourceOriginObserved"] for item in witness_evidence
    )
    array_mutation_mappings = 0
    for item in contract["types"]:
        direct_collection = any(
            interface.startswith(COLLECTION_COPY_INTERFACES)
            for interface in item.get("directInterfaces", [])
        )
        for member in item["members"]:
            for parameter in member.get("parameters", []):
                named_destination = (
                    parameter.get("name") in rules.get(
                        "arrayMutationParameterNames", ["destinationArray"],
                    ) and parameter.get("type", "").endswith("[]")
                )
                collection_copy_destination = (
                    direct_collection and member["name"] == "CopyTo" and
                    parameter.get("name") == "array" and
                    parameter.get("type", "").endswith("[]")
                )
                array_mutation_mappings += bool(
                    named_destination or collection_copy_destination
                )
    enumerator_support_projections = sum(
        (member.get("returnType") or "").startswith(
            "System.Collections.Generic.IEnumerator`1["
        )
        for item in contract["types"] for member in item["members"]
    )
    # The general accessor projection, counted over the whole contract rather
    # than over what happens to be implemented, so every branch of the rule is
    # a measured number even before a type using it exists.
    accessor_projection_counts: collections.Counter[str] = collections.Counter()
    for item in contract["types"]:
        for member in item["members"]:
            if member["kind"] != "property":
                continue
            verdict = accessor_fallibility.get((item["name"], member["name"]))
            getter_throws, writer_kind, writer_throws = accessor_projection(
                member, verdict,
            )
            indexed = bool(member.get("parameters"))
            accessor_projection_counts["ACCESSOR_PROJECTIONS"] += 1
            accessor_projection_counts["INDEXED_ACCESSOR_PROJECTIONS"] += indexed
            accessor_projection_counts["THROWING_GETTER_PROJECTIONS"] += getter_throws
            accessor_projection_counts["PROPERTY_SETTER_PROJECTIONS"] += (
                writer_kind == WRITER_PROPERTY
            )
            accessor_projection_counts["WRITER_METHOD_PROJECTIONS"] += (
                writer_kind == WRITER_METHOD
            )
            accessor_projection_counts["THROWING_WRITER_METHOD_PROJECTIONS"] += (
                writer_kind == WRITER_METHOD and writer_throws
            )
            accessor_projection_counts["INFALLIBLE_WRITER_METHOD_PROJECTIONS"] += (
                writer_kind == WRITER_METHOD and not writer_throws
            )
            accessor_projection_counts["GETTER_ONLY_PROJECTIONS"] += (
                writer_kind == WRITER_ABSENT
            )
            accessor_projection_counts["WRITE_ONLY_PROJECTIONS"] += (
                not member.get("get")
            )
    # A public CLR class whose declared constructors are all non-public cannot
    # be constructed or derived from outside its own assembly. The Swift
    # projection therefore exposes no public init; any initializer it needs is
    # internal implementation infrastructure. This is measured generally for
    # every implemented reference class, never per named type.
    nonpublic_construction_evidence: list[dict[str, Any]] = []
    for item in contract["types"]:
        if item["kind"] != "class":
            continue
        if any(member["kind"] == "constructor" for member in item["members"]):
            continue
        name = map_type_name(item["name"], rules)
        model = actual.get(name)
        if model is None:
            continue
        nonpublic_construction_evidence.append({
            "type": name,
            "clrSealed": bool(item.get("sealed")),
            "referencePublicConstructors": 0,
            "swiftPublicInitializers": sum(
                member.kind == "constructor" for member in model.members
            ),
            "reason": rules["nonPublicConstructionMapping"],
        })
    summary["ALLOWLIST_ENTRIES"] = len(rules.get("manualDiagnosticSuppressions", []))
    summary["APPLIED_ALLOWLIST_ENTRIES"] = applied_suppressions
    summary["LANGUAGE_PROJECTION_EXCLUSIONS"] = (
        enum_storage_exclusions + finalizer_mappings + namespace_markers +
        inherited_projections + protocol_witness_projections
    )
    summary["ENUM_STORAGE_FIELD_EXCLUSIONS"] = enum_storage_exclusions
    summary["FINALIZER_LANGUAGE_MAPPINGS"] = finalizer_mappings
    summary["NAMESPACE_MARKERS"] = namespace_markers
    summary["INHERITED_MEMBER_PROJECTIONS"] = inherited_projections
    summary["PROTOCOL_WITNESS_MEMBER_PROJECTIONS"] = protocol_witness_projections
    summary["ARRAY_MUTATION_MAPPINGS"] = array_mutation_mappings
    summary["COMPARABLE_INTERFACE_PROJECTIONS"] = sum(
        item["clrInterface"].startswith("System.IComparable`1[")
        for item in system_interface_evidence
    )
    summary["COLLECTION_INTERFACE_PROJECTIONS"] = sum(
        item["clrInterface"].startswith(
            "System.Collections.Generic.ICollection`1["
        )
        for item in system_interface_evidence
    )
    summary["ENUMERATOR_SUPPORT_PROJECTIONS"] = enumerator_support_projections
    for key in (
        "ACCESSOR_PROJECTIONS", "INDEXED_ACCESSOR_PROJECTIONS",
        "THROWING_GETTER_PROJECTIONS", "PROPERTY_SETTER_PROJECTIONS",
        "WRITER_METHOD_PROJECTIONS", "THROWING_WRITER_METHOD_PROJECTIONS",
        "INFALLIBLE_WRITER_METHOD_PROJECTIONS", "GETTER_ONLY_PROJECTIONS",
        "WRITE_ONLY_PROJECTIONS",
    ):
        summary[key] = accessor_projection_counts[key]
    summary["MEASURED_ACCESSOR_PROJECTIONS"] = len(accessor_evidence)
    # Every writer method the rule requires that no Swift symbol answers yet,
    # because the property or its whole type is still missing. Recording the
    # shape is not implementing it: these stay MISSING_MEMBER / MISSING_TYPE,
    # and a native runtime member must not gain a fabricated managed setter
    # just because its writer name is now known.
    measured_accessors = {
        (item["ownerType"], item["sourceProperty"]) for item in accessor_evidence
    }
    pending_accessors = [
        {
            "ownerType": owner_name,
            "sourceProperty": member.name,
            "typeState": (
                "partial" if owner_name in set(partial_types)
                else "missing" if owner_name in set(missing_types) else "complete"
            ),
            "readerThrows": bool(member.getter_throws),
            "writerName": member.writer_name,
            "writerThrows": bool(member.writer_throws),
            "indexed": bool(member.parameters),
            "static": member.static,
        }
        for owner_name, model in sorted(expected.items())
        for member in model.members
        if member.kind == "property" and member.writer_kind == WRITER_METHOD and
        (owner_name, member.name) not in measured_accessors
    ]
    summary["PENDING_ACCESSOR_PROJECTIONS"] = len(pending_accessors)
    summary["GLOBAL_OPTIONAL_OPERATOR_PROJECTIONS"] = len(
        rules.get("globalOperatorProjections", [])
    )
    summary["NONPUBLIC_CONSTRUCTION_PROJECTIONS"] = len(
        nonpublic_construction_evidence
    )
    # One measured event property per CLR event in the pinned contract, and the
    # support types they are all expressed through.
    summary["EVENT_PROJECTIONS"] = sum(
        member["kind"] == "event"
        for item in contract["types"] for member in item["members"]
    )
    summary["EVENT_SUPPORT_TYPE_MEASUREMENTS"] = len(support_evidence)
    summary["MEASURED_SUPPORT_BASE_PROJECTIONS"] = sum(
        map_clr_type(item["baseType"], rules) in MEASURED_SUPPORT_BASES
        for item in contract["types"] if item.get("baseType")
    )
    return {
        "schemaVersion": 1,
        "profile": contract["profile"],
        "reference": {
            "path": str(REFERENCE.relative_to(ROOT)),
            "sha256": hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        },
        "symbolGraph": str(graph_path),
        "summary": summary,
        "completeTypes": complete_types,
        "partialTypes": partial_types,
        "missingTypes": missing_types,
        "diagnostics": diagnostics,
        "protocolWitnessProjections": witness_evidence,
        "systemInterfaceProjections": system_interface_evidence,
        "accessorProjections": accessor_evidence,
        "pendingAccessorProjections": pending_accessors,
        "nonPublicConstructionProjections": nonpublic_construction_evidence,
        "eventSupportProjections": support_evidence,
        "typeScoreboard": [
            {
                "type": name,
                "status": "MISSING" if name in missing_types else ("COMPLETE" if name in complete_types else "PARTIAL"),
                "expectedMembers": len(model.members),
                "targetMembers": len(actual[name].members) if name in actual else 0,
                "diagnostics": type_diagnostics[name],
            }
            for name, model in sorted(expected.items())
        ],
    }


def render_missing_inventory(report: dict[str, Any]) -> str:
    lines = [
        "# XNA to Swift missing-type inventory",
        "",
        "Generated from the compiler Symbol Graph and the pinned XNA 4.0 Windows runtime contract.",
        "Normal strict status is intentionally red.",
        "",
        "```text",
    ]
    lines.extend(
        f"{key}={value}" for key, value in report["summary"].items()
        if isinstance(value, int)
    )
    lines.extend(["```", "", "## Complete types", ""])
    lines.extend(f"- `{name}`" for name in report["completeTypes"])
    lines.extend(["", "## Partial types and exact diagnostics", ""])
    scoreboard = {item["type"]: item for item in report["typeScoreboard"]}
    for name in report["partialTypes"]:
        item = scoreboard[name]
        lines.extend([
            f"### `{name}`", "",
            f"Expected members: {item['expectedMembers']}; emitted members: {item['targetMembers']}.", "",
        ])
        lines.extend(
            f"- `{diagnostic_item['category']}` — `{diagnostic_item['subject']}`: {diagnostic_item['detail']}"
            for diagnostic_item in item["diagnostics"]
        )
        lines.append("")
    lines.extend(["## Missing types", ""])
    lines.extend(f"- `{name}`" for name in report["missingTypes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol-graph", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inventory-output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--graph-self-test", action="store_true")
    parser.add_argument("--leak-only", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.graph_self_test:
        if not args.symbol_graph:
            parser.error("--graph-self-test requires --symbol-graph")
        symbol_graph_self_test(args.symbol_graph)
        return 0
    if not args.symbol_graph:
        parser.error("--symbol-graph is required unless --self-test is used")
    contract = load_json(REFERENCE)
    rules = load_json(RULES)
    accessor_fallibility = load_accessor_fallibility(rules)
    expected = build_expected(contract, rules, accessor_fallibility)
    (
        actual, parser_diagnostics, _, observed_witnesses, accessor_evidence,
        support,
    ) = parse_symbol_graph(
        args.symbol_graph, rules, ROOT / "Sources/CNA", expected,
    )
    support_evidence, support_diagnostics = event_support_evidence(support, rules)
    witness_evidence, witness_diagnostics = protocol_witness_projection_evidence(
        contract, rules, observed_witnesses,
    )
    system_interface_evidence, system_interface_diagnostics = (
        system_interface_projection_evidence(contract, rules)
    )
    diagnostics, applied_suppressions = apply_manual_suppressions(
        compare(expected, actual) + parser_diagnostics + witness_diagnostics +
        system_interface_diagnostics + support_diagnostics,
        rules.get("manualDiagnosticSuppressions", []),
    )
    report = make_report(
        contract, rules, expected, actual, diagnostics, args.symbol_graph,
        applied_suppressions, witness_evidence, accessor_evidence,
        system_interface_evidence, support_evidence, accessor_fallibility,
    )
    text = json.dumps(report, indent=2, sort_keys=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.inventory_output:
        args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_output.write_text(render_missing_inventory(report), encoding="utf-8")
    summary = report["summary"]
    print(" ".join(f"{key}={value}" for key, value in summary.items() if isinstance(value, int)), file=sys.stderr)
    if args.leak_only:
        return 1 if any(summary[key] for key in ("INTERNAL_TYPE_LEAK", "RAW_HANDLE_LEAK", "PUBLIC_NATIVE_FFI_LEAK")) else 0
    return 1 if summary["TOTAL_DIAGNOSTICS"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
