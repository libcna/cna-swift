// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework.Graphics {
    /// Callback-scoped facade over the Game-owned graphics device.
    public final class GraphicsDevice {
        private let handle: UInt64
        private let runtime: RuntimeState
        private let generation: UInt64
        private let callbackEpoch: UInt64

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

        internal func validatedHandle(_ operation: String) throws -> UInt64 {
            try runtime.validateGeneration(generation)
            try runtime.validateBorrowed(epoch: callbackEpoch, operation: operation)
            return handle
        }

        internal var runtimeState: RuntimeState { runtime }
    }
}
