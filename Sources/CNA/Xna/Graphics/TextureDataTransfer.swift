// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework.Graphics {
    /// `Texture.GetExpectedByteSizeFromFormat`, expressed against
    /// `SurfaceFormat` rather than D3D's own enumeration.
    ///
    /// XNA composes two switches: `ConvertXnaFormatToWindows` maps a
    /// `SurfaceFormat` to a `_D3DFORMAT`, and `GetExpectedByteSizeFromFormat`
    /// maps that to a byte size. Both were decoded from the pinned IL rather
    /// than recalled — the second is a 643-byte switch over ninety-eight
    /// D3D formats — and the composition is this table:
    ///
    /// ```text
    /// SurfaceFormat     D3DFORMAT   bytes
    /// Color                    21       4     (A8R8G8B8)
    /// Bgr565                   23       2
    /// Bgra5551                 25       2
    /// Bgra4444                 26       2
    /// Dxt1/Dxt3/Dxt5      FourCC       block-compressed
    /// NormalizedByte2          60       2
    /// NormalizedByte4          63       4
    /// Rgba1010102              31       4
    /// Rg32                     34       4
    /// Rgba64                   36       8
    /// Alpha8                   28       1
    /// Single                  114       4
    /// Vector2                 115       8
    /// Vector4                 116      16
    /// HalfSingle              111       2
    /// HalfVector2             112       4
    /// HalfVector4             113       8
    /// HdrBlendable            113       8
    /// ```
    ///
    /// `HalfVector4` and `HdrBlendable` really do share a D3D format, and so
    /// share a size; that is the table's own doing, not a transcription slip.
    ///
    /// The three DXT formats are block-compressed and have no per-texel size.
    /// `ValidateTotalSize` handles them separately — it divides both extents
    /// by four, rounding up, and uses eight bytes a block for DXT1 and sixteen
    /// for the other two — so `nil` here means "not a per-texel format" rather
    /// than "unknown".
    internal static func expectedByteSize(
        of format: SurfaceFormat
    ) -> Int32? {
        switch format {
        case .Color: return 4
        case .Bgr565: return 2
        case .Bgra5551: return 2
        case .Bgra4444: return 2
        case .Dxt1, .Dxt3, .Dxt5: return nil
        case .NormalizedByte2: return 2
        case .NormalizedByte4: return 4
        case .Rgba1010102: return 4
        case .Rg32: return 4
        case .Rgba64: return 8
        case .Alpha8: return 1
        case .Single: return 4
        case .Vector2: return 8
        case .Vector4: return 16
        case .HalfSingle: return 2
        case .HalfVector2: return 4
        case .HalfVector4: return 8
        case .HdrBlendable: return 8
        }
    }

    /// The `CNA_TEXTURE_DATA_*` identity a surface format's own element type
    /// carries.
    ///
    /// XNA never names an element type: `SetData<T>` blits `sizeof(T)` bytes
    /// and lets D3D interpret them by the surface's format. CNA's transfer
    /// asks for the type explicitly, so the projection supplies the one that
    /// matches the texture's format — which is the same interpretation, said
    /// out loud.
    ///
    /// Only `Color` is reachable on the qualified artifact:
    /// `build-probe/f55_grants.c` asks for every one of the twenty formats and
    /// gets `CNA_RESULT_NOT_SUPPORTED` for nineteen of them. The rest of this
    /// map is written from CNA's own header constants so that a renderer which
    /// grows a format does not need this table rewritten.
    internal static func nativeDataType(
        for format: SurfaceFormat
    ) -> UInt32? {
        switch format {
        case .Color: return 0
        case .Bgr565: return 1
        case .Bgra5551: return 2
        case .Bgra4444: return 3
        case .NormalizedByte2: return 5
        case .NormalizedByte4: return 6
        case .Rgba1010102: return 7
        case .Rg32: return 8
        case .Rgba64: return 9
        case .Alpha8: return 10
        case .Single: return 11
        case .Dxt1, .Dxt3, .Dxt5, .Vector2, .Vector4,
             .HalfSingle, .HalfVector2, .HalfVector4, .HdrBlendable:
            // CNA names no element type for these, and none can be created on
            // the qualified artifact either. A transfer against one is refused
            // rather than guessed at.
            return nil
        }
    }
}

/// `FrameworkResources.InvalidDataSize`, `InvalidTotalSize` and
/// `InvalidRectangle`, read out of the registered
/// `Microsoft.Xna.Framework.dll`.
internal let invalidDataSizeMessage =
    "The type you are using for T in this method is an invalid size for this "
    + "resource."

internal let invalidTotalSizeMessage =
    "The size of the data passed in is too large or too small for this "
    + "resource."

internal let invalidRectangleMessage =
    "The rectangle is too large or too small for this resource."

extension Microsoft.Xna.Framework.Graphics {
    /// `Texture3D.GetAndValidateBox`, as a predicate.
    ///
    /// ```text
    /// if (box.Right  > desc.Width)  fail;   // bgt.un
    /// if (box.Left  >= box.Right)   fail;   // bge.un
    /// if (box.Bottom > desc.Height) fail;
    /// if (box.Top   >= box.Bottom)  fail;
    /// if (box.Back   > desc.Depth)  fail;
    /// if (box.Front >= box.Back)    fail;
    /// ```
    ///
    /// All six comparisons are **unsigned**, so a negative coordinate becomes a
    /// value near `UInt32.max` and is caught by the first test it meets rather
    /// than passing a signed `>= 0` guard that XNA does not have. The failure
    /// is `ArgumentException(InvalidRectangle, "box")`.
    ///
    /// It lives here, apart from `Texture3D`, because no `Texture3D` can be
    /// constructed on a Reach device: the arithmetic would otherwise be
    /// unreachable and untestable on the qualified profile.
    internal static func volumeBoxIsValid(
        width: Int32, height: Int32, depth: Int32,
        left: Int32, top: Int32, right: Int32,
        bottom: Int32, front: Int32, back: Int32
    ) -> Bool {
        let uRight = UInt32(bitPattern: right), uLeft = UInt32(bitPattern: left)
        let uBottom = UInt32(bitPattern: bottom), uTop = UInt32(bitPattern: top)
        let uBack = UInt32(bitPattern: back), uFront = UInt32(bitPattern: front)
        return uRight <= UInt32(bitPattern: width) && uLeft < uRight
            && uBottom <= UInt32(bitPattern: height) && uTop < uBottom
            && uBack <= UInt32(bitPattern: depth) && uFront < uBack
    }
}
