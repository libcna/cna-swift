// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework.Graphics {
    public enum SpriteSortMode: UInt32 {
        case Deferred = 0
        case Immediate = 1
        case Texture = 2
        case BackToFront = 3
        case FrontToBack = 4
    }

    public struct SpriteEffects: OptionSet {
        public let rawValue: UInt32
        public init(rawValue: UInt32) { self.rawValue = rawValue }

        public static let None = SpriteEffects([])
        public static let FlipHorizontally = SpriteEffects(rawValue: 1)
        public static let FlipVertically = SpriteEffects(rawValue: 2)
    }

    public final class SpriteBatch: RuntimeOwnedChild {
        private let storage: NativeHandleStorage

        public init(graphicsDevice: GraphicsDevice) throws {
            let deviceHandle = try graphicsDevice.validatedHandle("SpriteBatch.init")
            let runtime = graphicsDevice.runtimeState
            var handle: UInt64 = 0
            try runtime.functions.check(
                runtime.functions.spriteBatchCreate(deviceHandle, &handle),
                operation: "cna_sprite_batch_create"
            )
            storage = NativeHandleStorage(
                handle: handle,
                typeName: "SpriteBatch",
                ownership: .owned,
                runtime: runtime,
                destroy: runtime.functions.spriteBatchDestroy
            )
            runtime.register(self)
        }

        public func Begin() throws {
            let handle = try storage.validatedHandle("SpriteBatch.Begin")
            var info = CNASwift_SpriteBatchBeginInfo()
            info.struct_size = UInt32(MemoryLayout<CNASwift_SpriteBatchBeginInfo>.size)
            info.struct_version = 1
            info.sort_mode = SpriteSortMode.Deferred.rawValue
            try storage.runtime.functions.check(
                storage.runtime.functions.spriteBatchBegin(handle, &info),
                operation: "cna_sprite_batch_begin"
            )
        }

        public func Draw(
            _ texture: Texture2D,
            position: Microsoft.Xna.Framework.Vector2,
            color: Microsoft.Xna.Framework.Color
        ) throws {
            try Draw(
                texture,
                position: position,
                sourceRectangle: nil,
                color: color,
                rotation: 0,
                origin: .Zero,
                scale: 1,
                effects: .None,
                layerDepth: 0
            )
        }

        public func Draw(
            _ texture: Texture2D,
            position: Microsoft.Xna.Framework.Vector2,
            sourceRectangle: Microsoft.Xna.Framework.Rectangle?,
            color: Microsoft.Xna.Framework.Color,
            rotation: Float,
            origin: Microsoft.Xna.Framework.Vector2,
            scale: Float,
            effects: SpriteEffects,
            layerDepth: Float
        ) throws {
            let batchHandle = try storage.validatedHandle("SpriteBatch.Draw")
            let textureHandle = try texture.validatedHandle("SpriteBatch.Draw texture")
            guard texture.runtimeState === storage.runtime else {
                throw CNAError.staleRuntimeGeneration(expected: storage.generation, actual: texture.runtimeState.generation)
            }
            var command = CNASwift_SpriteScaledCommand()
            command.struct_size = UInt32(MemoryLayout<CNASwift_SpriteScaledCommand>.size)
            command.struct_version = 1
            command.texture = textureHandle
            command.position = CNASwift_Vector2(x: position.X, y: position.Y)
            if let sourceRectangle {
                command.source = CNASwift_Rectangle(
                    x: sourceRectangle.X,
                    y: sourceRectangle.Y,
                    width: sourceRectangle.Width,
                    height: sourceRectangle.Height
                )
            }
            command.color = color.native
            command.rotation = rotation
            command.origin = CNASwift_Vector2(x: origin.X, y: origin.Y)
            command.scale = CNASwift_Vector2(x: scale, y: scale)
            command.effects = effects.rawValue
            command.layer_depth = layerDepth
            try storage.runtime.functions.check(
                storage.runtime.functions.spriteBatchSubmitScaled(batchHandle, &command, 1),
                operation: "cna_sprite_batch_submit_scaled_many"
            )
        }

        public func End() throws {
            let handle = try storage.validatedHandle("SpriteBatch.End")
            try storage.runtime.functions.check(
                storage.runtime.functions.spriteBatchEnd(handle),
                operation: "cna_sprite_batch_end"
            )
        }

        public func Dispose() throws { try storage.dispose(operation: "SpriteBatch.Dispose") }

        internal var runtimeObjectIsDisposed: Bool { storage.isDisposed }
        internal func disposeFromParent() throws { try Dispose() }
    }
}
