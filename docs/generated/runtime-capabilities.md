# Runtime capabilities

Qualified boundary: Swift 6.0.3, `x86_64-pc-linux-gnu`, canonical CNA C ABI
0.7.0, HEADLESS renderer, NULL audio.

| Operation | Status | Evidence |
|---|---|---|
| XNA namespace projection | VERIFIED_MANAGED | Compiler Symbol Graph emits `Microsoft.Xna.Framework`; namespace markers are measured exclusions. |
| Pure math/value foundation | VERIFIED_MANAGED | MathHelper, Point, Rectangle, and GameTime are complete; selected Vector2 and Color members are real but measured partial. |
| Game lifecycle | VERIFIED_NATIVE | CNA drives Initialize through shutdown; 60/600 frames pass. |
| Game callback error containment | VERIFIED_NATIVE | Errors in Initialize, LoadContent, Update, Draw, and UnloadContent return normally through C and rethrow at Swift boundaries. |
| Game recreation | VERIFIED_NATIVE | 20 cycles pass with generation invalidation. |
| GraphicsDevice / Clear | VERIFIED_NATIVE | Callback-borrowed device, native viewport, and native clear pass. |
| Texture2D stream load | VERIFIED_NATIVE | CNA decodes PNG bytes and reports dimensions. |
| SpriteBatch Begin/Draw/End | VERIFIED_NATIVE | Native scaled-command route passes template and stress. |
| Keyboard | VERIFIED_NATIVE | CNA query passes; HEADLESS observed no pressed keys. |
| Visible renderer output | BACKEND_BLOCKED | HEADLESS has no window; no visual claim is made. |
| Canonical CNA HEAD C API build | UPSTREAM_CNA_BLOCKED | Missing GameUpdateRequiredException header at unmodified HEAD. |
| Content/XNB | UNIMPLEMENTED_CNA_SWIFT | Deferred; fake ContentManager removed. |
| Effects/3D | UNIMPLEMENTED_CNA_SWIFT | Deferred; fake BasicEffect/cube removed. |
| Audio / Media / Storage | UNIMPLEMENTED_CNA_SWIFT | Outside Foundation-1. |
| Linux x86-64 | VERIFIED_NATIVE | Exact selected toolchain/artifact passed. |
| macOS / iOS / tvOS / visionOS | PLATFORM_PENDING | Not qualified. |
| Windows | PLATFORM_PENDING | No loader/runtime qualification. |
| Browser/Wasm | PLATFORM_PENDING | No artifact/runtime qualification. |

The machine-readable source is `docs/runtime-capabilities.json`.
