// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework {
    /// `open`, not `final`: XNA leaves the class derivable and its public
    /// `GraphicsDeviceManager(Game)` constructor is projected, so a consumer
    /// can genuinely derive from this one.
    open class GraphicsDeviceManager: RuntimeOwnedChild {
        private weak var game: Microsoft.Xna.Framework.Game?
        private let storage: NativeHandleStorage

        public init(game: Microsoft.Xna.Framework.Game) throws {
            let runtime = game.runtime
            try runtime.validateGeneration(runtime.generation)
            try runtime.owner.validate("GraphicsDeviceManager.init")
            var handle: UInt64 = 0
            try runtime.functions.check(
                runtime.functions.graphicsManagerCreate(runtime.gameHandle, &handle),
                operation: "cna_graphics_device_manager_create"
            )
            self.game = game
            storage = NativeHandleStorage(
                handle: handle,
                typeName: "GraphicsDeviceManager",
                ownership: .owned,
                runtime: runtime,
                destroy: runtime.functions.graphicsManagerDestroy
            )
            runtime.register(self)
        }

        public var GraphicsDevice: Microsoft.Xna.Framework.Graphics.GraphicsDevice {
            get throws {
                guard let game else { throw CNAError.disposedObject("GraphicsDeviceManager.Game") }
                return try game.GraphicsDevice
            }
        }

        public func ApplyChanges() throws {
            let handle = try storage.validatedHandle("GraphicsDeviceManager.ApplyChanges")
            try storage.runtime.functions.check(
                storage.runtime.functions.graphicsManagerApplyChanges(handle),
                operation: "cna_graphics_device_manager_apply_changes"
            )
        }

        public func Dispose() throws {
            try storage.dispose(operation: "GraphicsDeviceManager.Dispose")
        }

        internal var runtimeObjectIsDisposed: Bool { storage.isDisposed }
        internal func disposeFromParent() throws { try Dispose() }
    }
}
