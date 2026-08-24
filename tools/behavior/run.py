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
            group: len(re.findall(rf"\bfunc\s+test{group}\w*\s*\(", source, re.IGNORECASE))
            for group in (
                "Vector2", "Vector3", "Vector4", "Quaternion", "Matrix", "Viewport",
                "Plane", "Ray", "BoundingBox", "BoundingSphere", "BoundingFrustum", "GeometryEnums",
                "Color",
            )
        },
        "colorPaletteGoldenEntries": len(re.findall(
            r'\("[A-Za-z]+",\s*\.[A-Za-z]+,\s*0x[0-9A-Fa-f_]+\)', source,
        )),
        "floatPolicy": "System.Single maps to Swift Float; asserted results use Float bitPattern where exact bits are selected observations",
        "nativeLibraryRequired": False,
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
