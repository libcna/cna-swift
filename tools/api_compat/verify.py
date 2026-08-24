#!/usr/bin/env python3
"""Compiler-Symbol-Graph verifier for the strict CNA-Swift XNA projection."""

from __future__ import annotations

import argparse
import collections
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
    generic = re.fullmatch(r"(.+)`(\d+)\[(.*)]", text)
    if generic:
        base = map_type_name(f"{generic.group(1)}`{generic.group(2)}", rules)
        args = ", ".join(
            map_clr_type(item, rules, generic_parameters)
            for item in split_generic_arguments(generic.group(3))
        )
        return f"{base}<{args}>"
    return map_type_name(text, rules)


def member_is_omitted(member: dict[str, Any]) -> bool:
    return (member["kind"] == "field" and member["name"] == "value__") or member["name"] == "Finalize"


def expected_member(
    owner: str,
    source: dict[str, Any],
    rules: dict[str, Any],
    owner_kind: str,
    owner_generic_parameters: tuple[str, ...] = (),
    owner_direct_interfaces: tuple[str, ...] = (),
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
                item.startswith("System.Collections.Generic.ICollection`1[")
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
    if kind == "property":
        mutable = bool(source.get("set"))
    elif kind == "field":
        mutable = not bool(source.get("constant"))

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
    )


