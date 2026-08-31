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
    typealias GraphicsDeviceManagerDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias GraphicsDeviceGetViewportRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Viewport>?) -> UInt32
    typealias GraphicsDeviceClearRgbaRoute = @convention(c) (UInt64, Float, Float, Float, Float) -> UInt32
    typealias Texture2dCreateFromEncodedMemoryRoute = @convention(c) (UInt64, UnsafePointer<UInt8>?, UInt64, UnsafePointer<CNASwift_Texture2DDecodeInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias Texture2dGetInfoRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Texture2DInfo>?) -> UInt32
    typealias Texture2dDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias SpriteBatchCreateRoute = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias SpriteBatchBeginRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteBatchBeginInfo>?) -> UInt32
    typealias SpriteBatchSubmitScaledManyRoute = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteScaledCommand>?, UInt64) -> UInt32
    typealias SpriteBatchEndRoute = @convention(c) (UInt64) -> UInt32
    typealias SpriteBatchDestroyRoute = @convention(c) (UInt64) -> UInt32
    typealias KeyboardGetStateRoute = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias KeyboardGetStateForPlayerRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias GamepadGetStateRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GamePadState>?) -> UInt32
    typealias GamepadGetStateWithDeadZoneRoute = @convention(c) (UInt64, UInt32, UInt32, UnsafeMutablePointer<CNASwift_GamePadState>?) -> UInt32
    typealias GamepadGetCapabilitiesRoute = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_GamePadCapabilities>?) -> UInt32
    typealias GamepadSetVibrationRoute = @convention(c) (UInt64, UInt32, Float, Float, UnsafeMutablePointer<UInt8>?) -> UInt32

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
    let graphicsManagerDestroy: GraphicsDeviceManagerDestroyRoute
    let graphicsDeviceGetViewport: GraphicsDeviceGetViewportRoute
    let graphicsDeviceClearRGBA: GraphicsDeviceClearRgbaRoute
    let textureCreateMemory: Texture2dCreateFromEncodedMemoryRoute
    let textureGetInfo: Texture2dGetInfoRoute
    let textureDestroy: Texture2dDestroyRoute
    let spriteBatchCreate: SpriteBatchCreateRoute
    let spriteBatchBegin: SpriteBatchBeginRoute
    let spriteBatchSubmitScaled: SpriteBatchSubmitScaledManyRoute
    let spriteBatchEnd: SpriteBatchEndRoute
    let spriteBatchDestroy: SpriteBatchDestroyRoute
    let keyboardGetState: KeyboardGetStateRoute
    let keyboardGetStateForPlayer: KeyboardGetStateForPlayerRoute
    let gamePadGetState: GamepadGetStateRoute
    let gamePadGetStateWithDeadZone: GamepadGetStateWithDeadZoneRoute
    let gamePadGetCapabilities: GamepadGetCapabilitiesRoute
    let gamePadSetVibration: GamepadSetVibrationRoute

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
        graphicsManagerDestroy = try library.resolve("cna_graphics_device_manager_destroy", as: GraphicsDeviceManagerDestroyRoute.self)
        graphicsDeviceGetViewport = try library.resolve("cna_graphics_device_get_viewport", as: GraphicsDeviceGetViewportRoute.self)
        graphicsDeviceClearRGBA = try library.resolve("cna_graphics_device_clear_rgba", as: GraphicsDeviceClearRgbaRoute.self)
        textureCreateMemory = try library.resolve("cna_texture2d_create_from_encoded_memory", as: Texture2dCreateFromEncodedMemoryRoute.self)
        textureGetInfo = try library.resolve("cna_texture2d_get_info", as: Texture2dGetInfoRoute.self)
        textureDestroy = try library.resolve("cna_texture2d_destroy", as: Texture2dDestroyRoute.self)
        spriteBatchCreate = try library.resolve("cna_sprite_batch_create", as: SpriteBatchCreateRoute.self)
        spriteBatchBegin = try library.resolve("cna_sprite_batch_begin", as: SpriteBatchBeginRoute.self)
        spriteBatchSubmitScaled = try library.resolve("cna_sprite_batch_submit_scaled_many", as: SpriteBatchSubmitScaledManyRoute.self)
        spriteBatchEnd = try library.resolve("cna_sprite_batch_end", as: SpriteBatchEndRoute.self)
        spriteBatchDestroy = try library.resolve("cna_sprite_batch_destroy", as: SpriteBatchDestroyRoute.self)
        keyboardGetState = try library.resolve("cna_keyboard_get_state", as: KeyboardGetStateRoute.self)
        keyboardGetStateForPlayer = try library.resolve("cna_keyboard_get_state_for_player", as: KeyboardGetStateForPlayerRoute.self)
        gamePadGetState = try library.resolve("cna_gamepad_get_state", as: GamepadGetStateRoute.self)
        gamePadGetStateWithDeadZone = try library.resolve("cna_gamepad_get_state_with_dead_zone", as: GamepadGetStateWithDeadZoneRoute.self)
        gamePadGetCapabilities = try library.resolve("cna_gamepad_get_capabilities", as: GamepadGetCapabilitiesRoute.self)
        gamePadSetVibration = try library.resolve("cna_gamepad_set_vibration", as: GamepadSetVibrationRoute.self)
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
