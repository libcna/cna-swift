// SPDX-License-Identifier: MIT

import CNAShim
import Foundation

/// The admitted CNA C ABI window.
///
/// The rule is CNA's own, taken from `docs/c-api/ABI_VERSIONING.md` and from
/// the installed package's `SameMajorVersion` compatibility file rather than
/// invented here: *a consumer must reject a different major and may require a
/// minimum minor.* Under ABI `0.x` an incompatible change is what moves the
/// minor, so the minimum minor is the generation this binding is qualified
/// against; a later minor is admitted by the published rule, and every route it
/// might have removed still has to resolve by name before the runtime starts.
internal enum NativeABI {
    /// Packed as CNA packs it: bits 31..16 major, 15..8 minor, 7..0 patch.
    static func encode(major: UInt32, minor: UInt32, patch: UInt32) -> UInt32 {
        ((major & 0xFFFF) << 16) | ((minor & 0xFF) << 8) | (patch & 0xFF)
    }

    static func major(_ encoded: UInt32) -> UInt32 { (encoded >> 16) & 0xFFFF }
    static func minor(_ encoded: UInt32) -> UInt32 { (encoded >> 8) & 0xFF }
    static func patch(_ encoded: UInt32) -> UInt32 { encoded & 0xFF }

    static func describe(_ encoded: UInt32) -> String {
        "\(major(encoded)).\(minor(encoded)).\(patch(encoded))"
    }

    /// The only admitted major. A different major is rejected outright.
    static let admittedMajor: UInt32 = 0
    /// The lowest admitted minor within `admittedMajor`.
    static let minimumMinor: UInt32 = 21
    /// The exact version this binding's native gates were qualified against.
    static let qualifiedVersion: UInt32 = encode(major: 0, minor: 21, patch: 0)

    static func admits(_ encoded: UInt32) -> Bool {
        major(encoded) == admittedMajor && minor(encoded) >= minimumMinor
    }

    /// The admission window, spelled the way the diagnostic reports it.
    static var admittedDescription: String {
        "major \(admittedMajor) with minor \(minimumMinor) or later (qualified against \(describe(qualifiedVersion)))"
    }
}

