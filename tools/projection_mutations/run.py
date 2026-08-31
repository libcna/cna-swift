#!/usr/bin/env python3
"""Falsifiability controls for the projected exception payloads.

The payload of a projected CLR/XNA exception has four separately observable
parts — the class, the composed `Message`, `ParamName` and `HResult` — and a
test suite that asserted only the message would pass on a defect in any of the
other three. This harness plants one realistic defect at a time, runs the
tests, and requires them to fail; a surviving mutation is reported as a failure
of this gate.

Every mutation is one exact textual substitution, undone in a `finally`, and
the tree is proven byte-identical afterwards.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCEPTIONS = ROOT / "Sources/CNA/CNAExceptions.swift"
COLLECTIONS = ROOT / "Sources/CNA/CNACollections.swift"
DICTIONARY = ROOT / "Sources/CNA/CNADictionary.swift"
SERVICES = ROOT / "Sources/CNA/Xna/Framework/GameServiceContainer.swift"
RESOURCE = ROOT / "Sources/CNA/Xna/Graphics/GraphicsResource.swift"
TEXTURE2D = ROOT / "Sources/CNA/Xna/Graphics/Texture2D.swift"
RENDER_TARGET = ROOT / "Sources/CNA/Xna/Graphics/RenderTarget2D.swift"

# The WHOLE suite runs for every mutation, deliberately.
#
# The first version of this harness filtered to the suites that assert a
# projected payload. `swift test --filter` in this toolchain honours only one
# pattern -- an alternation regex and repeated `--filter` flags both selected a
# single suite -- so the baseline and every mutation ran fifteen tests instead
# of four hundred, and three real defects came back SURVIVED. Running
# everything costs about fifteen seconds a mutation and cannot be wrong in that
# way.

MUTATIONS: list[tuple[str, str, Path, str, str]] = [
    (
        "wrong-exception-class", "a raise site throwing a neighbouring class",
        DICTIONARY,
        "            throw CNAArgumentException(\n"
        "                message: CNADictionary.addingDuplicateMessage)",
        "            throw CNAArgumentOutOfRangeException(\n"
        "                message: CNADictionary.addingDuplicateMessage)",
    ),
    (
        "wrong-base-class", "a projected class on the wrong CLR base",
        EXCEPTIONS,
        "open class CNAKeyNotFoundException: CNASystemException {",
        "open class CNAKeyNotFoundException: CNAArgumentException {",
    ),
    (
        "dropped-message-composition", "Message no longer appending ParamName",
        EXCEPTIONS,
        "        let base = super.Message\n"
        "        guard let name = storedParamName, !name.isEmpty else { return base }",
        "        let base = super.Message\n"
        "        guard let name = storedParamName, name.isEmpty else { return base }",
    ),
    (
        "wrong-newline", "the composed separator taken from the host, not the IL",
        EXCEPTIONS,
        'internal static let environmentNewLine = "\\r\\n"',
        'internal static let environmentNewLine = "\\n"',
    ),
    (
        "inherited-hresult", "a subclass keeping the HResult its base assigned",
        EXCEPTIONS,
        "    public init(paramName: String?) {\n"
        "        super.init(\n"
        "            message: CNAArgumentNullException.argumentNullGenericMessage,\n"
        "            paramName: paramName)\n"
        "        HResult = CNAArgumentNullException.argumentNullHResult\n"
        "    }",
        "    public init(paramName: String?) {\n"
        "        super.init(\n"
        "            message: CNAArgumentNullException.argumentNullGenericMessage,\n"
        "            paramName: paramName)\n"
        "    }",
    ),
    (
        "transposed-constructor", "the two-argument overload's arguments swapped",
        EXCEPTIONS,
        "    public init(paramName: String?, message: String?) {\n"
        "        super.init(message: message, paramName: paramName)\n"
        "        HResult = CNAArgumentNullException.argumentNullHResult",
        "    public init(paramName: String?, message: String?) {\n"
        "        super.init(message: paramName, paramName: message)\n"
        "        HResult = CNAArgumentNullException.argumentNullHResult",
    ),
    (
        "confused-range-resource", "Insert reporting the indexer's message",
        COLLECTIONS,
        "    internal static var listInsertMessage: String {\n"
        '        "Index must be within the bounds of the List."\n'
        "    }",
        "    internal static var listInsertMessage: String {\n"
        '        "Index was out of range. Must be non-negative and less than "\n'
        '        + "the size of the collection."\n'
        "    }",
    ),
    (
        "confused-not-supported-resource",
        "the read-only guard reporting the parameterless default",
        COLLECTIONS,
        "    internal static var readOnlyCollectionMessage: String {\n"
        '        "Collection is read-only."\n'
        "    }",
        "    internal static var readOnlyCollectionMessage: String {\n"
        '        "Specified method is not supported."\n'
        "    }",
    ),
    (
        "swift-class-name-in-a-message",
        "a projected class reporting its Swift name to a user",
        EXCEPTIONS,
        '        "CNAArgumentException": "System.ArgumentException",\n',
        "",
    ),
    (
        "reverted-to-the-runtime-channel",
        "a CLR-shaped failure back on CNAError",
        SERVICES,
        "                throw CNAArgumentNullException(\n"
        "                    paramName: \"provider\",\n"
        "                    message: GameServiceContainer.serviceProviderCannotBeNullMessage)",
        "                throw CNAError.producerInvariant(\"provider\")",
    ),
    # The Foundation 38 derivability and ownership decisions.
    (
        "texture2d-resealed", "Texture2D final again, as it was", TEXTURE2D,
        "    open class Texture2D: Texture {",
        "    public final class Texture2D: Texture {",
    ),
    (
        "disposing-raised-before-release",
        "Disposing raised before the native release", RESOURCE,
        "            try storage.dispose(operation: \"\\(storage.typeName).Dispose\")\n"
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)",
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)\n"
        "            try storage.dispose(operation: \"\\(storage.typeName).Dispose\")",
    ),
    (
        "dispose-not-idempotent", "a second Dispose reaching the dead handle",
        RESOURCE,
        "            guard !storage.isDisposed else { return }\n"
        "            try storage.dispose",
        "            try storage.dispose",
    ),
    (
        "derived-type-name-lost",
        "the shared storage naming the base rather than the derived type",
        RENDER_TARGET,
        "                    typeName: \"RenderTarget2D\",",
        "                    typeName: \"Texture2D\",",
    ),
    (
        "content-lost-subscription-leaked",
        "disposal leaving the native subscription alive", RENDER_TARGET,
        "            unsubscribeFromNativeContentLost()\n"
        "            try super.Dispose(disposing)",
        "            try super.Dispose(disposing)",
    ),
]


def run_tests(swift_test: str) -> int:
    result = subprocess.run(
        [swift_test], cwd=ROOT, text=True, capture_output=True)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swift-test", default="swift-test")
    args = parser.parse_args()

    originals = {path: path.read_text(encoding="utf-8")
                 for path in {EXCEPTIONS, COLLECTIONS, DICTIONARY, SERVICES,
                              RESOURCE, TEXTURE2D, RENDER_TARGET}}

    if run_tests(args.swift_test) != 0:
        print("PROJECTION_MUTATION_BASELINE=RED — the unmutated tree already fails")
        return 1

    survivors: list[str] = []
    for name, description, path, old, new in MUTATIONS:
        text = originals[path]
        if text.count(old) != 1:
            survivors.append(
                f"{name}: the mutation site occurs {text.count(old)} times, not once")
            continue
        try:
            path.write_text(text.replace(old, new), encoding="utf-8")
            code = run_tests(args.swift_test)
        finally:
            path.write_text(text, encoding="utf-8")
        status = "CAUGHT" if code != 0 else "SURVIVED"
        print(f"{status:9} {name:34} {description}")
        if code == 0:
            survivors.append(f"{name}: {description}")

    for path, text in originals.items():
        if path.read_text(encoding="utf-8") != text:
            survivors.append(f"{path} was not restored")

    print(f"PROJECTION_MUTATIONS={len(MUTATIONS)} "
          f"CAUGHT={len(MUTATIONS) - len(survivors)} SURVIVORS={len(survivors)}")
    for survivor in survivors:
        print(f"  SURVIVOR {survivor}")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
