// SPDX-License-Identifier: MIT
// Reviewed Swift-side declarations for the bound slice of the CNA C ABI.
// Every structure here mirrors a canonical CNA_* structure field for field, and
// every callback mirrors a canonical callback type. tools/native_abi verifies
// both independently against the canonical CNA headers: field names, order,
// offsets and widths, and __builtin_types_compatible_p on the callbacks.
#ifndef CNA_SWIFT_SHIM_H
#define CNA_SWIFT_SHIM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint32_t CNASwift_Result;
typedef uint8_t CNASwift_Bool;
typedef uint64_t CNASwift_Handle;

typedef struct CNASwift_StringView {
    const char* data;
    uint64_t byte_length;
} CNASwift_StringView;

typedef struct CNASwift_Color {
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t a;
} CNASwift_Color;

typedef struct CNASwift_Vector2 {
    float x;
    float y;
} CNASwift_Vector2;

typedef struct CNASwift_Rectangle {
    int32_t x;
    int32_t y;
    int32_t width;
    int32_t height;
} CNASwift_Rectangle;

typedef struct CNASwift_GameTime {
    int64_t total_game_time_ticks;
    int64_t elapsed_game_time_ticks;
    CNASwift_Bool is_running_slowly;
    uint8_t reserved[7];
} CNASwift_GameTime;

typedef struct CNASwift_CallbackError {
    uint32_t struct_size;
    uint32_t struct_version;
    CNASwift_StringView message;
} CNASwift_CallbackError;

typedef CNASwift_Result (*CNASwift_GameLifecycleCallback)(
    CNASwift_Handle game,
    const CNASwift_GameTime* game_time,
    void* context,
    CNASwift_CallbackError* out_error);

typedef CNASwift_Result (*CNASwift_GameBeginDrawCallback)(
    CNASwift_Handle game,
    const CNASwift_GameTime* game_time,
    void* context,
    CNASwift_Bool* out_should_draw,
    CNASwift_CallbackError* out_error);

typedef struct CNASwift_GameCallbacks {
    uint32_t struct_size;
    uint32_t struct_version;
    CNASwift_GameLifecycleCallback load_content;
    CNASwift_GameLifecycleCallback update;
    CNASwift_GameLifecycleCallback draw;
    CNASwift_GameLifecycleCallback unload_content;
    CNASwift_GameLifecycleCallback exiting;
    void* context;
} CNASwift_GameCallbacks;

typedef struct CNASwift_GameFrameHooks {
    uint32_t struct_size;
    uint32_t struct_version;
    CNASwift_GameLifecycleCallback initialize;
    CNASwift_GameLifecycleCallback begin_run;
    CNASwift_GameLifecycleCallback end_run;
    CNASwift_GameBeginDrawCallback begin_draw;
    CNASwift_GameLifecycleCallback end_draw;
    void* context;
} CNASwift_GameFrameHooks;

typedef struct CNASwift_GameCreateInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    CNASwift_Bool is_fixed_time_step;
    uint8_t reserved[7];
    int64_t target_elapsed_time_ticks;
    CNASwift_StringView window_title;
    const CNASwift_GameCallbacks* callbacks;
} CNASwift_GameCreateInfo;

typedef struct CNASwift_Viewport {
    int32_t x;
    int32_t y;
    int32_t width;
    int32_t height;
    float min_depth;
    float max_depth;
} CNASwift_Viewport;

typedef struct CNASwift_Texture2DInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t width;
    uint32_t height;
    uint32_t level_count;
    uint32_t format;
} CNASwift_Texture2DInfo;

typedef struct CNASwift_TextureInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t level_count;
    uint32_t format;
} CNASwift_TextureInfo;

typedef struct CNASwift_RenderTarget2DCreateInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t width;
    uint32_t height;
    CNASwift_Bool mip_map;
    uint8_t reserved0[3];
    uint32_t format;
    uint32_t depth_format;
    int32_t multi_sample_count;
    uint32_t usage;
    uint32_t reserved1;
} CNASwift_RenderTarget2DCreateInfo;

