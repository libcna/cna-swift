// SPDX-License-Identifier: MIT

import CNAShim
import Foundation

internal final class NativeFunctions {
    static let requiredABIVersion: UInt32 = 0x0000_0700

    typealias GetABIVersion = @convention(c) () -> UInt32
    typealias ErrorMessageSize = @convention(c) (UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias ErrorMessageCopy = @convention(c) (UnsafeMutablePointer<CChar>?, UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameCreate = @convention(c) (UnsafePointer<CNASwift_GameCreateInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias GameSetFrameHooks = @convention(c) (UInt64, UnsafePointer<CNASwift_GameFrameHooks>?) -> UInt32
    typealias HandleOperation = @convention(c) (UInt64) -> UInt32
    typealias HandleOut = @convention(c) (UInt64, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias ViewportGet = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Viewport>?) -> UInt32
    typealias ClearRGBA = @convention(c) (UInt64, Float, Float, Float, Float) -> UInt32
    typealias TextureCreateMemory = @convention(c) (UInt64, UnsafePointer<UInt8>?, UInt64, UnsafePointer<CNASwift_Texture2DDecodeInfo>?, UnsafeMutablePointer<UInt64>?) -> UInt32
    typealias TextureInfoGet = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_Texture2DInfo>?) -> UInt32
    typealias SpriteBegin = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteBatchBeginInfo>?) -> UInt32
    typealias SpriteSubmitScaled = @convention(c) (UInt64, UnsafePointer<CNASwift_SpriteScaledCommand>?, UInt64) -> UInt32
    typealias KeyboardGet = @convention(c) (UInt64, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32
    typealias KeyboardGetPlayer = @convention(c) (UInt64, UInt32, UnsafeMutablePointer<CNASwift_KeyboardState>?) -> UInt32

    private static let lock = NSLock()
    private static var cached: Result<NativeFunctions, Error>?

    let library: NativeLibrary
    let getABIVersion: GetABIVersion
    let errorMessageSize: ErrorMessageSize
    let errorMessageCopy: ErrorMessageCopy
    let gameCreate: GameCreate
    let gameSetFrameHooks: GameSetFrameHooks
    let gameRun: HandleOperation
    let gameRunOneFrame: HandleOperation
    let gameRequestExit: HandleOperation
    let gameDestroy: HandleOperation
    let gameGetGraphicsDevice: HandleOut
    let graphicsManagerCreate: HandleOut
    let graphicsManagerApplyChanges: HandleOperation
    let graphicsManagerDestroy: HandleOperation
    let graphicsDeviceGetViewport: ViewportGet
    let graphicsDeviceClearRGBA: ClearRGBA
    let textureCreateMemory: TextureCreateMemory
    let textureGetInfo: TextureInfoGet
    let textureDestroy: HandleOperation
    let spriteBatchCreate: HandleOut
    let spriteBatchBegin: SpriteBegin
    let spriteBatchSubmitScaled: SpriteSubmitScaled
    let spriteBatchEnd: HandleOperation
    let spriteBatchDestroy: HandleOperation
    let keyboardGetState: KeyboardGet
    let keyboardGetStateForPlayer: KeyboardGetPlayer

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
        getABIVersion = try library.resolve("cna_get_abi_version", as: GetABIVersion.self)
        let actual = getABIVersion()
        guard actual == Self.requiredABIVersion else {
            throw CNAError.unsupportedABIVersion(expected: Self.requiredABIVersion, actual: actual)
        }

        errorMessageSize = try library.resolve("cna_error_get_last_message_size", as: ErrorMessageSize.self)
        errorMessageCopy = try library.resolve("cna_error_copy_last_message", as: ErrorMessageCopy.self)
        gameCreate = try library.resolve("cna_game_create", as: GameCreate.self)
        gameSetFrameHooks = try library.resolve("cna_game_set_frame_hooks_ext", as: GameSetFrameHooks.self)
        gameRun = try library.resolve("cna_game_run", as: HandleOperation.self)
        gameRunOneFrame = try library.resolve("cna_game_run_one_frame", as: HandleOperation.self)
        gameRequestExit = try library.resolve("cna_game_request_exit", as: HandleOperation.self)
        gameDestroy = try library.resolve("cna_game_destroy", as: HandleOperation.self)
        gameGetGraphicsDevice = try library.resolve("cna_game_get_graphics_device", as: HandleOut.self)
        graphicsManagerCreate = try library.resolve("cna_graphics_device_manager_create", as: HandleOut.self)
        graphicsManagerApplyChanges = try library.resolve("cna_graphics_device_manager_apply_changes", as: HandleOperation.self)
        graphicsManagerDestroy = try library.resolve("cna_graphics_device_manager_destroy", as: HandleOperation.self)
        graphicsDeviceGetViewport = try library.resolve("cna_graphics_device_get_viewport", as: ViewportGet.self)
        graphicsDeviceClearRGBA = try library.resolve("cna_graphics_device_clear_rgba", as: ClearRGBA.self)
        textureCreateMemory = try library.resolve("cna_texture2d_create_from_encoded_memory", as: TextureCreateMemory.self)
        textureGetInfo = try library.resolve("cna_texture2d_get_info", as: TextureInfoGet.self)
        textureDestroy = try library.resolve("cna_texture2d_destroy", as: HandleOperation.self)
        spriteBatchCreate = try library.resolve("cna_sprite_batch_create", as: HandleOut.self)
        spriteBatchBegin = try library.resolve("cna_sprite_batch_begin", as: SpriteBegin.self)
        spriteBatchSubmitScaled = try library.resolve("cna_sprite_batch_submit_scaled_many", as: SpriteSubmitScaled.self)
        spriteBatchEnd = try library.resolve("cna_sprite_batch_end", as: HandleOperation.self)
        spriteBatchDestroy = try library.resolve("cna_sprite_batch_destroy", as: HandleOperation.self)
        keyboardGetState = try library.resolve("cna_keyboard_get_state", as: KeyboardGet.self)
        keyboardGetStateForPlayer = try library.resolve("cna_keyboard_get_state_for_player", as: KeyboardGetPlayer.self)
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
