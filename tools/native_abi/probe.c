// SPDX-License-Identifier: MIT
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "CNA/C/cna.h"
#include "CNAShim.h"

#define LAYOUT(canonical, swift_side) \
    _Static_assert(sizeof(canonical) == sizeof(swift_side), "size mismatch: " #canonical); \
    _Static_assert(_Alignof(canonical) == _Alignof(swift_side), "align mismatch: " #canonical)

#define OFFSET(canonical, swift_side, field) \
    _Static_assert(offsetof(canonical, field) == offsetof(swift_side, field), \
        "offset mismatch: " #canonical "." #field)

LAYOUT(CNA_StringView, CNASwift_StringView);
OFFSET(CNA_StringView, CNASwift_StringView, data);
OFFSET(CNA_StringView, CNASwift_StringView, byte_length);
LAYOUT(CNA_Color, CNASwift_Color);
OFFSET(CNA_Color, CNASwift_Color, a);
LAYOUT(CNA_Vector2, CNASwift_Vector2);
OFFSET(CNA_Vector2, CNASwift_Vector2, y);
LAYOUT(CNA_Rectangle, CNASwift_Rectangle);
OFFSET(CNA_Rectangle, CNASwift_Rectangle, width);
LAYOUT(CNA_GameTime, CNASwift_GameTime);
OFFSET(CNA_GameTime, CNASwift_GameTime, is_running_slowly);
LAYOUT(CNA_CallbackError, CNASwift_CallbackError);
OFFSET(CNA_CallbackError, CNASwift_CallbackError, message);
LAYOUT(CNA_GameCallbacks, CNASwift_GameCallbacks);
OFFSET(CNA_GameCallbacks, CNASwift_GameCallbacks, context);
LAYOUT(CNA_GameFrameHooks, CNASwift_GameFrameHooks);
OFFSET(CNA_GameFrameHooks, CNASwift_GameFrameHooks, begin_draw);
LAYOUT(CNA_GameCreateInfo, CNASwift_GameCreateInfo);
OFFSET(CNA_GameCreateInfo, CNASwift_GameCreateInfo, callbacks);
LAYOUT(CNA_Viewport, CNASwift_Viewport);
OFFSET(CNA_Viewport, CNASwift_Viewport, min_depth);
LAYOUT(CNA_Texture2DInfo, CNASwift_Texture2DInfo);
OFFSET(CNA_Texture2DInfo, CNASwift_Texture2DInfo, format);
LAYOUT(CNA_Texture2DDecodeInfo, CNASwift_Texture2DDecodeInfo);
OFFSET(CNA_Texture2DDecodeInfo, CNASwift_Texture2DDecodeInfo, zoom);
LAYOUT(CNA_SpriteBatchBeginInfo, CNASwift_SpriteBatchBeginInfo);
OFFSET(CNA_SpriteBatchBeginInfo, CNASwift_SpriteBatchBeginInfo, sort_mode);
LAYOUT(CNA_SpriteScaledCommand, CNASwift_SpriteScaledCommand);
OFFSET(CNA_SpriteScaledCommand, CNASwift_SpriteScaledCommand, layer_depth);
LAYOUT(CNA_KeyboardState, CNASwift_KeyboardState);
OFFSET(CNA_KeyboardState, CNASwift_KeyboardState, pressed_key_words);
LAYOUT(CNA_GamePadAnalogState, CNASwift_GamePadAnalogState);
OFFSET(CNA_GamePadAnalogState, CNASwift_GamePadAnalogState, left_thumb_stick);
OFFSET(CNA_GamePadAnalogState, CNASwift_GamePadAnalogState, right_thumb_stick);
OFFSET(CNA_GamePadAnalogState, CNASwift_GamePadAnalogState, left_trigger);
OFFSET(CNA_GamePadAnalogState, CNASwift_GamePadAnalogState, right_trigger);
LAYOUT(CNA_GamePadState, CNASwift_GamePadState);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, struct_size);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, struct_version);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, is_connected);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, reserved0);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, packet_number);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, pressed_buttons);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, reserved1);
OFFSET(CNA_GamePadState, CNASwift_GamePadState, analog);
LAYOUT(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, struct_size);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, struct_version);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, gamepad_type);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, is_connected);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_a_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_b_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_x_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_y_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_back_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_start_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_big_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_dpad_up_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_dpad_down_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_dpad_left_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_dpad_right_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_left_shoulder_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_right_shoulder_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_left_stick_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_right_stick_button);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_left_x_thumb_stick);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_left_y_thumb_stick);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_right_x_thumb_stick);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_right_y_thumb_stick);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_left_trigger);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_right_trigger);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_left_vibration_motor);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_right_vibration_motor);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_voice_support);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_light_bar_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_trigger_vibration_motors_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_misc1_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_paddle1_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_paddle2_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_paddle3_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_paddle4_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_touchpad_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_gyro_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, has_accelerometer_ext);
OFFSET(CNA_GamePadCapabilities, CNASwift_GamePadCapabilities, reserved);

_Static_assert(CNA_ABI_VERSION == UINT32_C(0x00000700), "canonical header is not ABI 0.7.0");
_Static_assert(sizeof(CNA_Bool) == 1, "CNA_Bool width");
_Static_assert(CNA_FALSE == 0 && CNA_TRUE == 1, "CNA_Bool values");
_Static_assert(CNA_SPRITE_SORT_MODE_DEFERRED == 0, "SpriteSortMode.Deferred");
_Static_assert(CNA_SPRITE_EFFECT_NONE == 0, "SpriteEffects.None");
_Static_assert(CNA_SPRITE_EFFECT_FLIP_HORIZONTALLY == 1, "SpriteEffects.FlipHorizontally");
_Static_assert(CNA_SPRITE_EFFECT_FLIP_VERTICALLY == 2, "SpriteEffects.FlipVertically");
_Static_assert(CNA_PLAYER_INDEX_ONE == 0 && CNA_PLAYER_INDEX_TWO == 1 &&
    CNA_PLAYER_INDEX_THREE == 2 && CNA_PLAYER_INDEX_FOUR == 3, "PlayerIndex slots");