typedef struct CNASwift_RenderTargetInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t kind;
    uint32_t width;
    uint32_t height;
    uint32_t level_count;
    uint32_t format;
    uint32_t depth_format;
    int32_t multi_sample_count;
    uint32_t usage;
    CNASwift_Bool is_content_lost;
    CNASwift_Bool renderer_available;
    uint8_t reserved[2];
} CNASwift_RenderTargetInfo;

typedef void (*CNASwift_GameEventCallback)(void* context);

typedef void (*CNASwift_RenderTargetContentLostCallback)(
    CNASwift_Handle render_target,
    void* context);

typedef struct CNASwift_Texture2DDecodeInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t width;
    uint32_t height;
    CNASwift_Bool zoom;
    uint8_t reserved[7];
} CNASwift_Texture2DDecodeInfo;

typedef struct CNASwift_SpriteBatchBeginInfo {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t sort_mode;
    uint32_t reserved;
} CNASwift_SpriteBatchBeginInfo;

typedef struct CNASwift_SpriteScaledCommand {
    uint32_t struct_size;
    uint32_t struct_version;
    CNASwift_Handle texture;
    CNASwift_Vector2 position;
    CNASwift_Rectangle source;
    CNASwift_Color color;
    float rotation;
    CNASwift_Vector2 origin;
    CNASwift_Vector2 scale;
    uint32_t effects;
    float layer_depth;
} CNASwift_SpriteScaledCommand;

typedef struct CNASwift_KeyboardState {
    uint32_t struct_size;
    uint32_t struct_version;
    uint64_t pressed_key_words[4];
} CNASwift_KeyboardState;

typedef struct CNASwift_GamePadAnalogState {
    CNASwift_Vector2 left_thumb_stick;
    CNASwift_Vector2 right_thumb_stick;
    float left_trigger;
    float right_trigger;
} CNASwift_GamePadAnalogState;

typedef struct CNASwift_GamePadState {
    uint32_t struct_size;
    uint32_t struct_version;
    CNASwift_Bool is_connected;
    uint8_t reserved0[3];
    int32_t packet_number;
    uint32_t pressed_buttons;
    uint32_t reserved1;
    CNASwift_GamePadAnalogState analog;
} CNASwift_GamePadState;

typedef struct CNASwift_GamePadCapabilities {
    uint32_t struct_size;
    uint32_t struct_version;
    uint32_t gamepad_type;
    CNASwift_Bool is_connected;
    CNASwift_Bool has_a_button;
    CNASwift_Bool has_b_button;
    CNASwift_Bool has_x_button;
    CNASwift_Bool has_y_button;
    CNASwift_Bool has_back_button;
    CNASwift_Bool has_start_button;
    CNASwift_Bool has_big_button;
    CNASwift_Bool has_dpad_up_button;
    CNASwift_Bool has_dpad_down_button;
    CNASwift_Bool has_dpad_left_button;
    CNASwift_Bool has_dpad_right_button;
    CNASwift_Bool has_left_shoulder_button;
    CNASwift_Bool has_right_shoulder_button;
    CNASwift_Bool has_left_stick_button;
    CNASwift_Bool has_right_stick_button;
    CNASwift_Bool has_left_x_thumb_stick;
    CNASwift_Bool has_left_y_thumb_stick;
    CNASwift_Bool has_right_x_thumb_stick;
    CNASwift_Bool has_right_y_thumb_stick;
    CNASwift_Bool has_left_trigger;
    CNASwift_Bool has_right_trigger;
    CNASwift_Bool has_left_vibration_motor;
    CNASwift_Bool has_right_vibration_motor;
    CNASwift_Bool has_voice_support;
    CNASwift_Bool has_light_bar_ext;
    CNASwift_Bool has_trigger_vibration_motors_ext;
    CNASwift_Bool has_misc1_ext;
    CNASwift_Bool has_paddle1_ext;
    CNASwift_Bool has_paddle2_ext;
    CNASwift_Bool has_paddle3_ext;
    CNASwift_Bool has_paddle4_ext;
    CNASwift_Bool has_touchpad_ext;
    CNASwift_Bool has_gyro_ext;
    CNASwift_Bool has_accelerometer_ext;
    uint8_t reserved[1];
} CNASwift_GamePadCapabilities;

#ifdef __cplusplus
}
#endif

#endif
