#!/usr/bin/env python3
"""Audit an exact source archive and qualify a fresh independent consumer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

PACKAGE = '''// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CNAArchiveConsumer",
    dependencies: [.package(path: "{dependency}")],
    targets: [.executableTarget(
        name: "ArchiveCanary",
        dependencies: [.product(name: "CNA", package: "{identity}")]
    )]
)
'''

SOURCE = r'''import CNA
import Foundation

final class ArchiveGame: Microsoft.Xna.Framework.Game {
    let requested: Int
    var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?
    var texture: Microsoft.Xna.Framework.Graphics.Texture2D?
    var batch: Microsoft.Xna.Framework.Graphics.SpriteBatch?
    var updates = 0
    var draws = 0

    init(_ requested: Int) throws {
        self.requested = requested
        try super.init()
        manager = try Microsoft.Xna.Framework.GraphicsDeviceManager(game: self)
    }

    override func LoadContent() throws {
        let bytes = Data(base64Encoded: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+Xw2kWQAAAABJRU5ErkJggg==")!
        let device = try GraphicsDevice
        texture = try Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(
            device, stream: InputStream(data: bytes))
        batch = try Microsoft.Xna.Framework.Graphics.SpriteBatch(graphicsDevice: device)
    }

    override func Update(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        updates += 1
        _ = try Microsoft.Xna.Framework.Input.Keyboard.GetState()
    }

    override func Draw(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        guard let texture, let batch else { return }
        try GraphicsDevice.Clear(.CornflowerBlue)
        try batch.Begin()
        try batch.Draw(texture, position: .Zero, color: .White)
        try batch.End()
        draws += 1
        if draws == requested { try Exit() }
    }
}

do {
    let index = CommandLine.arguments.firstIndex(of: "--frames")!
    let requested = Int(CommandLine.arguments[index + 1])!
    let game = try ArchiveGame(requested)
    try game.Run()
    print("ARCHIVE_CANARY requested=\(requested) updates=\(game.updates) draws=\(game.draws) texture=\(game.texture?.Width ?? 0)x\(game.texture?.Height ?? 0)")
    try game.Dispose()
} catch {
    FileHandle.standardError.write(Data("archive canary failed: \(error)\n".utf8))
    Foundation.exit(1)
}
'''


def run(command: list[str], cwd: Path, environment: dict[str, str]) -> str:
    completed = subprocess.run(
        command, cwd=cwd, env=environment, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout


def validate_canary(output: str, requested: int) -> bool:
    match = re.search(
        r"ARCHIVE_CANARY requested=(\d+) updates=(\d+) draws=(\d+) texture=(\d+)x(\d+)",
        output,
    )
    if not match:
        return False
    observed_request, updates, draws, width, height = map(int, match.groups())
    return (
        observed_request == requested and
        updates >= requested and
        draws == requested and
        width == 1 and
        height == 1
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--swift-build", default="swift-build")
    parser.add_argument("--swift-run", default="swift-run")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.archive.is_absolute() or not args.archive.is_file():
        parser.error("--archive must be an absolute existing file")
    if not args.library.is_absolute() or not args.library.is_file():
        parser.error("--library must be an absolute existing file")

    forbidden: list[str] = []
    native_libraries: list[str] = []
    microsoft_reference_binaries: list[str] = []
    path_leaks: list[str] = []
    path_patterns = {
        str(Path.home()).encode(),
        str(Path.cwd().resolve()).encode(),
    }
    with zipfile.ZipFile(args.archive) as archive:
        entries = archive.namelist()
        for name in entries:
            parts = Path(name).parts
            if any(part in {".git", ".build"} for part in parts):
                forbidden.append(name)
            if name.endswith((".so", ".dylib", ".dll", ".a")):
                native_libraries.append(name)
            if (
                Path(name).name.lower().startswith("microsoft.xna.framework") and
                name.lower().endswith((".dll", ".exe"))
            ):
                microsoft_reference_binaries.append(name)
            if not name.endswith("/"):
                data = archive.read(name)
                if any(pattern and pattern in data for pattern in path_patterns):
                    path_leaks.append(name)

        with tempfile.TemporaryDirectory(prefix="cna-swift-archive-consumer-") as temporary:
            root = Path(temporary)
            extracted = root / "extracted"
            consumer = root / "consumer"
            archive.extractall(extracted)
            package_roots = [item for item in extracted.iterdir() if item.is_dir()]
            if len(package_roots) != 1:
                raise RuntimeError(f"archive has {len(package_roots)} package roots")
            dependency = package_roots[0]
            for path in sorted(dependency.rglob("*"), reverse=True):
                path.chmod(path.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
            dependency.chmod(dependency.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)

            sources = consumer / "Sources/ArchiveCanary"
            sources.mkdir(parents=True)
            identity = dependency.name.lower()
            (consumer / "Package.swift").write_text(
                PACKAGE.format(dependency=dependency.as_posix(), identity=identity), encoding="utf-8")
            (sources / "main.swift").write_text(SOURCE, encoding="utf-8")

            environment = os.environ.copy()
            environment["CNA_NATIVE_LIBRARY"] = str(args.library)
            scratch = root / "scratch"
            run([args.swift_build, "--scratch-path", str(scratch)], consumer, environment)
            debug_output = run([
                args.swift_run, "--scratch-path", str(scratch), "ArchiveCanary", "--frames", "60"
            ], consumer, environment)
            run([args.swift_build, "--scratch-path", str(scratch), "-c", "release"], consumer, environment)
            release_output = run([
                args.swift_run, "--scratch-path", str(scratch), "-c", "release",
                "ArchiveCanary", "--frames", "600"
            ], consumer, environment)
            if not validate_canary(debug_output, 60):
                raise RuntimeError(
                    "debug archive consumer callback/dimension evidence did not match:\n" +
                    debug_output
                )
            if not validate_canary(release_output, 600):
                raise RuntimeError(
                    "release archive consumer callback/dimension evidence did not match:\n" +
                    release_output
                )

    report = {
        "schemaVersion": 1,
        "SOURCE_ARCHIVE_FILENAME": args.archive.name,
        "SOURCE_ARCHIVE_SHA256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        "SOURCE_ARCHIVE_ENTRIES": len(entries),
        "FORBIDDEN_ENTRIES": forbidden,
        "NATIVE_LIBRARIES": native_libraries,
        "MICROSOFT_REFERENCE_BINARIES": microsoft_reference_binaries,
        "DEVELOPER_PATH_LEAKS": path_leaks,
        "DEBUG_BUILD": "PASS",
        "RELEASE_BUILD": "PASS",
        "RUN_60": "PASS",
        "RUN_600": "PASS",
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    print(" ".join(f"{key}={report[key]}" for key in (
        "SOURCE_ARCHIVE_FILENAME", "SOURCE_ARCHIVE_SHA256", "SOURCE_ARCHIVE_ENTRIES",
        "DEBUG_BUILD", "RELEASE_BUILD", "RUN_60", "RUN_600"
    )))
    return 1 if forbidden or native_libraries or path_leaks or microsoft_reference_binaries else 0


if __name__ == "__main__":
    raise SystemExit(main())
