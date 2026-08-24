# Runtime capabilities

Qualified boundary: Swift 6.0.3, `x86_64-pc-linux-gnu`, canonical CNA C ABI
0.7.0, HEADLESS renderer, NULL audio.

| Operation | Status | Evidence |
|---|---|---|
| XNA namespace projection | VERIFIED_MANAGED | Compiler Symbol Graph emits `Microsoft.Xna.Framework`; namespace markers are measured exclusions. |
| Pure math/value foundation | VERIFIED_MANAGED | MathHelper, Point, Rectangle, GameTime, the binary32/geometry closure, Color, and both packed-vector protocols are strict-complete managed Swift. |
| DisplayOrientation | VERIFIED_MANAGED | Exact root-framework Int32 OptionSet values 0/1/2/4; no display rotation or window-orientation capability is claimed. |
| BufferUsage | VERIFIED_MANAGED | Exact Graphics Int32 OptionSet values None=0 and WriteOnly=1; no buffer or GPU resource capability is claimed. |
| DepthFormat | VERIFIED_MANAGED | Exact Graphics non-flags Int32 enum values None=0, Depth16=1, Depth24=2, and Depth24Stencil8=3; no depth buffer, stencil, render-target, GPU-format, or native capability is claimed. |
| FillMode | VERIFIED_MANAGED | Exact Graphics non-flags Int32 enum values Solid=0 and WireFrame=1; no RasterizerState, polygon mode, or wireframe rendering capability is claimed. |
| SurfaceFormat | VERIFIED_MANAGED | Exact Graphics non-flags Int32 enum with all twenty pinned literals; no texture, render-target, display, GPU-format, DXT, HDR, or native capability is claimed. |
| Game lifecycle | VERIFIED_NATIVE | CNA drives Initialize through shutdown; 60/600 frames pass. |
| Game callback error containment | VERIFIED_NATIVE | Errors in Initialize, LoadContent, Update, Draw, and UnloadContent return normally through C and rethrow at Swift boundaries. |
| Game recreation | VERIFIED_NATIVE | 20 cycles pass with generation invalidation. |
| GraphicsDevice / Clear | VERIFIED_NATIVE | Callback-borrowed device, native viewport, and native clear pass. |
| Texture2D stream load | VERIFIED_NATIVE | CNA decodes PNG bytes and reports dimensions. |
| SpriteBatch Begin/Draw/End | VERIFIED_NATIVE | Native scaled-command route passes template and stress. |
| Keyboard | VERIFIED_NATIVE | CNA query passes; HEADLESS observed no pressed keys. |
| ButtonState | VERIFIED_MANAGED | Exact non-flags Int32 enum values. |
| Buttons | VERIFIED_MANAGED | Exact 25-identity Int32 OptionSet, combinations, undefined bits, and flags verifier coverage. |
| GamePadButtons | VERIFIED_MANAGED | Eleven physical properties plus exact value equality/hash/string/copy behavior. |
| GamePadDPad | VERIFIED_MANAGED | Asymmetric constructor/property order plus exact value behavior. |
| GamePadDeadZone / GamePadType | VERIFIED_MANAGED | Exact non-flags Int32 enum values, including BigButtonPad=768. |
| GamePadTriggers / GamePadThumbSticks | VERIFIED_MANAGED | Exact clamp order, special binary32 behavior, equality/hash/string/copies. |
| GamePadState | VERIFIED_MANAGED | Both constructors, packet/connection defaults, every physical/virtual/combined button query, equality/hash/string/copies. |
| GamePadCapabilities value | VERIFIED_MANAGED | Exactly 26 read-only properties and no public initializer. |
| GamePad.GetState default | VERIFIED_NATIVE_ROUTE | Canonical CNA IndependentAxes route returned a real disconnected snapshot; positive hardware path pending. |
| GamePad.GetState None | VERIFIED_NATIVE_ROUTE | Canonical explicit route returned a real disconnected snapshot; physical boundary path pending. |
| GamePad.GetState IndependentAxes | VERIFIED_NATIVE_ROUTE | Canonical explicit route returned a real disconnected snapshot; physical boundary path pending. |
| GamePad.GetState Circular | VERIFIED_NATIVE_ROUTE | Canonical explicit route returned a real disconnected snapshot; physical boundary path pending. |
| GamePad.GetCapabilities | VERIFIED_NATIVE_ROUTE | Canonical per-control route returned real all-false/Unknown disconnected capabilities; positive diversity pending. |
| GamePad.SetVibration | VERIFIED_NATIVE_ROUTE | Canonical route returned device-accepted=false for disconnected slot; physical rumble pending. |
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
