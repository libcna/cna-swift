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
import os
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
GAME = ROOT / "Sources/CNA/Xna/Framework/Game.swift"
CALLBACK_STATE = ROOT / "Sources/CNA/Runtime/CallbackState.swift"
MANAGER = ROOT / "Sources/CNA/Xna/Graphics/GraphicsDeviceManager.swift"
DRAWABLE = ROOT / "Sources/CNA/Xna/Framework/DrawableGameComponent.swift"
STATES = ROOT / "Sources/CNA/Xna/Graphics/GraphicsStates.swift"

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
        "            guard !IsDisposed else { return }\n"
        "            if let storage {\n"
        "                try storage.dispose(operation: \"\\(storage.typeName).Dispose\")\n"
        "            } else {\n"
        "                managedDisposed = true\n"
        "            }\n"
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)",
        "            guard !IsDisposed else { return }\n"
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)\n"
        "            if let storage {\n"
        "                try storage.dispose(operation: \"\\(storage.typeName).Dispose\")\n"
        "            } else {\n"
        "                managedDisposed = true\n"
        "            }",
    ),
    (
        "dispose-not-idempotent", "a second Dispose reaching the dead handle",
        RESOURCE,
        "            guard !IsDisposed else { return }\n"
        "            if let storage {",
        "            if let storage {",
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
    # The Foundation 39 Game surface.
    (
        "event-sender-is-the-parameter",
        "an On... method passing its sender parameter rather than the game",
        GAME,
        "        open func OnActivated(_ sender: Any?, args: CNAEventArgs) throws {\n"
        "            try activatedSource.Raise(self, args: args)",
        "        open func OnActivated(_ sender: Any?, args: CNAEventArgs) throws {\n"
        "            try activatedSource.Raise(sender, args: args)",
    ),
    (
        "target-elapsed-accepts-zero",
        "the strict TargetElapsedTime bound loosened to the sleep-time one",
        GAME,
        "            guard value > .zero else {\n"
        "                throw CNAArgumentOutOfRangeException(\n"
        "                    paramName: \"value\",\n"
        "                    message: Game.targetElapsedCannotBeZeroMessage)",
        "            guard value >= .zero else {\n"
        "                throw CNAArgumentOutOfRangeException(\n"
        "                    paramName: \"value\",\n"
        "                    message: Game.targetElapsedCannotBeZeroMessage)",
    ),
    (
        "inactive-sleep-refuses-zero",
        "the sleep-time bound tightened to the target-elapsed one", GAME,
        "            guard value >= .zero else {\n"
        "                throw CNAArgumentOutOfRangeException(\n"
        "                    paramName: \"value\",\n"
        "                    message: Game.inactiveSleepTimeCannotBeZeroMessage)",
        "            guard value > .zero else {\n"
        "                throw CNAArgumentOutOfRangeException(\n"
        "                    paramName: \"value\",\n"
        "                    message: Game.inactiveSleepTimeCannotBeZeroMessage)",
    ),
    (
        "mirror-moves-on-a-refused-write",
        "the mirror reporting a state the host never took", GAME,
        "                guard let handle = try? validatedHandle(\"Game.IsFixedTimeStep\") else { return }\n"
        "                guard runtime.functions.gameSetIsFixedTimeStep(handle, newValue ? 1 : 0) == 0\n"
        "                else { return }\n"
        "                mirroredIsFixedTimeStep = newValue",
        "                mirroredIsFixedTimeStep = newValue\n"
        "                guard let handle = try? validatedHandle(\"Game.IsFixedTimeStep\") else { return }\n"
        "                _ = runtime.functions.gameSetIsFixedTimeStep(handle, newValue ? 1 : 0)",
    ),
    (
        "teardown-callback-mapped-onto-exiting",
        "CNA's teardown notification mapped onto XNA's Exiting", CALLBACK_STATE,
        "        case .exiting:\n"
        "            // Deliberately NOT `OnExiting`.",
        "        case .exiting:\n"
        "            try game.OnExiting(game, args: CNAEventArgs.Empty)\n"
        "            // Deliberately NOT `OnExiting`.",
    ),
    # The Foundation 40 service producer and DrawableGameComponent.
    (
        "manager-registers-only-one-service",
        "the producer registered under one interface and not both", MANAGER,
        "            try game.Services.AddService(\n"
        "                Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService.self, provider: self)",
        "",
    ),
    (
        "duplicate-manager-accepted",
        "a second manager admitted where XNA refuses one", MANAGER,
        "            if game.Services.GetService(Microsoft.Xna.Framework.IGraphicsDeviceManager.self) != nil {",
        "            if false {",
    ),
    (
        "drawable-reload-guarded-by-the-one-time-flag",
        "the device-reset reload suppressed by Initialize's guard", DRAWABLE,
        "            deviceSubscriptions.append(deviceService.DeviceCreated.Add {\n"
        "                [weak self] _, _ in try self?.LoadContent()\n"
        "            })",
        "            deviceSubscriptions.append(deviceService.DeviceCreated.Add { _, _ in })",
    ),
    (
        "drawable-shares-the-game-message",
        "the two different missing-service messages confused", DRAWABLE,
        "        internal static let missingGraphicsDeviceServiceMessage =\n"
        "            \"Drawable components require a graphics device service in the game \"\n"
        "            + \"service container.\"",
        "        internal static let missingGraphicsDeviceServiceMessage =\n"
        "            Microsoft.Xna.Framework.Game.noGraphicsDeviceServiceMessage",
    ),
    (
        "drawable-visible-raises-without-a-change",
        "an unchanged write raising the change event", DRAWABLE,
        "                guard visible != newValue else { return }\n"
        "                visible = newValue",
        "                visible = newValue",
    ),
    (
        "host-subscriptions-leaked",
        "disposal leaving the four host subscriptions alive", GAME,
        "            releaseHostEventSubscriptions()\n"
        "            runtime.clearCallbackError()",
        "            runtime.clearCallbackError()",
    ),
    (
        "state-default-off-by-one", "a single IL-derived state default changed",
        STATES,
        "        private var maxAnisotropy: Int32 = 4",
        "        private var maxAnisotropy: Int32 = 1",
    ),
    (
        "multisample-antialias-default-inverted",
        "the RasterizerState default XNA turns ON, turned off",
        STATES,
        "        private var multiSampleAntiAlias = true",
        "        private var multiSampleAntiAlias = false",
    ),
    (
        "preset-blend-pair-transposed",
        "a preset's source and destination blend swapped",
        STATES,
        '        public static let Additive = BlendState(\n'
        '            source: .SourceAlpha, destination: .One, name: "BlendState.Additive")',
        '        public static let Additive = BlendState(\n'
        '            source: .One, destination: .SourceAlpha, name: "BlendState.Additive")',
    ),
    (
        "preset-address-mode-on-one-axis-only",
        "the presetting constructor writing only AddressU",
        STATES,
        "            addressU = address\n"
        "            addressV = address\n"
        "            addressW = address",
        "            addressU = address",
    ),
    (
        "bound-message-names-the-dynamic-type",
        "ThrowIfBound reading the dynamic class instead of the declaring one",
        STATES,
        "                of: \"{0}\", with: Self.boundStateTypeName))",
        "                of: \"{0}\", with: Microsoft.Xna.Framework.Graphics\n"
        "                    .GraphicsResource.clrTypeName(of: self)\n"
        "                    .split(separator: \".\").last.map(String.init) ?? \"\"))",
    ),
    (
        "setter-skips-the-bound-guard",
        "one state setter writing without calling ThrowIfBound",
        STATES,
        "        public func SetMultiSampleMask(_ value: Int32) throws {\n"
        "            try throwIfBound(); multiSampleMask = value",
        "        public func SetMultiSampleMask(_ value: Int32) throws {\n"
        "            multiSampleMask = value",
    ),
    (
        "preset-not-born-bound",
        "a static preset left mutable, so a caller can corrupt a shared global",
        STATES,
        "            alphaDestinationBlend = destination\n"
        "            Name = name\n"
        "            isBound = true",
        "            alphaDestinationBlend = destination\n"
        "            Name = name",
    ),
    (
        "fresh-state-born-bound",
        "the parameterless constructor binding, freezing a brand-new state",
        STATES,
        "        internal var isBound = false\n"
        "        internal static let boundStateTypeName = \"SamplerState\"",
        "        internal var isBound = true\n"
        "        internal static let boundStateTypeName = \"SamplerState\"",
    ),
    (
        "default-back-buffer-width-transcribed-wrong",
        "the GraphicsDeviceManager default back-buffer width off by a digit",
        MANAGER,
        "        public static let DefaultBackBufferWidth: Int32 = 800",
        "        public static let DefaultBackBufferWidth: Int32 = 640",
    ),
]