def build_expected(contract: dict[str, Any], rules: dict[str, Any]) -> dict[str, TypeModel]:
    models: dict[str, TypeModel] = {}
    for source_type in contract["types"]:
        name = map_type_name(source_type["name"], rules)
        kind = source_type["kind"]
        flags = bool(source_type.get("flags"))
        swift_kind = "struct" if kind == "enum" and flags else rules["typeKinds"][kind]
        generic_parameters = tuple(
            item["name"] for item in source_type.get("genericParameters", [])
        )
        model = TypeModel(
            name=name,
            kind=swift_kind,
            flags=flags,
            base=map_clr_type(source_type.get("baseType"), rules) if source_type.get("baseType") else None,
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
    if kind == "property":
        mutable = not ("let " in decl or ("{ get" in decl and " set" not in decl))
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


def indexed_setter_shape_diagnostics(
    owner_name: str,
    setter: Member,
    expected_property: Member,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    expected_parameters = expected_property.parameters + (
        expected_property.return_type,
    )
    expected_labels = expected_property.labels + ("_",)
    expected_directions = expected_property.directions + ("",)
    subject = f"{owner_name}.SetItem"
    if setter.static != expected_property.static or setter.kind != "method":
        result.append(diagnostic(
            "METHOD_SIGNATURE_MAPPING_MISMATCH", subject,
            "indexed-property setter kind/static identity differs",
        ))
    if setter.parameters != expected_parameters or setter.labels != expected_labels:
        result.append(diagnostic(
            "PARAMETER_MAPPING_MISMATCH", subject,
            "indexed-property setter index or element type differs",
        ))
    if setter.directions != expected_directions:
        result.append(diagnostic(
            "REF_OUT_MAPPING_MISMATCH", subject,
            "indexed-property setter parameter direction differs",
        ))
    if setter.return_type != "Void":
        result.append(diagnostic(
            "RETURN_MAPPING_MISMATCH", subject,
            f"indexed-property setter returns {setter.return_type}, expected Void",
        ))
    return result


def parse_symbol_graph(
    path: Path,
    rules: dict[str, Any],
    source_root: Path,
    expected: dict[str, TypeModel],
) -> tuple[
    dict[str, TypeModel], list[dict[str, Any]], int,
    list[dict[str, str]], list[dict[str, Any]],
]:
    graph = load_json(path)
    symbols = {item["identifier"]["precise"]: item for item in graph["symbols"]}
    markers = set(rules["namespaceMarkers"])
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
        if swift_kind not in TYPE_KINDS or not path_name.startswith("Microsoft.Xna.Framework") or path_name in markers:
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

    read_write_indexers = {
        (owner_name, member.name): member
        for owner_name, model in expected.items()
        for member in model.members
        if member.kind == "property" and member.parameters and member.mutable
    }
    indexed_candidates: dict[tuple[str, str], Member] = {}
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
        if (parent, member.name) in read_write_indexers:
            indexed_candidates[(parent, "getter")] = member
            continue
        if (
            member.name == "SetItem" and
            any(owner_name == parent for owner_name, _ in read_write_indexers)
        ):
            indexed_candidates[(parent, "setter")] = member
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

    # Swift cannot express a throwing setter. A read/write CLR indexer is
    # therefore emitted as throwing Item/SetItem methods, but remains one
    # source property identity in the strict scoreboard.
    indexed_evidence: list[dict[str, Any]] = []
    for (owner_name, property_name), expected_property in read_write_indexers.items():
        if owner_name not in types:
            continue
        getter = indexed_candidates.get((owner_name, "getter"))
        setter = indexed_candidates.get((owner_name, "setter"))
        valid_getter = bool(
            getter is not None and
            getter.static == expected_property.static and
            getter.parameters == expected_property.parameters and
            getter.labels == expected_property.labels and
            getter.directions == expected_property.directions and
            getter.return_type == expected_property.return_type
        )
        valid_setter = setter is not None
        if getter is not None:
            types[owner_name].members.append(dataclasses.replace(
                getter,
                kind="property",
                name=property_name,
                mutable=setter is not None,
            ))
        if setter is not None:
            setter_diagnostics = indexed_setter_shape_diagnostics(
                owner_name, setter, expected_property,
            )
            valid_setter = not setter_diagnostics
            diagnostics_context.extend(setter_diagnostics)
        indexed_evidence.append({
            "ownerType": owner_name,
            "sourceProperty": property_name,
            "getterSymbol": getter.display if getter else None,
            "setterSymbol": setter.display if setter else None,
            "getterObserved": valid_getter,
            "setterObserved": valid_setter,
            "reason": "Swift throwing accessors require a compiler-measured Item/SetItem expansion",
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

    return (
        types, diagnostics_context, strict_symbols, observed_projections,
        indexed_evidence,
    )


def comparable_kind(expected: Member, actual: Member) -> bool:
    if expected.kind == actual.kind:
        return True
    if expected.kind == "field" and actual.kind == "property":
        return "{ get" not in actual.declaration
    if expected.kind == "event" and actual.kind == "property":
        return True
    return False


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
        if expected_base and expected_base.startswith("Microsoft.Xna.Framework") and actual_type.base != expected_base:
            result.append(diagnostic("BASE_MAPPING_MISMATCH", name, f"expected base {expected_base}, found {actual_type.base}"))
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
                category = "PROPERTY_MAPPING_MISMATCH" if expected_member_model.kind in ("property", "field") else "METHOD_SIGNATURE_MAPPING_MISMATCH"
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
            if expected_member_model.kind in ("method", "property", "field") and expected_member_model.return_type != candidate.return_type:
                category = "RETURN_MAPPING_MISMATCH" if expected_member_model.kind == "method" else ("FIELD_MAPPING_MISMATCH" if expected_member_model.kind == "field" else "PROPERTY_MAPPING_MISMATCH")
                result.append(diagnostic(category, subject, f"expected {expected_member_model.return_type}, found {candidate.return_type}"))
            if expected_member_model.mutable is not None and candidate.mutable is not None and expected_member_model.mutable != candidate.mutable:
                category = "FIELD_MAPPING_MISMATCH" if expected_member_model.kind == "field" else "PROPERTY_MAPPING_MISMATCH"
                result.append(diagnostic(category, subject, f"expected mutable={expected_member_model.mutable}, found mutable={candidate.mutable}"))
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
        ("Int32",), ("_",), ("",), curve_key_name, mutable=True,
        identifier="curve-item",
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
        ("missing Item setter", "PROPERTY_MAPPING_MISMATCH",
         lambda m: setattr(m[curve_collection_name].members[0], "mutable", False)),
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
    for label, wanted, mutate in curve_mutations:
        models = copy.deepcopy(curve_good)
        mutate(models)
        if wanted not in curve_categories(models):
            failures.append(f"{label}: did not produce {wanted}")

    setter_good = Member(
        curve_collection_name, "method", "SetItem", False,
        ("Int32", curve_key_name), ("_", "_"), ("", ""), "Void",
        identifier="curve-set-item",
    )
    if indexed_setter_shape_diagnostics(
        curve_collection_name, setter_good, curve_item,
    ):
        failures.append("valid indexed-property setter rejected")
    setter_wrong_index = dataclasses.replace(
        setter_good, parameters=("Int", curve_key_name),
    )
    if "PARAMETER_MAPPING_MISMATCH" not in {
        item["category"] for item in indexed_setter_shape_diagnostics(
            curve_collection_name, setter_wrong_index, curve_item,
        )
    }:
        failures.append("wrong indexed-property setter index not detected")
    setter_wrong_element = dataclasses.replace(
        setter_good, parameters=("Int32", "Float"),
    )
    if "PARAMETER_MAPPING_MISMATCH" not in {
        item["category"] for item in indexed_setter_shape_diagnostics(
            curve_collection_name, setter_wrong_element, curve_item,
        )
    }:
        failures.append("wrong indexed-property setter element not detected")

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

    if failures:
        raise SystemExit("self-test failures:\n" + "\n".join(failures))
    print(
        "API_COMPAT_SELF_TESTS="
        f"{len(mutations) + 17 + len(protocol_mutations) + len(curve_mutations) + 5 + len(gamepad_mutations) + len(display_mutations) + 1 + len(buffer_mutations) + 1 + len(fill_mutations) + 1 + len(surface_mutations) + 1}"
    )
    print("API_COMPAT_SELF_TEST_STATUS=PASS")


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
    indexed_evidence: list[dict[str, Any]],
    system_interface_evidence: list[dict[str, Any]],
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
            interface.startswith("System.Collections.Generic.ICollection`1[")
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
    indexed_property_accessor_projections = sum(
        member["kind"] == "property" and bool(member.get("parameters")) and
        bool(member.get("get")) and bool(member.get("set"))
        for item in contract["types"] for member in item["members"]
    )
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
    summary["INDEXED_PROPERTY_ACCESSOR_PROJECTIONS"] = (
        indexed_property_accessor_projections
    )
    summary["GLOBAL_OPTIONAL_OPERATOR_PROJECTIONS"] = len(
        rules.get("globalOperatorProjections", [])
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
        "indexedPropertyAccessorProjections": indexed_evidence,
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
    parser.add_argument("--leak-only", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.symbol_graph:
        parser.error("--symbol-graph is required unless --self-test is used")
    contract = load_json(REFERENCE)
    rules = load_json(RULES)
    expected = build_expected(contract, rules)
    actual, parser_diagnostics, _, observed_witnesses, indexed_evidence = parse_symbol_graph(
        args.symbol_graph, rules, ROOT / "Sources/CNA", expected,
    )
    witness_evidence, witness_diagnostics = protocol_witness_projection_evidence(
        contract, rules, observed_witnesses,
    )
    system_interface_evidence, system_interface_diagnostics = (
        system_interface_projection_evidence(contract, rules)
    )
    diagnostics, applied_suppressions = apply_manual_suppressions(
        compare(expected, actual) + parser_diagnostics + witness_diagnostics +
        system_interface_diagnostics,
        rules.get("manualDiagnosticSuppressions", []),
    )
    report = make_report(
        contract, rules, expected, actual, diagnostics, args.symbol_graph,
        applied_suppressions, witness_evidence, indexed_evidence,
        system_interface_evidence,
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
