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
DRAWABLE_COMPONENT = ROOT / "Sources/CNA/Xna/Framework/DrawableGameComponent.swift"
TEXTUREDATA = ROOT / "Sources/CNA/Xna/Graphics/TextureDataTransfer.swift"
VERTEXBUFFER = ROOT / "Sources/CNA/Xna/Graphics/VertexBuffer.swift"
INDEXBUFFER = ROOT / "Sources/CNA/Xna/Graphics/IndexBuffer.swift"
BUFFERSUPPORT = ROOT / "Sources/CNA/Xna/Graphics/BufferSupport.swift"
BUFFERBINDING = ROOT / "Sources/CNA/Xna/Graphics/VertexBufferBinding.swift"
DYNAMICVERTEX = ROOT / "Sources/CNA/Xna/Graphics/DynamicVertexBuffer.swift"
DYNAMICINDEX = ROOT / "Sources/CNA/Xna/Graphics/DynamicIndexBuffer.swift"
PROFILECAPS = ROOT / "Sources/CNA/Xna/Graphics/ProfileCapabilities.swift"
TEXTURECUBE = ROOT / "Sources/CNA/Xna/Graphics/TextureCube.swift"
TEXTURE3D = ROOT / "Sources/CNA/Xna/Graphics/Texture3D.swift"
RTCUBE = ROOT / "Sources/CNA/Xna/Graphics/RenderTargetCube.swift"
RTBINDING = ROOT / "Sources/CNA/Xna/Graphics/RenderTargetBinding.swift"
RTSUPPORT = ROOT / "Sources/CNA/Xna/Graphics/RenderTargetSupport.swift"
RUNTIME = ROOT / "Sources/CNA/Runtime/RuntimeState.swift"
TEXTURECOLLECTION = ROOT / "Sources/CNA/Xna/Graphics/TextureCollection.swift"
EFFECT = ROOT / "Sources/CNA/Xna/Graphics/Effect.swift"
EFFECTCOLLECTIONS = ROOT / "Sources/CNA/Xna/Graphics/EffectCollections.swift"
EFFECTSUPPORT = ROOT / "Sources/CNA/Xna/Graphics/EffectSupport.swift"
DRAW = ROOT / "Sources/CNA/Xna/Graphics/GraphicsDeviceDraw.swift"
FONT = ROOT / "Sources/CNA/Xna/Graphics/SpriteFont.swift"
BUILDER = ROOT / "Sources/CNA/CNAStringBuilder.swift"
LIGHT = ROOT / "Sources/CNA/Xna/Graphics/DirectionalLight.swift"
STOCKSUPPORT = ROOT / "Sources/CNA/Xna/Graphics/StockEffectSupport.swift"
BASICEFFECT = ROOT / "Sources/CNA/Xna/Graphics/BasicEffect.swift"
ALPHATEST = ROOT / "Sources/CNA/Xna/Graphics/AlphaTestEffect.swift"
DUALTEXTURE = ROOT / "Sources/CNA/Xna/Graphics/DualTextureEffect.swift"
ENVMAP = ROOT / "Sources/CNA/Xna/Graphics/EnvironmentMapEffect.swift"
SKINNED = ROOT / "Sources/CNA/Xna/Graphics/SkinnedEffect.swift"

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
    # ---- Foundation 63: vertex and index buffer binding ------------------
    (
        "binding-cache-not-updated",
        "the bound bindings not recorded, so GetVertexBuffers answers nothing",
        DEVICE,
        "            runtime.cachedVertexBufferBindings = bindings",
        "            runtime.cachedVertexBufferBindings = []",
    ),
    (
        "binding-identity-lost",
        "GetVertexBuffers rebuilding its answer instead of returning what was bound",
        DEVICE,
        "            runtime.cachedVertexBufferBindings\n        }\n\n        /// `GraphicsDevice.Indices`.",
        "            []\n        }\n\n        /// `GraphicsDevice.Indices`.",
    ),
    (
        "device-identity-compared-by-facade",
        "the InvalidDevice test comparing facades, which differ between callbacks",
        DEVICE,
        "                guard binding.VertexBuffer.nativeStorage.runtime === runtime else {",
        "                guard binding.VertexBuffer.GraphicsDevice === self else {",
    ),
    (
        "vertex-stream-limit-not-checked",
        "more simultaneous streams accepted than the profile allows",
        DEVICE,
        "            guard bindings.count <= Int(capabilities.maxVertexStreams) else {",
        "            guard bindings.count <= Int(capabilities.maxVertexStreams) * 4 else {",
    ),
    (
        "indices-cache-not-updated",
        "the bound index buffer not recorded, so Indices answers nil",
        DEVICE,
        "            runtime.cachedIndexBuffer = value",
        "            runtime.cachedIndexBuffer = nil",
    ),
    (
        "indices-setter-skips-the-disposal-check",
        "a disposed index buffer reaching the device",
        DEVICE,
        '            let bufferHandle = try value?.validatedHandle("GraphicsDevice.Indices") ?? 0',
        '            let bufferHandle = value?.nativeStorage.handle ?? 0',
    ),
    # `vertex-offset-not-carried` -- dropping the binding's vertex offset on the
    # way to CNA -- was planted here and SURVIVED, and it is withdrawn rather
    # than kept as a mutation nothing can catch. Nothing in the current public
    # surface observes the offset the DEVICE received: `GetVertexBuffers()`
    # reads the managed cache, as XNA's does, and the only thing that would
    # notice a dropped offset is a draw. `cna_graphics_device_copy_vertex_buffers`
    # would answer, but binding a route for a test alone is what
    # docs/native-abi.md forbids. The claim becomes falsifiable when the draw
    # family lands, and it is recorded as not-yet-evidence until then.

    # ---- Foundation 62: the profile and its capability table -------------
    (
        "profile-limit-read-from-the-wrong-profile",
        "the capability table answering HiDef's limits for a Reach device",
        PROFILECAPS,
        "            profile == .Reach ? reach : hidef",
        "            profile == .Reach ? hidef : reach",
    ),
    (
        "max-texture-size-off-by-a-power",
        "a single extracted limit changed, which the pinned table must refuse",
        PROFILECAPS,
        "            maxTextureSize: 2048,",
        "            maxTextureSize: 4096,",
    ),
    (
        "thirty-two-bit-indices-allowed-on-reach",
        "the IndexElementSize32 refusal dropped, so Reach accepts what XNA refuses",
        PROFILECAPS,
        "            if elementSizeInBytes == 4, !indexElementSize32 {",
        "            if false, !indexElementSize32 {",
    ),
    (
        "aspect-ratio-divides-the-wrong-way",
        "the ceiling division written as a floor, so a texture at the limit is refused",
        PROFILECAPS,
        "            guard (longer + shorter - 1) / shorter <= maxTextureAspectRatio else {\n"
        "                try throwNotSupported(\n"
        "                    ProfileCapabilities.profileAspectRatio,\n"
        "                    \"Texture2D\", \"\\(maxTextureAspectRatio)\")",
        "            guard (longer + shorter) / shorter <= maxTextureAspectRatio else {\n"
        "                try throwNotSupported(\n"
        "                    ProfileCapabilities.profileAspectRatio,\n"
        "                    \"Texture2D\", \"\\(maxTextureAspectRatio)\")",
    ),
    (
        "profile-message-omits-the-profile",
        "ThrowNotSupportedException formatting the limit without naming the profile",
        PROFILECAPS,
        '                of: "{0}", with: "\\(profile)")',
        '                of: "{0}", with: "")',
    ),
    (
        "texture-size-limit-not-checked",
        "a texture larger than the profile allows accepted",
        PROFILECAPS,
        "            guard width <= maxTextureSize, height <= maxTextureSize else {",
        "            guard width <= maxTextureSize * 4, height <= maxTextureSize * 4 else {",
    ),

    # ---- Foundation 61: the dynamic buffers ------------------------------
    (
        "static-upload-takes-the-option-route",
        "the option-taking upload used for SetDataOptions.None, which a static buffer refuses",
        VERTEXBUFFER,
        "                if options == .None {",
        "                if false {",
    ),
    (
        "index-option-rides-the-windowed-route",
        "a streaming option forwarded to the windowed index upload, which CNA refuses",
        INDEXBUFFER,
        "            let forwarded = (options != .None && wholeBuffer)",
        "            let forwarded = (options != .None || wholeBuffer)",
    ),
    (
        "dynamic-vertex-buffer-created-static",
        "DynamicVertexBuffer created with the static flag, so its option overloads are refused",
        DYNAMICVERTEX,
        "                vertexCount: vertexCount, usage: usage, dynamic: true,\n"
        '                typeName: "DynamicVertexBuffer")\n'
        "            try subscribeToNativeContentLost()\n"
        "        }\n"
        "\n"
        "        /// `DynamicVertexBuffer(GraphicsDevice, Type, Int32, BufferUsage)`.",
        "                vertexCount: vertexCount, usage: usage, dynamic: false,\n"
        '                typeName: "DynamicVertexBuffer")\n'
        "            try subscribeToNativeContentLost()\n"
        "        }\n"
        "\n"
        "        /// `DynamicVertexBuffer(GraphicsDevice, Type, Int32, BufferUsage)`.",
    ),
    (
        "content-lost-subscription-not-released",
        "disposal leaving the native ContentLost registration alive",
        DYNAMICVERTEX,
        "            guard !IsDisposed else { return }\n"
        "            unsubscribeFromNativeContentLost()\n"
        "            try super.Dispose(disposing)",
        "            guard !IsDisposed else { return }\n"
        "            try super.Dispose(disposing)",
    ),
    (
        "index-content-lost-never-subscribed",
        "a dynamic index buffer that never registers for ContentLost",
        DYNAMICINDEX,
        "                indexCount: indexCount, usage: usage, dynamic: true,\n"
        '                typeName: "DynamicIndexBuffer")\n'
        "            try subscribeToNativeContentLost()\n"
        "        }\n"
        "\n"
        "        /// `DynamicIndexBuffer(GraphicsDevice, Type, Int32, BufferUsage)`.",
        "                indexCount: indexCount, usage: usage, dynamic: true,\n"
        '                typeName: "DynamicIndexBuffer")\n'
        "        }\n"
        "\n"
        "        /// `DynamicIndexBuffer(GraphicsDevice, Type, Int32, BufferUsage)`.",
    ),
    (
        "content-lost-flag-reports-true",
        "IsContentLost answering true on a host whose renderer cannot lose a device",
        DYNAMICVERTEX,
        "        public var IsContentLost: Bool { contentLost }",
        "        public var IsContentLost: Bool { true }",
    ),

    # ---- Foundation 60: the vertex and index buffers ---------------------
    (
        "copy-parameters-name-the-callers-parameter",
        "ValidateCopyParameters naming startIndex where the helper names dataIndex",
        BUFFERSUPPORT,
        '                paramName: "dataIndex", message: BufferResources.mustBeValidIndex)',
        '                paramName: "startIndex", message: BufferResources.mustBeValidIndex)',
    ),
    (
        "copy-parameters-blame-the-count-not-the-index",
        "the window test moved ahead of the index test, so an index past the end is blamed on elementCount",
        BUFFERSUPPORT,
        "        if dataIndex < 0 || Int(dataIndex) > dataLength {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        '                paramName: "dataIndex", message: BufferResources.mustBeValidIndex)\n'
        "        }\n"
        "        if Int(elementCount) + Int(dataIndex) > dataLength {",
        "        if Int(elementCount) + Int(dataIndex) > dataLength {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        '                paramName: "elementCount", message: BufferResources.mustBeValidIndex)\n'
        "        }\n"
        "        if dataIndex < 0 || Int(dataIndex) > dataLength {",
    ),
    (
        "empty-array-not-reported-as-null",
        "a zero-length array raising ArgumentException where XNA's ldlen branch raises ArgumentNullException",
        VERTEXBUFFER,
        "            guard arrayCount > 0 else {\n"
        "                throw CNAArgumentNullException(",
        "            guard arrayCount > 0 else {\n"
        "                throw CNAArgumentException(",
    ),
    (
        "write-only-buffer-allows-getdata",
        "the WriteOnly guard dropped, so GetData reaches a buffer XNA refuses",
        VERTEXBUFFER,
        "            if !isSetting, BufferUsage.contains(.WriteOnly) {",
        "            if false, BufferUsage.contains(.WriteOnly) {",
    ),
    (
        "vertex-stride-too-small-accepted",
        "a vertexStride below sizeof(T) accepted",
        VERTEXBUFFER,
        "                guard slack >= 0 else {",
        "                guard slack >= -64 else {",
    ),
    (
        "buffer-size-comparison-off-by-one",
        "a transfer that exactly fills the buffer refused",
        VERTEXBUFFER,
        "            guard bytes + Int(offsetInBytes) <= sizeInBytes else {",
        "            guard bytes + Int(offsetInBytes) < sizeInBytes else {",
    ),
    (
        "vertex-array-window-offset-ignored",
        "startIndex dropped, so the transfer always reads from the array's front",
        VERTEXBUFFER,
        "                byteOffset: Int(startIndex) * elementSize,",
        "                byteOffset: 0,",
    ),
    (
        "vertex-buffer-offset-ignored",
        "offsetInBytes dropped, so a windowed write lands at the buffer's front",
        VERTEXBUFFER,
        "                offsetInBytes: Int(offsetInBytes),",
        "                offsetInBytes: 0,",
    ),
    (
        "index-element-width-transposed",
        "SixteenBits measured as four bytes and ThirtyTwoBits as two",
        INDEXBUFFER,
        "            size == .SixteenBits ? 2 : 4",
        "            size == .SixteenBits ? 4 : 2",
    ),
    (
        "index-type-overload-maps-the-wrong-width",
        "typeof(short) mapped to a 32-bit index buffer",
        INDEXBUFFER,
        "            case ObjectIdentifier(Int16.self), ObjectIdentifier(UInt16.self):\n"
        "                return 2",
        "            case ObjectIdentifier(Int16.self), ObjectIdentifier(UInt16.self):\n"
        "                return 4",
    ),
    (
        "index-window-offset-ignored",
        "a windowed index write landing at the buffer's front",
        INDEXBUFFER,
        "                            plan.handle, UInt64(plan.offsetInBytes), pointer,",
        "                            plan.handle, 0, pointer,",
    ),
    (
        "binding-offset-compared-signed",
        "the vertex-offset bound compared signed, where the IL's bge.un is unsigned",
        BUFFERBINDING,
        "                  UInt32(bitPattern: vertexOffset)\n"
        "                    < UInt32(bitPattern: vertexBuffer.VertexCount) else {",
        "                  vertexOffset <= vertexBuffer.VertexCount else {",
    ),
    (
        "binding-blames-the-frequency-first",
        "the instance frequency checked before the offset, so the wrong one is blamed",
        BUFFERBINDING,
        "            guard vertexOffset >= 0,\n"
        "                  UInt32(bitPattern: vertexOffset)\n"
        "                    < UInt32(bitPattern: vertexBuffer.VertexCount) else {\n"
        '                throw CNAArgumentOutOfRangeException(paramName: "vertexOffset")\n'
        "            }\n"
        "            guard instanceFrequency >= 0 else {\n"
        '                throw CNAArgumentOutOfRangeException(paramName: "instanceFrequency")\n'
        "            }",
        "            guard instanceFrequency >= 0 else {\n"
        '                throw CNAArgumentOutOfRangeException(paramName: "instanceFrequency")\n'
        "            }\n"
        "            guard vertexOffset >= 0,\n"
        "                  UInt32(bitPattern: vertexOffset)\n"
        "                    < UInt32(bitPattern: vertexBuffer.VertexCount) else {\n"
        '                throw CNAArgumentOutOfRangeException(paramName: "vertexOffset")\n'
        "            }",
    ),
    (
        "from-type-size-test-reads-the-wrong-size",
        "a registered vertex type's measured size disagreeing with its declared stride, which FromType must refuse",
        VERTEXDECL,
        "                    size: MemoryLayout<VertexPositionColor>.size),",
        "                    size: MemoryLayout<VertexPositionColor>.size + 4),",
    ),

    # ---- Foundation 59: the image members and the disposal chain ---------
    (
        "disposing-flag-ignored-on-the-finalizer-path",
        "Disposing raised from Dispose(false), which XNA raises to nobody",
        RESOURCE,
        "            guard disposing else { return }\n"
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)",
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)",
    ),
    (
        "alpha-zero-texels-not-rewritten",
        "SaveAsPng encodes an alpha-0 texel's colour, where XNA writes Transparent",
        TEXTURE2D,
        "            for index in colors.indices where colors[index].A == 0 {\n"
        "                colors[index] = Microsoft.Xna.Framework.Color.Transparent\n"
        "            }",
        "            for index in colors.indices where colors[index].A == 255 {\n"
        "                colors[index] = colors[index]\n"
        "            }",
    ),
    (
        "encode-dimensions-transposed",
        "the encoded width and height swapped",
        TEXTURE2D,
        "                runtime.functions.textureGetEncodedByteCount(\n"
        "                    source, format, UInt32(bitPattern: width),\n"
        "                    UInt32(bitPattern: height), &byteCount),",
        "                runtime.functions.textureGetEncodedByteCount(\n"
        "                    source, format, UInt32(bitPattern: height),\n"
        "                    UInt32(bitPattern: width), &byteCount),",
    ),
    (
        "jpeg-saved-through-the-png-format",
        "SaveAsJpeg passing the PNG image-format constant",
        TEXTURE2D,
        "            try saveAsImage(stream, format: Texture2D.nativeImageFormatJpeg,",
        "            try saveAsImage(stream, format: Texture2D.nativeImageFormatPng,",
    ),
    (
        "fromstream-zoom-ignored",
        "the zoom flag dropped, so Scale|Crop decodes as Scale",
        TEXTURE2D,
        "            decode.zoom = zoom ? 1 : 0",
        "            decode.zoom = 0",
    ),
    (
        "fromstream-decode-dimensions-transposed",
        "the requested width and height swapped on the way to the decoder",
        TEXTURE2D,
        "            decode.width = UInt32(bitPattern: width)\n"
        "            decode.height = UInt32(bitPattern: height)",
        "            decode.width = UInt32(bitPattern: height)\n"
        "            decode.height = UInt32(bitPattern: width)",
    ),
    (
        "setdata-disposal-check-on-the-runtime-channel",
        "a disposed texture reported as CNAError instead of ObjectDisposedException",
        TEXTURE2D,
        "            let handle = try validatedHandle(\"Texture2D.SetData\")",
        "            let handle = try nativeStorage.validatedHandle(\"Texture2D.SetData\")",
    ),
    (
        "getdata-disposal-check-after-the-arguments",
        "the disposal check moved behind the three validations",
        TEXTURE2D,
        "            let handle = try validatedHandle(\"Texture2D.GetData\")\n"
        "            let plan = try transferPlan(\n"
        "                T.self, level: level, rect: rect, arrayCount: data.count,\n"
        "                startIndex: startIndex, elementCount: elementCount,\n"
        "                isSetting: false)",
        "            let plan = try transferPlan(\n"
        "                T.self, level: level, rect: rect, arrayCount: data.count,\n"
        "                startIndex: startIndex, elementCount: elementCount,\n"
        "                isSetting: false)\n"
        "            let handle = try validatedHandle(\"Texture2D.GetData\")",
    ),
    (
        "closed-stream-accepted-by-save",
        "SaveAsPng writing to a stream XNA refuses for CanWrite",
        TEXTURE2D,
        "            guard stream.streamStatus != .closed, stream.streamStatus != .error else {",
        "            guard stream.streamStatus != .error else {",
    ),

    # ---- Foundation 57: SetData and GetData ------------------------------
    (
        "format-byte-size-wrong-for-color",
        "the one format this artifact can create given the wrong byte size",
        TEXTUREDATA,
        "        case .Color: return 4\n"
        "        case .Bgr565: return 2",
        "        case .Color: return 2\n"
        "        case .Bgr565: return 2",
    ),
    (
        "element-size-rule-demands-an-exact-match",
        "a T that divides the format's size refused, where XNA accepts it",
        TEXTURE2D,
        "                guard formatSize > elementSize, formatSize % elementSize == 0 else {",
        "                guard false else {",
    ),
    (
        "rectangle-origin-test-loosened",
        "a negative rectangle origin accepted",
        TEXTURE2D,
        "                guard rect.X >= 0, rect.Width > 0, rect.Y >= 0, rect.Height > 0 else {",
        "                guard rect.X >= -1, rect.Width > 0, rect.Y >= 0, rect.Height > 0 else {",
    ),
    (
        "rectangle-edge-test-signed",
        "the edge comparison made signed, so an overflowing rectangle slips through",
        TEXTURE2D,
        "                let right = UInt32(bitPattern: rect.X &+ rect.Width)\n"
        "                let bottom = UInt32(bitPattern: rect.Y &+ rect.Height)\n"
        "                guard right <= UInt32(bitPattern: Width),\n"
        "                      bottom <= UInt32(bitPattern: Height) else {",
        "                let right = rect.X &+ rect.Width\n"
        "                let bottom = rect.Y &+ rect.Height\n"
        "                guard right <= Width,\n"
        "                      bottom <= Height else {",
    ),
    (
        "total-size-allows-a-short-window",
        "a window smaller than the region accepted",
        TEXTURE2D,
        "            guard regionBytes == windowBytes else {",
        "            guard regionBytes >= windowBytes else {",
    ),
    (
        "array-window-offset-ignored",
        "startIndex dropped, so the transfer always reads from the array's front",
        TEXTURE2D,
        "            let byteOffset = Int(startIndex) * Int(elementSize)",
        "            let byteOffset = 0 * Int(elementSize)",
    ),
    (
        "rectangle-never-reaches-the-transfer",
        "the region validated and then not sent, so the whole surface moves",
        TEXTURE2D,
        "            if let rect {\n"
        "                transfer.has_rectangle = 1",
        "            if let rect, false {\n"
        "                transfer.has_rectangle = 1",
    ),
    # ---- Foundation 55: the Texture2D constructors -----------------------
    (
        "texture-dimension-guard-accepts-zero",
        "the dimension guard written as `>= 0`, so a zero-sized texture is asked for",
        TEXTURE2D,
        "            guard width > 0 else {",
        "            guard width >= 0 else {",
    ),
    (
        "texture-dimension-guard-blames-the-wrong-parameter",
        "the height's refusal naming the width",
        TEXTURE2D,
        "                throw CNAArgumentOutOfRangeException(\n"
        "                    paramName: \"height\",",
        "                throw CNAArgumentOutOfRangeException(\n"
        "                    paramName: \"width\",",
    ),
    (
        "short-texture-constructor-defaults-to-mipmaps",
        "the three-parameter constructor forwarding mipMap true, not the IL's ldc.i4.0",
        TEXTURE2D,
        "            try self.init(graphicsDevice: graphicsDevice, width: width,\n"
        "                          height: height, mipMap: false, format: .Color)",
        "            try self.init(graphicsDevice: graphicsDevice, width: width,\n"
        "                          height: height, mipMap: true, format: .Color)",
    ),
    (
        # Aimed at the level count and not at the dimensions, because
        # `build-probe/f55_grants.c` shows CNA granting the requested width and
        # height EXACTLY in every case tried -- 7x3 and 5000x5000 included --
        # so "reports what was asked for" and "reports what was granted" are
        # indistinguishable there and no test could separate them. The level
        # count is the one field where the grant is not the request: a mipped
        # 16x16 comes back with five levels and the request carries none.
        "created-texture-reports-a-level-count-of-its-own",
        "the granted mip level count replaced by a constant",
        TEXTURE2D,
        "                    levelCount: Int32(info.level_count),\n"
        "                    format: grantedFormat\n"
        "                )\n"
        "            } catch {",
        "                    levelCount: 1,\n"
        "                    format: grantedFormat\n"
        "                )\n"
        "            } catch {",
    ),
    # ---- Foundation 54: Begin's states and when they are applied ---------
    (
        "deferred-batch-applies-its-states-at-begin",
        "SetRenderState called from Begin for every sort mode, not just Immediate",
        BATCH,
        "            if sortMode == .Immediate {\n"
        "                try setRenderState()\n"
        "            }",
        "            try setRenderState()",
    ),
    (
        "immediate-batch-defers-its-states",
        "SetRenderState called from End for every sort mode, not just the deferred ones",
        BATCH,
        "            if spriteSortMode != .Immediate {\n"
        "                try setRenderState()\n"
        "            }",
        "            try setRenderState()",
    ),
    (
        "null-blend-state-defaults-to-opaque",
        "the blend default taken as Opaque, not SetRenderState's AlphaBlend",
        BATCH,
        "        private var resolvedBlendState: BlendState { blendState ?? .AlphaBlend }",
        "        private var resolvedBlendState: BlendState { blendState ?? .Opaque }",
    ),
    (
        "null-depth-state-defaults-to-default",
        "the depth default taken as DepthStencilState.Default, not None",
        BATCH,
        "            depthStencilState ?? .None",
        "            depthStencilState ?? .Default",
    ),
    (
        "sampler-applied-to-the-wrong-slot",
        "SetRenderState writing the sampler to slot one",
        BATCH,
        "            try device.SamplerStates?.SetItem(0, resolvedSamplerState)",
        "            try device.SamplerStates?.SetItem(1, resolvedSamplerState)",
    ),
    (
        "render-state-applied-around-the-device-members",
        "the states pushed to CNA without going through the device, so nothing binds",
        BATCH,
        "            try device.SetBlendState(resolvedBlendState)",
        "            _ = resolvedBlendState",
    ),
    # ---- Foundation 53: the SpriteBatch Draw family ----------------------
    #
    # Only one control here, and the reason is measured rather than assumed.
    # Three more were written -- a uniform scale written to one axis, a
    # transposed destination rectangle, and an absent source rectangle sent as
    # something other than CNA's zero-by-zero -- and all three survived a full
    # run, because NOTHING IN THIS ENVIRONMENT CAN SEE WHAT A SPRITE COMMAND
    # CONTAINS. The qualified HEADLESS artifact has no pixel readback of any
    # kind:
    #
    #   build-probe/f53_readback.c  back buffer      -> CNA_RESULT_NOT_SUPPORTED
    #   build-probe/f53_rtread.c    render target    -> CNA_RESULT_NOT_SUPPORTED
    #
    # and CNA accepts every field value those mutations produce, so the call
    # returns zero either way. The three are withdrawn rather than left here
    # claiming coverage they cannot have. What IS covered is the structure:
    # which command shape each overload uses, and the begin/end rule they all
    # obey.
    (
        "destination-draw-unguarded",
        "the destination family skipping the begin/end rule the position family keeps",
        BATCH,
        "            guard inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeDrawMessage)\n"
        "            }\n"
        "            let batchHandle = try validatedHandle(\"SpriteBatch.Draw\")\n"
        "            let textureHandle = try texture.validatedHandle(\"SpriteBatch.Draw texture\")\n"
        "            guard texture.runtimeState === nativeStorage.runtime else {\n"
        "                throw CNAError.staleRuntimeGeneration(\n"
        "                    expected: nativeStorage.generation,\n"
        "                    actual: texture.runtimeState.generation)\n"
        "            }\n"
        "            var command = CNASwift_SpriteCommand()",
        "            let batchHandle = try validatedHandle(\"SpriteBatch.Draw\")\n"
        "            let textureHandle = try texture.validatedHandle(\"SpriteBatch.Draw texture\")\n"
        "            guard texture.runtimeState === nativeStorage.runtime else {\n"
        "                throw CNAError.staleRuntimeGeneration(\n"
        "                    expected: nativeStorage.generation,\n"
        "                    actual: texture.runtimeState.generation)\n"
        "            }\n"
        "            var command = CNASwift_SpriteCommand()",
    ),
    # ---- Foundation 52: the manager's raisers and its disposal -----------
    (
        "raiser-substitutes-itself-for-the-sender",
        "a device raiser passing `self` where the IL passes its argument",
        MANAGER,
        "        open func OnDeviceCreated(_ sender: Any?, args: CNAEventArgs) throws {\n"
        "            try deviceCreatedSource.Raise(sender, args: args)",
        "        open func OnDeviceCreated(_ sender: Any?, args: CNAEventArgs) throws {\n"
        "            try deviceCreatedSource.Raise(self, args: args)",
    ),
    (
        "two-raisers-crossed",
        "OnDeviceReset raising the resetting event",
        MANAGER,
        "        open func OnDeviceReset(_ sender: Any?, args: CNAEventArgs) throws {\n"
        "            try deviceResetSource.Raise(sender, args: args)",
        "        open func OnDeviceReset(_ sender: Any?, args: CNAEventArgs) throws {\n"
        "            try deviceResettingSource.Raise(sender, args: args)",
    ),
    (
        "native-events-bypass-the-raisers",
        "the native device events raising the delegates directly, so an "
        "override never runs",
        MANAGER,
        "                case GraphicsDeviceManager.eventDeviceCreated:\n"
        "                    try OnDeviceCreated(self, args: CNAEventArgs.Empty)",
        "                case GraphicsDeviceManager.eventDeviceCreated:\n"
        "                    try deviceCreatedSource.Raise(self, args: CNAEventArgs.Empty)",
    ),
    (
        "dispose-false-still-disposes",
        "Dispose(false) doing the work `disposing` guards",
        MANAGER,
        "            guard disposing else { return }",
        "            guard !disposing || true else { return }",
    ),
    (
        "dispose-removes-the-manager-service",
        "Dispose removing IGraphicsDeviceManager, which XNA leaves registered",
        MANAGER,
        "                    game.Services.RemoveService(\n"
        "                        Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService.self)",
        "                    game.Services.RemoveService(\n"
        "                        Microsoft.Xna.Framework.IGraphicsDeviceManager.self)",
    ),
    (
        "disposed-raised-before-the-removal",
        "Disposed raised first, so a handler sees a service still registered",
        MANAGER,
        "            guard disposing else { return }\n"
        "            if let game {",
        "            guard disposing else { return }\n"
        "            try disposedSource.Raise(self, args: CNAEventArgs.Empty)\n"
        "            if let game {",
    ),
    # ---- Foundation 51: the GraphicsDeviceManager preferences ------------
    (
        "vsync-default-taken-from-the-clr",
        "SynchronizeWithVerticalRetrace defaulting to false, not the ctor's ldc.i4.1",
        MANAGER,
        "        private var synchronizeWithVerticalRetracePreference = true",
        "        private var synchronizeWithVerticalRetracePreference = false",
    ),
    (
        "depth-preference-default-taken-from-the-clr",
        "PreferredDepthStencilFormat defaulting to None, not the ctor's ldc.i4.2",
        MANAGER,
        "        private var depthStencilFormat: Microsoft.Xna.Framework.Graphics.DepthFormat = .Depth24",
        "        private var depthStencilFormat: Microsoft.Xna.Framework.Graphics.DepthFormat = .None",
    ),
    (
        "dimension-setter-accepts-zero",
        "the dimension guard written as `>= 0`, so zero is accepted",
        MANAGER,
        "        public func SetPreferredBackBufferWidth(_ value: Int32) throws {\n"
        "            guard value > 0 else {",
        "        public func SetPreferredBackBufferWidth(_ value: Int32) throws {\n"
        "            guard value >= 0 else {",
    ),
    (
        "dimension-refusal-still-stores",
        "the width stored before the guard, so a refused value takes effect",
        MANAGER,
        "            backBufferWidth = value\n"
        "            useResizedBackBuffer = false",
        "            backBufferWidth = max(value, backBufferWidth)\n"
        "            useResizedBackBuffer = false",
    ),
    (
        "apply-changes-loses-its-short-circuit",
        "ApplyChanges reconfiguring the device on every call again",
        MANAGER,
        "            if GraphicsDevice != nil, !isDeviceDirty { return }",
        "            if GraphicsDevice != nil, isDeviceDirty { return }",
    ),
    (
        "a-preference-setter-forgets-the-dirty-flag",
        "a setter that stores without marking the device dirty",
        MANAGER,
        "            set { preferMultiSamplingPreference = newValue; isDeviceDirty = true }",
        "            set { preferMultiSamplingPreference = newValue }",
    ),
    (
        "toggle-full-screen-does-not-apply",
        "ToggleFullScreen flipping the field and never changing the device",
        MANAGER,
        "            IsFullScreen = !IsFullScreen\n"
        "            try changeDevice()",
        "            IsFullScreen = !IsFullScreen",
    ),
    (
        "a-pushed-preference-is-dropped",
        "the back-buffer height never handed to CNA",
        MANAGER,
        "            try functions.check(\n"
        "                functions.graphicsManagerSetPreferredBackBufferHeight(handle, backBufferHeight),\n"
        "                operation: \"cna_graphics_device_manager_set_preferred_back_buffer_height\")",
        "            _ = backBufferHeight",
    ),
    # ---- Foundation 50: the messages implemented members raise -----------
    (
        "sprite-batch-second-begin-unguarded",
        "a second Begin left to CNA, which reports a result code and not XNA's rule",
        BATCH,
        "            guard !inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: endMustBeCalledBeforeBeginMessage)\n"
        "            }",
        "            if false {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: endMustBeCalledBeforeBeginMessage)\n"
        "            }",
    ),
    (
        "sprite-batch-rule-checked-after-the-handle",
        "the begin/end rule decided after the handle, so a disposed batch "
        "reports its disposal rather than the rule it broke",
        BATCH,
        "            guard inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeEndMessage)\n"
        "            }\n"
        "            let handle = try validatedHandle(\"SpriteBatch.End\")",
        "            let handle = try validatedHandle(\"SpriteBatch.End\")\n"
        "            guard inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeEndMessage)\n"
        "            }",
    ),
    (
        "sprite-batch-end-guard-inverted",
        "End refusing inside a pair and accepting outside one",
        BATCH,
        "            guard inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeEndMessage)\n"
        "            }",
        "            guard !inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeEndMessage)\n"
        "            }",
    ),
    (
        # Anchored on the scaled funnel's own next line: Foundation 53 gave the
        # destination funnel the identical guard, and an anchor that matches
        # both is a stale site, which the precondition catches before a run.
        "sprite-batch-draw-unguarded",
        "Draw outside a pair left to CNA",
        BATCH,
        "            guard inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeDrawMessage)\n"
        "            }\n"
        "            let batchHandle = try validatedHandle(\"SpriteBatch.Draw\")\n"
        "            let textureHandle = try texture.validatedHandle(\"SpriteBatch.Draw texture\")\n"
        "            guard texture.runtimeState === nativeStorage.runtime else {\n"
        "                throw CNAError.staleRuntimeGeneration(expected: nativeStorage.generation, actual: texture.runtimeState.generation)\n"
        "            }",
        "            let batchHandle = try validatedHandle(\"SpriteBatch.Draw\")\n"
        "            let textureHandle = try texture.validatedHandle(\"SpriteBatch.Draw texture\")\n"
        "            guard texture.runtimeState === nativeStorage.runtime else {\n"
        "                throw CNAError.staleRuntimeGeneration(expected: nativeStorage.generation, actual: texture.runtimeState.generation)\n"
        "            }",
    ),
    (
        "sprite-batch-pair-never-closes",
        "End leaving the pair open, so the next Begin is refused",
        BATCH,
        "            inBeginEndPair = false\n"
        "        }",
        "        }",
    ),
    (
        "sprite-batch-draw-and-end-messages-collapsed",
        "the Draw and End messages made the same string",
        BATCH,
        'internal let beginMustBeCalledBeforeDrawMessage =\n'
        '    "Begin must be called successfully before a Draw can be called."',
        'internal let beginMustBeCalledBeforeDrawMessage =\n'
        '    "Begin must be called successfully before End can be called."',
    ),
    (
        "drawable-device-getter-uses-its-siblings-message",
        "the defect Foundation 50 repaired, put back",
        DRAWABLE_COMPONENT,
        "                        message: DrawableGameComponent\n"
        "                            .propertyCannotBeCalledBeforeInitializeMessage)",
        "                        message: DrawableGameComponent\n"
        "                            .missingGraphicsDeviceServiceMessage)",
    ),
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
        "            if let slotZero = boundRenderTargetSlotZero {\n"
        "                return (slotZero.renderTargetWidth, slotZero.renderTargetHeight)\n"
        "            }",
        "            if let slotZero = boundRenderTargetSlotZero, false {\n"
        "                return (slotZero.renderTargetWidth, slotZero.renderTargetHeight)\n"
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
        "                if let target = boundRenderTargetDepthFormat {",
        "                if let target = boundRenderTargetDepthFormat, false {",
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
        "            recordActiveRenderTargets([binding])\n"
        "        }\n"
        "\n"
        "        /// `GraphicsDevice.SetRenderTarget(RenderTargetCube renderTarget, CubeMapFace cubeMapFace)`.",
        "            recordActiveRenderTargets([])\n"
        "        }\n"
        "\n"
        "        /// `GraphicsDevice.SetRenderTarget(RenderTargetCube renderTarget, CubeMapFace cubeMapFace)`.",
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
        "            guard disposing else { return }\n"
        "            try disposingSource.Raise(self, args: CNAEventArgs.Empty)",
        "            guard !IsDisposed else { return }\n"
        "            guard disposing else { return }\n"
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
        "            if let storage {\n"
        "                try storage.dispose(operation: \"\\(storage.typeName).Dispose\")",
        "            if let storage {\n"
        "                try storage.dispose(operation: \"\\(storage.typeName).Dispose\")",
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
        "            contentLostSubscription?.release()\n"
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
    # ---- Foundation 64: TextureCube and Texture3D ------------------------
    (
        "cube-size-limit-is-the-texture-limit",
        "MaxCubeSize read as MaxTextureSize, so a 1024 cube is accepted",
        PROFILECAPS,
        "            guard size <= maxCubeSize else {",
        "            guard size <= maxTextureSize else {",
    ),
    (
        "cube-power-of-two-test-dropped",
        "a non-power-of-two cube accepted where Reach refuses one",
        PROFILECAPS,
        "            if !nonPow2Cube, !ProfileCapabilities.isPowerOfTwo(size) {",
        "            if false, !ProfileCapabilities.isPowerOfTwo(size) {",
    ),
    (
        "cube-format-list-is-the-texture-list",
        "ValidCubeFormats read as ValidTextureFormats, a different list",
        PROFILECAPS,
        "            guard validCubeFormats.contains(format) else {",
        "            guard validTextureFormats.contains(format) else {",
    ),
    (
        "volume-zero-extent-test-dropped",
        "a Texture3D allowed past the check that makes Reach refuse every one",
        PROFILECAPS,
        "            guard maxVolumeExtent != 0 else {",
        "            guard true else {",
    ),
    (
        "volume-extent-guards-run-after-the-profile-test",
        "a non-positive extent reported as a profile refusal, not its own name",
        PROFILECAPS,
        "            for (value, name) in [(width, \"width\"), (height, \"height\"), (depth, \"depth\")] {\n"
        "                guard value > 0 else {\n"
        "                    throw CNAArgumentOutOfRangeException(\n"
        "                        paramName: name,\n"
        "                        message: Microsoft.Xna.Framework.Graphics.Texture2D\n"
        "                            .resourcesMustBeGreaterThanZeroSizeMessage)\n"
        "                }\n"
        "            }",
        "",
    ),
    (
        "volume-aspect-ratio-ignores-the-depth",
        "Max/Min taken over width and height only, never over all three extents",
        PROFILECAPS,
        "            let longer = max(max(width, height), depth)\n"
        "            let shorter = min(min(width, height), depth)",
        "            let longer = max(width, height)\n"
        "            let shorter = min(width, height)",
    ),
    (
        "cube-empty-array-not-reported-as-null",
        "a zero-length array falling through to the size tests",
        TEXTURECUBE,
        "            guard arrayCount > 0 else {",
        "            guard arrayCount >= 0 else {",
    ),
    (
        "cube-window-not-validate-copy-parameters",
        "the array window silently accepted instead of raising MustBeValidIndex",
        TEXTURECUBE,
        "            try Microsoft.Xna.Framework.Graphics.validateCopyParameters(\n"
        "                dataLength: arrayCount, dataIndex: startIndex,\n"
        "                elementCount: elementCount)",
        "",
    ),
    (
        "cube-disposal-checked-after-the-arguments",
        "a disposed cube reporting a bad argument instead of the disposal",
        TEXTURECUBE,
        "            let handle = try validatedHandle(\n"
        "                isSetting ? \"TextureCube.SetData\" : \"TextureCube.GetData\")\n"
        "            guard arrayCount > 0 else {",
        "            guard arrayCount > 0 else {",
    ),
    (
        "cube-transfer-does-not-reach-the-route",
        "SetData accepted and discarded rather than handed to CNA",
        TEXTURECUBE,
        "                            functions.textureCubeSetData(\n"
        "                                plan.handle, transfer, $0, plan.elementCount)",
        "                            CNA_Result(0)",
    ),
    (
        "volume-box-test-signed-not-unsigned",
        "a negative box coordinate slipping past a comparison XNA makes unsigned",
        TEXTUREDATA,
        "        return uRight <= UInt32(bitPattern: width) && uLeft < uRight\n"
        "            && uBottom <= UInt32(bitPattern: height) && uTop < uBottom\n"
        "            && uBack <= UInt32(bitPattern: depth) && uFront < uBack",
        "        return right <= width && left < right\n"
        "            && bottom <= height && top < bottom\n"
        "            && back <= depth && front < back",
    ),
    (
        "texture2d-empty-array-not-reported-as-null",
        "Texture2D's zero-length array falling through to the size tests",
        TEXTURE2D,
        "            guard arrayCount > 0 else {",
        "            guard arrayCount >= 0 else {",
    ),
    (
        "texture2d-window-not-validate-copy-parameters",
        "Texture2D's array window silently accepted instead of MustBeValidIndex",
        TEXTURE2D,
        "            try Microsoft.Xna.Framework.Graphics.validateCopyParameters(\n"
        "                dataLength: arrayCount, dataIndex: startIndex,\n"
        "                elementCount: elementCount)",
        "",
    ),
    # ---- Foundation 65: the render-target family --------------------------
    (
        "cube-target-reads-the-cube-info-route",
        "RenderTargetCube's description read where CNA answers zeros",
        RTCUBE,
        "                    runtime.functions.renderTargetGetInfo(handle, &info),\n"
        "                    operation: \"cna_render_target_get_info\")",
        "                    runtime.functions.renderTargetGetInfo(handle, &info),\n"
        "                    operation: \"cna_render_target_get_info\")\n"
        "                info.width = 0; info.height = 0; info.level_count = 0",
    ),
    (
        "cube-target-skips-the-profile-checks",
        "a 1024 or non-power-of-two cube target accepted where Reach refuses one",
        RTCUBE,
        "            try graphicsDevice.profileCapabilities.validateCubeCreation(\n"
        "                size: size, format: preferredFormat)",
        "",
    ),
    (
        "cube-target-does-not-release-its-subscription",
        "a disposed cube target leaving a native callback addressing freed state",
        RTCUBE,
        "            contentLostSubscription?.release()\n"
        "            try super.Dispose(disposing)",
        "            try super.Dispose(disposing)",
    ),
    (
        "binding-2d-face-is-not-positive-x",
        "a 2D binding carrying a face where XNA stores ldc.i4.0",
        RTBINDING,
        "            storedRenderTarget = renderTarget\n"
        "            storedCubeMapFace = .PositiveX",
        "            storedRenderTarget = renderTarget\n"
        "            storedCubeMapFace = .NegativeZ",
    ),
    (
        "render-target-cache-not-updated",
        "what was bound not recorded, so GetRenderTargets answers the wrong array",
        DEVICE,
        "            recordActiveRenderTargets(renderTargets)",
        "            recordActiveRenderTargets([])",
    ),
    # `render-target-identity-lost` -- rebuilding each binding from the target it
    # already holds -- was planted here and SURVIVED, because it is a NO-OP: a
    # RenderTargetBinding is a struct with no identity of its own, so rebuilding
    # one around the same target is indistinguishable from returning it. It is
    # replaced rather than scored. What `GetRenderTargets` can actually get
    # wrong is covered: `render-target-cache-not-updated` catches the wrong
    # array, and `cube-face-not-carried-to-the-device` covers the face.
    #
    # `testTheReturnedArrayIsACopy` asserts a claim no mutation can falsify
    # either: Swift's Array is a value, so a returned array simply cannot alias
    # the cache. The test documents the guarantee rather than proving code.
    (
        "render-target-limit-unchecked",
        "two simultaneous targets accepted where Reach's MaxRenderTargets is 1",
        DEVICE,
        "            guard bindings.count <= Int(capabilities.maxRenderTargets) else {",
        "            guard bindings.count <= Int(capabilities.maxVertexStreams) else {",
    ),
    (
        "render-target-device-compared-by-facade",
        "the device-identity test comparing per-callback tokens",
        DEVICE,
        "                guard target.nativeStorage.runtime === runtime else {\n"
        "                    throw CNAInvalidOperationException(\n"
        "                        message: GraphicsDevice.invalidDeviceMessage)\n"
        "                }\n"
        "                guard index > 0 else { continue }",
        "                guard target.GraphicsDevice === self else {\n"
        "                    throw CNAInvalidOperationException(\n"
        "                        message: GraphicsDevice.invalidDeviceMessage)\n"
        "                }\n"
        "                guard index > 0 else { continue }",
    ),
    # `render-target-binder-skips-the-disposal-check` was planted here and
    # SURVIVED, and the reason is that the check is REDUNDANT on every reachable
    # input: whichever binder runs, the handle is validated again where it is
    # actually used, and that second validation raises the same
    # ObjectDisposedException with the same message. The check stays because
    # XNA's `Helpers.CheckDisposed` is there and because its ORDER matters --
    # ahead of the device-identity test, so a target that is both disposed and
    # foreign reports the disposal. That ordering needs two devices to observe
    # and CNA runs one game at a time, so the claim is recorded as not yet
    # evidence rather than kept as a mutation nothing can catch.
    # `cube-face-not-carried-to-the-device` -- binding the positive-X face
    # whatever was asked -- was planted here and SURVIVED, for exactly the
    # reason `vertex-offset-not-carried` was withdrawn in Foundation 63:
    # `GetRenderTargets()` reads the managed cache, as XNA's does, and nothing
    # in the public surface observes the face the DEVICE received.
    # `cna_graphics_device_copy_render_targets` does answer it -- the probe
    # reads face 3 back from a cube binding -- but binding a route for a test
    # alone is what docs/native-abi.md forbids. Recorded as not yet evidence;
    # it becomes falsifiable when something renders through a face.
    (
        "same-size-test-ignores-the-pixel-size",
        "IsSameSize comparing extents only, never the format's byte width",
        RTSUPPORT,
        "        left.width == right.width\n"
        "            && left.height == right.height\n"
        "            && left.samples == right.samples\n"
        "            && left.pixelSize == right.pixelSize",
        "        left.width == right.width\n"
        "            && left.height == right.height",
    ),
    (
        "bound-resources-not-released-at-shutdown",
        "the retain cycle Foundation 65 closed, reopened",
        RUNTIME,
        "        releaseBoundResources()\n"
        "        RuntimeRegistry.leave(self)",
        "        RuntimeRegistry.leave(self)",
    ),
    # ---- Foundation 66: TextureCollection and the three bound-state checks ---
    (
        "texture-collections-not-profile-sized",
        "the vertex collections 16 slots long on a profile that has none",
        RUNTIME,
        "        return Int(vertex ? capabilities.maxVertexSamplers : capabilities.maxSamplers)",
        "        return Int(capabilities.maxSamplers)",
    ),
    (
        "texture-slot-cache-not-updated",
        "what was bound not recorded, so Textures[i] answers nil",
        TEXTURECOLLECTION,
        "            slots[resolved] = value\n"
        "        }",
        "        }",
    ),
    (
        "texture-slot-value-checked-after-the-index",
        "an active render target reported as a bad index",
        TEXTURECOLLECTION,
        "        public func SetItem(_ index: Int32, _ value: Texture?) throws {\n"
        "            if let value {",
        "        public func SetItem(_ index: Int32, _ value: Texture?) throws {\n"
        "            _ = try checkedIndex(index)\n"
        "            if let value {",
    ),
    (
        "texture-slot-render-target-test-dropped",
        "the device's own render target accepted as a sampler source",
        TEXTURECOLLECTION,
        "                guard !value.isActiveRenderTarget else {",
        "                guard value.isActiveRenderTarget else {",
    ),
    (
        "vertex-texture-format-rule-applied-to-both-stages",
        "the pixel collection refusing every format the vertex rule refuses",
        TEXTURECOLLECTION,
        "                if textureOffset > 0 {",
        "                if textureOffset >= 0 {",
    ),
    (
        "texture-slot-binder-does-not-reach-the-device",
        "a slot recorded managed-side and never bound natively",
        TEXTURECOLLECTION,
        "            try device.runtimeState.functions.check(\n"
        "                device.runtimeState.functions.graphicsDeviceSetTexture(\n"
        "                    deviceHandle, stage, UInt32(resolved), textureHandle),\n"
        "                operation: \"cna_graphics_device_set_texture\")",
        "            _ = (deviceHandle, textureHandle)",
    ),
    (
        "disposed-texture-stays-in-the-collection",
        "a disposed texture still answered by Textures[i]",
        RESOURCE,
        "                for collection in storage.runtime.liveTextureCollections {\n"
        "                    collection.forget(self)\n"
        "                }",
        "",
    ),
    (
        "active-render-target-flag-never-set",
        "nothing ever marked as the device's target, so three checks never fire",
        DEVICE,
        "            for binding in bindings {\n"
        "                binding.RenderTarget.isActiveRenderTarget = true\n"
        "            }",
        "",
    ),
    (
        "active-render-target-flag-never-cleared",
        "a target that was unbound still refusing to be sampled or written",
        DEVICE,
        "            for previous in runtime.cachedRenderTargetBindings {\n"
        "                previous.RenderTarget.isActiveRenderTarget = false\n"
        "            }",
        "",
    ),
    (
        "resource-in-use-scan-dropped",
        "SetData accepted on a texture bound to a sampler",
        TEXTUREDATA,
        "        for collection in nativeStorage.runtime.liveTextureCollections\n"
        "        where collection.holds(self) {",
        "        for collection in nativeStorage.runtime.liveTextureCollections\n"
        "        where false && collection.holds(self) {",
    ),
    (
        "resource-in-use-scan-ignores-is-setting",
        "GetData refused on a bound texture, which XNA allows",
        TEXTUREDATA,
        "        guard isSetting else { return }",
        "        guard isSetting || true else { return }",
    ),
    (
        "must-resolve-render-target-not-checked-in-transfers",
        "SetData accepted on the device's own render target",
        TEXTUREDATA,
        "        if checksRenderTarget, isActiveRenderTarget {",
        "        if checksRenderTarget, false, isActiveRenderTarget {",
    ),
    # ---- Foundation 67: the Effect core -----------------------------------
    (
        "effect-collection-element-not-cached",
        "a fresh CNA view per index read, so collection[0] !== collection[0]",
        EFFECTSUPPORT,
        "            if let existing = cached[Int(index)] { return existing }",
        "            _ = cached[Int(index)]",
    ),
    # `effect-collection-index-throws-instead-of-nil` -- relaxing the bound from
    # `<` to `<=` -- was planted here and SURVIVED as a NO-OP: one past the end
    # gets past the guard and `get_at` then fails, so the answer is still nil.
    # It is replaced rather than scored, with one that changes the answer.
    (
        "effect-collection-index-clamps-instead-of-nil",
        "an out-of-range index answering element zero rather than null",
        EFFECTSUPPORT,
        "            guard index >= 0, index < count else { return nil }",
        "            guard index >= 0, index < count else {\n"
        "                return count > 0 ? element(at: 0) : nil\n"
        "            }",
    ),
    (
        "effect-name-scan-compares-the-wrong-key",
        "a name lookup that matches nothing, or the wrong element",
        EFFECTSUPPORT,
        "                if key(candidate) == name { return candidate }",
        "                if key(candidate) != name { return candidate }",
    ),
    (
        "effect-string-ignores-the-written-length",
        "a native string read back with its buffer padding attached",
        EFFECTSUPPORT,
        "        let used = buffer.prefix(Int(min(written, bytes))).map { UInt8(bitPattern: $0) }",
        "        let used = buffer.map { UInt8(bitPattern: $0) } + [UInt8(65)]",
    ),
    (
        "effect-pass-apply-skips-the-disposal-check",
        "a pass applying through a disposed effect",
        EFFECTCOLLECTIONS,
        "            _ = try effect.validatedHandle(\"EffectPass.Apply\")",
        "            _ = effect.nativeStorage.handle",
    ),
    (
        "effect-pass-apply-skips-the-current-technique-test",
        "a pass of a non-current technique applying anyway",
        EFFECTCOLLECTIONS,
        "            guard effect.CurrentTechnique === technique else {",
        "            guard effect.CurrentTechnique !== technique else {",
    ),
    (
        "effect-pass-apply-does-not-call-on-apply",
        "the derived hook never firing",
        EFFECTCOLLECTIONS,
        "            try effect.OnApply()\n"
        "            try box.runtime.functions.check(\n"
        "                box.runtime.functions.effectPassApply(",
        "            try box.runtime.functions.check(\n"
        "                box.runtime.functions.effectPassApply(",
    ),
    (
        "effect-pass-apply-does-not-reach-the-route",
        "Apply accepted and discarded rather than handed to CNA",
        EFFECTCOLLECTIONS,
        "                box.runtime.functions.effectPassApply(\n"
        "                    try box.validated(\"EffectPass.Apply\")),\n"
        "                operation: \"cna_effect_pass_apply\")",
        "                CNA_Result(0)),\n"
        "                operation: \"cna_effect_pass_apply\")",
    ),
    (
        "effect-technique-passes-not-cached",
        "a fresh pass collection per read, losing pass identity",
        EFFECTCOLLECTIONS,
        "            if let passes { return passes }",
        "            if let passes, false { return passes }",
    ),
    (
        "effect-current-technique-is-a-third-view",
        "CurrentTechnique answering an object the collection never handed out",
        EFFECT,
        "            let resolved = collection?[name] ?? collection?[Int32(0)]",
        "            let resolved = EffectTechnique(\n"
        "                handle: handle, runtime: nativeStorage.runtime, owner: self)",
    ),
    (
        "effect-techniques-not-cached",
        "a fresh technique collection per read, so Techniques !== Techniques",
        EFFECT,
        "            if let techniques { return techniques }",
        "            if let techniques, false { return techniques }",
    ),
    (
        "effect-code-length-not-a-multiple-of-four",
        "a badly sized effect array accepted and handed to CNA",
        EFFECT,
        "            guard effectCode.count % 4 == 0 else {",
        "            guard effectCode.count % 1 == 0 else {",
    ),
    (
        "effect-empty-code-not-reported-as-null",
        "an empty effect array reaching the native compiler",
        EFFECT,
        "            guard !effectCode.isEmpty else {",
        "            guard effectCode.isEmpty || true else {",
    ),
    (
        "effect-apply-also-calls-on-apply",
        "the derived hook firing twice for one application",
        EFFECT,
        "        internal func apply() throws {\n"
        "            try nativeStorage.runtime.functions.check(",
        "        internal func apply() throws {\n"
        "            try OnApply()\n"
        "            try nativeStorage.runtime.functions.check(",
    ),
    # ---- Foundation 68: the draw family -----------------------------------
    (
        "draw-accepts-zero-primitives",
        "a draw of nothing accepted where XNA raises MustDrawSomething",
        DRAW,
        "        guard primitiveCount > 0 else {",
        "        guard primitiveCount >= 0 else {",
    ),
    (
        "draw-primitive-limit-unchecked",
        "more primitives than the profile allows reaching the device",
        DRAW,
        "        guard primitiveCount <= capabilities.maxPrimitiveCount else {",
        "        guard primitiveCount <= capabilities.maxVertexBufferSize else {",
    ),
    (
        "draw-vertex-count-checked-after-the-primitive-count",
        "a bad numVertices reported as a bad primitiveCount",
        DRAW,
        "        let handle = try validatedHandle(\"GraphicsDevice.DrawIndexedPrimitives\")\n"
        "        guard numVertices > 0 else {",
        "        let handle = try validatedHandle(\"GraphicsDevice.DrawIndexedPrimitives\")\n"
        "        try validatePrimitiveCount(primitiveCount)\n"
        "        guard numVertices > 0 else {",
    ),
    (
        "draw-instance-stream-mask-always-zero",
        "a non-instanced draw accepted with an instanced stream bound",
        DRAW,
        "        for (index, binding) in runtimeState.cachedVertexBufferBindings.enumerated()\n"
        "        where binding.InstanceFrequency != 0 {",
        "        for (index, binding) in runtimeState.cachedVertexBufferBindings.enumerated()\n"
        "        where binding.InstanceFrequency == 0 {",
    ),
    (
        "instanced-draw-accepts-a-uniform-stream-set",
        "an instanced draw accepted with every stream instanced, or none",
        DRAW,
        "        guard mask != 0, !allOne else {",
        "        guard mask == 0 || allOne || true else {",
    ),
    (
        "user-draw-empty-array-not-reported-as-null",
        "an empty user vertex array falling through to the offset test",
        DRAW,
        "        guard count > 0 else {\n"
        "            throw CNAArgumentNullException(\n"
        "                paramName: \"vertexData\",",
        "        guard count >= 0 else {\n"
        "            throw CNAArgumentNullException(\n"
        "                paramName: \"vertexData\",",
    ),
    (
        "user-draw-offset-not-bounded-by-the-array",
        "a vertex offset past the end of the caller's array accepted",
        DRAW,
        "        guard vertexOffset >= 0, Int(vertexOffset) < count else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"vertexOffset\",",
        "        guard vertexOffset >= 0, Int(vertexOffset) <= count else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"vertexOffset\",",
    ),
    (
        "user-draw-element-count-test-is-signed",
        "an overflowing offset plus element count slipping past an unsigned test",
        DRAW,
        "        let end = UInt32(bitPattern: elements) &+ UInt32(bitPattern: offset)\n"
        "        return end <= UInt32(clamping: count)",
        "        let end = elements &+ offset\n"
        "        return end <= Int32(clamping: count)",
    ),
    (
        "user-draw-element-count-not-consulted",
        "a primitive count the array cannot supply accepted",
        DRAW,
        "        guard Microsoft.Xna.Framework.Graphics.GraphicsDevice.arrayHolds(\n"
        "            offset: vertexOffset, elements: needed, count: count) else {",
        "        guard Microsoft.Xna.Framework.Graphics.GraphicsDevice.arrayHolds(\n"
        "            offset: vertexOffset, elements: 0, count: count) else {",
    ),
    (
        "user-indexed-draw-allows-32-bit-indices-on-reach",
        "32-bit user indices accepted where Reach refuses them",
        DRAW,
        "            guard capabilities.indexElementSize32 else {",
        "            guard !capabilities.indexElementSize32 else {",
    ),
    (
        "draw-does-not-reach-the-route",
        "DrawPrimitives accepted and discarded rather than handed to CNA",
        DRAW,
        "            runtimeState.functions.graphicsDeviceDrawPrimitives(\n"
        "                handle, UInt32(bitPattern: primitiveType.rawValue),\n"
        "                startVertex, primitiveCount),",
        "            CNA_Result(0),",
    ),
    (
        "primitive-type-not-carried-to-the-route",
        "every draw submitted as a triangle list whatever was asked",
        DRAW,
        "                handle, UInt32(bitPattern: primitiveType.rawValue),\n"
        "                startVertex, primitiveCount),",
        "                handle, 0,\n"
        "                startVertex, primitiveCount),",
    ),

    # ---- Foundation 69: the stock effects --------------------------------
    (
        "light-getter-reads-the-wrong-cache",
        "a light's getters answering another field than the one XNA reads",
        LIGHT,
        "        public var DiffuseColor: Microsoft.Xna.Framework.Vector3 { cachedDiffuseColor }",
        "        public var DiffuseColor: Microsoft.Xna.Framework.Vector3 { cachedSpecularColor }",
    ),
    (
        "disabling-a-light-clears-its-cache",
        "set_Enabled(false) clearing what the light remembers, not just the parameter",
        LIGHT,
        "                try diffuseColorParam?.SetValue(\n"
        "                    Microsoft.Xna.Framework.Vector3.Zero)",
        "                cachedDiffuseColor = Microsoft.Xna.Framework.Vector3.Zero\n"
        "                try diffuseColorParam?.SetValue(\n"
        "                    Microsoft.Xna.Framework.Vector3.Zero)",
    ),
    (
        "enabled-setter-is-not-a-no-op",
        "set_Enabled re-pushing when the value has not changed",
        LIGHT,
        "            guard enabled != value else { return }",
        "            if enabled == value && false { return }",
    ),
    (
        "diffuse-written-while-disabled",
        "set_DiffuseColor writing its parameter regardless of Enabled",
        LIGHT,
        "            if enabled { try diffuseColorParam?.SetValue(value) }\n"
        "            cachedDiffuseColor = value",
        "            try diffuseColorParam?.SetValue(value)\n"
        "            cachedDiffuseColor = value",
    ),
    (
        "direction-written-only-while-enabled",
        "set_Direction consulting Enabled, which XNA's does not",
        LIGHT,
        "            try directionParam?.SetValue(value)\n"
        "            cachedDirection = value",
        "            if enabled { try directionParam?.SetValue(value) }\n"
        "            cachedDirection = value",
    ),
    (
        "clone-runs-the-setters",
        "the clone constructor assigning through the setters, so a clone writes parameters",
        LIGHT,
        "                enabled = cloneSource.enabled\n"
        "                cachedDirection = cloneSource.cachedDirection",
        "                try SetEnabled(cloneSource.enabled)\n"
        "                cachedDirection = cloneSource.cachedDirection",
    ),
    (
        "default-lighting-table-altered",
        "one component of EffectHelpers' default lighting table changed",
        STOCKSUPPORT,
        "            Microsoft.Xna.Framework.Vector3(-0.5265408, -0.5735765, -0.6275069))",
        "            Microsoft.Xna.Framework.Vector3(-0.5265408, -0.5735765, -0.6275))",
    ),
    (
        "default-lighting-specular-shared",
        "light1's specular set from its diffuse instead of Zero",
        STOCKSUPPORT,
        "        try light1.SetSpecularColor(Microsoft.Xna.Framework.Vector3.Zero)",
        "        try light1.SetSpecularColor(\n"
        "            Microsoft.Xna.Framework.Vector3(0.9647059, 0.7607844, 0.4078432))",
    ),
    (
        "default-lighting-leaves-lights-off",
        "EnableDefaultLighting setting the three lights' values but not enabling them",
        STOCKSUPPORT,
        "        try light0.SetEnabled(true)",
        "        try light0.SetEnabled(false)",
    ),
    (
        "default-lighting-does-not-enable-lighting",
        "BasicEffect.EnableDefaultLighting leaving LightingEnabled alone",
        BASICEFFECT,
        "            LightingEnabled = true\n"
        "            AmbientLightColor = try Microsoft.Xna.Framework.Graphics",
        "            AmbientLightColor = try Microsoft.Xna.Framework.Graphics",
    ),
    (
        "effect-lights-not-cached",
        "an effect fetching a fresh light view per call, so its lights lose identity",
        BASICEFFECT,
        "        public var DirectionalLight0: DirectionalLight? { light0 }",
        "        public var DirectionalLight0: DirectionalLight? {\n"
        "            try? Microsoft.Xna.Framework.Graphics.stockEffectLights(\n"
        "                handle: try validatedHandle(\"BasicEffect.DirectionalLight0\"),\n"
        "                runtime: nativeStorage.runtime).0\n"
        "        }",
    ),
    (
        "always-lit-effect-accepts-false",
        "SkinnedEffect agreeing to disable lighting instead of refusing",
        SKINNED,
        "            guard !value else { return }\n"
        "            throw CNANotSupportedException(",
        "            guard value else { return }\n"
        "            throw CNANotSupportedException(",
    ),
    (
        "always-lit-effect-names-the-wrong-type",
        "CantDisableLighting formatted with the other always-lit effect's name",
        SKINNED,
        "                    .replacingOccurrences(of: \"{0}\", with: \"SkinnedEffect\"))",
        "                    .replacingOccurrences(of: \"{0}\", with: \"EnvironmentMapEffect\"))",
    ),
    (
        "max-bones-off-by-one",
        "SetBoneTransforms accepting one more bone than MaxBones",
        SKINNED,
        "            guard boneTransforms.count <= Int(SkinnedEffect.MaxBones) else {",
        "            guard boneTransforms.count <= Int(SkinnedEffect.MaxBones) + 1 else {",
    ),
    (
        "empty-bone-array-accepted",
        "SetBoneTransforms accepting an empty array instead of refusing it as null",
        SKINNED,
        "            guard !boneTransforms.isEmpty else {",
        "            guard boneTransforms.count >= 0 else {",
    ),
    # `bone-reader-skips-the-fourth-diagonal` was planted here and WITHDRAWN,
    # not scored. It deleted `matrix.M44 = 1` from GetBoneTransforms, which
    # reproduces the loop at IL_0051; `build-probe/f69_bones.c` then measured
    # that CNA already answers `m44 = 1` for a bone written with `m44 = 0`,
    # keeping the rest of the fourth column. The managed restoration is
    # therefore invisible on this artifact and no test can be written that the
    # mutation would fail. The reason is recorded in SkinnedEffect.swift where
    # the line stands.
    (
        "weights-per-vertex-accepts-three",
        "WeightsPerVertex admitting a value XNA refuses",
        SKINNED,
        "            guard value == 1 || value == 2 || value == 4 else {",
        "            guard value == 1 || value == 2 || value == 3 || value == 4 else {",
    ),
    (
        "weights-per-vertex-writes-before-testing",
        "the refused value stored anyway, so the property changes on a throw",
        SKINNED,
        "            guard value == 1 || value == 2 || value == 4 else {\n"
        "                throw CNAArgumentOutOfRangeException(",
        "            state.weightsPerVertex = value\n"
        "            guard value == 1 || value == 2 || value == 4 else {\n"
        "                throw CNAArgumentOutOfRangeException(",
    ),
    (
        "dual-texture-layers-collapse",
        "Texture2 reading and writing layer zero, so the two properties are one",
        DUALTEXTURE,
        "        private static let secondLayer: UInt32 = 1",
        "        private static let secondLayer: UInt32 = 0",
    ),
    (
        "alpha-default-not-one",
        "the cached alpha starting at something other than what the constructor sets",
        STOCKSUPPORT,
        "        var alpha: Float = 1",
        "        var alpha: Float = 0",
    ),
    (
        "fog-end-default-not-one",
        "fogEnd starting at zero, which is not what the constructor's IL sets",
        STOCKSUPPORT,
        "        var fogEnd: Float = 1",
        "        var fogEnd: Float = 0",
    ),
    (
        "weights-per-vertex-default-not-four",
        "WeightsPerVertex starting at a value XNA's field default is not",
        STOCKSUPPORT,
        "        var weightsPerVertex: Int32 = 4",
        "        var weightsPerVertex: Int32 = 2",
    ),
    (
        "setter-does-not-mark-dirty",
        "an assignment that never reaches the device because it is not recorded",
        BASICEFFECT,
        "            set { state.alpha = newValue; state.mark(.alpha) }",
        "            set { state.alpha = newValue }",
    ),
    (
        "clone-loses-the-cached-state",
        "the clone constructor starting from defaults instead of the source's state",
        BASICEFFECT,
        "            state = cloneSource.state\n"
        "            texture = cloneSource.texture",
        "            texture = cloneSource.texture",
    ),
    (
        "texture-identity-not-tracked",
        "an assigned texture forgotten, so the getter answers nil for a set texture",
        BASICEFFECT,
        "                nativeStorage.runtime.functions.basicEffectSetTexture($0, $1)\n"
        "            }\n"
        "            texture = value",
        "                nativeStorage.runtime.functions.basicEffectSetTexture($0, $1)\n"
        "            }",
    ),
    (
        "alpha-test-effect-claims-lighting",
        "an unlit effect conforming to IEffectLights, which XNA's does not",
        ALPHATEST,
        "    open class AlphaTestEffect: Effect, IEffectMatrices, IEffectFog {",
        "    open class AlphaTestEffect: Effect, IEffectMatrices, IEffectFog, IEffectLights {",
    ),
    (
        "environment-map-lighting-reads-a-field",
        "the always-on getter answering stored state instead of true",
        ENVMAP,
        "        public var LightingEnabled: Bool { true }",
        "        public var LightingEnabled: Bool { state.lightingEnabled }",
    ),

    # ---- Foundation 70: SpriteFont and DrawString -------------------------
    (
        "measure-does-not-clamp-the-first-bearing",
        "the first glyph of a line adding a negative left bearing instead of clamping it",
        FONT,
        "                if firstOfLine {\n"
        "                    left = max(left, 0)",
        "                if firstOfLine {\n"
        "                    left = min(left, 0)",
    ),
    (
        "measure-clamps-every-bearing",
        "the clamp applied to every glyph, not only the first of a line",
        FONT,
        "                var left = glyph.kerning.x\n"
        "                if firstOfLine {",
        "                var left = max(glyph.kerning.x, 0)\n"
        "                if firstOfLine {",
    ),
    (
        "measure-omits-the-inter-glyph-spacing",
        "Spacing never added, so every string measures as if spacing were zero",
        FONT,
        "                    size.X += spacing + rightBearing",
        "                    size.X += rightBearing",
    ),
    (
        "measure-omits-the-trailing-bearing",
        "the last glyph's right bearing dropped from the width",
        FONT,
        "            size.X += max(rightBearing, 0)\n"
        "            size.Y += Float(lines * lineSpacing)",
        "            size.Y += Float(lines * lineSpacing)",
    ),
    (
        "measure-does-not-clamp-the-trailing-bearing",
        "a negative trailing bearing shrinking the measured width",
        FONT,
        "            size.X += max(rightBearing, 0)\n"
        "            size.Y += Float(lines * lineSpacing)",
        "            size.X += rightBearing\n"
        "            size.Y += Float(lines * lineSpacing)",
    ),
    (
        "measure-counts-the-carriage-return",
        "'\\r' measured as a glyph instead of skipped before every other test",
        FONT,
        "                if unit == 13 { continue }          // '\\r'",
        "                if unit == 13 && false { continue } // '\\r'",
    ),
    (
        "measure-height-uses-the-glyph-bounds",
        "the height taken from the atlas rectangle rather than the cropping one",
        FONT,
        "                size.Y = max(size.Y, Float(glyph.cropping.height))",
        "                size.Y = max(size.Y, Float(glyph.glyph_bounds.height))",
    ),
    (
        "measure-forgets-the-widest-line",
        "a multi-line measurement answering only the last line's width",
        FONT,
        "            size.X = max(size.X, widest)",
        "            size.X = size.X",
    ),
    (
        "measure-does-not-add-the-line-heights",
        "every extra line costing nothing, so one line and five measure the same",
        FONT,
        "            size.Y += Float(lines * lineSpacing)",
        "            size.Y += Float(0 * lineSpacing)",
    ),
    (
        "measure-of-an-empty-string-is-not-zero",
        "an empty string measured as one empty line instead of Vector2.Zero",
        FONT,
        "            guard !units.isEmpty else { return .Zero }",
        "            guard units.count < 0 else { return .Zero }",
    ),
    (
        "character-search-misses-the-ends",
        "a binary search that never examines the first or last character",
        FONT,
        "            var low = 0\n"
        "            var high = characterMap.count - 1",
        "            var low = 1\n"
        "            var high = characterMap.count - 2",
    ),
    # `character-fallback-recurses-without-a-guard` was planted here and
    # WITHDRAWN. It removed GetIndexForCharacter's `defaultCharacter != unit`
    # guard, which matters only for a font whose DEFAULT character is itself
    # absent from the glyph table -- the one state in which the fallback
    # recurses for ever. `build-probe/f70_default.c` measures that CNA refuses
    # to build such a font ("defaultCharacter is not present in characters"),
    # and `cna_sprite_font_set_default_character` refuses the same change
    # afterwards. No route this projection has can reach the state, so no test
    # can be written that the mutation would fail. The guard stays: it is
    # XNA's, and it is the difference between reporting a character and
    # hanging.
    (
        "character-refusal-drops-its-parameter-name",
        "GetIndexForCharacter's refusal losing the ParamName XNA gives it",
        FONT,
        "                message: SpriteFont.characterNotInFontMessage(unit),\n"
        "                paramName: \"character\")",
        "                message: SpriteFont.characterNotInFontMessage(unit))",
    ),
    (
        "default-character-refusal-gains-a-parameter-name",
        "set_DefaultCharacter's refusal naming a parameter, which XNA's does not",
        FONT,
        "                    throw CNAArgumentException(\n"
        "                        message: SpriteFont.characterNotInFontMessage(value))",
        "                    throw CNAArgumentException(\n"
        "                        message: SpriteFont.characterNotInFontMessage(value),\n"
        "                        paramName: \"value\")",
    ),
    (
        "default-character-accepts-anything",
        "a fallback character the font does not have accepted instead of refused",
        FONT,
        "                guard characterMap.contains(value) else {",
        "                guard characterMap.contains(value) || true else {",
    ),
    (
        "default-character-written-before-the-test",
        "the refused fallback stored anyway, so the property changes on a throw",
        FONT,
        "            if let value {\n"
        "                guard characterMap.contains(value) else {",
        "            defaultCharacter = value\n"
        "            if let value {\n"
        "                guard characterMap.contains(value) else {",
    ),
    (
        "character-message-hex-not-padded",
        "the numeric placeholder formatted without XNA's four-digit hex width",
        FONT,
        "                    of: \"{1:x4}\", with: String(format: \"%04x\", Int(value)))",
        "                    of: \"{1:x4}\", with: String(format: \"%x\", Int(value)))",
    ),
    (
        "characters-collection-rebuilt-per-call",
        "Characters answering a fresh collection each time, so it has no identity",
        FONT,
        "            if let charactersView { return charactersView }",
        "            if let charactersView, false { return charactersView }",
    ),
    (
        "layout-change-never-reaches-the-device",
        "an assigned LineSpacing that no draw ever pushes",
        FONT,
        "            if pendingLineSpacing {",
        "            if pendingLineSpacing && false {",
    ),
    # `layout-flush-does-not-clear-its-flag` was planted here and REPLACED,
    # not scored: leaving the flag set re-pushes the SAME value on the next
    # draw, and no answer changes. The replacement crosses the two flags,
    # which does change one.
    (
        "layout-flush-crosses-its-two-flags",
        "Spacing pushed under LineSpacing's flag, so setting one alone is lost",
        FONT,
        "            if pendingSpacing {",
        "            if pendingLineSpacing {",
    ),
    (
        "draw-string-skips-the-begin-check",
        "a draw outside a begin/end pair reaching CNA instead of reporting XNA's rule",
        BATCH,
        "            guard inBeginEndPair else {\n"
        "                throw CNAInvalidOperationException(\n"
        "                    message: beginMustBeCalledBeforeDrawMessage)\n"
        "            }\n"
        "            // Every character has to be in the font",
        "            // Every character has to be in the font",
    ),
    (
        "draw-string-refuses-an-empty-string",
        "an empty string refused outside a pair, which XNA accepts",
        BATCH,
        "            let drawsAGlyph = units.contains { $0 != 13 && $0 != 10 }",
        "            let drawsAGlyph = !units.isEmpty",
    ),
    (
        "draw-string-does-not-validate-its-characters",
        "an unknown character forwarded to CNA instead of reported the way XNA does",
        BATCH,
        "            _ = try spriteFont.measure(units)",
        "            _ = units",
    ),
    # `draw-string-uniform-scale-widened-wrongly` was planted here and
    # WITHDRAWN, for Foundation 65's reason and Foundation 68's: a submitted
    # sprite is not readable back. The uniform-scale overload widens one scale
    # into `Vector2(scale, scale)`, and a mutation to `Vector2(scale, 1)`
    # produces a command CNA accepts exactly as readily -- there is no query
    # for what a batch was given, no pixel readback to see the result, and no
    # scale the route refuses. The widening is asserted by reading, not by
    # testing, and this records that it is.

    # ---- Foundation 71: System.Text.StringBuilder -------------------------
    (
        "builder-length-counts-characters",
        "Length counting Swift Characters instead of UTF-16 code units",
        BUILDER,
        "    public var Length: Int32 { Int32(units.count) }",
        "    public var Length: Int32 { Int32(String(decoding: units, as: UTF16.self).count) }",
    ),
    (
        "builder-indexer-getter-throws-the-setter-s-exception",
        "get_Chars raising ArgumentOutOfRangeException where XNA raises a bare IndexOutOfRangeException",
        BUILDER,
        "            throw CNAIndexOutOfRangeException()",
        "            throw CNAArgumentOutOfRangeException(paramName: \"index\")",
    ),
    (
        "builder-indexer-setter-throws-the-getter-s-exception",
        "set_Chars raising IndexOutOfRangeException where XNA raises ArgumentOutOfRangeException",
        BUILDER,
        "    public func SetItem(_ index: Int32, _ value: UInt16) throws {\n"
        "        guard index >= 0, index < Length else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"index\", message: CNAStringBuilder.indexOutOfRange)",
        "    public func SetItem(_ index: Int32, _ value: UInt16) throws {\n"
        "        guard index >= 0, index < Length else {\n"
        "            throw CNAIndexOutOfRangeException()",
    ),
    (
        "builder-set-length-does-not-pad",
        "growing the length leaving the new units unwritten instead of NUL",
        BUILDER,
        "            units.append(contentsOf: repeatElement(0, count: wanted - units.count))",
        "            units.append(contentsOf: repeatElement(32, count: wanted - units.count))",
    ),
    (
        "builder-set-length-refusals-transposed",
        "set_Length reporting the ceiling message for a negative value and vice versa",
        BUILDER,
        "                paramName: \"value\", message: CNAStringBuilder.negativeLength)\n"
        "        }\n"
        "        guard value <= maxCapacity else {",
        "                paramName: \"value\", message: CNAStringBuilder.smallCapacity)\n"
        "        }\n"
        "        guard value <= maxCapacity else {",
    ),
    (
        "builder-append-ignores-max-capacity",
        "the shared growth guard removed, so a builder grows past MaxCapacity",
        BUILDER,
        "        guard required <= Int(maxCapacity) else {",
        "        guard required <= Int(maxCapacity) || true else {",
    ),
    # `builder-repeat-count-written-before-testing` was planted here and
    # REPLACED, not scored: it moved the append before the guard, and with a
    # NEGATIVE count there is nothing to append -- `max(0, -1)` writes zero
    # elements and the guard still throws, so no answer changes. The
    # replacement refuses a count XNA accepts, which does.
    (
        "builder-repeat-count-refuses-zero",
        "Append(char, 0) refused, though XNA's `>= 0` accepts it and writes nothing",
        BUILDER,
        "        guard repeatCount >= 0 else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"repeatCount\", message: CNAStringBuilder.negativeCount)",
        "        guard repeatCount > 0 else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"repeatCount\", message: CNAStringBuilder.negativeCount)",
    ),
    (
        "builder-append-line-uses-the-host-separator",
        "AppendLine emitting the host's newline instead of the Windows CLR's",
        BUILDER,
        "    internal static let newLine = \"\\r\\n\"",
        "    internal static let newLine = \"\\n\"",
    ),
    (
        "builder-insert-refuses-the-end",
        "Insert at Length refused, though XNA's unsigned bound accepts it",
        BUILDER,
        "        guard index >= 0, index <= Length else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"index\", message: CNAStringBuilder.indexOutOfRange)\n"
        "        }\n"
        "        let inserted = Array(value.utf16)",
        "        guard index >= 0, index < Length else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"index\", message: CNAStringBuilder.indexOutOfRange)\n"
        "        }\n"
        "        let inserted = Array(value.utf16)",
    ),
    (
        "builder-remove-names-start-index-for-its-range",
        "Remove's range refusal naming startIndex, where XNA's names index",
        BUILDER,
        "        guard length <= Length - startIndex else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"index\", message: CNAStringBuilder.indexOutOfRange)",
        "        guard length <= Length - startIndex else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"startIndex\", message: CNAStringBuilder.indexOutOfRange)",
    ),
    (
        "builder-clear-drops-the-capacity",
        "Clear rebuilding the store, so the capacity it exists to keep is lost",
        BUILDER,
        "        units.removeAll(keepingCapacity: true)\n"
        "        return self",
        "        units.removeAll(keepingCapacity: true)\n"
        "        capacity = CNAStringBuilder.defaultCapacity\n"
        "        return self",
    ),
    (
        "builder-to-string-range-refusals-reordered",
        "ToString testing its length before its start index, so a doubly wrong call misreports",
        BUILDER,
        "        guard startIndex >= 0 else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"startIndex\", message: CNAStringBuilder.startIndex)\n"
        "        }\n"
        "        guard startIndex <= Length else {",
        "        guard length >= 0 else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"length\", message: CNAStringBuilder.negativeLength)\n"
        "        }\n"
        "        guard startIndex >= 0 else {\n"
        "            throw CNAArgumentOutOfRangeException(\n"
        "                paramName: \"startIndex\", message: CNAStringBuilder.startIndex)\n"
        "        }\n"
        "        guard startIndex <= Length else {",
    ),
    (
        "builder-zero-capacity-ignores-the-ceiling",
        "a zero capacity taking sixteen even when MaxCapacity is smaller",
        BUILDER,
        "            ? min(CNAStringBuilder.defaultCapacity, maxCapacity)",
        "            ? CNAStringBuilder.defaultCapacity",
    ),
    (
        "builder-must-be-positive-not-formatted",
        "the one formatted mscorlib message left with its placeholder unfilled",
        BUILDER,
        "                message: CNAStringBuilder.mustBePositive\n"
        "                    .replacingOccurrences(of: \"{0}\", with: \"capacity\"))",
        "                message: CNAStringBuilder.mustBePositive)",
    ),
    (
        "measure-string-builder-reads-a-copy",
        "MeasureString(StringBuilder) measuring a rendered String, so code units are lost",
        FONT,
        "            try measure(text.codeUnits)",
        "            try measure(Array(text.ToString().utf16).filter { $0 < 0xD800 })",
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


# A mutated suite that HANGS is still a suite that does not pass, but without a
# deadline it stalls the whole run: `from-type-size-test-reads-the-wrong-size`
# inflates a registered vertex size by four, and the test binary it produces
# blocks instead of failing. One such mutation held a 278-mutation run
# indefinitely, which is worse than a survivor -- a survivor is at least
# reported.
#
# The deadline is generous on purpose. It is not a performance budget; it is
# the line between "slow" and "never", and a mutation that trips it is scored
# as caught-by-hang rather than silently as caught, because the two are
# different facts about the projection.
TEST_TIMEOUT_SECONDS = 600


def run_tests(swift_test: str) -> tuple[int, bool]:
    """(exit status, whether it ran out of time)."""
    try:
        result = subprocess.run(
            [swift_test], cwd=ROOT, text=True, capture_output=True,
            timeout=TEST_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        # The child is killed by `subprocess.run`, but the test BINARY it
        # spawned is not its process group's only member and outlives it.
        subprocess.run(["pkill", "-9", "-f", "CNAPackageTests.xctest"],
                       capture_output=True)
        return 1, True
    return result.returncode, False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swift-test", default="swift-test")
    # Running one milestone's own mutations, while the STALENESS check below
    # still runs over all of them.
    #
    # The full run is what the handoff repeats; a milestone that has just
    # written twenty-seven of them needs to see those twenty-seven fail and
    # be fixed, and paying eighty minutes per iteration to learn it is how a
    # mutation ends up merged unrun. The filter narrows only which mutations
    # are PLANTED -- every site is still checked for staleness, so a selective
    # run cannot hide a mutation whose site has drifted away.
    # Auditing the tree for a mutation someone committed.
    #
    # A mutation is applied to the WORKING TREE while its test runs, so
    # anything that reads the tree during a run sees it -- and `git add -A`
    # during a run commits it. That is not hypothetical: this harness's own
    # `texture-size-limit-not-checked` reached a commit that way, weakening a
    # profile bound by four, and it was found by accident when the run was
    # killed and left the file's *repair* as the visible diff.
    #
    # "Do not commit during a run" is a rule, and rules of that shape get
    # broken. This is the mechanical version, and it is cheap: every
    # mutation's replacement text is a string this file already holds.
    parser.add_argument(
        "--audit-tree", action="store_true",
        help="report any mutation's replacement text present in the working "
             "tree, and change nothing")
    parser.add_argument(
        "--only", default=None,
        help="plant only the mutations whose name contains one of these "
             "comma-separated substrings")
    args = parser.parse_args()

    if args.audit_tree:
        planted = []
        for name, _description, path, old_text, new_text in MUTATIONS:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            # The replacement present AND the original absent is what
            # distinguishes a planted mutation from a replacement string that
            # merely happens to occur -- several are substrings of ordinary
            # code.
            if new_text in text and old_text not in text:
                planted.append((name, path))
        print(f"PROJECTION_MUTATION_TREE_AUDIT={len(MUTATIONS)} "
              f"PLANTED={len(planted)}")
        for name, path in planted:
            print(f"  PLANTED {name}: {path} holds this mutation's replacement "
                  "text and not its original")
        return 1 if planted else 0

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

    # Derived from MUTATIONS rather than listed beside it. The list used to be
    # written out by hand and drifted the moment Foundation 60 added mutations
    # in three new files: the run died on a KeyError instead of reporting a
    # stale site, which is the one failure this pre-check exists to avoid. A
    # file with no mutation does not need reading, and a file with one cannot
    # be forgotten.
    originals = {path: path.read_text(encoding="utf-8")
                 for path in {item[2] for item in MUTATIONS}}

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

    baseline, baseline_hung = run_tests(args.swift_test)
    if baseline != 0:
        print("PROJECTION_MUTATION_BASELINE="
              + ("HUNG — the unmutated tree did not finish in "
                 f"{TEST_TIMEOUT_SECONDS}s" if baseline_hung
                 else "RED — the unmutated tree already fails"))
        return 1

    wanted = None if args.only is None else [
        part for part in args.only.split(",") if part
    ]
    selected = [
        item for item in MUTATIONS
        if wanted is None or any(part in item[0] for part in wanted)
    ]
    if args.only is not None and not selected:
        print(f"PROJECTION_MUTATIONS=NONE no mutation name contains {args.only!r}")
        return 1

    survivors: list[str] = []
    for name, description, path, old, new in selected:
        text = originals[path]
        if text.count(old) != 1:
            survivors.append(
                f"{name}: the mutation site occurs {text.count(old)} times, not once")
            continue
        mutated = text.replace(old, new)
        try:
            path.write_text(mutated, encoding="utf-8")
            code, hung = run_tests(args.swift_test)
        finally:
            # Restore ONLY what this harness wrote.
            #
            # `originals` is a snapshot taken before the first mutation, and
            # restoring from it unconditionally overwrites anything that
            # changed the file meanwhile -- which is not hypothetical: an edit
            # made to a mutated file during a run was silently reverted, and
            # the loss was noticed only because the next build failed on a
            # mutation's own text. The tree lock stops a second HARNESS; it
            # cannot stop an editor, and this is the part that can.
            #
            # A file that no longer holds exactly what was written is left
            # alone and reported. Losing a mutation's score is recoverable;
            # losing someone's work is not.
            collided = path.read_text(encoding="utf-8") != mutated
            if not collided:
                path.write_text(text, encoding="utf-8")
        if collided:
            print(
                f"PROJECTION_MUTATION_COLLISION={name}\n"
                f"  {path} changed underneath the run and was NOT restored.\n"
                "  It still holds whatever overwrote the mutation, plus the\n"
                "  mutation itself. This harness's snapshot was discarded\n"
                "  rather than written over the change; recover the file by\n"
                "  hand and re-run.")
            return 1
        status = "HUNG" if hung else ("CAUGHT" if code != 0 else "SURVIVED")
        print(f"{status:9} {name:34} {description}")
        if code == 0:
            survivors.append(f"{name}: {description}")

    for path, text in originals.items():
        if path.read_text(encoding="utf-8") != text:
            survivors.append(f"{path} was not restored")

    scope = "" if args.only is None else f" SELECTED={args.only!r}"
    print(f"PROJECTION_MUTATIONS={len(selected)} "
          f"CAUGHT={len(selected) - len(survivors)} SURVIVORS={len(survivors)}"
          f"{scope} DECLARED={len(MUTATIONS)}")
    for survivor in survivors:
        print(f"  SURVIVOR {survivor}")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
