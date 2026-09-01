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

        /// `FrameworkResources.ResourcesMustBeGreaterThanZeroSize`, read out
        /// of the registered `Microsoft.Xna.Framework.dll`. One message serves
        /// both dimensions; only the parameter name differs.
        internal static let resourcesMustBeGreaterThanZeroSizeMessage =
            "Resource size must be greater than zero."

        /// `Texture2D(GraphicsDevice graphicsDevice, Int32 width, Int32 height)`.
        ///
        /// Thirty bytes, and every one of them forwards:
        ///
        /// ```text
        /// CreateTexture(graphicsDevice, width, height,
        ///               mipMap: false, 0, 1, format: SurfaceFormat.Color)
        /// ```
        ///
        /// `ldc.i4.0` for `mipMap` and `ldc.i4.0` for `format` — which is
        /// `SurfaceFormat.Color`, the zero-valued case — so the short
        /// constructor is the long one with two literals, not a different
        /// creation path.
        ///
        /// The two arguments between them are `ldc.i4.0` and `ldc.i4.1` in
        /// **both** constructors, so neither is a projected parameter; they
        /// are `CreateTexture`'s own D3D usage and pool, and CNA's create
        /// info has no counterpart for either.
        public convenience init(
            graphicsDevice: GraphicsDevice,
            width: Int32,
            height: Int32
        ) throws {
            try self.init(graphicsDevice: graphicsDevice, width: width,
                          height: height, mipMap: false, format: .Color)
        }

        /// `Texture2D(GraphicsDevice, Int32, Int32, Boolean, SurfaceFormat)`.
        ///
        /// Both constructors wrap `CreateTexture` in a `try`/`finally` whose
        /// handler is `this.Dispose(true)`: a texture whose creation throws
        /// disposes itself on the way out. There is nothing to dispose here —
        /// the Swift initializer has no handle until the native create
        /// succeeds, and a failed `init` never produces an object — so the
        /// handler has no counterpart rather than an empty one.
        ///
        /// CNA reports back what it actually granted, and those values become
        /// `Width`, `Height`, `LevelCount` and `Format` rather than the ones
        /// that were asked for. `RenderTarget2D` reads its own grants the same
        /// way, and for the same reason: "preferred" is what the parameter
        /// name means.
        public convenience init(
            graphicsDevice: GraphicsDevice,
            width: Int32,
            height: Int32,
            mipMap: Bool,
            format: SurfaceFormat
        ) throws {
            // `Texture2D.ValidateCreationParameters(width, height, format,
            // mipMap)` opens with two `bgt` tests against zero, each naming
            // its own parameter:
            //
            //     if (width  <= 0) throw new ArgumentOutOfRangeException(
            //         "width",  ResourcesMustBeGreaterThanZeroSize);
            //     if (height <= 0) throw new ArgumentOutOfRangeException(
            //         "height", ResourcesMustBeGreaterThanZeroSize);
            //
            // One message, two parameter names, and the width is tested
            // first -- so a texture that is invalid in both dimensions blames
            // the width.
            //
            // What follows in that method is the GraphicsProfile capability
            // family -- DXT alignment, power-of-two rules, the maximum size
            // for the profile in force, and format support. None of it is
            // projected, and the blocker is named in
            // `tools/api_compat/recorded-message-absences.json`: the checks
            // read the device's profile, and `GraphicsDevice.GraphicsProfile`
            // is not a projected member. Inventing a profile to check against
            // would fabricate the fact the check depends on.
            guard width > 0 else {
                throw CNAArgumentOutOfRangeException(
                    paramName: "width",
                    message: Texture2D.resourcesMustBeGreaterThanZeroSizeMessage)
            }
            guard height > 0 else {
                throw CNAArgumentOutOfRangeException(
                    paramName: "height",
                    message: Texture2D.resourcesMustBeGreaterThanZeroSizeMessage)
            }
            let deviceHandle = try graphicsDevice.validatedHandle("Texture2D.init")
            let runtime = graphicsDevice.runtimeState

            var create = CNASwift_Texture2DCreateInfo()
            create.struct_size = UInt32(MemoryLayout<CNASwift_Texture2DCreateInfo>.size)
            create.struct_version = 1
            create.width = UInt32(bitPattern: width)
            create.height = UInt32(bitPattern: height)
            create.mip_map = mipMap ? 1 : 0
            create.format = UInt32(bitPattern: format.rawValue)

            var handle: UInt64 = 0
            try runtime.functions.check(
                withUnsafePointer(to: &create) {
                    runtime.functions.textureCreate(deviceHandle, $0, &handle)
                },
                operation: "cna_texture2d_create"
            )

            var info = CNASwift_Texture2DInfo()
            info.struct_size = UInt32(MemoryLayout<CNASwift_Texture2DInfo>.size)
            info.struct_version = 1
            do {
                try runtime.functions.check(
                    runtime.functions.textureGetInfo(handle, &info),
                    operation: "cna_texture2d_get_info"
                )
                guard info.width <= UInt32(Int32.max), info.height <= UInt32(Int32.max),
                      info.level_count <= UInt32(Int32.max) else {
                    throw CNAError.nativeFailure(
                        operation: "Texture2D dimensions", result: 10,
                        message: "dimensions exceed the XNA Int32 range")
                }
                guard let grantedFormat = SurfaceFormat(
                    rawValue: Int32(bitPattern: info.format)) else {
                    throw CNAError.nativeFailure(
                        operation: "Texture2D.Format", result: 1,
                        message: "native surface format \(info.format) is not an XNA SurfaceFormat")
                }
                self.init(
                    handle: handle,
                    runtime: runtime,
                    device: graphicsDevice,
                    typeName: "Texture2D",
                    destroy: runtime.functions.textureDestroy,
                    width: Int32(info.width),
                    height: Int32(info.height),
                    levelCount: Int32(info.level_count),
                    format: grantedFormat
                )
            } catch {
                // The native texture exists and this initializer will not
                // return an object to own it, so it is released here. This is
                // the counterpart of XNA's `finally`, at the only place a
                // Swift initializer can put one.
                _ = runtime.functions.textureDestroy(handle)
                throw error
            }
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