_Static_assert(CNA_GAMEPAD_DEAD_ZONE_NONE == 0, "GamePadDeadZone.None");
_Static_assert(CNA_GAMEPAD_DEAD_ZONE_INDEPENDENT_AXES == 1,
    "GamePadDeadZone.IndependentAxes");
_Static_assert(CNA_GAMEPAD_DEAD_ZONE_CIRCULAR == 2, "GamePadDeadZone.Circular");
_Static_assert(CNA_GAMEPAD_BUTTON_NONE == 0, "Buttons empty mask");
_Static_assert(CNA_GAMEPAD_BUTTON_DPAD_UP == 1, "Buttons.DPadUp");
_Static_assert(CNA_GAMEPAD_BUTTON_DPAD_DOWN == 2, "Buttons.DPadDown");
_Static_assert(CNA_GAMEPAD_BUTTON_DPAD_LEFT == 4, "Buttons.DPadLeft");
_Static_assert(CNA_GAMEPAD_BUTTON_DPAD_RIGHT == 8, "Buttons.DPadRight");
_Static_assert(CNA_GAMEPAD_BUTTON_START == 16, "Buttons.Start");
_Static_assert(CNA_GAMEPAD_BUTTON_BACK == 32, "Buttons.Back");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_STICK == 64, "Buttons.LeftStick");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_STICK == 128, "Buttons.RightStick");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_SHOULDER == 256, "Buttons.LeftShoulder");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_SHOULDER == 512, "Buttons.RightShoulder");
_Static_assert(CNA_GAMEPAD_BUTTON_BIG_BUTTON == 2048, "Buttons.BigButton");
_Static_assert(CNA_GAMEPAD_BUTTON_A == 4096, "Buttons.A");
_Static_assert(CNA_GAMEPAD_BUTTON_B == 8192, "Buttons.B");
_Static_assert(CNA_GAMEPAD_BUTTON_X == 16384, "Buttons.X");
_Static_assert(CNA_GAMEPAD_BUTTON_Y == 32768, "Buttons.Y");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_THUMBSTICK_LEFT == 2097152,
    "Buttons.LeftThumbstickLeft");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_TRIGGER == 4194304, "Buttons.RightTrigger");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_TRIGGER == 8388608, "Buttons.LeftTrigger");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_THUMBSTICK_UP == 16777216,
    "Buttons.RightThumbstickUp");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_THUMBSTICK_DOWN == 33554432,
    "Buttons.RightThumbstickDown");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_THUMBSTICK_RIGHT == 67108864,
    "Buttons.RightThumbstickRight");
_Static_assert(CNA_GAMEPAD_BUTTON_RIGHT_THUMBSTICK_LEFT == 134217728,
    "Buttons.RightThumbstickLeft");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_THUMBSTICK_UP == 268435456,
    "Buttons.LeftThumbstickUp");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_THUMBSTICK_DOWN == 536870912,
    "Buttons.LeftThumbstickDown");
_Static_assert(CNA_GAMEPAD_BUTTON_LEFT_THUMBSTICK_RIGHT == 1073741824,
    "Buttons.LeftThumbstickRight");
_Static_assert(CNA_GAMEPAD_TYPE_UNKNOWN == 0, "GamePadType.Unknown");
_Static_assert(CNA_GAMEPAD_TYPE_GAMEPAD == 1, "GamePadType.GamePad");
_Static_assert(CNA_GAMEPAD_TYPE_WHEEL == 2, "GamePadType.Wheel");
_Static_assert(CNA_GAMEPAD_TYPE_ARCADE_STICK == 3, "GamePadType.ArcadeStick");
_Static_assert(CNA_GAMEPAD_TYPE_FLIGHT_STICK == 4, "GamePadType.FlightStick");
_Static_assert(CNA_GAMEPAD_TYPE_DANCE_PAD == 5, "GamePadType.DancePad");
_Static_assert(CNA_GAMEPAD_TYPE_GUITAR == 6, "GamePadType.Guitar");
_Static_assert(CNA_GAMEPAD_TYPE_ALTERNATE_GUITAR == 7,
    "GamePadType.AlternateGuitar");
_Static_assert(CNA_GAMEPAD_TYPE_DRUM_KIT == 8, "GamePadType.DrumKit");
_Static_assert(CNA_GAMEPAD_TYPE_BIG_BUTTON_PAD == 9, "CNA BigButtonPad compact identity");

int main(void) {
    if (CNA_GAMEPAD_LEFT_DEAD_ZONE != (7849.0f / 32768.0f) ||
        CNA_GAMEPAD_RIGHT_DEAD_ZONE != (8689.0f / 32768.0f) ||
        CNA_GAMEPAD_TRIGGER_THRESHOLD != (30.0f / 255.0f)) {
        return 1;
    }
    printf("ABI_VERSION=%u\n", (unsigned) CNA_ABI_VERSION);
    printf("LAYOUTS=18\n");
    printf("CALLBACKS=2\n");
    printf("CONSTANTS=54\n");
    printf("CNA_BOOL_SIZE=%zu\n", sizeof(CNA_Bool));
    return 0;
}
