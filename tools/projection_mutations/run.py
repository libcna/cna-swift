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
import fcntl
import os
import signal
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
RUNTIME_STATE = ROOT / "Sources/CNA/Runtime/RuntimeState.swift"
BATCH = ROOT / "Sources/CNA/Xna/Graphics/SpriteBatch.swift"
VERTEXDECL = ROOT / "Sources/CNA/Xna/Graphics/VertexDeclaration.swift"
VERTEXCOLOR = ROOT / "Sources/CNA/Xna/Graphics/VertexPositionColor.swift"
VERTEXNORMAL = ROOT / "Sources/CNA/Xna/Graphics/VertexPositionNormalTexture.swift"
DEVICE = ROOT / "Sources/CNA/Xna/Graphics/GraphicsDevice.swift"
STATEBRIDGE = ROOT / "Sources/CNA/Xna/Graphics/GraphicsStateNativeBridge.swift"
SAMPLERS = ROOT / "Sources/CNA/Xna/Graphics/SamplerStateCollection.swift"

# Two mutation harnesses editing the same working tree at once corrupts both.
# `tools/native_abi/mutations.py` mutates NativeManifest.swift,
# NativeFunctions.swift, CNAShim.h and Keyboard.swift; this one mutates twenty
# other files under Sources/ and runs the whole test suite for each. Run them
# together and a `swift test` here can compile the other harness's planted
# defect, reporting a CAUGHT the mutation under test did not earn -- a false
# pass, which is the direction that hides a survivor. That happened once,
# during Foundation 48, and cost a full re-run to be sure of the result.
#
# The lock is advisory and holds between these two scripts only. It is not a
# claim that the tree is otherwise untouched.
TREE_LOCK = ROOT / ".mutation-gate.lock"