def require_native_library() -> str | None:
    """The runtime suites skip without an explicit native library.

    Sixteen of the mutations below are caught only by tests that start a CNA
    runtime. With `CNA_NATIVE_LIBRARY` unset those tests SKIP rather than fail,
    every one of those mutations comes back SURVIVED, and the gate reports a
    coverage loss as a projection defect. Refusing to run is the honest
    behaviour.
    """
    selected = os.environ.get("CNA_NATIVE_LIBRARY")
    if not selected:
        return "CNA_NATIVE_LIBRARY is not set"
    if not Path(selected).is_file():
        return f"CNA_NATIVE_LIBRARY={selected!r} is not a file"
    return None


def run_tests(swift_test: str) -> int:
    result = subprocess.run(
        [swift_test], cwd=ROOT, text=True, capture_output=True)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swift-test", default="swift-test")
    args = parser.parse_args()

    problem = require_native_library()
    if problem is not None:
        print(f"PROJECTION_MUTATION_PRECONDITION=FAILED — {problem}")
        return 1

    originals = {path: path.read_text(encoding="utf-8")
                 for path in {EXCEPTIONS, COLLECTIONS, DICTIONARY, SERVICES,
                              RESOURCE, TEXTURE2D, RENDER_TARGET, GAME,
                              CALLBACK_STATE, MANAGER, DRAWABLE, STATES}}

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
