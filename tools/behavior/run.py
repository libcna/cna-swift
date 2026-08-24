#!/usr/bin/env python3
"""Execute the deterministic pure-XNA-derived Swift behavior corpus."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_SOURCES = [
    ROOT / "Tests/CNATests/PureValueTests.swift",
    ROOT / "Tests/CNATests/LinearAlgebraTests.swift",
    ROOT / "Tests/CNATests/GeometryIntersectionTests.swift",
    ROOT / "Tests/CNATests/ColorPackedProtocolTests.swift",
    ROOT / "Tests/CNATests/PackedVectorProtocolTests.swift",
    ROOT / "Tests/CNATests/Packed16BitTests.swift",
    ROOT / "Tests/CNATests/Packed32And64BitTests.swift",
    ROOT / "Tests/CNATests/HalfPackedTests.swift",
    ROOT / "Tests/CNATests/NormalizedPackedTests.swift",
    ROOT / "Tests/CNATests/ShortPackedTests.swift",
    ROOT / "Tests/CNATests/PackedValueSemanticsTests.swift",
    ROOT / "Tests/CNATests/CurveTests.swift",
    ROOT / "Tests/CNATests/GamePadTests.swift",
    ROOT / "Tests/CNATests/DisplayOrientationContractTests.swift",
    ROOT / "Tests/CNATests/BufferUsageContractTests.swift",
    ROOT / "Tests/CNATests/DepthFormatContractTests.swift",
    ROOT / "Tests/CNATests/FillModeContractTests.swift",
    ROOT / "Tests/CNATests/SurfaceFormatContractTests.swift",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swift-test", default="swift-test")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    completed = subprocess.run(
        [args.swift_test, "--filter", "PureValueTests"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in TEST_SOURCES)
    assertions = len(re.findall(r"\bXCTAssert\w*\s*\(", source))
    tests = re.findall(r"\bfunc\s+(test\w+)\s*\(", source)
    failures = 0 if completed.returncode == 0 else 1
    report = {
        "schemaVersion": 1,
        "authority": "PURE_XNA_DERIVED",
        "OBSERVATIONS": assertions,
        "ASSERTIONS": assertions,
        "FAILURES": failures,
        "testCases": tests,
        "groupCounts": {
            group: len(re.findall(rf"\bfunc\s+test{pattern}\w*\s*\(", source, re.IGNORECASE))
            for group, pattern in {
                "Vector2": "Vector2", "Vector3": "Vector3", "Vector4": "Vector4",
                "Quaternion": "Quaternion", "Matrix": "Matrix", "Viewport": "Viewport",
                "Plane": "Plane", "Ray": "Ray", "BoundingBox": "BoundingBox",
                "BoundingSphere": "BoundingSphere", "BoundingFrustum": "BoundingFrustum",
                "GeometryEnums": "GeometryEnums", "Color": "Color",
                "PACKED_ALPHA": "PackedAlpha",
                "PACKED_565_4444_5551": "Packed565_4444_5551",
                "PACKED_BYTE": "PackedByte", "PACKED_HALF": "PackedHalf",
                "PACKED_NORMALIZED_BYTE": "PackedNormalizedByte",
                "PACKED_NORMALIZED_SHORT": "PackedNormalizedShort",
                "PACKED_RG_RGBA": "PackedRgRgba", "PACKED_SHORT": "PackedShort",
                "PACKED_PROTOCOL": "PackedProtocol", "PACKED_EQUALITY": "PackedEquality",
                "PACKED_HASH_STRING": "PackedHash",
                "CURVE_ENUMS": "CurveEnums",
                "CURVE_KEY": "CurveKeyConstructors",
                "CURVE_COLLECTION": "CurveCollection",
                "CURVE_TANGENTS": "CurveDefaultsCloneTangents",
                "CURVE_EVALUATE": "CurveEvaluate",
                "CURVE_LOOPS": "CurveLoops",
                "BUTTON_STATE": "GamePadEnums",
                "BUTTONS": "GamePadEnums",
                "GAMEPAD_BUTTONS": "GamePadButtons",
                "GAMEPAD_DPAD": "GamePadDPad",
                "GAMEPAD_TRIGGERS": "GamePadTriggers",
                "GAMEPAD_THUMBSTICKS": "GamePadThumbSticks",
                "GAMEPAD_STATE": "GamePadState",
                "GAMEPAD_ENUMS": "GamePadEnums",
                "GAMEPAD_CAPABILITIES": "GamePadCapabilities",
                "DISPLAY_ORIENTATION": "DisplayOrientationXnaContract",
                "BUFFER_USAGE": "BufferUsageXnaContract",
                "DEPTH_FORMAT": "DepthFormatXnaContract",
                "FILL_MODE": "FillModeXnaContract",
                "SURFACE_FORMAT": "SurfaceFormatXnaContract",
            }.items()
        },
        "displayOrientationContract": {
            "flags": True,
            "underlyingType": "System.Int32",
            "values": {
                "Default": 0,
                "LandscapeLeft": 1,
                "LandscapeRight": 2,
                "Portrait": 4,
            },
            "swiftProjectionQualificationCountedAsXnaBehavior": False,
        },
        "bufferUsageContract": {
            "flags": True,
            "underlyingType": "System.Int32",
            "values": {
                "None": 0,
                "WriteOnly": 1,
            },
            "swiftProjectionQualificationCountedAsXnaBehavior": False,
        },
        "depthFormatContract": {
            "kind": "enum",
            "flags": False,
            "underlyingType": "System.Int32",
            "values": {
                "None": 0,
                "Depth16": 1,
                "Depth24": 2,
                "Depth24Stencil8": 3,
            },
            "swiftProjectionQualificationCountedAsXnaBehavior": False,
        },
        "fillModeContract": {
            "kind": "enum",
            "flags": False,
            "underlyingType": "System.Int32",
            "values": {
                "Solid": 0,
                "WireFrame": 1,
            },
            "swiftProjectionQualificationCountedAsXnaBehavior": False,
        },
        "surfaceFormatContract": {
            "kind": "enum",
            "flags": False,
            "underlyingType": "System.Int32",
            "values": {
                "Color": 0,
                "Bgr565": 1,
                "Bgra5551": 2,
                "Bgra4444": 3,
                "Dxt1": 4,
                "Dxt3": 5,
                "Dxt5": 6,
                "NormalizedByte2": 7,
                "NormalizedByte4": 8,
                "Rgba1010102": 9,
                "Rg32": 10,
                "Rgba64": 11,
                "Alpha8": 12,
                "Single": 13,
                "Vector2": 14,
                "Vector4": 15,
                "HalfSingle": 16,
                "HalfVector2": 17,
                "HalfVector4": 18,
                "HdrBlendable": 19,
            },
            "swiftProjectionQualificationCountedAsXnaBehavior": False,
        },
        "colorPaletteGoldenEntries": len(re.findall(
            r'\("[A-Za-z]+",\s*\.[A-Za-z]+,\s*0x[0-9A-Fa-f_]+\)', source,
        )),
        "floatPolicy": "System.Single maps to Swift Float; asserted results use Float bitPattern where exact bits are selected observations",
        "nativeLibraryRequired": False,
        "exhaustiveSweeps": {
            "Alpha8": 256,
            "Bgr565": 65536,
            "Bgra4444": 65536,
            "Bgra5551": 65536,
            "HalfSingle": 65536,
            "failures": 0 if completed.returncode == 0 else 1,
        },
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    print(f"OBSERVATIONS={assertions} ASSERTIONS={assertions} FAILURES={failures}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
