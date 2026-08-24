// SPDX-License-Identifier: MIT

internal enum NativeOwnership: String {
    case owned = "OWNED"
    case borrowed = "BORROWED"
    case parentOwned = "PARENT_OWNED"
    case processGlobal = "PROCESS_GLOBAL"
    case managedValue = "MANAGED_VALUE"
}

internal struct NativeManifestEntry {
    let symbol: String
    let cReturn: String
    let cParameters: [String]
    let ownership: NativeOwnership
    let resultLifetime: String
    let errorLifetime: String
    let callbackABI: String?
}

/// The reviewed Foundation-1 function manifest. The corresponding Swift
/// function types live beside `NativeFunctions`, and tools/native_abi compares
/// this metadata and the Clang shim to canonical CNA headers.
internal let nativeManifest: [NativeManifestEntry] = [
    .init(symbol: "cna_get_abi_version", cReturn: "uint32_t", cParameters: [], ownership: .processGlobal, resultLifetime: "value", errorLifetime: "none", callbackABI: nil),
    .init(symbol: "cna_error_get_last_message_size", cReturn: "CNA_Result", cParameters: ["uint64_t* out_bytes"], ownership: .processGlobal, resultLifetime: "value", errorLifetime: "thread-local until next fallible call", callbackABI: nil),
    .init(symbol: "cna_error_copy_last_message", cReturn: "CNA_Result", cParameters: ["char* destination", "uint64_t capacity", "uint64_t* out_bytes"], ownership: .processGlobal, resultLifetime: "caller-owned copy", errorLifetime: "thread-local preserved", callbackABI: nil),
    .init(symbol: "cna_game_create", cReturn: "CNA_Result", cParameters: ["const CNA_GameCreateInfo* create_info", "CNA_Handle* out_game"], ownership: .owned, resultLifetime: "until cna_game_destroy", errorLifetime: "thread-local", callbackABI: "CNA_GameCallbacks"),
    .init(symbol: "cna_game_set_frame_hooks_ext", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "const CNA_GameFrameHooks* hooks"], ownership: .borrowed, resultLifetime: "table copied", errorLifetime: "thread-local", callbackABI: "CNA_GameFrameHooks"),
    .init(symbol: "cna_game_run", cReturn: "CNA_Result", cParameters: ["CNA_Handle game"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_game_run_one_frame", cReturn: "CNA_Result", cParameters: ["CNA_Handle game"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_game_request_exit", cReturn: "CNA_Result", cParameters: ["CNA_Handle game"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_game_destroy", cReturn: "CNA_Result", cParameters: ["CNA_Handle game"], ownership: .owned, resultLifetime: "handle invalid after successful release", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_game_get_graphics_device", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_Handle* out_graphics_device"], ownership: .borrowed, resultLifetime: "current callback only", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_graphics_device_manager_create", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_Handle* out_manager"], ownership: .owned, resultLifetime: "until manager destroy", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_graphics_device_manager_apply_changes", cReturn: "CNA_Result", cParameters: ["CNA_Handle manager"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_graphics_device_manager_destroy", cReturn: "CNA_Result", cParameters: ["CNA_Handle manager"], ownership: .owned, resultLifetime: "handle invalid after success", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_graphics_device_get_viewport", cReturn: "CNA_Result", cParameters: ["CNA_Handle graphics_device", "CNA_Viewport* out_viewport"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_graphics_device_clear_rgba", cReturn: "CNA_Result", cParameters: ["CNA_Handle graphics_device", "float r", "float g", "float b", "float a"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_texture2d_create_from_encoded_memory", cReturn: "CNA_Result", cParameters: ["CNA_Handle graphics_device", "const uint8_t* encoded_data", "uint64_t encoded_byte_count", "const CNA_Texture2DDecodeInfo* decode_info", "CNA_Handle* out_texture"], ownership: .owned, resultLifetime: "game child until texture destroy", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_texture2d_get_info", cReturn: "CNA_Result", cParameters: ["CNA_Handle texture", "CNA_Texture2DInfo* out_info"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_texture2d_destroy", cReturn: "CNA_Result", cParameters: ["CNA_Handle texture"], ownership: .owned, resultLifetime: "handle invalid after success", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_sprite_batch_create", cReturn: "CNA_Result", cParameters: ["CNA_Handle graphics_device", "CNA_Handle* out_sprite_batch"], ownership: .owned, resultLifetime: "game child until batch destroy", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_sprite_batch_begin", cReturn: "CNA_Result", cParameters: ["CNA_Handle sprite_batch", "const CNA_SpriteBatchBeginInfo* begin_info"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_sprite_batch_submit_scaled_many", cReturn: "CNA_Result", cParameters: ["CNA_Handle sprite_batch", "const CNA_SpriteScaledCommand* commands", "uint64_t command_count"], ownership: .borrowed, resultLifetime: "commands copied", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_sprite_batch_end", cReturn: "CNA_Result", cParameters: ["CNA_Handle sprite_batch"], ownership: .borrowed, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_sprite_batch_destroy", cReturn: "CNA_Result", cParameters: ["CNA_Handle sprite_batch"], ownership: .owned, resultLifetime: "handle invalid after success", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_keyboard_get_state", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_KeyboardState* out_state"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_keyboard_get_state_for_player", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_PlayerIndex player_index", "CNA_KeyboardState* out_state"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_gamepad_get_state", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_PlayerIndex player_index", "CNA_GamePadState* out_state"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_gamepad_get_state_with_dead_zone", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_PlayerIndex player_index", "CNA_GamePadDeadZone dead_zone_mode", "CNA_GamePadState* out_state"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_gamepad_get_capabilities", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_PlayerIndex player_index", "CNA_GamePadCapabilities* out_capabilities"], ownership: .managedValue, resultLifetime: "caller-owned value", errorLifetime: "thread-local", callbackABI: nil),
    .init(symbol: "cna_gamepad_set_vibration", cReturn: "CNA_Result", cParameters: ["CNA_Handle game", "CNA_PlayerIndex player_index", "float left_motor", "float right_motor", "CNA_Bool* out_applied"], ownership: .processGlobal, resultLifetime: "value", errorLifetime: "thread-local", callbackABI: nil),
]
