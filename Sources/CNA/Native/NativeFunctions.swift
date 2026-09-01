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
    typealias Texture2dDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias SpriteBatchCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteBatchBeginRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteBatchBeginInfo>?) -> UInt32
    typealias SpriteBatchSubmitScaledManyRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteScaledCommand>?, UInt64) -> UInt32
    typealias SpriteBatchSubmitManyRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteCommand>?, UInt64) -> UInt32
    typealias SpriteBatchEndRoute = @convention(c) (UInt64) -> UInt32
    typealias SpriteBatchDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias KeyboardGetStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias KeyboardGetStateForPlayerRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias GamepadGetStateRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GamePadState>?) -> UInt32
    typealias GamepadGetStateWithDeadZoneRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafeMutablePointer<CNASwift_GamePadState>?) -> UInt32
    typealias GamepadGetCapabilitiesRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GamePadCapabilities>?) -> UInt32
    typealias GamepadSetVibrationRoute = @convention(c) (UInt64, UInt32, Float, Float, UnsafeMutablePointer<UInt8>?) -> UInt32
    typealias TextureGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_TextureInfo>?) -> UInt32
    typealias RenderTarget2dCreateRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_RenderTarget2DCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias RenderTargetGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_RenderTargetInfo>?) -> UInt32
    typealias RenderTargetDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceSetRenderTarget2dRoute = @convention(c) (UInt64, UInt64) -> UInt32
    typealias GraphicsDeviceClearOptionsRoute = @convention(c) (UInt64, UInt32, CNASwift_Color, Float, Int32) -> UInt32
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
    let textureDestroy: Texture2dDestroyRoute
    let spriteBatchCreate: SpriteBatchCreateRoute
    let spriteBatchBegin: SpriteBatchBeginRoute
    let spriteBatchSubmitScaled: SpriteBatchSubmitScaledManyRoute
    let spriteBatchSubmit: SpriteBatchSubmitManyRoute
    let spriteBatchEnd: SpriteBatchEndRoute
    let spriteBatchDestroy: SpriteBatchDestroyRoute
    let keyboardGetState: KeyboardGetStateRoute
    let keyboardGetStateForPlayer: KeyboardGetStateForPlayerRoute
    let gamePadGetState: GamepadGetStateRoute
    let gamePadGetStateWithDeadZone: GamepadGetStateWithDeadZoneRoute
    let gamePadGetCapabilities: GamepadGetCapabilitiesRoute
    let gamePadSetVibration: GamepadSetVibrationRoute
    let textureCommonGetInfo: TextureGetInfoRoute
    let renderTarget2DCreate: RenderTarget2dCreateRoute
    let renderTargetGetInfo: RenderTargetGetInfoRoute
    let renderTargetDestroy: RenderTargetDestroyRoute
    let graphicsDeviceSetRenderTarget2D: GraphicsDeviceSetRenderTarget2dRoute
    let graphicsDeviceClearOptions: GraphicsDeviceClearOptionsRoute
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
        textureDestroy = try library.resolve("cna_texture2d_destroy", as: Texture2dDestroyRoute.self)
        spriteBatchCreate = try library.resolve("cna_sprite_batch_create", as: SpriteBatchCreateRoute.self)
        spriteBatchBegin = try library.resolve("cna_sprite_batch_begin", as: SpriteBatchBeginRoute.self)
        spriteBatchSubmitScaled = try library.resolve("cna_sprite_batch_submit_scaled_many", as: SpriteBatchSubmitScaledManyRoute.self)
        spriteBatchSubmit = try library.resolve("cna_sprite_batch_submit_many", as: SpriteBatchSubmitManyRoute.self)
        spriteBatchEnd = try library.resolve("cna_sprite_batch_end", as: SpriteBatchEndRoute.self)
        spriteBatchDestroy = try library.resolve("cna_sprite_batch_destroy", as: SpriteBatchDestroyRoute.self)
        keyboardGetState = try library.resolve("cna_keyboard_get_state", as: KeyboardGetStateRoute.self)
        keyboardGetStateForPlayer = try library.resolve("cna_keyboard_get_state_for_player", as: KeyboardGetStateForPlayerRoute.self)
        gamePadGetState = try library.resolve("cna_gamepad_get_state", as: GamepadGetStateRoute.self)
        gamePadGetStateWithDeadZone = try library.resolve("cna_gamepad_get_state_with_dead_zone", as: GamepadGetStateWithDeadZoneRoute.self)
        gamePadGetCapabilities = try library.resolve("cna_gamepad_get_capabilities", as: GamepadGetCapabilitiesRoute.self)
        gamePadSetVibration = try library.resolve("cna_gamepad_set_vibration", as: GamepadSetVibrationRoute.self)
        textureCommonGetInfo = try library.resolve("cna_texture_get_info", as: TextureGetInfoRoute.self)
        renderTarget2DCreate = try library.resolve("cna_render_target2d_create", as: RenderTarget2dCreateRoute.self)
        renderTargetGetInfo = try library.resolve("cna_render_target_get_info", as: RenderTargetGetInfoRoute.self)
        renderTargetDestroy = try library.resolve("cna_render_target_destroy", as: RenderTargetDestroyRoute.self)
        graphicsDeviceSetRenderTarget2D = try library.resolve("cna_graphics_device_set_render_target2d", as: GraphicsDeviceSetRenderTarget2dRoute.self)
        graphicsDeviceClearOptions = try library.resolve("cna_graphics_device_clear_options", as: GraphicsDeviceClearOptionsRoute.self)
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