def acquire_tree_lock(name: str):
    """Take the exclusive tree lock, or return None if another gate holds it."""
    handle = TREE_LOCK.open("w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    handle.write(f"{os.getpid()} {name}\n")
    handle.flush()
    return handle


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
    # ---- Foundation 49: the validation Foundation 47 dropped -------------
    (
        "viewport-origin-test-loosened",
        "a negative viewport origin accepted",
        DEVICE,
        "            guard value.X >= 0, value.Y >= 0, value.Width > 0, value.Height > 0 else {",
        "            guard value.X >= -1, value.Y >= 0, value.Width > 0, value.Height > 0 else {",
    ),
    (
        "viewport-extent-test-uses-blt",
        "a zero-width viewport accepted, as `blt` rather than `ble` would",
        DEVICE,
        "            guard value.X >= 0, value.Y >= 0, value.Width > 0, value.Height > 0 else {",
        "            guard value.X >= 0, value.Y >= 0, value.Width >= 0, value.Height > 0 else {",
    ),
    (
        "viewport-bounds-checked-additively",
        "the viewport's extent compared without its origin",
        DEVICE,
        "            guard value.X &+ value.Width <= bounds.width,\n"
        "                  value.Y &+ value.Height <= bounds.height else {",
        "            guard value.Width <= bounds.width,\n"
        "                  value.Height <= bounds.height else {",
    ),
    (
        "viewport-depth-comparison-ordered",
        "MaxDepth >= MinDepth compared as an ordered branch, so NaN passes",
        DEVICE,
        "            if !(Double(value.MaxDepth) >= Double(value.MinDepth)) {",
        "            if Double(value.MaxDepth) < Double(value.MinDepth) {",
    ),
    # WITHDRAWN: "viewport-depth-range-rejects-nan-early". Rewriting the depth
    # RANGE test as a requirement rejects NaN one branch early — but it throws
    # the same exception with the same message, so which branch rejected it is
    # not observable from outside. The restructuring that this mutation was
    # written to protect is still worth having: it is what makes
    # "viewport-depth-comparison-ordered" catchable at all, and that one is a
    # real behavioural difference. This one was tried, survived, and is
    # recorded here rather than deleted quietly.
    (
        "viewport-bounds-always-the-backbuffer",
        "the bounds read from the presentation parameters even with a target bound",
        DEVICE,
        "            if let target = runtime.currentRenderTarget, !target.IsDisposed {\n"
        "                return (target.Width, target.Height)\n"
        "            }",
        "            if let target = runtime.currentRenderTarget, target.IsDisposed {\n"
        "                return (target.Width, target.Height)\n"
        "            }",
    ),
    (
        "scissor-negative-test-uses-ble",
        "an empty scissor rectangle rejected, as `ble` rather than `blt` would",
        DEVICE,
        "            guard value.X >= 0, value.Width >= 0,\n"
        "                  value.Y >= 0, value.Height >= 0 else {",
        "            guard value.X >= 0, value.Width > 0,\n"
        "                  value.Y >= 0, value.Height >= 0 else {",
    ),
    # WITHDRAWN: "scissor-edge-test-drops-the-origin". Removing XNA's
    # `X <= targetW` / `Y <= targetH` comparisons changes nothing observable —
    # with X and Width already known non-negative, `right <= targetW` implies
    # `X <= targetW`, and the overflowing width that breaks the implication is
    # rejected by the following pair regardless. It survived a full run, which
    # is what a gate that cannot fail looks like. The comparisons stay in the
    # projection because XNA has them; the mutation does not stay here.
    (
        "scissor-overflow-pair-dropped",
        "the pair of tests only an int32 overflow reaches, removed as redundant",
        DEVICE,
        "            guard right &- value.X <= bounds.width,\n"
        "                  bottom &- value.Y <= bounds.height else {",
        "            guard right &- value.X <= Int32.max,\n"
        "                  bottom &- value.Y <= Int32.max else {",
    ),
    (
        "invalid-bounds-messages-exchanged",
        "the viewport and scissor messages swapped",
        STATEBRIDGE,
        'internal let scissorInvalidMessage =\n'
        '    "The scissor rectangle is invalid. The scissor rectangle cannot be larger "',
        'internal let scissorInvalidMessage =\n'
        '    "The viewport is invalid. The scissor rectangle cannot be larger "',
    ),
    # ---- Foundation 48: Clear, and the DefaultClearOptions rule ----------
    (
        "default-clear-options-ignores-the-render-target",
        "get_DefaultClearOptions always reading the presentation parameters",
        DEVICE,
        "                if let target = runtime.currentRenderTarget, !target.IsDisposed {",
        "                if let target = runtime.currentRenderTarget, target.IsDisposed {",
    ),
    (
        "default-clear-options-drops-stencil",
        "Depth24Stencil8 clearing depth but not stencil",
        DEVICE,
        "                if format == .Depth24Stencil8 {\n"
        "                    return [.Target, .DepthBuffer, .Stencil]\n"
        "                }",
        "                if format == .Depth24Stencil8 {\n"
        "                    return [.Target, .DepthBuffer]\n"
        "                }",
    ),
    (
        "set-render-target-forgets-to-record",
        "SetRenderTarget not recording the target DefaultClearOptions reads",
        DEVICE,
        "            runtime.currentRenderTarget = renderTarget",
        "            _ = renderTarget",
    ),
    (
        "null-depth-diagnosis-fires-on-every-failure",
        "every failed clear blamed on an absent depth or stencil buffer",
        DEVICE,
        "            guard try defaultClearOptions.intersection(requested) == requested else {",
        "            guard try defaultClearOptions.intersection(requested) != requested else {",
    ),
    (
        "null-depth-diagnosis-never-fires",
        "a clear of buffers the device lacks reported as a bare native failure",
        DEVICE,
        "                throw CNAInvalidOperationException(message: cannotClearNullDepthMessage)",
        "                _ = cannotClearNullDepthMessage",
    ),
    (
        "clear-options-drops-undeclared-bits",
        "an option XNA does not declare silently narrowed away",
        STATEBRIDGE,
        "        native |= UInt32(bitPattern: value.rawValue & ~declared)",
        "        native |= 0",
    ),
    (
        "clear-options-swaps-depth-and-stencil",
        "DepthBuffer and Stencil mapped to each other's canonical bits",
        STATEBRIDGE,
        "        if value.contains(.DepthBuffer) { native |= 2 }\n"
        "        if value.contains(.Stencil) { native |= 4 }",
        "        if value.contains(.DepthBuffer) { native |= 4 }\n"
        "        if value.contains(.Stencil) { native |= 2 }",
    ),
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
        "        internal weak var attachedDevice: "
        "Microsoft.Xna.Framework.Graphics.GraphicsDevice?\n"
        "        internal static let boundStateTypeName = \"SamplerState\"",
        "        internal var isBound = true\n"
        "        internal weak var attachedDevice: "
        "Microsoft.Xna.Framework.Graphics.GraphicsDevice?\n"
        "        internal static let boundStateTypeName = \"SamplerState\"",
    ),
    (
        "disposal-back-on-the-runtime-channel",
        "a use-after-dispose reported as a CNA runtime failure again",
        RESOURCE,
        "            guard !storage.isDisposed else {\n"
        "                throw CNAObjectDisposedException(objectName: storage.typeName)\n"
        "            }",
        "            guard !storage.isDisposed else {\n"
        "                throw CNAError.disposedObject(storage.typeName)\n"
        "            }",
    ),
    (
        "sprite-batch-guard-bypasses-the-class",
        "one resource reaching its handle past its own disposal guard",
        BATCH,
        '            let handle = try validatedHandle("SpriteBatch.Begin")',
        '            let handle = try nativeStorage.validatedHandle("SpriteBatch.Begin")',
    ),
    (
        "object-disposed-on-the-wrong-base",
        "ObjectDisposedException derived from SystemException, not "
        "InvalidOperationException",
        EXCEPTIONS,
        "open class CNAObjectDisposedException: CNAInvalidOperationException {",
        "open class CNAObjectDisposedException: CNASystemException {",
    ),
    (
        "object-name-not-collapsed-to-empty",
        "ObjectName answering nil where the CLR getter answers String.Empty",
        EXCEPTIONS,
        '    public var ObjectName: String { storedObjectName ?? "" }',
        '    public var ObjectName: String { storedObjectName ?? " " }',
    ),
    (
        "object-disposed-constructor-transposed",
        "the single-argument constructor treated as a message, not an object name",
        EXCEPTIONS,
        "    public init(objectName: String?) {\n"
        "        storedObjectName = objectName\n"
        "        super.init(\n"
        "            message: CNAObjectDisposedException.objectDisposedGenericMessage)",
        "    public init(objectName: String?) {\n"
        "        storedObjectName = nil\n"
        "        super.init(message: objectName)",
    ),
    (
        "stride-summed-instead-of-maximised",
        "the vertex stride as a sum of element sizes rather than the widest end",
        VERTEXDECL,
        "                let end = element.Offset + typeSize(element.VertexElementFormat)\n"
        "                if maximum < end { maximum = end }",
        "                maximum += typeSize(element.VertexElementFormat)",
    ),
    (
        "one-type-size-wrong",
        "a single VertexElementFormat size off by a half",
        VERTEXDECL,
        "            case .HalfVector4: return 8",
        "            case .HalfVector4: return 4",
    ),
    (
        "duplicate-check-ignores-the-usage-index",
        "two elements treated as duplicates on usage alone",
        VERTEXDECL,
        "                for earlier in elements[..<index] where\n"
        "                    earlier.VertexElementUsage == element.VertexElementUsage\n"
        "                    && earlier.UsageIndex == element.UsageIndex {",
        "                for earlier in elements[..<index] where\n"
        "                    earlier.VertexElementUsage == element.VertexElementUsage {",
    ),
    (
        "overlap-check-dropped",
        "two elements allowed to claim the same byte of the vertex",
        VERTEXDECL,
        "                    guard owner[byte] < 0 else {",
        "                    guard true else {",
    ),
    (
        "alignment-checked-before-the-stride-fit",
        "the two per-element checks in the wrong order, so a doubly-invalid "
        "element reports the wrong message",
        VERTEXDECL,
        "                guard element.Offset >= 0,\n"
        "                      element.Offset + size <= vertexStride else {",
        "                guard element.Offset & 3 == 0, element.Offset >= 0,\n"
        "                      element.Offset + size <= vertexStride else {",
    ),
    (
        "empty-element-array-refused",
        "an empty element array rejected where XNA accepts it in silence",
        VERTEXDECL,
        "            guard !elements.isEmpty else {\n"
        "                storedElements = nil",
        "            guard !elements.isEmpty, false else {\n"
        "                storedElements = nil",
    ),
    (
        "vertex-element-quadruple-transposed",
        "a static declaration's element offset and format exchanged",
        VERTEXCOLOR,
        "                VertexElement(12, .Color, .Color, 0),",
        "                VertexElement(16, .Color, .Color, 0),",
    ),
    (
        "vertex-declaration-name-dropped",
        "a static declaration left unnamed where the class constructor names it",
        VERTEXCOLOR,
        '            .named("VertexPositionColor.VertexDeclaration")',
        "",
    ),
    (
        "vertex-hash-drops-a-word",
        "one word of a vertex layout left out of the folded hash",
        VERTEXNORMAL,
        "            let hash = Position.X.bitPattern\n"
        "                ^ Position.Y.bitPattern\n"
        "                ^ Position.Z.bitPattern\n"
        "                ^ Normal.X.bitPattern",
        "            let hash = Position.X.bitPattern\n"
        "                ^ Position.Y.bitPattern\n"
        "                ^ Position.Z.bitPattern",
    ),
    (
        "vertex-equality-ignores-a-field",
        "a vertex field left out of op_Equality",
        VERTEXNORMAL,
        "            lhs.Position == rhs.Position\n"
        "                && lhs.Normal == rhs.Normal\n"
        "                && lhs.TextureCoordinate == rhs.TextureCoordinate",
        "            lhs.Position == rhs.Position\n"
        "                && lhs.Normal == rhs.Normal",
    ),
    (
        "blend-function-passed-through-raw",
        "the one enum CNA numbers differently, cast instead of mapped",
        STATEBRIDGE,
        "            case .Min: return 4\n"
        "            case .Max: return 3",
        "            case .Min: return 3\n"
        "            case .Max: return 4",
    ),
    (
        "blend-descriptor-channels-transposed",
        "the colour and alpha channels written to each other's POD fields",
        STATEBRIDGE,
        "        native.alpha_destination_blend = Codes.blend(AlphaDestinationBlend)\n"
        "        native.alpha_source_blend = Codes.blend(AlphaSourceBlend)",
        "        native.alpha_destination_blend = Codes.blend(ColorDestinationBlend)\n"
        "        native.alpha_source_blend = Codes.blend(ColorSourceBlend)",
    ),
    (
        "device-setter-skips-the-attachment",
        "a state cached without being bound, so it stays writable afterwards",
        DEVICE,
        "            try value.attach(to: self)\n"
        "            var native = value.nativeDescriptor()\n"
        "            try runtime.functions.check(\n"
        "                runtime.functions.graphicsDeviceSetDepthStencilState(handle, &native),",
        "            var native = value.nativeDescriptor()\n"
        "            try runtime.functions.check(\n"
        "                runtime.functions.graphicsDeviceSetDepthStencilState(handle, &native),",
    ),
    (
        "device-setter-forgets-the-copied-value",
        "set_BlendState caching the state but not the value it copies out",
        DEVICE,
        "            runtime.cachedBlendFactor = value.BlendFactor",
        "",
    ),
    (
        "sampler-slot-identity-lost",
        "the collection storing a copy rather than the caller's own instance",
        SAMPLERS,
        "            slots[resolved] = value",
        "            slots[resolved] = SamplerState()",
    ),
    (
        "sampler-collection-rebuilt-per-access",
        "a new collection per device read, losing every slot already written",
        RUNTIME_STATE,
        "        if let existing = pixelSamplerStates {\n"
        "            existing.rebind(to: device)\n"
        "            return existing\n"
        "        }",
        "",
    ),
    (
        "copied-value-writer-skips-the-device",
        "a direct write cached without reaching the device it must push to",
        DEVICE,
        "            let handle = try validatedHandle(\"GraphicsDevice.MultiSampleMask\")\n"
        "            try runtime.functions.check(\n"
        "                runtime.functions.graphicsDeviceSetMultiSampleMask(handle, value),\n"
        "                operation: \"cna_graphics_device_set_multi_sample_mask\")\n"
        "            runtime.cachedMultiSampleMask = value",
        "            runtime.cachedMultiSampleMask = value",
    ),
    (
        "viewport-writer-does-not-reach-the-device",
        "SetViewport accepted and discarded rather than pushed",
        DEVICE,
        "            try runtime.functions.check(\n"
        "                runtime.functions.graphicsDeviceSetViewport(handle, native),\n"
        "                operation: \"cna_graphics_device_set_viewport\")",
        "            _ = native",
    ),
    (
        "scissor-rectangle-fields-transposed",
        "the scissor rectangle's origin and extent exchanged on the way out",
        DEVICE,
        "            native.x = value.X\n"
        "            native.y = value.Y\n"
        "            native.width = value.Width\n"
        "            native.height = value.Height\n"
        "            try runtime.functions.check(\n"
        "                runtime.functions.graphicsDeviceSetScissorRectangle(handle, native),",
        "            native.x = value.Width\n"
        "            native.y = value.Height\n"
        "            native.width = value.X\n"
        "            native.height = value.Y\n"
        "            try runtime.functions.check(\n"
        "                runtime.functions.graphicsDeviceSetScissorRectangle(handle, native),",
    ),
    (
        "device-status-values-shifted",
        "the three GraphicsDeviceStatus values mapped one place along",
        DEVICE,
        "                case 0: return .Normal\n"
        "                case 1: return .Lost\n"
        "                case 2: return .NotReset",
        "                case 0: return .Lost\n"
        "                case 1: return .NotReset\n"
        "                case 2: return .Normal",
    ),
    (
        "default-back-buffer-width-transcribed-wrong",
        "the GraphicsDeviceManager default back-buffer width off by a digit",
        MANAGER,
        "        public static let DefaultBackBufferWidth: Int32 = 800",
        "        public static let DefaultBackBufferWidth: Int32 = 640",
    ),
]


