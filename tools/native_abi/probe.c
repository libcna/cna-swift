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

_Static_assert(CNA_ABI_VERSION == UINT32_C(0x00000700), "canonical header is not ABI 0.7.0");
_Static_assert(sizeof(CNA_Bool) == 1, "CNA_Bool width");
_Static_assert(CNA_FALSE == 0 && CNA_TRUE == 1, "CNA_Bool values");
_Static_assert(CNA_SPRITE_SORT_MODE_DEFERRED == 0, "SpriteSortMode.Deferred");
_Static_assert(CNA_SPRITE_EFFECT_NONE == 0, "SpriteEffects.None");
_Static_assert(CNA_SPRITE_EFFECT_FLIP_HORIZONTALLY == 1, "SpriteEffects.FlipHorizontally");
_Static_assert(CNA_SPRITE_EFFECT_FLIP_VERTICALLY == 2, "SpriteEffects.FlipVertically");

int main(void) {
    printf("ABI_VERSION=%u\n", (unsigned) CNA_ABI_VERSION);
    printf("LAYOUTS=15\n");
    printf("CALLBACKS=2\n");
    printf("CONSTANTS=8\n");
    printf("CNA_BOOL_SIZE=%zu\n", sizeof(CNA_Bool));
    return 0;
}
