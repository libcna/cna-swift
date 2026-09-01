// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework.Graphics {
    /// Callback-scoped facade over the Game-owned graphics device.
    ///
    /// `open`, not `final`: XNA leaves the class derivable. Construction stays
    /// `private`, exactly as XNA's own accessible constructor is not yet
    /// projected, so the class is formally derivable and not yet constructible
    /// from outside — which is the honest state of a runtime-partial type
    /// rather than a strengthened one.
    open class GraphicsDevice {
        private let handle: UInt64
        private let runtime: RuntimeState
        private let generation: UInt64
        private let callbackEpoch: UInt64

        /// Wraps a device handle the graphics device manager handed out.
        ///
        /// Both this and `borrow(from:)` produce the same callback-scoped
        /// facade; they differ only in which route supplied the handle.
        internal convenience init(borrowedHandle: UInt64, runtime: RuntimeState) {
            self.init(handle: borrowedHandle, runtime: runtime)
        }

        private init(handle: UInt64, runtime: RuntimeState) {
            self.handle = handle
            self.runtime = runtime
            generation = runtime.generation
            callbackEpoch = runtime.callbackEpoch
        }

        internal static func borrow(from runtime: RuntimeState) throws -> GraphicsDevice {
            try runtime.validateBorrowed(epoch: runtime.callbackEpoch, operation: "Game.GraphicsDevice")
            var handle: UInt64 = 0
            try runtime.functions.check(
                runtime.functions.gameGetGraphicsDevice(runtime.gameHandle, &handle),
                operation: "cna_game_get_graphics_device"
            )
            return GraphicsDevice(handle: handle, runtime: runtime)
        }

        public var Viewport: Microsoft.Xna.Framework.Graphics.Viewport {
            get throws {
                let handle = try validatedHandle("GraphicsDevice.Viewport")
                var native = CNASwift_Viewport()
                try runtime.functions.check(
                    runtime.functions.graphicsDeviceGetViewport(handle, &native),
                    operation: "cna_graphics_device_get_viewport"
                )
                return Microsoft.Xna.Framework.Graphics.Viewport(native: native)
            }
        }

        /// `GraphicsDevice.set_Viewport(Viewport value)`.
        ///
        /// A writer method, not a Swift `set`: the CLR setter is fallible —
        /// `Helpers.CheckDisposed` and then a push that can raise
        /// `ArgumentException` — and Swift has no throwing setter. This is the
        /// projection of the CLR setter accessor and not a new XNA member; the
        /// verifier has been asking for it by name since the reader landed.
        public func SetViewport(
            _ value: Microsoft.Xna.Framework.Graphics.Viewport
        ) throws {
            let handle = try validatedHandle("GraphicsDevice.Viewport")
            var native = CNASwift_Viewport()
            native.x = value.X
            native.y = value.Y
            native.width = value.Width
            native.height = value.Height
            native.min_depth = value.MinDepth
            native.max_depth = value.MaxDepth
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetViewport(handle, native),
                operation: "cna_graphics_device_set_viewport")
        }

        /// `GraphicsDevice.ScissorRectangle`.
        ///
        /// Both accessors are `IL_DIRECT_THROW`, so the reader throws and the
        /// writer is a throwing `SetScissorRectangle` — the same shape
        /// `Viewport` has, for the same reason.
        public var ScissorRectangle: Microsoft.Xna.Framework.Rectangle {
            get throws {
                let handle = try validatedHandle("GraphicsDevice.ScissorRectangle")
                var native = CNASwift_Rectangle()
                try runtime.functions.check(
                    runtime.functions.graphicsDeviceGetScissorRectangle(handle, &native),
                    operation: "cna_graphics_device_get_scissor_rectangle")
                return Microsoft.Xna.Framework.Rectangle(
                    native.x, native.y, native.width, native.height)
            }
        }

        /// `GraphicsDevice.set_ScissorRectangle(Rectangle value)`.
        public func SetScissorRectangle(
            _ value: Microsoft.Xna.Framework.Rectangle
        ) throws {
            let handle = try validatedHandle("GraphicsDevice.ScissorRectangle")
            var native = CNASwift_Rectangle()
            native.x = value.X
            native.y = value.Y
            native.width = value.Width
            native.height = value.Height
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetScissorRectangle(handle, native),
                operation: "cna_graphics_device_set_scissor_rectangle")
        }

        /// `GraphicsDevice.GraphicsDeviceStatus`.
        ///
        /// `IL_DIRECT_THROW` and no setter, so a throwing reader only. CNA and
        /// XNA agree on all three values — `Normal` 0, `Lost` 1, `NotReset` 2 —
        /// and the conversion is still an explicit map: eight of the nine state
        /// enums agreed in Foundation 45 too, and the ninth did not.
        public var GraphicsDeviceStatus: Microsoft.Xna.Framework.Graphics.GraphicsDeviceStatus {
            get throws {
                let handle = try validatedHandle("GraphicsDevice.GraphicsDeviceStatus")
                var native: UInt32 = 0
                try runtime.functions.check(
                    runtime.functions.graphicsDeviceGetStatus(handle, &native),
                    operation: "cna_graphics_device_get_status")
                switch native {
                case 0: return .Normal
                case 1: return .Lost
                case 2: return .NotReset
                default:
                    throw CNAError.producerInvariant(
                        "cna_graphics_device_get_status answered \(native), which is "
                        + "outside the three values GraphicsDeviceStatus declares")
                }
            }
        }

        public func Clear(_ color: Microsoft.Xna.Framework.Color) throws {
            let handle = try validatedHandle("GraphicsDevice.Clear")
            let scale: Float = 1 / 255
            try runtime.functions.check(
                runtime.functions.graphicsDeviceClearRGBA(
                    handle,
                    Float(color.R) * scale,
                    Float(color.G) * scale,
                    Float(color.B) * scale,
                    Float(color.A) * scale
                ),
                operation: "cna_graphics_device_clear_rgba"
            )
        }

        /// `GraphicsDevice.SetRenderTarget(RenderTarget2D renderTarget)`.
        ///
        /// A nil target restores the backbuffer, which is what XNA's null
        /// argument does and what `CNA_INVALID_HANDLE` means to
        /// `cna_graphics_device_set_render_target2d`.
        public func SetRenderTarget(
            _ renderTarget: RenderTarget2D?
        ) throws {
            let deviceHandle = try validatedHandle("GraphicsDevice.SetRenderTarget")
            let targetHandle = try renderTarget.map {
                try $0.validatedHandle("GraphicsDevice.SetRenderTarget")
            } ?? 0
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetRenderTarget2D(deviceHandle, targetHandle),
                operation: "cna_graphics_device_set_render_target2d"
            )
        }

        // ------------------------------------------------------------------
        // Device state.
        //
        // The cache lives on `RuntimeState`, not here: this facade is built
        // fresh on every access because CNA's device handle is a per-callback
        // capability token rather than the device's identity, measured with
        // `build-probe/f42b_identity.c`. `RuntimeState` is the object with the
        // device's lifetime.
        // ------------------------------------------------------------------

        /// `GraphicsDevice.BlendState`.
        ///
        /// `ldfld cachedBlendState; ret` — a bare field read with no failure
        /// path, so the reader does not throw, and Optional because the field
        /// is null until something assigns one.
        public var BlendState: BlendState? { runtime.cachedBlendState }

        /// `GraphicsDevice.set_BlendState(BlendState value)`.
        ///
        /// The IL, in order: refuse null; return when the value is the same
        /// instance **and** the dirty flag is clear; end an active effect pass
        /// whose state flags include bit 1; `value.Apply(this)`; cache the
        /// instance; copy `cachedBlendFactor` and `cachedMultiSampleMask` out
        /// of it; clear the flag. There is no effect pass here yet, so that
        /// step has nothing to end.
        public func SetBlendState(_ value: BlendState?) throws {
            guard let value else {
                throw CNAArgumentNullException(
                    paramName: "value", message: GraphicsDevice.nullNotAllowedMessage)
            }
            if value === runtime.cachedBlendState && !runtime.blendStateDirty { return }
            let handle = try validatedHandle("GraphicsDevice.BlendState")
            try value.attach(to: self)
            var native = value.nativeDescriptor()
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetBlendState(handle, &native),
                operation: "cna_graphics_device_set_blend_state")
            runtime.cachedBlendState = value
            runtime.cachedBlendFactor = value.BlendFactor
            runtime.cachedMultiSampleMask = value.MultiSampleMask
            runtime.blendStateDirty = false
        }

        /// `GraphicsDevice.DepthStencilState`.
        public var DepthStencilState: DepthStencilState? {
            runtime.cachedDepthStencilState
        }

        /// `GraphicsDevice.set_DepthStencilState(DepthStencilState value)`.
        ///
        /// The same shape as `set_BlendState`, with its own dirty flag, its
        /// own effect-state bit (2), and `cachedReferenceStencil` as the one
        /// value it copies out.
        public func SetDepthStencilState(_ value: DepthStencilState?) throws {
            guard let value else {
                throw CNAArgumentNullException(
                    paramName: "value", message: GraphicsDevice.nullNotAllowedMessage)
            }
            if value === runtime.cachedDepthStencilState
                && !runtime.depthStencilStateDirty { return }
            let handle = try validatedHandle("GraphicsDevice.DepthStencilState")
            try value.attach(to: self)
            var native = value.nativeDescriptor()
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetDepthStencilState(handle, &native),
                operation: "cna_graphics_device_set_depth_stencil_state")
            runtime.cachedDepthStencilState = value
            runtime.cachedReferenceStencil = value.ReferenceStencil
            runtime.depthStencilStateDirty = false
        }

        /// `GraphicsDevice.RasterizerState`.
        public var RasterizerState: RasterizerState? { runtime.cachedRasterizerState }

        /// `GraphicsDevice.set_RasterizerState(RasterizerState value)`.
        ///
        /// **Not symmetric with the other two.** Its early-out is `beq` alone —
        /// the same instance always returns, with no dirty flag to force a
        /// re-apply — and it copies nothing out of the state. Writing all three
        /// from one template would be wrong in two different ways at once.
        public func SetRasterizerState(_ value: RasterizerState?) throws {
            guard let value else {
                throw CNAArgumentNullException(
                    paramName: "value", message: GraphicsDevice.nullNotAllowedMessage)
            }
            if value === runtime.cachedRasterizerState { return }
            let handle = try validatedHandle("GraphicsDevice.RasterizerState")
            try value.attach(to: self)
            var native = value.nativeDescriptor()
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetRasterizerState(handle, &native),
                operation: "cna_graphics_device_set_rasterizer_state")
            runtime.cachedRasterizerState = value
        }

        /// `GraphicsDevice.SamplerStates`.
        ///
        /// `ldfld pSamplerState; ret` — a bare field read with no failure path
        /// and no setter, so a plain non-throwing reader.
        ///
        /// **Optional**, and that is proven rather than defensive: the pinned
        /// verdict is `PROVEN_NULLABLE_SUCCESS` on the evidence that *no
        /// constructor of `GraphicsDevice` assigns `pSamplerState`* — the
        /// collection is built when the device is created, not when the object
        /// is, so a device that has not created its D3D device yet answers
        /// null. The analogue here is a facade whose handle no longer
        /// validates: a stale generation, or a read outside the callback that
        /// produced it.
        ///
        /// XNA builds it with offset `0`; it lives on the runtime here, for
        /// the reason recorded there.
        public var SamplerStates: SamplerStateCollection? {
            guard (try? validatedHandle("GraphicsDevice.SamplerStates")) != nil else {
                return nil
            }
            return runtime.samplerStates(for: self, vertex: false)
        }

        /// `GraphicsDevice.VertexSamplerStates`, built with offset `0x101` —
        /// `D3DVERTEXTEXTURESAMPLER0`. Optional on the same proof.
        public var VertexSamplerStates: SamplerStateCollection? {
            guard (try? validatedHandle("GraphicsDevice.VertexSamplerStates")) != nil else {
                return nil
            }
            return runtime.samplerStates(for: self, vertex: true)
        }

        /// `GraphicsDevice.BlendFactor`.
        ///
        /// `ldflda cachedBlendFactor; ldobj; ret` — the same field
        /// `set_BlendState` copies out of the state it accepts, read directly.
        /// No failure path, so the reader does not throw.
        public var BlendFactor: Microsoft.Xna.Framework.Color {
            runtime.cachedBlendFactor
        }

        /// `GraphicsDevice.set_BlendFactor(Color value)`.
        ///
        /// A throwing writer method: the recorded verdict is
        /// `IL_REACHABLE_THROW` with `ObjectDisposedException`, because the
        /// setter opens with `Helpers.CheckDisposed(this, pComPtr)` and then
        /// pushes to the device. Reproduced with the same guard —
        /// `validatedHandle` raises the projected class — and CNA's own
        /// `cna_graphics_device_set_blend_factor`.
        public func SetBlendFactor(_ value: Microsoft.Xna.Framework.Color) throws {
            let handle = try validatedHandle("GraphicsDevice.BlendFactor")
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetBlendFactor(
                    handle,
                    CNASwift_Color(r: value.R, g: value.G, b: value.B, a: value.A)),
                operation: "cna_graphics_device_set_blend_factor")
            runtime.cachedBlendFactor = value
        }

        /// `GraphicsDevice.MultiSampleMask`, the other value `set_BlendState`
        /// copies out.
        public var MultiSampleMask: Int32 { runtime.cachedMultiSampleMask }

        /// `GraphicsDevice.set_MultiSampleMask(Int32 value)`.
        public func SetMultiSampleMask(_ value: Int32) throws {
            let handle = try validatedHandle("GraphicsDevice.MultiSampleMask")
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetMultiSampleMask(handle, value),
                operation: "cna_graphics_device_set_multi_sample_mask")
            runtime.cachedMultiSampleMask = value
        }

        /// `GraphicsDevice.ReferenceStencil`, the value
        /// `set_DepthStencilState` copies out.
        public var ReferenceStencil: Int32 { runtime.cachedReferenceStencil }

        /// `GraphicsDevice.set_ReferenceStencil(Int32 value)`.
        public func SetReferenceStencil(_ value: Int32) throws {
            let handle = try validatedHandle("GraphicsDevice.ReferenceStencil")
            try runtime.functions.check(
                runtime.functions.graphicsDeviceSetReferenceStencil(handle, value),
                operation: "cna_graphics_device_set_reference_stencil")
            runtime.cachedReferenceStencil = value
        }

        /// The exact `NullNotAllowed` message, read out of
        /// `Microsoft.Xna.Framework.dll`'s own resource table. All three
        /// setters raise `ArgumentNullException("value", NullNotAllowed)` —
        /// paramName **first**, because that overload is
        /// `.ctor(String paramName, String message)`.
        internal static let nullNotAllowedMessage =
            "This method does not accept null for this parameter."

        internal func validatedHandle(_ operation: String) throws -> UInt64 {
            try runtime.validateGeneration(generation)
            try runtime.validateBorrowed(epoch: callbackEpoch, operation: operation)
            return handle
        }

        internal var runtimeState: RuntimeState { runtime }
    }
}
