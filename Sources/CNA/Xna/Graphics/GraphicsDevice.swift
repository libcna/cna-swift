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

        internal func validatedHandle(_ operation: String) throws -> UInt64 {
            try runtime.validateGeneration(generation)
            try runtime.validateBorrowed(epoch: callbackEpoch, operation: operation)
            return handle
        }

        internal var runtimeState: RuntimeState { runtime }
    }
}
