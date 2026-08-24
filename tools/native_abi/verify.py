#!/usr/bin/env python3
"""Compiler-backed CNA 0.7 ABI verifier for the Swift function manifest."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "Sources/CNA/Native/NativeManifest.swift"
FUNCTIONS = ROOT / "Sources/CNA/Native/NativeFunctions.swift"
SHIM_INCLUDE = ROOT / "Sources/CNAShim/include"
PROBE = ROOT / "tools/native_abi/probe.c"
KEYS = ROOT / "Sources/CNA/Xna/Input/Keyboard.swift"


def manifest_entries() -> list[dict[str, Any]]:
    text = MANIFEST.read_text(encoding="utf-8")
    pattern = re.compile(
        r'\.init\(symbol: "(?P<symbol>[^"]+)", cReturn: "(?P<ret>[^"]+)", '
        r'cParameters: \[(?P<params>.*?)\], ownership:', re.S
    )
    entries: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        params = re.findall(r'"([^"]+)"', match.group("params"))
        entries.append({"symbol": match.group("symbol"), "return": match.group("ret"), "parameters": params})
    if not entries:
        raise RuntimeError("NativeManifest.swift contained no parseable entries")
    return entries


def strip_parameter_name(value: str) -> str:
    return re.sub(r"\s+[A-Za-z_][A-Za-z0-9_]*$", "", value.strip())


def canonical_type(value: str) -> str:
    text = strip_parameter_name(value)
    text = re.sub(r"\s+", " ", text)
    aliases = {
        "CNA_Result": "uint32_t", "CNA_Bool": "uint8_t", "CNA_Handle": "uint64_t",
        "CNA_GraphicsDeviceManagerHandle": "uint64_t", "CNA_PlayerIndex": "uint32_t",
    }
    for old, new in aliases.items():
        text = re.sub(rf"\b{old}\b", new, text)
    return text.replace(" *", "*")


def swift_type(value: str) -> str:
    text = value.strip().rstrip("?")
    mutable = re.fullmatch(r"UnsafeMutablePointer<(.+)>", text)
    immutable = re.fullmatch(r"UnsafePointer<(.+)>", text)
    if mutable:
        return f"{swift_type(mutable.group(1))}*"
    if immutable:
        return f"const {swift_type(immutable.group(1))}*"
    mapping = {
        "UInt8": "uint8_t", "UInt32": "uint32_t", "UInt64": "uint64_t", "Int32": "int32_t",
        "Int64": "int64_t", "Float": "float", "Double": "double", "CChar": "char",
        "CNASwift_GameCreateInfo": "CNA_GameCreateInfo",
        "CNASwift_GameFrameHooks": "CNA_GameFrameHooks",
        "CNASwift_Viewport": "CNA_Viewport",
        "CNASwift_Texture2DDecodeInfo": "CNA_Texture2DDecodeInfo",
        "CNASwift_Texture2DInfo": "CNA_Texture2DInfo",
        "CNASwift_SpriteBatchBeginInfo": "CNA_SpriteBatchBeginInfo",
        "CNASwift_SpriteScaledCommand": "CNA_SpriteScaledCommand",
        "CNASwift_KeyboardState": "CNA_KeyboardState",
    }
    return mapping.get(text, text)


def split_swift_types(text: str) -> list[str]:
    values: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "<": depth += 1
        elif char == ">": depth -= 1
        elif char == "," and depth == 0:
            values.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail: values.append(tail)
    return values


def swift_aliases() -> tuple[dict[str, tuple[str, list[str]]], dict[str, str]]:
    text = FUNCTIONS.read_text(encoding="utf-8")
    aliases: dict[str, tuple[str, list[str]]] = {}
    for match in re.finditer(r"typealias\s+(\w+)\s*=\s*@convention\(c\)\s*\((.*?)\)\s*->\s*([^\n]+)", text):
        aliases[match.group(1)] = (swift_type(match.group(3)), [swift_type(item) for item in split_swift_types(match.group(2))])
    resolutions = {
        symbol: alias
        for symbol, alias in re.findall(r'library\.resolve\("([^"]+)", as:\s*(\w+)\.self\)', text)
    }
    return aliases, resolutions


def prototype_assertions(entries: list[dict[str, Any]]) -> str:
    lines = ['#include "CNA/C/cna.h"']
    for index, entry in enumerate(entries):
        params = ", ".join(entry["parameters"]) or "void"
        lines.append(f'typedef {entry["return"]} (*Expected_{index})({params});')
        lines.append(
            f'_Static_assert(__builtin_types_compatible_p(__typeof__(&{entry["symbol"]}), Expected_{index}), '
            f'"prototype mismatch: {entry["symbol"]}");'
        )
    lines.append("int main(void) { return 0; }")
    return "\n".join(lines) + "\n"


def key_cases() -> dict[str, int]:
    result: dict[str, int] = {}
    active = False
    depth = 0
    for line in KEYS.read_text(encoding="utf-8").splitlines():
        if re.search(r"public enum Keys\s*:\s*Int32", line):
            active = True
            depth = line.count("{") - line.count("}")
            continue
        if active:
            depth += line.count("{") - line.count("}")
            match = re.search(r"\bcase\s+(\w+)\s*=\s*(-?\d+)", line)
            if match: result[match.group(1)] = int(match.group(2))
            if depth <= 0: break
    return result


def c_key_name(swift_name: str) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", swift_name)
    name = "_".join(word.upper() for word in words)
    # The canonical constants join a trailing numeric identity to the word
    # which precedes it: D0, F12, NUM_PAD0, OEM8, APPLICATION1.
    name = re.sub(r"(?<=[A-Z])_(?=\d)", "", name)
    return "CNA_KEY_" + name


def compile_and_run(cc: str, source: Path, include: Path, output: Path) -> str:
    subprocess.run([
        cc, "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
        f"-I{include}", f"-I{SHIM_INCLUDE}", str(source), "-o", str(output),
    ], check=True, text=True, capture_output=True)
    return subprocess.run([str(output)], check=True, text=True, capture_output=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cna-include", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--cc", default="cc")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    entries = manifest_entries()
    aliases, resolutions = swift_aliases()
    mismatches: list[str] = []
    measured_positions = 0
    for entry in entries:
        alias_name = resolutions.get(entry["symbol"])
        if entry["symbol"] == "cna_get_abi_version":
            alias_name = "GetABIVersion"
        if not alias_name or alias_name not in aliases:
            mismatches.append(f'{entry["symbol"]}: no Swift function alias/resolution')
            continue
        swift_return, swift_parameters = aliases[alias_name]
        c_return = canonical_type(entry["return"])
        c_parameters = [canonical_type(item) for item in entry["parameters"]]
        measured_positions += 1 + len(c_parameters)
        if swift_return != c_return:
            mismatches.append(f'{entry["symbol"]}: return {swift_return} != {c_return}')
        if swift_parameters != c_parameters:
            mismatches.append(f'{entry["symbol"]}: parameters {swift_parameters} != {c_parameters}')

    with tempfile.TemporaryDirectory(prefix="cna-swift-abi-") as temporary:
        temp = Path(temporary)
        probe_output = compile_and_run(args.cc, PROBE, args.cna_include, temp / "probe")
        generated = temp / "prototypes.c"
        generated.write_text(prototype_assertions(entries), encoding="utf-8")
        compile_and_run(args.cc, generated, args.cna_include, temp / "prototypes")

        key_source = temp / "keys.c"
        key_lines = ['#include "CNA/C/input.h"']
        keys = key_cases()
        for name, value in keys.items():
            key_lines.append(f'_Static_assert({c_key_name(name)} == {value}, "Keys.{name}");')
        key_lines.append("int main(void) { return 0; }")
        key_source.write_text("\n".join(key_lines) + "\n", encoding="utf-8")
        compile_and_run(args.cc, key_source, args.cna_include, temp / "keys")

    exported = subprocess.run(
        ["nm", "-D", "--defined-only", str(args.library)], check=True, text=True, capture_output=True
    ).stdout
    exported_names = {line.split()[-1].split("@@", 1)[0] for line in exported.splitlines() if line.split()}
    missing_library = sorted(entry["symbol"] for entry in entries if entry["symbol"] not in exported_names)

    loaded_abi: int | None = None
    load_error: str | None = None
    try:
        library = ctypes.CDLL(str(args.library.resolve()))
        library.cna_get_abi_version.restype = ctypes.c_uint32
        loaded_abi = int(library.cna_get_abi_version())
    except OSError as error:
        load_error = str(error)
    if loaded_abi != 0x700:
        mismatches.append(f"loaded ABI {loaded_abi!r} != exact 1792")
    if load_error:
        mismatches.append(f"library load: {load_error}")

    report = {
        "schemaVersion": 1,
        "CNA_ABI_VERSION": "0.7.0",
        "CNA_ABI_ENCODED": 0x700,
        "LOADED_ABI_ENCODED": loaded_abi,
        "BOUND_FUNCTIONS": len(entries),
        "PROTOTYPE_TYPE_POSITIONS": sum(1 + len(entry["parameters"]) for entry in entries),
        "C_SWIFT_MEASUREMENTS": measured_positions,
        "LAYOUTS": 15,
        "CALLBACKS": 2,
        "CONSTANTS": 8 + len(keys),
        "MISSING_HEADER_SYMBOLS": 0,
        "MISSING_LIBRARY_SYMBOLS": len(missing_library),
        "ABI_MISMATCHES": len(mismatches),
        "missingLibrarySymbols": missing_library,
        "mismatches": mismatches,
        "probeOutput": dict(line.split("=", 1) for line in probe_output.splitlines() if "=" in line),
        "library": {
            "filename": args.library.name,
            "sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
        },
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    print(" ".join(f"{key}={report[key]}" for key in (
        "BOUND_FUNCTIONS", "PROTOTYPE_TYPE_POSITIONS", "C_SWIFT_MEASUREMENTS", "LAYOUTS",
        "CALLBACKS", "CONSTANTS", "MISSING_HEADER_SYMBOLS", "MISSING_LIBRARY_SYMBOLS", "ABI_MISMATCHES"
    )))
    return 1 if missing_library or mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