internal final class NativeFunctions {
    // Every route has a type of its own. Two routes never share one, even when
    // their C prototypes coincide, so tools/native_abi can pair each stored
    // property with exactly one canonical symbol instead of accepting any
    // structurally compatible alias.
    typealias GetAbiVersionRoute = @convention(c) () -> UInt32
    typealias ErrorGetLastMessageSizeRoute = @convention(c) (UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias ErrorCopyLastMessageRoute = @convention(c) (UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameCreateRoute = @convention(c) (UnsafePointer<CNASwift_GameCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameSetFrameHooksExtRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_GameFrameHooks>?) -> UInt32
    typealias FrameworkDispatcherUpdateRoute = @convention(c) (UInt64) -> UInt32
    typealias TitleContainerReadExtRoute = @convention(c) (UInt64, CNASwift_StringView, UnsafeMutablePointer<UInt8>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameRunRoute = @convention(c) (UInt64) -> UInt32
    typealias GameRunOneFrameRoute = @convention(c) (UInt64) -> UInt32
    typealias GameRequestExitRoute = @convention(c) (UInt64) -> UInt32
    typealias GameDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GameGetGraphicsDeviceRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceManagerCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceManagerApplyChangesRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceManagerSetGraphicsProfileRoute = @convention(c) (UInt64, UInt32) -> UInt32
    typealias GraphicsDeviceManagerSetIsFullScreenRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GraphicsDeviceManagerSetPreferMultiSamplingRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GraphicsDeviceManagerSetPreferredBackBufferFormatRoute = @convention(c) (UInt64, UInt32) -> UInt32
    typealias GraphicsDeviceManagerSetPreferredBackBufferWidthRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias GraphicsDeviceManagerSetPreferredBackBufferHeightRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias GraphicsDeviceManagerSetPreferredDepthStencilFormatRoute = @convention(c) (UInt64, UInt32) -> UInt32
    typealias GraphicsDeviceManagerSetSynchronizeWithVerticalRetraceRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GraphicsDeviceManagerSetSupportedOrientationsRoute = @convention(c) (UInt64, UInt32) -> UInt32
    typealias GraphicsDeviceManagerDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceGetViewportRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Viewport>?) -> UInt32
    typealias Texture2dCreateFromEncodedMemoryRoute = @convention(c) (UInt64, UnsafePointer<UInt8>?, UInt64, UnsafePointer<CNASwift_Texture2DDecodeInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture2dGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Texture2DInfo>?) -> UInt32
    typealias Texture2dCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_Texture2DCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture2dDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias Texture2dSetDataRoute = @convention(c) (UInt64, UInt32, UnsafePointer<CNASwift_Texture2DTransfer>?, UnsafeRawPointer?, UInt64) -> UInt32
    typealias Texture2dGetDataRoute = @convention(c) (UInt64, UInt32, UnsafePointer<CNASwift_Texture2DTransfer>?, UnsafeMutableRawPointer?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture2dGetEncodedByteCountRoute = @convention(c) (UInt64, UInt32, UInt32, UInt32, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture2dCopyEncodedRoute = @convention(c) (UInt64, UInt32, UInt32, UInt32, UnsafeMutablePointer<UInt8>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture2dCreateCpuOnlyRgba8Route = @convention(c) (UInt32, UInt32, UInt32, UnsafePointer<CNASwift_Color>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias VertexDeclarationCreateWithStrideRoute = @convention(c) (Int32, UnsafePointer<CNASwift_VertexElement>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias VertexDeclarationDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias VertexBufferCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_VertexBufferCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias VertexBufferDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias VertexBufferSetDataRawAtRoute = @convention(c) (UInt64, UInt64, UnsafeRawPointer?, UInt64, UInt64, UInt32) -> UInt32
    typealias VertexBufferGetDataRawRoute = @convention(c) (UInt64, UInt64, UnsafeMutableRawPointer?, UInt64, UInt64, UInt32) -> UInt32
    typealias IndexBufferCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_IndexBufferCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias IndexBufferDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias IndexBufferSetDataAtRoute = @convention(c) (UInt64, UInt64, UnsafePointer<CNASwift_IndexBufferTransfer>?, UnsafeRawPointer?, UInt64) -> UInt32
    typealias IndexBufferGetDataRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_IndexBufferTransfer>?, UnsafeMutableRawPointer?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias VertexBufferSetDataRawAtWithOptionsRoute = @convention(c) (UInt64, UInt64, UnsafeRawPointer?, UInt64, UInt64, UInt32, UInt32) -> UInt32
    typealias VertexBufferSubscribeContentLostRoute = @convention(c) (UInt64, CNASwift_VertexBufferContentLostCallback?, UnsafeMutableRawPointer?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias VertexBufferUnsubscribeContentLostRoute = @convention(c) (UInt64) -> UInt32
    typealias IndexBufferSetDataRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_IndexBufferTransfer>?, UnsafeRawPointer?, UInt64) -> UInt32
    typealias IndexBufferSubscribeContentLostRoute = @convention(c) (UInt64, CNASwift_IndexBufferContentLostCallback?, UnsafeMutableRawPointer?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias IndexBufferUnsubscribeContentLostRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceGetGraphicsProfileRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt32>?) -> UInt32
    typealias GraphicsDeviceSetVertexBuffersRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_VertexBufferBinding>?, UInt64) -> UInt32
    typealias GraphicsDeviceSetIndexBufferRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias TexturecubeCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_TextureCubeCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias TexturecubeDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias TexturecubeGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_TextureCubeInfo>?) -> UInt32
    typealias TexturecubeSetDataRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_TextureCubeTransfer>?, UnsafePointer<CNASwift_Color>?, UInt64) -> UInt32
    typealias TexturecubeGetDataRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_TextureCubeTransfer>?, UnsafeMutablePointer<CNASwift_Color>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture3dCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_Texture3DCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture3dDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias Texture3dGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Texture3DInfo>?) -> UInt32
    typealias Texture3dSetDataRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_Texture3DTransfer>?, UnsafePointer<CNASwift_Color>?, UInt64) -> UInt32
    typealias Texture3dGetDataRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_Texture3DTransfer>?, UnsafeMutablePointer<CNASwift_Color>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteBatchCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteBatchBeginWithEffectRoute = @convention(c) (UInt64, UInt32, UnsafePointer<CNASwift_BlendState>?, UnsafePointer<CNASwift_SamplerState>?, UnsafePointer<CNASwift_DepthStencilState>?, UnsafePointer<CNASwift_RasterizerState>?, UInt64, UnsafePointer<CNASwift_Matrix>?) -> UInt32
    typealias SpriteBatchBeginWithStatesRoute = @convention(c) (UInt64, UInt32, UnsafePointer<CNASwift_BlendState>?, UnsafePointer<CNASwift_SamplerState>?, UnsafePointer<CNASwift_DepthStencilState>?, UnsafePointer<CNASwift_RasterizerState>?) -> UInt32
    typealias SpriteFontCreateRoute = @convention(c) (UnsafePointer<CNASwift_SpriteFontCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteFontDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias SpriteFontGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_SpriteFontInfo>?) -> UInt32
    typealias SpriteFontCopyCharactersRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt16>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteFontCopyGlyphsRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_SpriteFontGlyph>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteFontSetDefaultCharacterRoute = @convention(c) (UInt64, UInt8, UInt16) -> UInt32
    typealias SpriteFontSetLineSpacingRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias SpriteFontSetSpacingRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias SpriteBatchDrawStringRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteTextCommand>?) -> UInt32
    typealias SpriteBatchSubmitScaledManyRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteScaledCommand>?, UInt64) -> UInt32
    typealias SpriteBatchSubmitManyRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteCommand>?, UInt64) -> UInt32
    typealias SpriteBatchEndRoute = @convention(c) (UInt64) -> UInt32
    typealias SpriteBatchDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsAdapterGetCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsAdapterGetInfoRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GraphicsAdapterInfo>?) -> UInt32
    typealias GraphicsAdapterCopyDescriptionRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsAdapterCopyDeviceNameRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsAdapterGetCurrentDisplayModeRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_DisplayMode>?) -> UInt32
    typealias GraphicsAdapterGetDisplayModeCountRoute = @convention(c) (UInt64, UInt32, UInt8, UInt32, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsAdapterCopyDisplayModesRoute = @convention(c) (UInt64, UInt32, UInt8, UInt32, UnsafeMutablePointer<CNASwift_DisplayMode>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsAdapterSetDevicePreferencesRoute = @convention(c) (UInt64, UInt32, UInt8, UInt8) -> UInt32
    typealias GraphicsAdapterIsProfileSupportedRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GraphicsAdapterQueryBackbufferFormatRoute = @convention(c) (UInt64, UInt32, UInt32, UInt32, UInt32, Int32, UnsafeMutablePointer<CNASwift_GraphicsFormatSelection>?) -> UInt32
    typealias GraphicsAdapterQueryRenderTargetFormatRoute = @convention(c) (UInt64, UInt32, UInt32, UInt32, UInt32, Int32, UnsafeMutablePointer<CNASwift_GraphicsFormatSelection>?) -> UInt32
    typealias GameWindowGetTitleSizeRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameWindowCopyTitleRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameWindowGetScreenDeviceNameSizeRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameWindowCopyScreenDeviceNameRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameWindowGetNativeHandleExtRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameWindowGetClientBoundsRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Rectangle>?) -> UInt32
    typealias GameWindowGetCurrentOrientationRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt32>?) -> UInt32
    typealias GameWindowGetAllowUserResizingRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GameWindowSetAllowUserResizingRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GameWindowBeginScreenDeviceChangeRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GameWindowEndScreenDeviceChangeRoute = @convention(c) (UInt64, CNASwift_StringView, Int32, Int32) -> UInt32
    typealias GameSetWindowTitleRoute = @convention(c) (UInt64, CNASwift_StringView) -> UInt32
    typealias ContentManagerCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_ContentManagerCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias ContentManagerDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias ContentManagerUnloadRoute = @convention(c) (UInt64) -> UInt32
    typealias ContentManagerGetRootDirectorySizeRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias ContentManagerCopyRootDirectoryRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias ContentManagerLoadTexture2dRoute = @convention(c) (UInt64, CNASwift_StringView, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias MouseGetStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_MouseState>?) -> UInt32
    typealias MouseSetPositionRoute = @convention(c) (UInt64, Int32, Int32) -> UInt32
    typealias MouseSetWindowHandleRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias KeyboardGetStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias KeyboardGetStateForPlayerRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias GamepadGetStateRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GamePadState>?) -> UInt32
    typealias GamepadGetStateWithDeadZoneRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafeMutablePointer<CNASwift_GamePadState>?) -> UInt32
    typealias GamepadGetCapabilitiesRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GamePadCapabilities>?) -> UInt32
    typealias GamepadSetVibrationRoute = @convention(c) (UInt64, UInt32, Float, Float, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias TextureGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_TextureInfo>?) -> UInt32
    typealias RenderTarget2dCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_RenderTarget2DCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias OcclusionQueryCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias OcclusionQueryDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias OcclusionQueryBeginRoute = @convention(c) (UInt64) -> UInt32
    typealias OcclusionQueryEndRoute = @convention(c) (UInt64) -> UInt32
    typealias OcclusionQueryGetIsCompleteRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias OcclusionQueryGetPixelCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias RenderTargetGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_RenderTargetInfo>?) -> UInt32
    typealias RenderTargetDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceSetRenderTarget2dRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias RenderTargetCubeCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_RenderTargetCubeCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceSetRenderTargetCubeRoute = @convention(c) (UInt64, UInt64, UInt32) -> UInt32
    typealias GraphicsDeviceSetRenderTargetsRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_RenderTargetBinding>?, UInt64) -> UInt32
    typealias GraphicsDeviceGetRenderTargetCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceGetTextureRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafeMutablePointer<CNASwift_TextureSlotInfo>?) -> UInt32
    typealias GraphicsDeviceSetTextureRoute = @convention(c) (UInt64, UInt32, UInt32, UInt64) -> UInt32
    typealias GraphicsDeviceDrawPrimitivesRoute = @convention(c) (UInt64, UInt32, Int32, Int32) -> UInt32
    typealias GraphicsDeviceDrawIndexedPrimitivesRoute = @convention(c) (UInt64, UInt32, Int32, Int32, Int32, Int32, Int32) -> UInt32
    typealias GraphicsDeviceDrawInstancedPrimitivesRoute = @convention(c) (UInt64, UInt32, Int32, Int32, Int32, Int32, Int32, Int32) -> UInt32
    typealias GraphicsDeviceDrawUserPrimitivesRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_UserPrimitives>?) -> UInt32
    typealias GraphicsDeviceDrawUserIndexedPrimitivesRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_UserPrimitives>?, UnsafePointer<CNASwift_UserIndices>?) -> UInt32
    typealias PrimitiveTypeGetVertexCountRoute = @convention(c) (UInt32, Int32, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias EffectMaterialCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias DirectionalLightDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias DirectionalLightGetDiffuseColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias DirectionalLightSetDiffuseColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias DirectionalLightGetDirectionRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias DirectionalLightSetDirectionRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias DirectionalLightGetSpecularColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias DirectionalLightSetSpecularColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias DirectionalLightGetEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias DirectionalLightSetEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias BasicEffectCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectMatricesGetWorldRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Matrix>?) -> UInt32
    typealias EffectMatricesSetWorldRoute = @convention(c) (UInt64, CNASwift_Matrix) -> UInt32
    typealias EffectMatricesGetViewRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Matrix>?) -> UInt32
    typealias EffectMatricesSetViewRoute = @convention(c) (UInt64, CNASwift_Matrix) -> UInt32
    typealias EffectMatricesGetProjectionRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Matrix>?) -> UInt32
    typealias EffectMatricesSetProjectionRoute = @convention(c) (UInt64, CNASwift_Matrix) -> UInt32
    typealias EffectFogGetColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias EffectFogSetColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias EffectFogGetEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias EffectFogSetEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias EffectFogGetStartRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias EffectFogSetStartRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias EffectFogGetEndRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias EffectFogSetEndRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias EffectLightsGetAmbientColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias EffectLightsSetAmbientColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias EffectLightsGetDirectionalLightRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectLightsGetEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias EffectLightsSetEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias BasicEffectGetVertexColorEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias BasicEffectSetVertexColorEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias BasicEffectGetPreferPerPixelLightingRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias BasicEffectSetPreferPerPixelLightingRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias BasicEffectGetDiffuseColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias BasicEffectSetDiffuseColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias BasicEffectGetEmissiveColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias BasicEffectSetEmissiveColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias BasicEffectGetSpecularColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias BasicEffectSetSpecularColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias BasicEffectGetSpecularPowerRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias BasicEffectSetSpecularPowerRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias BasicEffectGetAlphaRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias BasicEffectSetAlphaRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias BasicEffectGetTextureEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias BasicEffectSetTextureEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias BasicEffectGetTextureRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias BasicEffectSetTextureRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias AlphaTestEffectCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias AlphaTestEffectGetDiffuseColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias AlphaTestEffectSetDiffuseColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias AlphaTestEffectGetAlphaRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias AlphaTestEffectSetAlphaRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias AlphaTestEffectGetTextureRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias AlphaTestEffectSetTextureRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias AlphaTestEffectGetVertexColorEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias AlphaTestEffectSetVertexColorEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias AlphaTestEffectGetAlphaFunctionRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt32>?) -> UInt32
    typealias AlphaTestEffectSetAlphaFunctionRoute = @convention(c) (UInt64, UInt32) -> UInt32
    typealias AlphaTestEffectGetReferenceAlphaRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias AlphaTestEffectSetReferenceAlphaRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias DualTextureEffectCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias DualTextureEffectGetDiffuseColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias DualTextureEffectSetDiffuseColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias DualTextureEffectGetAlphaRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias DualTextureEffectSetAlphaRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias DualTextureEffectGetTextureRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<UInt8>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias DualTextureEffectSetTextureRoute = @convention(c) (UInt64, UInt32, UInt64) -> UInt32
    typealias DualTextureEffectGetVertexColorEnabledRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias DualTextureEffectSetVertexColorEnabledRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias EnvironmentMapEffectCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EnvironmentMapEffectGetDiffuseColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias EnvironmentMapEffectSetDiffuseColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias EnvironmentMapEffectGetEmissiveColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias EnvironmentMapEffectSetEmissiveColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias EnvironmentMapEffectGetAlphaRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias EnvironmentMapEffectSetAlphaRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias EnvironmentMapEffectGetTextureRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EnvironmentMapEffectSetTextureRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias EnvironmentMapEffectGetEnvironmentMapRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EnvironmentMapEffectSetEnvironmentMapRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias EnvironmentMapEffectGetAmountRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias EnvironmentMapEffectSetAmountRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias EnvironmentMapEffectGetSpecularRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias EnvironmentMapEffectSetSpecularRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias EnvironmentMapEffectGetFresnelFactorRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias EnvironmentMapEffectSetFresnelFactorRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias SkinnedEffectCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SkinnedEffectGetDiffuseColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias SkinnedEffectSetDiffuseColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias SkinnedEffectGetEmissiveColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias SkinnedEffectSetEmissiveColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias SkinnedEffectGetSpecularColorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias SkinnedEffectSetSpecularColorRoute = @convention(c) (UInt64, CNASwift_Vector3) -> UInt32
    typealias SkinnedEffectGetSpecularPowerRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias SkinnedEffectSetSpecularPowerRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias SkinnedEffectGetAlphaRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias SkinnedEffectSetAlphaRoute = @convention(c) (UInt64, Float) -> UInt32
    typealias SkinnedEffectGetPreferPerPixelLightingRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias SkinnedEffectSetPreferPerPixelLightingRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias SkinnedEffectGetTextureRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SkinnedEffectSetTextureRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias SkinnedEffectGetWeightsPerVertexRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias SkinnedEffectSetWeightsPerVertexRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias SkinnedEffectSetBoneTransformsRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_Matrix>?, UInt64) -> UInt32
    typealias SkinnedEffectCopyBoneTransformsRoute = @convention(c) (UInt64, UInt64, UnsafeMutablePointer<CNASwift_Matrix>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectCreateEmptyRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectCreateCompiledRoute = @convention(c) (UInt64, UnsafePointer<UInt8>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectCloneRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectDisposeRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectApplyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectGetParametersRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectGetTechniquesRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectGetCurrentTechniqueRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectSetCurrentTechniqueRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias EffectGetGraphicsDeviceRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectTechniqueDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectTechniqueGetNameByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectTechniqueCopyNameRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectTechniqueGetPassesRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectTechniqueGetAnnotationsRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectTechniqueCollectionDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectTechniqueCollectionGetCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectTechniqueCollectionGetAtRoute = @convention(c) (UInt64, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectPassDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectPassGetNameByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectPassCopyNameRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectPassGetAnnotationsRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectPassApplyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectPassCollectionDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectPassCollectionGetCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectPassCollectionGetAtRoute = @convention(c) (UInt64, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectParameterGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_EffectParameterInfo>?) -> UInt32
    typealias EffectParameterGetNameByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterCopyNameRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterGetSemanticByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterCopySemanticRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterGetElementsRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterGetStructureMembersRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterGetAnnotationsRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterGetValueRoute = @convention(c) (UInt64, UInt32, UnsafeMutableRawPointer?) -> UInt32
    typealias EffectParameterSetValueRoute = @convention(c) (UInt64, UInt32, UnsafeRawPointer?) -> UInt32
    typealias EffectParameterGetValuesRoute = @convention(c) (UInt64, UInt32, UInt64, UnsafeMutableRawPointer?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterSetValuesRoute = @convention(c) (UInt64, UInt32, UnsafeRawPointer?, UInt64) -> UInt32
    typealias EffectParameterGetValueStringByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterCopyValueStringRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterSetValueStringRoute = @convention(c) (UInt64, CNASwift_StringView) -> UInt32
    typealias EffectParameterGetValueTextureRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterSetValueTextureRoute = @convention(c) (UInt64, UInt32, UInt64) -> UInt32
    typealias EffectParameterCollectionDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectParameterCollectionGetCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectParameterCollectionGetAtRoute = @convention(c) (UInt64, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectAnnotationGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_EffectAnnotationInfo>?) -> UInt32
    typealias EffectAnnotationGetNameByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationCopyNameRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationGetSemanticByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationCopySemanticRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationGetValueBooleanRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias EffectAnnotationGetValueInt32Route = @convention(c) (UInt64, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias EffectAnnotationGetValueSingleRoute = @convention(c) (UInt64, UnsafeMutablePointer<Float>?) -> UInt32
    typealias EffectAnnotationGetValueVector2Route = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector2>?) -> UInt32
    typealias EffectAnnotationGetValueVector3Route = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector3>?) -> UInt32
    typealias EffectAnnotationGetValueVector4Route = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Vector4>?) -> UInt32
    typealias EffectAnnotationGetValueMatrixRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Matrix>?) -> UInt32
    typealias EffectAnnotationGetValueStringByteCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationCopyValueStringRoute = @convention(c) (UInt64, UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationCollectionDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias EffectAnnotationCollectionGetCountRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias EffectAnnotationCollectionGetAtRoute = @convention(c) (UInt64, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceClearOptionsRoute = @convention(c) (UInt64, UInt32, CNASwift_Color, Float, Int32) -> UInt32
    typealias GraphicsDeviceCreateRoute = @convention(c) (UInt32, UInt32, UnsafePointer<CNASwift_PresentationParameters>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceGetIsDisposedRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GraphicsDeviceDisposeRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDevicePresentRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceResetRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceResetWithParametersRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_PresentationParameters>?, UnsafePointer<UInt32>?) -> UInt32
    typealias GraphicsDeviceGetPresentationParametersRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_PresentationParameters>?) -> UInt32
    typealias GraphicsDeviceSetViewportRoute = @convention(c) (UInt64, CNASwift_Viewport) -> UInt32
    typealias GraphicsDeviceGetScissorRectangleRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Rectangle>?) -> UInt32
    typealias GraphicsDeviceSetScissorRectangleRoute = @convention(c) (UInt64, CNASwift_Rectangle) -> UInt32
    typealias GraphicsDeviceGetStatusRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt32>?) -> UInt32
    typealias GraphicsDeviceGetBlendFactorRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Color>?) -> UInt32
    typealias GraphicsDeviceSetBlendFactorRoute = @convention(c) (UInt64, CNASwift_Color) -> UInt32
    typealias GraphicsDeviceGetMultiSampleMaskRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias GraphicsDeviceSetMultiSampleMaskRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias GraphicsDeviceGetReferenceStencilRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int32>?) -> UInt32
    typealias GraphicsDeviceSetReferenceStencilRoute = @convention(c) (UInt64, Int32) -> UInt32
    typealias GraphicsDeviceGetBlendStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_BlendState>?) -> UInt32
    typealias GraphicsDeviceSetBlendStateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_BlendState>?) -> UInt32
    typealias GraphicsDeviceGetDepthStencilStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_DepthStencilState>?) -> UInt32
    typealias GraphicsDeviceSetDepthStencilStateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_DepthStencilState>?) -> UInt32
    typealias GraphicsDeviceGetRasterizerStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_RasterizerState>?) -> UInt32
    typealias GraphicsDeviceSetRasterizerStateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_RasterizerState>?) -> UInt32
    typealias GraphicsDeviceGetSamplerStateRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafeMutablePointer<CNASwift_SamplerState>?) -> UInt32
    typealias GraphicsDeviceSetSamplerStateRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafePointer<CNASwift_SamplerState>?) -> UInt32
    typealias RenderTargetSubscribeContentLostRoute = @convention(c) (UInt64, CNASwift_RenderTargetContentLostCallback?, UnsafeMutableRawPointer?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias RenderTargetUnsubscribeContentLostRoute = @convention(c) (UInt64) -> UInt32
    typealias GameTickRoute = @convention(c) (UInt64) -> UInt32
    typealias GameSuppressDrawRoute = @convention(c) (UInt64) -> UInt32
    typealias GameResetElapsedTimeRoute = @convention(c) (UInt64) -> UInt32
    typealias GameGetIsActiveRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GameGetIsMouseVisibleRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GameSetIsMouseVisibleRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GameGetIsFixedTimeStepRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GameSetIsFixedTimeStepRoute = @convention(c) (UInt64, UInt8) -> UInt32
    typealias GameGetTargetElapsedTimeTicksRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int64>?) -> UInt32
    typealias GameSetTargetElapsedTimeTicksRoute = @convention(c) (UInt64, Int64) -> UInt32
    typealias GameGetInactiveSleepTimeTicksRoute = @convention(c) (UInt64, UnsafeMutablePointer<Int64>?) -> UInt32
    typealias GameSetInactiveSleepTimeTicksRoute = @convention(c) (UInt64, Int64) -> UInt32
    typealias GameSubscribeRoute = @convention(c) (UInt64, UInt32, CNASwift_GameEventCallback?, UnsafeMutableRawPointer?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameUnsubscribeRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceManagerCreateDeviceRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceManagerBeginDrawRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias GraphicsDeviceManagerEndDrawRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceManagerGetGraphicsDeviceRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GraphicsDeviceManagerSubscribeRoute = @convention(c) (UInt64, UInt32, CNASwift_GameEventCallback?, UnsafeMutableRawPointer?, UnsafeMutablePointer<UInt64>?) -> UInt32

    private static let lock = NSLock()
    private static var cached: Result<NativeFunctions, Error>?

    let library: NativeLibrary
    /// The ABI the admitted library actually reported, kept so diagnostics and
    /// tests can state the measured generation rather than the required one.
    let abiVersion: UInt32
    let getABIVersion: GetAbiVersionRoute
    let errorMessageSize: ErrorGetLastMessageSizeRoute
    let errorMessageCopy: ErrorCopyLastMessageRoute
    let gameCreate: GameCreateRoute
    let gameSetFrameHooks: GameSetFrameHooksExtRoute
    let gameRun: GameRunRoute
    let gameRunOneFrame: GameRunOneFrameRoute
    let frameworkDispatcherUpdate: FrameworkDispatcherUpdateRoute
    let titleContainerRead: TitleContainerReadExtRoute
    let gameRequestExit: GameRequestExitRoute
    let gameDestroy: GameDestroyRoute
    let gameGetGraphicsDevice: GameGetGraphicsDeviceRoute
    let graphicsManagerCreate: GraphicsDeviceManagerCreateRoute
    let graphicsManagerApplyChanges: GraphicsDeviceManagerApplyChangesRoute
    let graphicsManagerSetGraphicsProfile: GraphicsDeviceManagerSetGraphicsProfileRoute
    let graphicsManagerSetIsFullScreen: GraphicsDeviceManagerSetIsFullScreenRoute
    let graphicsManagerSetPreferMultiSampling: GraphicsDeviceManagerSetPreferMultiSamplingRoute
    let graphicsManagerSetPreferredBackBufferFormat: GraphicsDeviceManagerSetPreferredBackBufferFormatRoute
    let graphicsManagerSetPreferredBackBufferWidth: GraphicsDeviceManagerSetPreferredBackBufferWidthRoute
    let graphicsManagerSetPreferredBackBufferHeight: GraphicsDeviceManagerSetPreferredBackBufferHeightRoute
    let graphicsManagerSetPreferredDepthStencilFormat: GraphicsDeviceManagerSetPreferredDepthStencilFormatRoute
    let graphicsManagerSetSynchronizeWithVerticalRetrace: GraphicsDeviceManagerSetSynchronizeWithVerticalRetraceRoute
    let graphicsManagerSetSupportedOrientations: GraphicsDeviceManagerSetSupportedOrientationsRoute
    let graphicsManagerDestroy: GraphicsDeviceManagerDestroyRoute
    let graphicsDeviceGetViewport: GraphicsDeviceGetViewportRoute
    let textureCreateMemory: Texture2dCreateFromEncodedMemoryRoute
    let textureGetInfo: Texture2dGetInfoRoute
    let textureCreate: Texture2dCreateRoute
    let textureDestroy: Texture2dDestroyRoute
    let textureSetData: Texture2dSetDataRoute
    let textureGetData: Texture2dGetDataRoute
    let textureGetEncodedByteCount: Texture2dGetEncodedByteCountRoute
    let textureCopyEncoded: Texture2dCopyEncodedRoute
    let textureCreateCpuOnly: Texture2dCreateCpuOnlyRgba8Route
    let vertexDeclarationCreateWithStride: VertexDeclarationCreateWithStrideRoute
    let vertexDeclarationDestroy: VertexDeclarationDestroyRoute
    let vertexBufferCreate: VertexBufferCreateRoute
    let vertexBufferDestroy: VertexBufferDestroyRoute
    let vertexBufferSetDataRawAt: VertexBufferSetDataRawAtRoute
    let vertexBufferGetDataRaw: VertexBufferGetDataRawRoute
    let indexBufferCreate: IndexBufferCreateRoute
    let indexBufferDestroy: IndexBufferDestroyRoute
    let indexBufferSetDataAt: IndexBufferSetDataAtRoute
    let indexBufferGetData: IndexBufferGetDataRoute
    let vertexBufferSetDataRawAtWithOptions: VertexBufferSetDataRawAtWithOptionsRoute
    let vertexBufferSubscribeContentLost: VertexBufferSubscribeContentLostRoute
    let vertexBufferUnsubscribeContentLost: VertexBufferUnsubscribeContentLostRoute
    let indexBufferSetData: IndexBufferSetDataRoute
    let indexBufferSubscribeContentLost: IndexBufferSubscribeContentLostRoute
    let indexBufferUnsubscribeContentLost: IndexBufferUnsubscribeContentLostRoute
    let graphicsDeviceGetGraphicsProfile: GraphicsDeviceGetGraphicsProfileRoute
    let graphicsDeviceSetVertexBuffers: GraphicsDeviceSetVertexBuffersRoute
    let graphicsDeviceSetIndexBuffer: GraphicsDeviceSetIndexBufferRoute
    let textureCubeCreate: TexturecubeCreateRoute
    let textureCubeDestroy: TexturecubeDestroyRoute
    let textureCubeGetInfo: TexturecubeGetInfoRoute
    let textureCubeSetData: TexturecubeSetDataRoute
    let textureCubeGetData: TexturecubeGetDataRoute
    let texture3DCreate: Texture3dCreateRoute
    let texture3DDestroy: Texture3dDestroyRoute
    let texture3DGetInfo: Texture3dGetInfoRoute
    let texture3DSetData: Texture3dSetDataRoute
    let texture3DGetData: Texture3dGetDataRoute
    let spriteBatchCreate: SpriteBatchCreateRoute
    let spriteBatchBeginWithEffect: SpriteBatchBeginWithEffectRoute
    let spriteBatchBeginWithStates: SpriteBatchBeginWithStatesRoute
    let spriteBatchSubmitScaled: SpriteBatchSubmitScaledManyRoute
    let spriteFontCreate: SpriteFontCreateRoute
    let spriteFontDestroy: SpriteFontDestroyRoute
    let spriteFontGetInfo: SpriteFontGetInfoRoute
    let spriteFontCopyCharacters: SpriteFontCopyCharactersRoute
    let spriteFontCopyGlyphs: SpriteFontCopyGlyphsRoute
    let spriteFontSetDefaultCharacter: SpriteFontSetDefaultCharacterRoute
    let spriteFontSetLineSpacing: SpriteFontSetLineSpacingRoute
    let spriteFontSetSpacing: SpriteFontSetSpacingRoute
    let spriteBatchDrawString: SpriteBatchDrawStringRoute
    let spriteBatchSubmit: SpriteBatchSubmitManyRoute
    let spriteBatchEnd: SpriteBatchEndRoute
    let spriteBatchDestroy: SpriteBatchDestroyRoute
    let graphicsAdapterGetCount: GraphicsAdapterGetCountRoute
    let graphicsAdapterGetInfo: GraphicsAdapterGetInfoRoute
    let graphicsAdapterCopyDescription: GraphicsAdapterCopyDescriptionRoute
    let graphicsAdapterCopyDeviceName: GraphicsAdapterCopyDeviceNameRoute
    let graphicsAdapterGetCurrentDisplayMode: GraphicsAdapterGetCurrentDisplayModeRoute
    let graphicsAdapterGetDisplayModeCount: GraphicsAdapterGetDisplayModeCountRoute
    let graphicsAdapterCopyDisplayModes: GraphicsAdapterCopyDisplayModesRoute
    let graphicsAdapterSetDevicePreferences: GraphicsAdapterSetDevicePreferencesRoute
    let graphicsAdapterIsProfileSupported: GraphicsAdapterIsProfileSupportedRoute
    let graphicsAdapterQueryBackbufferFormat: GraphicsAdapterQueryBackbufferFormatRoute
    let graphicsAdapterQueryRenderTargetFormat: GraphicsAdapterQueryRenderTargetFormatRoute
    let gameWindowGetTitleSize: GameWindowGetTitleSizeRoute
    let gameWindowCopyTitle: GameWindowCopyTitleRoute
    let gameWindowGetScreenDeviceNameSize: GameWindowGetScreenDeviceNameSizeRoute
    let gameWindowCopyScreenDeviceName: GameWindowCopyScreenDeviceNameRoute
    let gameWindowGetNativeHandle: GameWindowGetNativeHandleExtRoute
    let gameWindowGetClientBounds: GameWindowGetClientBoundsRoute
    let gameWindowGetCurrentOrientation: GameWindowGetCurrentOrientationRoute
    let gameWindowGetAllowUserResizing: GameWindowGetAllowUserResizingRoute
    let gameWindowSetAllowUserResizing: GameWindowSetAllowUserResizingRoute
    let gameWindowBeginScreenDeviceChange: GameWindowBeginScreenDeviceChangeRoute
    let gameWindowEndScreenDeviceChange: GameWindowEndScreenDeviceChangeRoute
    let gameSetWindowTitle: GameSetWindowTitleRoute
    let contentManagerCreate: ContentManagerCreateRoute
    let contentManagerDestroy: ContentManagerDestroyRoute
    let contentManagerUnload: ContentManagerUnloadRoute
    let contentManagerGetRootDirectorySize: ContentManagerGetRootDirectorySizeRoute
    let contentManagerCopyRootDirectory: ContentManagerCopyRootDirectoryRoute
    let contentManagerLoadTexture2d: ContentManagerLoadTexture2dRoute
    let mouseGetState: MouseGetStateRoute
    let mouseSetPosition: MouseSetPositionRoute
    let mouseSetWindowHandle: MouseSetWindowHandleRoute
    let keyboardGetState: KeyboardGetStateRoute
    let keyboardGetStateForPlayer: KeyboardGetStateForPlayerRoute
    let gamePadGetState: GamepadGetStateRoute
    let gamePadGetStateWithDeadZone: GamepadGetStateWithDeadZoneRoute
    let gamePadGetCapabilities: GamepadGetCapabilitiesRoute
    let gamePadSetVibration: GamepadSetVibrationRoute
    let textureCommonGetInfo: TextureGetInfoRoute
    let renderTarget2DCreate: RenderTarget2dCreateRoute
    let occlusionQueryCreate: OcclusionQueryCreateRoute
    let occlusionQueryDestroy: OcclusionQueryDestroyRoute
    let occlusionQueryBegin: OcclusionQueryBeginRoute
    let occlusionQueryEnd: OcclusionQueryEndRoute
    let occlusionQueryGetIsComplete: OcclusionQueryGetIsCompleteRoute
    let occlusionQueryGetPixelCount: OcclusionQueryGetPixelCountRoute
    let renderTargetGetInfo: RenderTargetGetInfoRoute
    let renderTargetDestroy: RenderTargetDestroyRoute
    let graphicsDeviceSetRenderTarget2D: GraphicsDeviceSetRenderTarget2dRoute
    let renderTargetCubeCreate: RenderTargetCubeCreateRoute
    let graphicsDeviceSetRenderTargetCube: GraphicsDeviceSetRenderTargetCubeRoute
    let graphicsDeviceSetRenderTargets: GraphicsDeviceSetRenderTargetsRoute
    let graphicsDeviceGetRenderTargetCount: GraphicsDeviceGetRenderTargetCountRoute
    let graphicsDeviceGetTexture: GraphicsDeviceGetTextureRoute
    let graphicsDeviceSetTexture: GraphicsDeviceSetTextureRoute
    let graphicsDeviceDrawPrimitives: GraphicsDeviceDrawPrimitivesRoute
    let graphicsDeviceDrawIndexedPrimitives: GraphicsDeviceDrawIndexedPrimitivesRoute
    let graphicsDeviceDrawInstancedPrimitives: GraphicsDeviceDrawInstancedPrimitivesRoute
    let graphicsDeviceDrawUserPrimitives: GraphicsDeviceDrawUserPrimitivesRoute
    let graphicsDeviceDrawUserIndexedPrimitives: GraphicsDeviceDrawUserIndexedPrimitivesRoute
    let primitiveTypeGetVertexCount: PrimitiveTypeGetVertexCountRoute
    let effectMaterialCreate: EffectMaterialCreateRoute
    let directionalLightDestroy: DirectionalLightDestroyRoute
    let directionalLightGetDiffuseColor: DirectionalLightGetDiffuseColorRoute
    let directionalLightSetDiffuseColor: DirectionalLightSetDiffuseColorRoute
    let directionalLightGetDirection: DirectionalLightGetDirectionRoute
    let directionalLightSetDirection: DirectionalLightSetDirectionRoute
    let directionalLightGetSpecularColor: DirectionalLightGetSpecularColorRoute
    let directionalLightSetSpecularColor: DirectionalLightSetSpecularColorRoute
    let directionalLightGetEnabled: DirectionalLightGetEnabledRoute
    let directionalLightSetEnabled: DirectionalLightSetEnabledRoute
    let basicEffectCreate: BasicEffectCreateRoute
    let effectMatricesGetWorld: EffectMatricesGetWorldRoute
    let effectMatricesSetWorld: EffectMatricesSetWorldRoute
    let effectMatricesGetView: EffectMatricesGetViewRoute
    let effectMatricesSetView: EffectMatricesSetViewRoute
    let effectMatricesGetProjection: EffectMatricesGetProjectionRoute
    let effectMatricesSetProjection: EffectMatricesSetProjectionRoute
    let effectFogGetColor: EffectFogGetColorRoute
    let effectFogSetColor: EffectFogSetColorRoute
    let effectFogGetEnabled: EffectFogGetEnabledRoute
    let effectFogSetEnabled: EffectFogSetEnabledRoute
    let effectFogGetStart: EffectFogGetStartRoute
    let effectFogSetStart: EffectFogSetStartRoute
    let effectFogGetEnd: EffectFogGetEndRoute
    let effectFogSetEnd: EffectFogSetEndRoute
    let effectLightsGetAmbientColor: EffectLightsGetAmbientColorRoute
    let effectLightsSetAmbientColor: EffectLightsSetAmbientColorRoute
    let effectLightsGetDirectionalLight: EffectLightsGetDirectionalLightRoute
    let effectLightsGetEnabled: EffectLightsGetEnabledRoute
    let effectLightsSetEnabled: EffectLightsSetEnabledRoute
    let basicEffectGetVertexColorEnabled: BasicEffectGetVertexColorEnabledRoute
    let basicEffectSetVertexColorEnabled: BasicEffectSetVertexColorEnabledRoute
    let basicEffectGetPreferPerPixelLighting: BasicEffectGetPreferPerPixelLightingRoute
    let basicEffectSetPreferPerPixelLighting: BasicEffectSetPreferPerPixelLightingRoute
    let basicEffectGetDiffuseColor: BasicEffectGetDiffuseColorRoute
    let basicEffectSetDiffuseColor: BasicEffectSetDiffuseColorRoute
    let basicEffectGetEmissiveColor: BasicEffectGetEmissiveColorRoute
    let basicEffectSetEmissiveColor: BasicEffectSetEmissiveColorRoute
    let basicEffectGetSpecularColor: BasicEffectGetSpecularColorRoute
    let basicEffectSetSpecularColor: BasicEffectSetSpecularColorRoute
    let basicEffectGetSpecularPower: BasicEffectGetSpecularPowerRoute
    let basicEffectSetSpecularPower: BasicEffectSetSpecularPowerRoute
    let basicEffectGetAlpha: BasicEffectGetAlphaRoute
    let basicEffectSetAlpha: BasicEffectSetAlphaRoute
    let basicEffectGetTextureEnabled: BasicEffectGetTextureEnabledRoute
    let basicEffectSetTextureEnabled: BasicEffectSetTextureEnabledRoute
    let basicEffectGetTexture: BasicEffectGetTextureRoute
    let basicEffectSetTexture: BasicEffectSetTextureRoute
    let alphaTestEffectCreate: AlphaTestEffectCreateRoute
    let alphaTestEffectGetDiffuseColor: AlphaTestEffectGetDiffuseColorRoute
    let alphaTestEffectSetDiffuseColor: AlphaTestEffectSetDiffuseColorRoute
    let alphaTestEffectGetAlpha: AlphaTestEffectGetAlphaRoute
    let alphaTestEffectSetAlpha: AlphaTestEffectSetAlphaRoute
    let alphaTestEffectGetTexture: AlphaTestEffectGetTextureRoute
    let alphaTestEffectSetTexture: AlphaTestEffectSetTextureRoute
    let alphaTestEffectGetVertexColorEnabled: AlphaTestEffectGetVertexColorEnabledRoute
    let alphaTestEffectSetVertexColorEnabled: AlphaTestEffectSetVertexColorEnabledRoute
    let alphaTestEffectGetAlphaFunction: AlphaTestEffectGetAlphaFunctionRoute
    let alphaTestEffectSetAlphaFunction: AlphaTestEffectSetAlphaFunctionRoute
    let alphaTestEffectGetReferenceAlpha: AlphaTestEffectGetReferenceAlphaRoute
    let alphaTestEffectSetReferenceAlpha: AlphaTestEffectSetReferenceAlphaRoute
    let dualTextureEffectCreate: DualTextureEffectCreateRoute
    let dualTextureEffectGetDiffuseColor: DualTextureEffectGetDiffuseColorRoute
    let dualTextureEffectSetDiffuseColor: DualTextureEffectSetDiffuseColorRoute
    let dualTextureEffectGetAlpha: DualTextureEffectGetAlphaRoute
    let dualTextureEffectSetAlpha: DualTextureEffectSetAlphaRoute
    let dualTextureEffectGetTexture: DualTextureEffectGetTextureRoute
    let dualTextureEffectSetTexture: DualTextureEffectSetTextureRoute
    let dualTextureEffectGetVertexColorEnabled: DualTextureEffectGetVertexColorEnabledRoute
    let dualTextureEffectSetVertexColorEnabled: DualTextureEffectSetVertexColorEnabledRoute
    let environmentMapEffectCreate: EnvironmentMapEffectCreateRoute
    let environmentMapEffectGetDiffuseColor: EnvironmentMapEffectGetDiffuseColorRoute
    let environmentMapEffectSetDiffuseColor: EnvironmentMapEffectSetDiffuseColorRoute
    let environmentMapEffectGetEmissiveColor: EnvironmentMapEffectGetEmissiveColorRoute
    let environmentMapEffectSetEmissiveColor: EnvironmentMapEffectSetEmissiveColorRoute
    let environmentMapEffectGetAlpha: EnvironmentMapEffectGetAlphaRoute
    let environmentMapEffectSetAlpha: EnvironmentMapEffectSetAlphaRoute
    let environmentMapEffectGetTexture: EnvironmentMapEffectGetTextureRoute
    let environmentMapEffectSetTexture: EnvironmentMapEffectSetTextureRoute
    let environmentMapEffectGetEnvironmentMap: EnvironmentMapEffectGetEnvironmentMapRoute
    let environmentMapEffectSetEnvironmentMap: EnvironmentMapEffectSetEnvironmentMapRoute
    let environmentMapEffectGetAmount: EnvironmentMapEffectGetAmountRoute
    let environmentMapEffectSetAmount: EnvironmentMapEffectSetAmountRoute
    let environmentMapEffectGetSpecular: EnvironmentMapEffectGetSpecularRoute
    let environmentMapEffectSetSpecular: EnvironmentMapEffectSetSpecularRoute
    let environmentMapEffectGetFresnelFactor: EnvironmentMapEffectGetFresnelFactorRoute
    let environmentMapEffectSetFresnelFactor: EnvironmentMapEffectSetFresnelFactorRoute
    let skinnedEffectCreate: SkinnedEffectCreateRoute
    let skinnedEffectGetDiffuseColor: SkinnedEffectGetDiffuseColorRoute
    let skinnedEffectSetDiffuseColor: SkinnedEffectSetDiffuseColorRoute
    let skinnedEffectGetEmissiveColor: SkinnedEffectGetEmissiveColorRoute
    let skinnedEffectSetEmissiveColor: SkinnedEffectSetEmissiveColorRoute
    let skinnedEffectGetSpecularColor: SkinnedEffectGetSpecularColorRoute
    let skinnedEffectSetSpecularColor: SkinnedEffectSetSpecularColorRoute
    let skinnedEffectGetSpecularPower: SkinnedEffectGetSpecularPowerRoute
    let skinnedEffectSetSpecularPower: SkinnedEffectSetSpecularPowerRoute
    let skinnedEffectGetAlpha: SkinnedEffectGetAlphaRoute
    let skinnedEffectSetAlpha: SkinnedEffectSetAlphaRoute
    let skinnedEffectGetPreferPerPixelLighting: SkinnedEffectGetPreferPerPixelLightingRoute
    let skinnedEffectSetPreferPerPixelLighting: SkinnedEffectSetPreferPerPixelLightingRoute
    let skinnedEffectGetTexture: SkinnedEffectGetTextureRoute
    let skinnedEffectSetTexture: SkinnedEffectSetTextureRoute
    let skinnedEffectGetWeightsPerVertex: SkinnedEffectGetWeightsPerVertexRoute
    let skinnedEffectSetWeightsPerVertex: SkinnedEffectSetWeightsPerVertexRoute
    let skinnedEffectSetBoneTransforms: SkinnedEffectSetBoneTransformsRoute
    let skinnedEffectCopyBoneTransforms: SkinnedEffectCopyBoneTransformsRoute
    let effectCreateEmpty: EffectCreateEmptyRoute
    let effectCreateCompiled: EffectCreateCompiledRoute
    let effectDestroy: EffectDestroyRoute
    let effectClone: EffectCloneRoute
    let effectDisposeResources: EffectDisposeRoute
    let effectApply: EffectApplyRoute
    let effectGetParameters: EffectGetParametersRoute
    let effectGetTechniques: EffectGetTechniquesRoute
    let effectGetCurrentTechnique: EffectGetCurrentTechniqueRoute
    let effectSetCurrentTechnique: EffectSetCurrentTechniqueRoute
    let effectGetGraphicsDevice: EffectGetGraphicsDeviceRoute
    let effectTechniqueDestroy: EffectTechniqueDestroyRoute
    let effectTechniqueGetNameByteCount: EffectTechniqueGetNameByteCountRoute
    let effectTechniqueCopyName: EffectTechniqueCopyNameRoute
    let effectTechniqueGetPasses: EffectTechniqueGetPassesRoute
    let effectTechniqueGetAnnotations: EffectTechniqueGetAnnotationsRoute
    let effectTechniqueCollectionDestroy: EffectTechniqueCollectionDestroyRoute
    let effectTechniqueCollectionGetCount: EffectTechniqueCollectionGetCountRoute
    let effectTechniqueCollectionGetAt: EffectTechniqueCollectionGetAtRoute
    let effectPassDestroy: EffectPassDestroyRoute
    let effectPassGetNameByteCount: EffectPassGetNameByteCountRoute
    let effectPassCopyName: EffectPassCopyNameRoute
    let effectPassGetAnnotations: EffectPassGetAnnotationsRoute
    let effectPassApply: EffectPassApplyRoute
    let effectPassCollectionDestroy: EffectPassCollectionDestroyRoute
    let effectPassCollectionGetCount: EffectPassCollectionGetCountRoute
    let effectPassCollectionGetAt: EffectPassCollectionGetAtRoute
    let effectParameterDestroy: EffectParameterDestroyRoute
    let effectParameterGetInfo: EffectParameterGetInfoRoute
    let effectParameterGetNameByteCount: EffectParameterGetNameByteCountRoute
    let effectParameterCopyName: EffectParameterCopyNameRoute
    let effectParameterGetSemanticByteCount: EffectParameterGetSemanticByteCountRoute
    let effectParameterCopySemantic: EffectParameterCopySemanticRoute
    let effectParameterGetElements: EffectParameterGetElementsRoute
    let effectParameterGetStructureMembers: EffectParameterGetStructureMembersRoute
    let effectParameterGetAnnotations: EffectParameterGetAnnotationsRoute
    let effectParameterGetValue: EffectParameterGetValueRoute
    let effectParameterSetValue: EffectParameterSetValueRoute
    let effectParameterGetValues: EffectParameterGetValuesRoute
    let effectParameterSetValues: EffectParameterSetValuesRoute
    let effectParameterGetValueStringByteCount: EffectParameterGetValueStringByteCountRoute
    let effectParameterCopyValueString: EffectParameterCopyValueStringRoute
    let effectParameterSetValueString: EffectParameterSetValueStringRoute
    let effectParameterGetValueTexture: EffectParameterGetValueTextureRoute
    let effectParameterSetValueTexture: EffectParameterSetValueTextureRoute
    let effectParameterCollectionDestroy: EffectParameterCollectionDestroyRoute
    let effectParameterCollectionGetCount: EffectParameterCollectionGetCountRoute
    let effectParameterCollectionGetAt: EffectParameterCollectionGetAtRoute
    let effectAnnotationDestroy: EffectAnnotationDestroyRoute
    let effectAnnotationGetInfo: EffectAnnotationGetInfoRoute
    let effectAnnotationGetNameByteCount: EffectAnnotationGetNameByteCountRoute
    let effectAnnotationCopyName: EffectAnnotationCopyNameRoute
    let effectAnnotationGetSemanticByteCount: EffectAnnotationGetSemanticByteCountRoute
    let effectAnnotationCopySemantic: EffectAnnotationCopySemanticRoute
    let effectAnnotationGetValueBoolean: EffectAnnotationGetValueBooleanRoute
    let effectAnnotationGetValueInt32: EffectAnnotationGetValueInt32Route
    let effectAnnotationGetValueSingle: EffectAnnotationGetValueSingleRoute
    let effectAnnotationGetValueVector2: EffectAnnotationGetValueVector2Route
    let effectAnnotationGetValueVector3: EffectAnnotationGetValueVector3Route
    let effectAnnotationGetValueVector4: EffectAnnotationGetValueVector4Route
    let effectAnnotationGetValueMatrix: EffectAnnotationGetValueMatrixRoute
    let effectAnnotationGetValueStringByteCount: EffectAnnotationGetValueStringByteCountRoute
    let effectAnnotationCopyValueString: EffectAnnotationCopyValueStringRoute
    let effectAnnotationCollectionDestroy: EffectAnnotationCollectionDestroyRoute
    let effectAnnotationCollectionGetCount: EffectAnnotationCollectionGetCountRoute
    let effectAnnotationCollectionGetAt: EffectAnnotationCollectionGetAtRoute
    let graphicsDeviceClearOptions: GraphicsDeviceClearOptionsRoute
    let graphicsDeviceCreate: GraphicsDeviceCreateRoute
    let graphicsDeviceDestroy: GraphicsDeviceDestroyRoute
    let graphicsDeviceGetIsDisposed: GraphicsDeviceGetIsDisposedRoute
    let graphicsDeviceDispose: GraphicsDeviceDisposeRoute
    let graphicsDevicePresent: GraphicsDevicePresentRoute
    let graphicsDeviceReset: GraphicsDeviceResetRoute
    let graphicsDeviceResetWithParameters: GraphicsDeviceResetWithParametersRoute
    let graphicsDeviceGetPresentationParameters: GraphicsDeviceGetPresentationParametersRoute
    let graphicsDeviceSetViewport: GraphicsDeviceSetViewportRoute
    let graphicsDeviceGetScissorRectangle: GraphicsDeviceGetScissorRectangleRoute
    let graphicsDeviceSetScissorRectangle: GraphicsDeviceSetScissorRectangleRoute
    let graphicsDeviceGetStatus: GraphicsDeviceGetStatusRoute
    let graphicsDeviceGetBlendFactor: GraphicsDeviceGetBlendFactorRoute
    let graphicsDeviceSetBlendFactor: GraphicsDeviceSetBlendFactorRoute
    let graphicsDeviceGetMultiSampleMask: GraphicsDeviceGetMultiSampleMaskRoute
    let graphicsDeviceSetMultiSampleMask: GraphicsDeviceSetMultiSampleMaskRoute
    let graphicsDeviceGetReferenceStencil: GraphicsDeviceGetReferenceStencilRoute
    let graphicsDeviceSetReferenceStencil: GraphicsDeviceSetReferenceStencilRoute
    let graphicsDeviceGetBlendState: GraphicsDeviceGetBlendStateRoute
    let graphicsDeviceSetBlendState: GraphicsDeviceSetBlendStateRoute
    let graphicsDeviceGetDepthStencilState: GraphicsDeviceGetDepthStencilStateRoute
    let graphicsDeviceSetDepthStencilState: GraphicsDeviceSetDepthStencilStateRoute
    let graphicsDeviceGetRasterizerState: GraphicsDeviceGetRasterizerStateRoute
    let graphicsDeviceSetRasterizerState: GraphicsDeviceSetRasterizerStateRoute
    let graphicsDeviceGetSamplerState: GraphicsDeviceGetSamplerStateRoute
    let graphicsDeviceSetSamplerState: GraphicsDeviceSetSamplerStateRoute
    let renderTargetSubscribeContentLost: RenderTargetSubscribeContentLostRoute
    let renderTargetUnsubscribeContentLost: RenderTargetUnsubscribeContentLostRoute
    let gameTick: GameTickRoute
    let gameSuppressDraw: GameSuppressDrawRoute
    let gameResetElapsedTime: GameResetElapsedTimeRoute
    let gameGetIsActive: GameGetIsActiveRoute
    let gameGetIsMouseVisible: GameGetIsMouseVisibleRoute
    let gameSetIsMouseVisible: GameSetIsMouseVisibleRoute
    let gameGetIsFixedTimeStep: GameGetIsFixedTimeStepRoute
    let gameSetIsFixedTimeStep: GameSetIsFixedTimeStepRoute
    let gameGetTargetElapsedTimeTicks: GameGetTargetElapsedTimeTicksRoute
    let gameSetTargetElapsedTimeTicks: GameSetTargetElapsedTimeTicksRoute
    let gameGetInactiveSleepTimeTicks: GameGetInactiveSleepTimeTicksRoute
    let gameSetInactiveSleepTimeTicks: GameSetInactiveSleepTimeTicksRoute
    let gameSubscribe: GameSubscribeRoute
    let gameUnsubscribe: GameUnsubscribeRoute
    let graphicsManagerCreateDevice: GraphicsDeviceManagerCreateDeviceRoute
    let graphicsManagerBeginDraw: GraphicsDeviceManagerBeginDrawRoute
    let graphicsManagerEndDraw: GraphicsDeviceManagerEndDrawRoute
    let graphicsManagerGetGraphicsDevice: GraphicsDeviceManagerGetGraphicsDeviceRoute
    let graphicsManagerSubscribe: GraphicsDeviceManagerSubscribeRoute

    static func load() throws -> NativeFunctions {
        lock.lock()
        defer { lock.unlock() }
        if let cached { return try cached.get() }
        do {
            let functions = try NativeFunctions()
            cached = .success(functions)
            return functions
        } catch {
            cached = .failure(error)
            throw error
        }
    }

    private init() throws {
        library = try NativeLibrary()
        getABIVersion = try library.resolve("cna_get_abi_version", as: GetAbiVersionRoute.self)
        let actual = getABIVersion()
        guard NativeABI.admits(actual) else {
            throw CNAError.unsupportedABIVersion(
                admitted: NativeABI.admittedDescription,
                actual: NativeABI.describe(actual),
                actualEncoded: actual,
                path: library.admittedPath
            )
        }
        abiVersion = actual

        errorMessageSize = try library.resolve("cna_error_get_last_message_size", as: ErrorGetLastMessageSizeRoute.self)
        errorMessageCopy = try library.resolve("cna_error_copy_last_message", as: ErrorCopyLastMessageRoute.self)
        gameCreate = try library.resolve("cna_game_create", as: GameCreateRoute.self)
        gameSetFrameHooks = try library.resolve("cna_game_set_frame_hooks_ext", as: GameSetFrameHooksExtRoute.self)
        gameRun = try library.resolve("cna_game_run", as: GameRunRoute.self)
        gameRunOneFrame = try library.resolve("cna_game_run_one_frame", as: GameRunOneFrameRoute.self)
        frameworkDispatcherUpdate = try library.resolve("cna_framework_dispatcher_update", as: FrameworkDispatcherUpdateRoute.self)
        titleContainerRead = try library.resolve("cna_title_container_read_ext", as: TitleContainerReadExtRoute.self)
        gameRequestExit = try library.resolve("cna_game_request_exit", as: GameRequestExitRoute.self)
        gameDestroy = try library.resolve("cna_game_destroy", as: GameDestroyRoute.self)
        gameGetGraphicsDevice = try library.resolve("cna_game_get_graphics_device", as: GameGetGraphicsDeviceRoute.self)
        graphicsManagerCreate = try library.resolve("cna_graphics_device_manager_create", as: GraphicsDeviceManagerCreateRoute.self)
        graphicsManagerApplyChanges = try library.resolve("cna_graphics_device_manager_apply_changes", as: GraphicsDeviceManagerApplyChangesRoute.self)
        graphicsManagerSetGraphicsProfile = try library.resolve("cna_graphics_device_manager_set_graphics_profile", as: GraphicsDeviceManagerSetGraphicsProfileRoute.self)
        graphicsManagerSetIsFullScreen = try library.resolve("cna_graphics_device_manager_set_is_full_screen", as: GraphicsDeviceManagerSetIsFullScreenRoute.self)
        graphicsManagerSetPreferMultiSampling = try library.resolve("cna_graphics_device_manager_set_prefer_multi_sampling", as: GraphicsDeviceManagerSetPreferMultiSamplingRoute.self)
        graphicsManagerSetPreferredBackBufferFormat = try library.resolve("cna_graphics_device_manager_set_preferred_back_buffer_format", as: GraphicsDeviceManagerSetPreferredBackBufferFormatRoute.self)
        graphicsManagerSetPreferredBackBufferWidth = try library.resolve("cna_graphics_device_manager_set_preferred_back_buffer_width", as: GraphicsDeviceManagerSetPreferredBackBufferWidthRoute.self)
        graphicsManagerSetPreferredBackBufferHeight = try library.resolve("cna_graphics_device_manager_set_preferred_back_buffer_height", as: GraphicsDeviceManagerSetPreferredBackBufferHeightRoute.self)
        graphicsManagerSetPreferredDepthStencilFormat = try library.resolve("cna_graphics_device_manager_set_preferred_depth_stencil_format", as: GraphicsDeviceManagerSetPreferredDepthStencilFormatRoute.self)
        graphicsManagerSetSynchronizeWithVerticalRetrace = try library.resolve("cna_graphics_device_manager_set_synchronize_with_vertical_retrace", as: GraphicsDeviceManagerSetSynchronizeWithVerticalRetraceRoute.self)
        graphicsManagerSetSupportedOrientations = try library.resolve("cna_graphics_device_manager_set_supported_orientations", as: GraphicsDeviceManagerSetSupportedOrientationsRoute.self)
        graphicsManagerDestroy = try library.resolve("cna_graphics_device_manager_destroy", as: GraphicsDeviceManagerDestroyRoute.self)
        graphicsDeviceGetViewport = try library.resolve("cna_graphics_device_get_viewport", as: GraphicsDeviceGetViewportRoute.self)
        textureCreateMemory = try library.resolve("cna_texture2d_create_from_encoded_memory", as: Texture2dCreateFromEncodedMemoryRoute.self)
        textureGetInfo = try library.resolve("cna_texture2d_get_info", as: Texture2dGetInfoRoute.self)
        textureCreate = try library.resolve("cna_texture2d_create", as: Texture2dCreateRoute.self)
        textureDestroy = try library.resolve("cna_texture2d_destroy", as: Texture2dDestroyRoute.self)
        textureSetData = try library.resolve("cna_texture2d_set_data", as: Texture2dSetDataRoute.self)
        textureGetData = try library.resolve("cna_texture2d_get_data", as: Texture2dGetDataRoute.self)
        textureGetEncodedByteCount = try library.resolve("cna_texture2d_get_encoded_byte_count", as: Texture2dGetEncodedByteCountRoute.self)
        textureCopyEncoded = try library.resolve("cna_texture2d_copy_encoded", as: Texture2dCopyEncodedRoute.self)
        textureCreateCpuOnly = try library.resolve("cna_texture2d_create_cpu_only_rgba8", as: Texture2dCreateCpuOnlyRgba8Route.self)
        vertexDeclarationCreateWithStride = try library.resolve("cna_vertex_declaration_create_with_stride", as: VertexDeclarationCreateWithStrideRoute.self)
        vertexDeclarationDestroy = try library.resolve("cna_vertex_declaration_destroy", as: VertexDeclarationDestroyRoute.self)
        vertexBufferCreate = try library.resolve("cna_vertex_buffer_create", as: VertexBufferCreateRoute.self)
        vertexBufferDestroy = try library.resolve("cna_vertex_buffer_destroy", as: VertexBufferDestroyRoute.self)
        vertexBufferSetDataRawAt = try library.resolve("cna_vertex_buffer_set_data_raw_at", as: VertexBufferSetDataRawAtRoute.self)
        vertexBufferGetDataRaw = try library.resolve("cna_vertex_buffer_get_data_raw", as: VertexBufferGetDataRawRoute.self)
        indexBufferCreate = try library.resolve("cna_index_buffer_create", as: IndexBufferCreateRoute.self)
        indexBufferDestroy = try library.resolve("cna_index_buffer_destroy", as: IndexBufferDestroyRoute.self)
        indexBufferSetDataAt = try library.resolve("cna_index_buffer_set_data_at", as: IndexBufferSetDataAtRoute.self)
        indexBufferGetData = try library.resolve("cna_index_buffer_get_data", as: IndexBufferGetDataRoute.self)
        vertexBufferSetDataRawAtWithOptions = try library.resolve("cna_vertex_buffer_set_data_raw_at_with_options", as: VertexBufferSetDataRawAtWithOptionsRoute.self)
        vertexBufferSubscribeContentLost = try library.resolve("cna_vertex_buffer_subscribe_content_lost", as: VertexBufferSubscribeContentLostRoute.self)
        vertexBufferUnsubscribeContentLost = try library.resolve("cna_vertex_buffer_unsubscribe_content_lost", as: VertexBufferUnsubscribeContentLostRoute.self)
        indexBufferSetData = try library.resolve("cna_index_buffer_set_data", as: IndexBufferSetDataRoute.self)
        indexBufferSubscribeContentLost = try library.resolve("cna_index_buffer_subscribe_content_lost", as: IndexBufferSubscribeContentLostRoute.self)
        indexBufferUnsubscribeContentLost = try library.resolve("cna_index_buffer_unsubscribe_content_lost", as: IndexBufferUnsubscribeContentLostRoute.self)
        graphicsDeviceGetGraphicsProfile = try library.resolve("cna_graphics_device_get_graphics_profile", as: GraphicsDeviceGetGraphicsProfileRoute.self)
        graphicsDeviceSetVertexBuffers = try library.resolve("cna_graphics_device_set_vertex_buffers", as: GraphicsDeviceSetVertexBuffersRoute.self)
        graphicsDeviceSetIndexBuffer = try library.resolve("cna_graphics_device_set_index_buffer", as: GraphicsDeviceSetIndexBufferRoute.self)
        textureCubeCreate = try library.resolve("cna_texturecube_create", as: TexturecubeCreateRoute.self)
        textureCubeDestroy = try library.resolve("cna_texturecube_destroy", as: TexturecubeDestroyRoute.self)
        textureCubeGetInfo = try library.resolve("cna_texturecube_get_info", as: TexturecubeGetInfoRoute.self)
        textureCubeSetData = try library.resolve("cna_texturecube_set_data", as: TexturecubeSetDataRoute.self)
        textureCubeGetData = try library.resolve("cna_texturecube_get_data", as: TexturecubeGetDataRoute.self)
        texture3DCreate = try library.resolve("cna_texture3d_create", as: Texture3dCreateRoute.self)
        texture3DDestroy = try library.resolve("cna_texture3d_destroy", as: Texture3dDestroyRoute.self)
        texture3DGetInfo = try library.resolve("cna_texture3d_get_info", as: Texture3dGetInfoRoute.self)
        texture3DSetData = try library.resolve("cna_texture3d_set_data", as: Texture3dSetDataRoute.self)
        texture3DGetData = try library.resolve("cna_texture3d_get_data", as: Texture3dGetDataRoute.self)
        spriteBatchCreate = try library.resolve("cna_sprite_batch_create", as: SpriteBatchCreateRoute.self)
        spriteBatchBeginWithEffect = try library.resolve("cna_sprite_batch_begin_with_effect", as: SpriteBatchBeginWithEffectRoute.self)
        spriteBatchBeginWithStates = try library.resolve("cna_sprite_batch_begin_with_states", as: SpriteBatchBeginWithStatesRoute.self)
        spriteBatchSubmitScaled = try library.resolve("cna_sprite_batch_submit_scaled_many", as: SpriteBatchSubmitScaledManyRoute.self)
        spriteFontCreate = try library.resolve("cna_sprite_font_create", as: SpriteFontCreateRoute.self)
        spriteFontDestroy = try library.resolve("cna_sprite_font_destroy", as: SpriteFontDestroyRoute.self)
        spriteFontGetInfo = try library.resolve("cna_sprite_font_get_info", as: SpriteFontGetInfoRoute.self)
        spriteFontCopyCharacters = try library.resolve("cna_sprite_font_copy_characters", as: SpriteFontCopyCharactersRoute.self)
        spriteFontCopyGlyphs = try library.resolve("cna_sprite_font_copy_glyphs", as: SpriteFontCopyGlyphsRoute.self)
        spriteFontSetDefaultCharacter = try library.resolve("cna_sprite_font_set_default_character", as: SpriteFontSetDefaultCharacterRoute.self)
        spriteFontSetLineSpacing = try library.resolve("cna_sprite_font_set_line_spacing", as: SpriteFontSetLineSpacingRoute.self)
        spriteFontSetSpacing = try library.resolve("cna_sprite_font_set_spacing", as: SpriteFontSetSpacingRoute.self)
        spriteBatchDrawString = try library.resolve("cna_sprite_batch_draw_string", as: SpriteBatchDrawStringRoute.self)
        spriteBatchSubmit = try library.resolve("cna_sprite_batch_submit_many", as: SpriteBatchSubmitManyRoute.self)
        spriteBatchEnd = try library.resolve("cna_sprite_batch_end", as: SpriteBatchEndRoute.self)
        spriteBatchDestroy = try library.resolve("cna_sprite_batch_destroy", as: SpriteBatchDestroyRoute.self)
        graphicsAdapterGetCount = try library.resolve("cna_graphics_adapter_get_count", as: GraphicsAdapterGetCountRoute.self)
        graphicsAdapterGetInfo = try library.resolve("cna_graphics_adapter_get_info", as: GraphicsAdapterGetInfoRoute.self)
        graphicsAdapterCopyDescription = try library.resolve("cna_graphics_adapter_copy_description", as: GraphicsAdapterCopyDescriptionRoute.self)
        graphicsAdapterCopyDeviceName = try library.resolve("cna_graphics_adapter_copy_device_name", as: GraphicsAdapterCopyDeviceNameRoute.self)
        graphicsAdapterGetCurrentDisplayMode = try library.resolve("cna_graphics_adapter_get_current_display_mode", as: GraphicsAdapterGetCurrentDisplayModeRoute.self)
        graphicsAdapterGetDisplayModeCount = try library.resolve("cna_graphics_adapter_get_display_mode_count", as: GraphicsAdapterGetDisplayModeCountRoute.self)
        graphicsAdapterCopyDisplayModes = try library.resolve("cna_graphics_adapter_copy_display_modes", as: GraphicsAdapterCopyDisplayModesRoute.self)
        graphicsAdapterSetDevicePreferences = try library.resolve("cna_graphics_adapter_set_device_preferences", as: GraphicsAdapterSetDevicePreferencesRoute.self)
        graphicsAdapterIsProfileSupported = try library.resolve("cna_graphics_adapter_is_profile_supported", as: GraphicsAdapterIsProfileSupportedRoute.self)
        graphicsAdapterQueryBackbufferFormat = try library.resolve("cna_graphics_adapter_query_backbuffer_format", as: GraphicsAdapterQueryBackbufferFormatRoute.self)
        graphicsAdapterQueryRenderTargetFormat = try library.resolve("cna_graphics_adapter_query_render_target_format", as: GraphicsAdapterQueryRenderTargetFormatRoute.self)
        gameWindowGetTitleSize = try library.resolve("cna_game_window_get_title_size", as: GameWindowGetTitleSizeRoute.self)
        gameWindowCopyTitle = try library.resolve("cna_game_window_copy_title", as: GameWindowCopyTitleRoute.self)
        gameWindowGetScreenDeviceNameSize = try library.resolve("cna_game_window_get_screen_device_name_size", as: GameWindowGetScreenDeviceNameSizeRoute.self)
        gameWindowCopyScreenDeviceName = try library.resolve("cna_game_window_copy_screen_device_name", as: GameWindowCopyScreenDeviceNameRoute.self)
        gameWindowGetNativeHandle = try library.resolve("cna_game_window_get_native_handle_ext", as: GameWindowGetNativeHandleExtRoute.self)
        gameWindowGetClientBounds = try library.resolve("cna_game_window_get_client_bounds", as: GameWindowGetClientBoundsRoute.self)
        gameWindowGetCurrentOrientation = try library.resolve("cna_game_window_get_current_orientation", as: GameWindowGetCurrentOrientationRoute.self)
        gameWindowGetAllowUserResizing = try library.resolve("cna_game_window_get_allow_user_resizing", as: GameWindowGetAllowUserResizingRoute.self)
        gameWindowSetAllowUserResizing = try library.resolve("cna_game_window_set_allow_user_resizing", as: GameWindowSetAllowUserResizingRoute.self)
        gameWindowBeginScreenDeviceChange = try library.resolve("cna_game_window_begin_screen_device_change", as: GameWindowBeginScreenDeviceChangeRoute.self)
        gameWindowEndScreenDeviceChange = try library.resolve("cna_game_window_end_screen_device_change", as: GameWindowEndScreenDeviceChangeRoute.self)
        gameSetWindowTitle = try library.resolve("cna_game_set_window_title", as: GameSetWindowTitleRoute.self)
        contentManagerCreate = try library.resolve("cna_content_manager_create", as: ContentManagerCreateRoute.self)
        contentManagerDestroy = try library.resolve("cna_content_manager_destroy", as: ContentManagerDestroyRoute.self)
        contentManagerUnload = try library.resolve("cna_content_manager_unload", as: ContentManagerUnloadRoute.self)
        contentManagerGetRootDirectorySize = try library.resolve("cna_content_manager_get_root_directory_size", as: ContentManagerGetRootDirectorySizeRoute.self)
        contentManagerCopyRootDirectory = try library.resolve("cna_content_manager_copy_root_directory", as: ContentManagerCopyRootDirectoryRoute.self)
        contentManagerLoadTexture2d = try library.resolve("cna_content_manager_load_texture2d", as: ContentManagerLoadTexture2dRoute.self)
        mouseGetState = try library.resolve("cna_mouse_get_state", as: MouseGetStateRoute.self)
        mouseSetPosition = try library.resolve("cna_mouse_set_position", as: MouseSetPositionRoute.self)
        mouseSetWindowHandle = try library.resolve("cna_mouse_set_window_handle", as: MouseSetWindowHandleRoute.self)
        keyboardGetState = try library.resolve("cna_keyboard_get_state", as: KeyboardGetStateRoute.self)
        keyboardGetStateForPlayer = try library.resolve("cna_keyboard_get_state_for_player", as: KeyboardGetStateForPlayerRoute.self)
        gamePadGetState = try library.resolve("cna_gamepad_get_state", as: GamepadGetStateRoute.self)
        gamePadGetStateWithDeadZone = try library.resolve("cna_gamepad_get_state_with_dead_zone", as: GamepadGetStateWithDeadZoneRoute.self)
        gamePadGetCapabilities = try library.resolve("cna_gamepad_get_capabilities", as: GamepadGetCapabilitiesRoute.self)
        gamePadSetVibration = try library.resolve("cna_gamepad_set_vibration", as: GamepadSetVibrationRoute.self)
        textureCommonGetInfo = try library.resolve("cna_texture_get_info", as: TextureGetInfoRoute.self)
        renderTarget2DCreate = try library.resolve("cna_render_target2d_create", as: RenderTarget2dCreateRoute.self)
        occlusionQueryCreate = try library.resolve("cna_occlusion_query_create", as: OcclusionQueryCreateRoute.self)
        occlusionQueryDestroy = try library.resolve("cna_occlusion_query_destroy", as: OcclusionQueryDestroyRoute.self)
        occlusionQueryBegin = try library.resolve("cna_occlusion_query_begin", as: OcclusionQueryBeginRoute.self)
        occlusionQueryEnd = try library.resolve("cna_occlusion_query_end", as: OcclusionQueryEndRoute.self)
        occlusionQueryGetIsComplete = try library.resolve("cna_occlusion_query_get_is_complete", as: OcclusionQueryGetIsCompleteRoute.self)
        occlusionQueryGetPixelCount = try library.resolve("cna_occlusion_query_get_pixel_count", as: OcclusionQueryGetPixelCountRoute.self)
        renderTargetGetInfo = try library.resolve("cna_render_target_get_info", as: RenderTargetGetInfoRoute.self)
        renderTargetDestroy = try library.resolve("cna_render_target_destroy", as: RenderTargetDestroyRoute.self)
        graphicsDeviceSetRenderTarget2D = try library.resolve("cna_graphics_device_set_render_target2d", as: GraphicsDeviceSetRenderTarget2dRoute.self)
        renderTargetCubeCreate = try library.resolve("cna_render_target_cube_create", as: RenderTargetCubeCreateRoute.self)
        graphicsDeviceSetRenderTargetCube = try library.resolve("cna_graphics_device_set_render_target_cube", as: GraphicsDeviceSetRenderTargetCubeRoute.self)
        graphicsDeviceSetRenderTargets = try library.resolve("cna_graphics_device_set_render_targets", as: GraphicsDeviceSetRenderTargetsRoute.self)
        graphicsDeviceGetRenderTargetCount = try library.resolve("cna_graphics_device_get_render_target_count", as: GraphicsDeviceGetRenderTargetCountRoute.self)
        graphicsDeviceGetTexture = try library.resolve("cna_graphics_device_get_texture", as: GraphicsDeviceGetTextureRoute.self)
        graphicsDeviceSetTexture = try library.resolve("cna_graphics_device_set_texture", as: GraphicsDeviceSetTextureRoute.self)
        graphicsDeviceDrawPrimitives = try library.resolve("cna_graphics_device_draw_primitives", as: GraphicsDeviceDrawPrimitivesRoute.self)
        graphicsDeviceDrawIndexedPrimitives = try library.resolve("cna_graphics_device_draw_indexed_primitives", as: GraphicsDeviceDrawIndexedPrimitivesRoute.self)
        graphicsDeviceDrawInstancedPrimitives = try library.resolve("cna_graphics_device_draw_instanced_primitives", as: GraphicsDeviceDrawInstancedPrimitivesRoute.self)
        graphicsDeviceDrawUserPrimitives = try library.resolve("cna_graphics_device_draw_user_primitives", as: GraphicsDeviceDrawUserPrimitivesRoute.self)
        graphicsDeviceDrawUserIndexedPrimitives = try library.resolve("cna_graphics_device_draw_user_indexed_primitives", as: GraphicsDeviceDrawUserIndexedPrimitivesRoute.self)
        primitiveTypeGetVertexCount = try library.resolve("cna_primitive_type_get_vertex_count", as: PrimitiveTypeGetVertexCountRoute.self)
        effectMaterialCreate = try library.resolve("cna_effect_material_create", as: EffectMaterialCreateRoute.self)
        directionalLightDestroy = try library.resolve("cna_directional_light_destroy", as: DirectionalLightDestroyRoute.self)
        directionalLightGetDiffuseColor = try library.resolve("cna_directional_light_get_diffuse_color", as: DirectionalLightGetDiffuseColorRoute.self)
        directionalLightSetDiffuseColor = try library.resolve("cna_directional_light_set_diffuse_color", as: DirectionalLightSetDiffuseColorRoute.self)
        directionalLightGetDirection = try library.resolve("cna_directional_light_get_direction", as: DirectionalLightGetDirectionRoute.self)
        directionalLightSetDirection = try library.resolve("cna_directional_light_set_direction", as: DirectionalLightSetDirectionRoute.self)
        directionalLightGetSpecularColor = try library.resolve("cna_directional_light_get_specular_color", as: DirectionalLightGetSpecularColorRoute.self)
        directionalLightSetSpecularColor = try library.resolve("cna_directional_light_set_specular_color", as: DirectionalLightSetSpecularColorRoute.self)
        directionalLightGetEnabled = try library.resolve("cna_directional_light_get_enabled", as: DirectionalLightGetEnabledRoute.self)
        directionalLightSetEnabled = try library.resolve("cna_directional_light_set_enabled", as: DirectionalLightSetEnabledRoute.self)
        basicEffectCreate = try library.resolve("cna_basic_effect_create", as: BasicEffectCreateRoute.self)
        effectMatricesGetWorld = try library.resolve("cna_effect_matrices_get_world", as: EffectMatricesGetWorldRoute.self)
        effectMatricesSetWorld = try library.resolve("cna_effect_matrices_set_world", as: EffectMatricesSetWorldRoute.self)
        effectMatricesGetView = try library.resolve("cna_effect_matrices_get_view", as: EffectMatricesGetViewRoute.self)
        effectMatricesSetView = try library.resolve("cna_effect_matrices_set_view", as: EffectMatricesSetViewRoute.self)
        effectMatricesGetProjection = try library.resolve("cna_effect_matrices_get_projection", as: EffectMatricesGetProjectionRoute.self)
        effectMatricesSetProjection = try library.resolve("cna_effect_matrices_set_projection", as: EffectMatricesSetProjectionRoute.self)
        effectFogGetColor = try library.resolve("cna_effect_fog_get_color", as: EffectFogGetColorRoute.self)
        effectFogSetColor = try library.resolve("cna_effect_fog_set_color", as: EffectFogSetColorRoute.self)
        effectFogGetEnabled = try library.resolve("cna_effect_fog_get_enabled", as: EffectFogGetEnabledRoute.self)
        effectFogSetEnabled = try library.resolve("cna_effect_fog_set_enabled", as: EffectFogSetEnabledRoute.self)
        effectFogGetStart = try library.resolve("cna_effect_fog_get_start", as: EffectFogGetStartRoute.self)
        effectFogSetStart = try library.resolve("cna_effect_fog_set_start", as: EffectFogSetStartRoute.self)
        effectFogGetEnd = try library.resolve("cna_effect_fog_get_end", as: EffectFogGetEndRoute.self)
        effectFogSetEnd = try library.resolve("cna_effect_fog_set_end", as: EffectFogSetEndRoute.self)
        effectLightsGetAmbientColor = try library.resolve("cna_effect_lights_get_ambient_color", as: EffectLightsGetAmbientColorRoute.self)
        effectLightsSetAmbientColor = try library.resolve("cna_effect_lights_set_ambient_color", as: EffectLightsSetAmbientColorRoute.self)
        effectLightsGetDirectionalLight = try library.resolve("cna_effect_lights_get_directional_light", as: EffectLightsGetDirectionalLightRoute.self)
        effectLightsGetEnabled = try library.resolve("cna_effect_lights_get_enabled", as: EffectLightsGetEnabledRoute.self)
        effectLightsSetEnabled = try library.resolve("cna_effect_lights_set_enabled", as: EffectLightsSetEnabledRoute.self)
        basicEffectGetVertexColorEnabled = try library.resolve("cna_basic_effect_get_vertex_color_enabled", as: BasicEffectGetVertexColorEnabledRoute.self)
        basicEffectSetVertexColorEnabled = try library.resolve("cna_basic_effect_set_vertex_color_enabled", as: BasicEffectSetVertexColorEnabledRoute.self)
        basicEffectGetPreferPerPixelLighting = try library.resolve("cna_basic_effect_get_prefer_per_pixel_lighting", as: BasicEffectGetPreferPerPixelLightingRoute.self)
        basicEffectSetPreferPerPixelLighting = try library.resolve("cna_basic_effect_set_prefer_per_pixel_lighting", as: BasicEffectSetPreferPerPixelLightingRoute.self)
        basicEffectGetDiffuseColor = try library.resolve("cna_basic_effect_get_diffuse_color", as: BasicEffectGetDiffuseColorRoute.self)
        basicEffectSetDiffuseColor = try library.resolve("cna_basic_effect_set_diffuse_color", as: BasicEffectSetDiffuseColorRoute.self)
        basicEffectGetEmissiveColor = try library.resolve("cna_basic_effect_get_emissive_color", as: BasicEffectGetEmissiveColorRoute.self)
        basicEffectSetEmissiveColor = try library.resolve("cna_basic_effect_set_emissive_color", as: BasicEffectSetEmissiveColorRoute.self)
        basicEffectGetSpecularColor = try library.resolve("cna_basic_effect_get_specular_color", as: BasicEffectGetSpecularColorRoute.self)
        basicEffectSetSpecularColor = try library.resolve("cna_basic_effect_set_specular_color", as: BasicEffectSetSpecularColorRoute.self)
        basicEffectGetSpecularPower = try library.resolve("cna_basic_effect_get_specular_power", as: BasicEffectGetSpecularPowerRoute.self)
        basicEffectSetSpecularPower = try library.resolve("cna_basic_effect_set_specular_power", as: BasicEffectSetSpecularPowerRoute.self)
        basicEffectGetAlpha = try library.resolve("cna_basic_effect_get_alpha", as: BasicEffectGetAlphaRoute.self)
        basicEffectSetAlpha = try library.resolve("cna_basic_effect_set_alpha", as: BasicEffectSetAlphaRoute.self)
        basicEffectGetTextureEnabled = try library.resolve("cna_basic_effect_get_texture_enabled", as: BasicEffectGetTextureEnabledRoute.self)
        basicEffectSetTextureEnabled = try library.resolve("cna_basic_effect_set_texture_enabled", as: BasicEffectSetTextureEnabledRoute.self)
        basicEffectGetTexture = try library.resolve("cna_basic_effect_get_texture", as: BasicEffectGetTextureRoute.self)
        basicEffectSetTexture = try library.resolve("cna_basic_effect_set_texture", as: BasicEffectSetTextureRoute.self)
        alphaTestEffectCreate = try library.resolve("cna_alpha_test_effect_create", as: AlphaTestEffectCreateRoute.self)
        alphaTestEffectGetDiffuseColor = try library.resolve("cna_alpha_test_effect_get_diffuse_color", as: AlphaTestEffectGetDiffuseColorRoute.self)
        alphaTestEffectSetDiffuseColor = try library.resolve("cna_alpha_test_effect_set_diffuse_color", as: AlphaTestEffectSetDiffuseColorRoute.self)
        alphaTestEffectGetAlpha = try library.resolve("cna_alpha_test_effect_get_alpha", as: AlphaTestEffectGetAlphaRoute.self)
        alphaTestEffectSetAlpha = try library.resolve("cna_alpha_test_effect_set_alpha", as: AlphaTestEffectSetAlphaRoute.self)
        alphaTestEffectGetTexture = try library.resolve("cna_alpha_test_effect_get_texture", as: AlphaTestEffectGetTextureRoute.self)
        alphaTestEffectSetTexture = try library.resolve("cna_alpha_test_effect_set_texture", as: AlphaTestEffectSetTextureRoute.self)
        alphaTestEffectGetVertexColorEnabled = try library.resolve("cna_alpha_test_effect_get_vertex_color_enabled", as: AlphaTestEffectGetVertexColorEnabledRoute.self)
        alphaTestEffectSetVertexColorEnabled = try library.resolve("cna_alpha_test_effect_set_vertex_color_enabled", as: AlphaTestEffectSetVertexColorEnabledRoute.self)
        alphaTestEffectGetAlphaFunction = try library.resolve("cna_alpha_test_effect_get_alpha_function", as: AlphaTestEffectGetAlphaFunctionRoute.self)
        alphaTestEffectSetAlphaFunction = try library.resolve("cna_alpha_test_effect_set_alpha_function", as: AlphaTestEffectSetAlphaFunctionRoute.self)
        alphaTestEffectGetReferenceAlpha = try library.resolve("cna_alpha_test_effect_get_reference_alpha", as: AlphaTestEffectGetReferenceAlphaRoute.self)
        alphaTestEffectSetReferenceAlpha = try library.resolve("cna_alpha_test_effect_set_reference_alpha", as: AlphaTestEffectSetReferenceAlphaRoute.self)
        dualTextureEffectCreate = try library.resolve("cna_dual_texture_effect_create", as: DualTextureEffectCreateRoute.self)
        dualTextureEffectGetDiffuseColor = try library.resolve("cna_dual_texture_effect_get_diffuse_color", as: DualTextureEffectGetDiffuseColorRoute.self)
        dualTextureEffectSetDiffuseColor = try library.resolve("cna_dual_texture_effect_set_diffuse_color", as: DualTextureEffectSetDiffuseColorRoute.self)
        dualTextureEffectGetAlpha = try library.resolve("cna_dual_texture_effect_get_alpha", as: DualTextureEffectGetAlphaRoute.self)
        dualTextureEffectSetAlpha = try library.resolve("cna_dual_texture_effect_set_alpha", as: DualTextureEffectSetAlphaRoute.self)
        dualTextureEffectGetTexture = try library.resolve("cna_dual_texture_effect_get_texture", as: DualTextureEffectGetTextureRoute.self)
        dualTextureEffectSetTexture = try library.resolve("cna_dual_texture_effect_set_texture", as: DualTextureEffectSetTextureRoute.self)
        dualTextureEffectGetVertexColorEnabled = try library.resolve("cna_dual_texture_effect_get_vertex_color_enabled", as: DualTextureEffectGetVertexColorEnabledRoute.self)
        dualTextureEffectSetVertexColorEnabled = try library.resolve("cna_dual_texture_effect_set_vertex_color_enabled", as: DualTextureEffectSetVertexColorEnabledRoute.self)
        environmentMapEffectCreate = try library.resolve("cna_environment_map_effect_create", as: EnvironmentMapEffectCreateRoute.self)
        environmentMapEffectGetDiffuseColor = try library.resolve("cna_environment_map_effect_get_diffuse_color", as: EnvironmentMapEffectGetDiffuseColorRoute.self)
        environmentMapEffectSetDiffuseColor = try library.resolve("cna_environment_map_effect_set_diffuse_color", as: EnvironmentMapEffectSetDiffuseColorRoute.self)
        environmentMapEffectGetEmissiveColor = try library.resolve("cna_environment_map_effect_get_emissive_color", as: EnvironmentMapEffectGetEmissiveColorRoute.self)
        environmentMapEffectSetEmissiveColor = try library.resolve("cna_environment_map_effect_set_emissive_color", as: EnvironmentMapEffectSetEmissiveColorRoute.self)
        environmentMapEffectGetAlpha = try library.resolve("cna_environment_map_effect_get_alpha", as: EnvironmentMapEffectGetAlphaRoute.self)
        environmentMapEffectSetAlpha = try library.resolve("cna_environment_map_effect_set_alpha", as: EnvironmentMapEffectSetAlphaRoute.self)
        environmentMapEffectGetTexture = try library.resolve("cna_environment_map_effect_get_texture", as: EnvironmentMapEffectGetTextureRoute.self)
        environmentMapEffectSetTexture = try library.resolve("cna_environment_map_effect_set_texture", as: EnvironmentMapEffectSetTextureRoute.self)
        environmentMapEffectGetEnvironmentMap = try library.resolve("cna_environment_map_effect_get_environment_map", as: EnvironmentMapEffectGetEnvironmentMapRoute.self)
        environmentMapEffectSetEnvironmentMap = try library.resolve("cna_environment_map_effect_set_environment_map", as: EnvironmentMapEffectSetEnvironmentMapRoute.self)
        environmentMapEffectGetAmount = try library.resolve("cna_environment_map_effect_get_amount", as: EnvironmentMapEffectGetAmountRoute.self)
        environmentMapEffectSetAmount = try library.resolve("cna_environment_map_effect_set_amount", as: EnvironmentMapEffectSetAmountRoute.self)
        environmentMapEffectGetSpecular = try library.resolve("cna_environment_map_effect_get_specular", as: EnvironmentMapEffectGetSpecularRoute.self)
        environmentMapEffectSetSpecular = try library.resolve("cna_environment_map_effect_set_specular", as: EnvironmentMapEffectSetSpecularRoute.self)
        environmentMapEffectGetFresnelFactor = try library.resolve("cna_environment_map_effect_get_fresnel_factor", as: EnvironmentMapEffectGetFresnelFactorRoute.self)
        environmentMapEffectSetFresnelFactor = try library.resolve("cna_environment_map_effect_set_fresnel_factor", as: EnvironmentMapEffectSetFresnelFactorRoute.self)
        skinnedEffectCreate = try library.resolve("cna_skinned_effect_create", as: SkinnedEffectCreateRoute.self)
        skinnedEffectGetDiffuseColor = try library.resolve("cna_skinned_effect_get_diffuse_color", as: SkinnedEffectGetDiffuseColorRoute.self)
        skinnedEffectSetDiffuseColor = try library.resolve("cna_skinned_effect_set_diffuse_color", as: SkinnedEffectSetDiffuseColorRoute.self)
        skinnedEffectGetEmissiveColor = try library.resolve("cna_skinned_effect_get_emissive_color", as: SkinnedEffectGetEmissiveColorRoute.self)
        skinnedEffectSetEmissiveColor = try library.resolve("cna_skinned_effect_set_emissive_color", as: SkinnedEffectSetEmissiveColorRoute.self)
        skinnedEffectGetSpecularColor = try library.resolve("cna_skinned_effect_get_specular_color", as: SkinnedEffectGetSpecularColorRoute.self)
        skinnedEffectSetSpecularColor = try library.resolve("cna_skinned_effect_set_specular_color", as: SkinnedEffectSetSpecularColorRoute.self)
        skinnedEffectGetSpecularPower = try library.resolve("cna_skinned_effect_get_specular_power", as: SkinnedEffectGetSpecularPowerRoute.self)
        skinnedEffectSetSpecularPower = try library.resolve("cna_skinned_effect_set_specular_power", as: SkinnedEffectSetSpecularPowerRoute.self)
        skinnedEffectGetAlpha = try library.resolve("cna_skinned_effect_get_alpha", as: SkinnedEffectGetAlphaRoute.self)
        skinnedEffectSetAlpha = try library.resolve("cna_skinned_effect_set_alpha", as: SkinnedEffectSetAlphaRoute.self)
        skinnedEffectGetPreferPerPixelLighting = try library.resolve("cna_skinned_effect_get_prefer_per_pixel_lighting", as: SkinnedEffectGetPreferPerPixelLightingRoute.self)
        skinnedEffectSetPreferPerPixelLighting = try library.resolve("cna_skinned_effect_set_prefer_per_pixel_lighting", as: SkinnedEffectSetPreferPerPixelLightingRoute.self)
        skinnedEffectGetTexture = try library.resolve("cna_skinned_effect_get_texture", as: SkinnedEffectGetTextureRoute.self)
        skinnedEffectSetTexture = try library.resolve("cna_skinned_effect_set_texture", as: SkinnedEffectSetTextureRoute.self)
        skinnedEffectGetWeightsPerVertex = try library.resolve("cna_skinned_effect_get_weights_per_vertex", as: SkinnedEffectGetWeightsPerVertexRoute.self)
        skinnedEffectSetWeightsPerVertex = try library.resolve("cna_skinned_effect_set_weights_per_vertex", as: SkinnedEffectSetWeightsPerVertexRoute.self)
        skinnedEffectSetBoneTransforms = try library.resolve("cna_skinned_effect_set_bone_transforms", as: SkinnedEffectSetBoneTransformsRoute.self)
        skinnedEffectCopyBoneTransforms = try library.resolve("cna_skinned_effect_copy_bone_transforms", as: SkinnedEffectCopyBoneTransformsRoute.self)
        effectCreateEmpty = try library.resolve("cna_effect_create_empty", as: EffectCreateEmptyRoute.self)
        effectCreateCompiled = try library.resolve("cna_effect_create_compiled", as: EffectCreateCompiledRoute.self)
        effectDestroy = try library.resolve("cna_effect_destroy", as: EffectDestroyRoute.self)
        effectClone = try library.resolve("cna_effect_clone", as: EffectCloneRoute.self)
        effectDisposeResources = try library.resolve("cna_effect_dispose", as: EffectDisposeRoute.self)
        effectApply = try library.resolve("cna_effect_apply", as: EffectApplyRoute.self)
        effectGetParameters = try library.resolve("cna_effect_get_parameters", as: EffectGetParametersRoute.self)
        effectGetTechniques = try library.resolve("cna_effect_get_techniques", as: EffectGetTechniquesRoute.self)
        effectGetCurrentTechnique = try library.resolve("cna_effect_get_current_technique", as: EffectGetCurrentTechniqueRoute.self)
        effectSetCurrentTechnique = try library.resolve("cna_effect_set_current_technique", as: EffectSetCurrentTechniqueRoute.self)
        effectGetGraphicsDevice = try library.resolve("cna_effect_get_graphics_device", as: EffectGetGraphicsDeviceRoute.self)
        effectTechniqueDestroy = try library.resolve("cna_effect_technique_destroy", as: EffectTechniqueDestroyRoute.self)
        effectTechniqueGetNameByteCount = try library.resolve("cna_effect_technique_get_name_byte_count", as: EffectTechniqueGetNameByteCountRoute.self)
        effectTechniqueCopyName = try library.resolve("cna_effect_technique_copy_name", as: EffectTechniqueCopyNameRoute.self)
        effectTechniqueGetPasses = try library.resolve("cna_effect_technique_get_passes", as: EffectTechniqueGetPassesRoute.self)
        effectTechniqueGetAnnotations = try library.resolve("cna_effect_technique_get_annotations", as: EffectTechniqueGetAnnotationsRoute.self)
        effectTechniqueCollectionDestroy = try library.resolve("cna_effect_technique_collection_destroy", as: EffectTechniqueCollectionDestroyRoute.self)
        effectTechniqueCollectionGetCount = try library.resolve("cna_effect_technique_collection_get_count", as: EffectTechniqueCollectionGetCountRoute.self)
        effectTechniqueCollectionGetAt = try library.resolve("cna_effect_technique_collection_get_at", as: EffectTechniqueCollectionGetAtRoute.self)
        effectPassDestroy = try library.resolve("cna_effect_pass_destroy", as: EffectPassDestroyRoute.self)
        effectPassGetNameByteCount = try library.resolve("cna_effect_pass_get_name_byte_count", as: EffectPassGetNameByteCountRoute.self)
        effectPassCopyName = try library.resolve("cna_effect_pass_copy_name", as: EffectPassCopyNameRoute.self)
        effectPassGetAnnotations = try library.resolve("cna_effect_pass_get_annotations", as: EffectPassGetAnnotationsRoute.self)
        effectPassApply = try library.resolve("cna_effect_pass_apply", as: EffectPassApplyRoute.self)
        effectPassCollectionDestroy = try library.resolve("cna_effect_pass_collection_destroy", as: EffectPassCollectionDestroyRoute.self)
        effectPassCollectionGetCount = try library.resolve("cna_effect_pass_collection_get_count", as: EffectPassCollectionGetCountRoute.self)
        effectPassCollectionGetAt = try library.resolve("cna_effect_pass_collection_get_at", as: EffectPassCollectionGetAtRoute.self)
        effectParameterDestroy = try library.resolve("cna_effect_parameter_destroy", as: EffectParameterDestroyRoute.self)
        effectParameterGetInfo = try library.resolve("cna_effect_parameter_get_info", as: EffectParameterGetInfoRoute.self)
        effectParameterGetNameByteCount = try library.resolve("cna_effect_parameter_get_name_byte_count", as: EffectParameterGetNameByteCountRoute.self)
        effectParameterCopyName = try library.resolve("cna_effect_parameter_copy_name", as: EffectParameterCopyNameRoute.self)
        effectParameterGetSemanticByteCount = try library.resolve("cna_effect_parameter_get_semantic_byte_count", as: EffectParameterGetSemanticByteCountRoute.self)
        effectParameterCopySemantic = try library.resolve("cna_effect_parameter_copy_semantic", as: EffectParameterCopySemanticRoute.self)
        effectParameterGetElements = try library.resolve("cna_effect_parameter_get_elements", as: EffectParameterGetElementsRoute.self)
        effectParameterGetStructureMembers = try library.resolve("cna_effect_parameter_get_structure_members", as: EffectParameterGetStructureMembersRoute.self)
        effectParameterGetAnnotations = try library.resolve("cna_effect_parameter_get_annotations", as: EffectParameterGetAnnotationsRoute.self)
        effectParameterGetValue = try library.resolve("cna_effect_parameter_get_value", as: EffectParameterGetValueRoute.self)
        effectParameterSetValue = try library.resolve("cna_effect_parameter_set_value", as: EffectParameterSetValueRoute.self)
        effectParameterGetValues = try library.resolve("cna_effect_parameter_get_values", as: EffectParameterGetValuesRoute.self)
        effectParameterSetValues = try library.resolve("cna_effect_parameter_set_values", as: EffectParameterSetValuesRoute.self)
        effectParameterGetValueStringByteCount = try library.resolve("cna_effect_parameter_get_value_string_byte_count", as: EffectParameterGetValueStringByteCountRoute.self)
        effectParameterCopyValueString = try library.resolve("cna_effect_parameter_copy_value_string", as: EffectParameterCopyValueStringRoute.self)
        effectParameterSetValueString = try library.resolve("cna_effect_parameter_set_value_string", as: EffectParameterSetValueStringRoute.self)
        effectParameterGetValueTexture = try library.resolve("cna_effect_parameter_get_value_texture", as: EffectParameterGetValueTextureRoute.self)
        effectParameterSetValueTexture = try library.resolve("cna_effect_parameter_set_value_texture", as: EffectParameterSetValueTextureRoute.self)
        effectParameterCollectionDestroy = try library.resolve("cna_effect_parameter_collection_destroy", as: EffectParameterCollectionDestroyRoute.self)
        effectParameterCollectionGetCount = try library.resolve("cna_effect_parameter_collection_get_count", as: EffectParameterCollectionGetCountRoute.self)
        effectParameterCollectionGetAt = try library.resolve("cna_effect_parameter_collection_get_at", as: EffectParameterCollectionGetAtRoute.self)
        effectAnnotationDestroy = try library.resolve("cna_effect_annotation_destroy", as: EffectAnnotationDestroyRoute.self)
        effectAnnotationGetInfo = try library.resolve("cna_effect_annotation_get_info", as: EffectAnnotationGetInfoRoute.self)
        effectAnnotationGetNameByteCount = try library.resolve("cna_effect_annotation_get_name_byte_count", as: EffectAnnotationGetNameByteCountRoute.self)
        effectAnnotationCopyName = try library.resolve("cna_effect_annotation_copy_name", as: EffectAnnotationCopyNameRoute.self)
        effectAnnotationGetSemanticByteCount = try library.resolve("cna_effect_annotation_get_semantic_byte_count", as: EffectAnnotationGetSemanticByteCountRoute.self)
        effectAnnotationCopySemantic = try library.resolve("cna_effect_annotation_copy_semantic", as: EffectAnnotationCopySemanticRoute.self)
        effectAnnotationGetValueBoolean = try library.resolve("cna_effect_annotation_get_value_boolean", as: EffectAnnotationGetValueBooleanRoute.self)
        effectAnnotationGetValueInt32 = try library.resolve("cna_effect_annotation_get_value_int32", as: EffectAnnotationGetValueInt32Route.self)
        effectAnnotationGetValueSingle = try library.resolve("cna_effect_annotation_get_value_single", as: EffectAnnotationGetValueSingleRoute.self)
        effectAnnotationGetValueVector2 = try library.resolve("cna_effect_annotation_get_value_vector2", as: EffectAnnotationGetValueVector2Route.self)
        effectAnnotationGetValueVector3 = try library.resolve("cna_effect_annotation_get_value_vector3", as: EffectAnnotationGetValueVector3Route.self)
        effectAnnotationGetValueVector4 = try library.resolve("cna_effect_annotation_get_value_vector4", as: EffectAnnotationGetValueVector4Route.self)
        effectAnnotationGetValueMatrix = try library.resolve("cna_effect_annotation_get_value_matrix", as: EffectAnnotationGetValueMatrixRoute.self)
        effectAnnotationGetValueStringByteCount = try library.resolve("cna_effect_annotation_get_value_string_byte_count", as: EffectAnnotationGetValueStringByteCountRoute.self)
        effectAnnotationCopyValueString = try library.resolve("cna_effect_annotation_copy_value_string", as: EffectAnnotationCopyValueStringRoute.self)
        effectAnnotationCollectionDestroy = try library.resolve("cna_effect_annotation_collection_destroy", as: EffectAnnotationCollectionDestroyRoute.self)
        effectAnnotationCollectionGetCount = try library.resolve("cna_effect_annotation_collection_get_count", as: EffectAnnotationCollectionGetCountRoute.self)
        effectAnnotationCollectionGetAt = try library.resolve("cna_effect_annotation_collection_get_at", as: EffectAnnotationCollectionGetAtRoute.self)
        graphicsDeviceClearOptions = try library.resolve("cna_graphics_device_clear_options", as: GraphicsDeviceClearOptionsRoute.self)
        graphicsDeviceCreate = try library.resolve("cna_graphics_device_create", as: GraphicsDeviceCreateRoute.self)
        graphicsDeviceDestroy = try library.resolve("cna_graphics_device_destroy", as: GraphicsDeviceDestroyRoute.self)
        graphicsDeviceGetIsDisposed = try library.resolve("cna_graphics_device_get_is_disposed", as: GraphicsDeviceGetIsDisposedRoute.self)
        graphicsDeviceDispose = try library.resolve("cna_graphics_device_dispose", as: GraphicsDeviceDisposeRoute.self)
        graphicsDevicePresent = try library.resolve("cna_graphics_device_present", as: GraphicsDevicePresentRoute.self)
        graphicsDeviceReset = try library.resolve("cna_graphics_device_reset", as: GraphicsDeviceResetRoute.self)
        graphicsDeviceResetWithParameters = try library.resolve("cna_graphics_device_reset_with_parameters", as: GraphicsDeviceResetWithParametersRoute.self)
        graphicsDeviceGetPresentationParameters = try library.resolve("cna_graphics_device_get_presentation_parameters", as: GraphicsDeviceGetPresentationParametersRoute.self)
        graphicsDeviceSetViewport = try library.resolve("cna_graphics_device_set_viewport", as: GraphicsDeviceSetViewportRoute.self)
        graphicsDeviceGetScissorRectangle = try library.resolve("cna_graphics_device_get_scissor_rectangle", as: GraphicsDeviceGetScissorRectangleRoute.self)
        graphicsDeviceSetScissorRectangle = try library.resolve("cna_graphics_device_set_scissor_rectangle", as: GraphicsDeviceSetScissorRectangleRoute.self)
        graphicsDeviceGetStatus = try library.resolve("cna_graphics_device_get_status", as: GraphicsDeviceGetStatusRoute.self)
        graphicsDeviceGetBlendFactor = try library.resolve("cna_graphics_device_get_blend_factor", as: GraphicsDeviceGetBlendFactorRoute.self)
        graphicsDeviceSetBlendFactor = try library.resolve("cna_graphics_device_set_blend_factor", as: GraphicsDeviceSetBlendFactorRoute.self)
        graphicsDeviceGetMultiSampleMask = try library.resolve("cna_graphics_device_get_multi_sample_mask", as: GraphicsDeviceGetMultiSampleMaskRoute.self)
        graphicsDeviceSetMultiSampleMask = try library.resolve("cna_graphics_device_set_multi_sample_mask", as: GraphicsDeviceSetMultiSampleMaskRoute.self)
        graphicsDeviceGetReferenceStencil = try library.resolve("cna_graphics_device_get_reference_stencil", as: GraphicsDeviceGetReferenceStencilRoute.self)
        graphicsDeviceSetReferenceStencil = try library.resolve("cna_graphics_device_set_reference_stencil", as: GraphicsDeviceSetReferenceStencilRoute.self)
        graphicsDeviceGetBlendState = try library.resolve("cna_graphics_device_get_blend_state", as: GraphicsDeviceGetBlendStateRoute.self)
        graphicsDeviceSetBlendState = try library.resolve("cna_graphics_device_set_blend_state", as: GraphicsDeviceSetBlendStateRoute.self)
        graphicsDeviceGetDepthStencilState = try library.resolve("cna_graphics_device_get_depth_stencil_state", as: GraphicsDeviceGetDepthStencilStateRoute.self)
        graphicsDeviceSetDepthStencilState = try library.resolve("cna_graphics_device_set_depth_stencil_state", as: GraphicsDeviceSetDepthStencilStateRoute.self)
        graphicsDeviceGetRasterizerState = try library.resolve("cna_graphics_device_get_rasterizer_state", as: GraphicsDeviceGetRasterizerStateRoute.self)
        graphicsDeviceSetRasterizerState = try library.resolve("cna_graphics_device_set_rasterizer_state", as: GraphicsDeviceSetRasterizerStateRoute.self)
        graphicsDeviceGetSamplerState = try library.resolve("cna_graphics_device_get_sampler_state", as: GraphicsDeviceGetSamplerStateRoute.self)
        graphicsDeviceSetSamplerState = try library.resolve("cna_graphics_device_set_sampler_state", as: GraphicsDeviceSetSamplerStateRoute.self)
        renderTargetSubscribeContentLost = try library.resolve("cna_render_target_subscribe_content_lost", as: RenderTargetSubscribeContentLostRoute.self)
        renderTargetUnsubscribeContentLost = try library.resolve("cna_render_target_unsubscribe_content_lost", as: RenderTargetUnsubscribeContentLostRoute.self)
        gameTick = try library.resolve("cna_game_tick", as: GameTickRoute.self)
        gameSuppressDraw = try library.resolve("cna_game_suppress_draw", as: GameSuppressDrawRoute.self)
        gameResetElapsedTime = try library.resolve("cna_game_reset_elapsed_time", as: GameResetElapsedTimeRoute.self)
        gameGetIsActive = try library.resolve("cna_game_get_is_active", as: GameGetIsActiveRoute.self)
        gameGetIsMouseVisible = try library.resolve("cna_game_get_is_mouse_visible", as: GameGetIsMouseVisibleRoute.self)
        gameSetIsMouseVisible = try library.resolve("cna_game_set_is_mouse_visible", as: GameSetIsMouseVisibleRoute.self)
        gameGetIsFixedTimeStep = try library.resolve("cna_game_get_is_fixed_time_step", as: GameGetIsFixedTimeStepRoute.self)
        gameSetIsFixedTimeStep = try library.resolve("cna_game_set_is_fixed_time_step", as: GameSetIsFixedTimeStepRoute.self)
        gameGetTargetElapsedTimeTicks = try library.resolve("cna_game_get_target_elapsed_time_ticks", as: GameGetTargetElapsedTimeTicksRoute.self)
        gameSetTargetElapsedTimeTicks = try library.resolve("cna_game_set_target_elapsed_time_ticks", as: GameSetTargetElapsedTimeTicksRoute.self)
        gameGetInactiveSleepTimeTicks = try library.resolve("cna_game_get_inactive_sleep_time_ticks", as: GameGetInactiveSleepTimeTicksRoute.self)
        gameSetInactiveSleepTimeTicks = try library.resolve("cna_game_set_inactive_sleep_time_ticks", as: GameSetInactiveSleepTimeTicksRoute.self)
        gameSubscribe = try library.resolve("cna_game_subscribe", as: GameSubscribeRoute.self)
        gameUnsubscribe = try library.resolve("cna_game_unsubscribe", as: GameUnsubscribeRoute.self)
        graphicsManagerCreateDevice = try library.resolve("cna_graphics_device_manager_create_device", as: GraphicsDeviceManagerCreateDeviceRoute.self)
        graphicsManagerBeginDraw = try library.resolve("cna_graphics_device_manager_begin_draw", as: GraphicsDeviceManagerBeginDrawRoute.self)
        graphicsManagerEndDraw = try library.resolve("cna_graphics_device_manager_end_draw", as: GraphicsDeviceManagerEndDrawRoute.self)
        graphicsManagerGetGraphicsDevice = try library.resolve("cna_graphics_device_manager_get_graphics_device", as: GraphicsDeviceManagerGetGraphicsDeviceRoute.self)
        graphicsManagerSubscribe = try library.resolve("cna_graphics_device_manager_subscribe", as: GraphicsDeviceManagerSubscribeRoute.self)
    }

    func check(_ result: UInt32, operation: String) throws {
        guard result == 0 else {
            throw CNAError.nativeFailure(operation: operation, result: result, message: lastErrorMessage())
        }
    }

    private func lastErrorMessage() -> String {
        var size: UInt64 = 0
        guard errorMessageSize(&size) == 0, size > 0, size <= UInt64(Int.max) else { return "no native diagnostic" }
        var bytes = [CChar](repeating: 0, count: Int(size) + 1)
        var required: UInt64 = 0
        let result = bytes.withUnsafeMutableBufferPointer {
            errorMessageCopy($0.baseAddress, size, &required)
        }
        guard result == 0 else { return "native diagnostic copy failed with result \(result)" }
        return String(decoding: bytes.prefix(Int(required)).map { UInt8(bitPattern: $0) }, as: UTF8.self)
    }
}
