// SPDX-License-Identifier: MIT

import CNAShim
import Foundation

extension Microsoft.Xna.Framework.Graphics {
    /// The `Microsoft.Xna.Framework.Graphics.Texture2D` projection.
    ///
    /// `open`, not `final`: XNA leaves the class derivable and
    /// `RenderTarget2D` is the derived class that proves it. Its native
    /// storage, its disposal and its whole `GraphicsResource` surface come
    /// from the base, so a subclass inherits one handle with one owner and one
    /// destruction path rather than acquiring a second of each.
    open class Texture2D: Texture {
        public let Width: Int32
        public let Height: Int32

        // `get_Bounds` is
        //     ldloca V_0; ldc.i4.0; ldc.i4.0;
        //     ldfld _width; ldfld _height;
        //     call Rectangle::.ctor(int32,int32,int32,int32); ldloc.0; ret
        // -- a rectangle at the origin over the texture's own dimensions, with
        // no branch, no call out and no failure path. Both dimensions are
        // already CNA members read once from `cna_texture2d_get_info`, so this
        // composes them exactly as XNA does and reaches no native surface of
        // its own.
        public var Bounds: Microsoft.Xna.Framework.Rectangle {
            Microsoft.Xna.Framework.Rectangle(0, 0, Width, Height)
        }

        /// The designated initializer every concrete 2D texture uses.
        ///
        /// The destroy route is a parameter rather than a constant, because a
        /// `RenderTarget2D` is released through `cna_render_target_destroy`
        /// and an ordinary texture through `cna_texture2d_destroy`. One
        /// storage, one owner, one route — chosen by the concrete class.
        internal init(
            handle: UInt64,
            runtime: RuntimeState,
            device: GraphicsDevice?,
            typeName: String,
            destroy: @escaping NativeDestroyRoute,
            width: Int32,
            height: Int32,
            levelCount: Int32,
            format: SurfaceFormat
        ) {
            Width = width
            Height = height
            super.init(
                storage: NativeHandleStorage(
                    handle: handle,
                    typeName: typeName,
                    ownership: .owned,
                    runtime: runtime,
                    destroy: destroy
                ),
                device: device,
                levelCount: levelCount,
                format: format
            )
            runtime.register(self)
        }

        public static func FromStream(
            _ graphicsDevice: GraphicsDevice,
            stream: InputStream
        ) throws -> Texture2D {
            let deviceHandle = try graphicsDevice.validatedHandle("Texture2D.FromStream")
            var encoded = Data()
            if stream.streamStatus == .notOpen { stream.open() }
            var buffer = [UInt8](repeating: 0, count: 16_384)
            while true {
                let count = stream.read(&buffer, maxLength: buffer.count)
                if count == 0 { break }
                if count < 0 {
                    throw CNAError.streamFailure(stream.streamError?.localizedDescription ?? "unknown read error")
                }
                encoded.append(buffer, count: count)
            }
            guard !encoded.isEmpty else { throw CNAError.streamFailure("encoded image stream is empty") }

            let runtime = graphicsDevice.runtimeState
            var handle: UInt64 = 0
            let result = encoded.withUnsafeBytes { rawBuffer -> UInt32 in
                runtime.functions.textureCreateMemory(
                    deviceHandle,
                    rawBuffer.bindMemory(to: UInt8.self).baseAddress,
                    UInt64(rawBuffer.count),
                    nil,
                    &handle
                )
            }
            try runtime.functions.check(result, operation: "cna_texture2d_create_from_encoded_memory")

            var info = CNASwift_Texture2DInfo()
            info.struct_size = UInt32(MemoryLayout<CNASwift_Texture2DInfo>.size)
            info.struct_version = 1
            do {
                try runtime.functions.check(
                    runtime.functions.textureGetInfo(handle, &info),
                    operation: "cna_texture2d_get_info"
                )
            } catch {
                _ = runtime.functions.textureDestroy(handle)
                throw error
            }
            guard info.width <= UInt32(Int32.max), info.height <= UInt32(Int32.max) else {
                _ = runtime.functions.textureDestroy(handle)
                throw CNAError.nativeFailure(operation: "Texture2D dimensions", result: 10, message: "dimensions exceed XNA Int32 range")
            }
            let common: (levelCount: Int32, format: SurfaceFormat)
            do {
                common = try Texture.readCommonInfo(handle: handle, runtime: runtime)
            } catch {
                _ = runtime.functions.textureDestroy(handle)
                throw error
            }
            return Texture2D(
                handle: handle,
                runtime: runtime,
                device: graphicsDevice,
                typeName: "Texture2D",
                destroy: runtime.functions.textureDestroy,
                width: Int32(info.width),
                height: Int32(info.height),
                levelCount: common.levelCount,
                format: common.format
            )
        }
    }
}