def restore_on_termination() -> None:
    """Turn SIGTERM and SIGHUP into an exception, so `finally` still runs.

    Every mutation is undone in a `finally`, which a normal exit or a Ctrl-C
    honours -- but a `timeout`, a killed background job or a closed terminal
    sends SIGTERM, whose default handler terminates the process outright and
    leaves the planted defect in the working tree. That has happened twice, and
    both times the next run reported the stranded mutation as an unrelated
    failure somewhere else entirely.

    Raising `KeyboardInterrupt` from the handler puts SIGTERM on the same
    footing as Ctrl-C: the `finally` unwinds, the tree is restored, and the
    caller still sees a nonzero exit. SIGKILL cannot be caught, which is why
    the site-staleness precondition above exists as the backstop.
    """
    def handler(signum: int, _frame: object) -> None:
        raise KeyboardInterrupt(f"terminated by signal {signum}")
    for received in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(received, handler)


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
    tree_lock = acquire_tree_lock("projection_mutations")
    if tree_lock is None:
        print("MUTATION_GATE=BUSY — another mutation harness holds "
              f"{TREE_LOCK.name}; these two gates cannot share a working tree")
        return 1


    restore_on_termination()

    problem = require_native_library()
    if problem is not None:
        print(f"PROJECTION_MUTATION_PRECONDITION=FAILED — {problem}")
        return 1

    originals = {path: path.read_text(encoding="utf-8")
                 for path in {EXCEPTIONS, COLLECTIONS, DICTIONARY, SERVICES,
                              RESOURCE, TEXTURE2D, RENDER_TARGET, GAME,
                              CALLBACK_STATE, MANAGER, DRAWABLE, STATES, BATCH,
                              VERTEXDECL, VERTEXCOLOR, VERTEXNORMAL,
                              DEVICE, STATEBRIDGE, SAMPLERS,
                              RUNTIME_STATE}}

    # Every mutation site is checked BEFORE the baseline runs. A site that has
    # drifted is reported as a stale gate rather than as a survivor forty
    # minutes later, and a run that would have been wasted is not started.
    # Three sites had drifted at least once when the code they aimed at was
    # legitimately edited, and each cost a full run to discover.
    stale = [
        f"{name}: the mutation site occurs {originals[path].count(old)} times, not once"
        for name, _description, path, old, _new in MUTATIONS
        if originals[path].count(old) != 1
    ]
    if stale:
        print(f"PROJECTION_MUTATION_SITES=STALE COUNT={len(stale)}")
        for item in stale:
            print(f"  STALE {item}")
        return 1

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
