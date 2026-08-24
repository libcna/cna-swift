# CNA-Swift normative plan and status

**Milestone:** Foundation 6 — complete the Microsoft XNA Framework 4.0 GamePad
family over the completed Foundation 1–5 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata and reference IL are the
   public shape and managed behavior authorities.
2. Native runtime work follows Swift XNA facade → internal CNA-Swift runtime →
   canonical CNA C ABI 0.7.0 → CNA. No SDL/platform bypass or local semantic
   shim is permitted.
3. A missing member is preferable to fabricated PacketNumber, capabilities,
   disconnected state, dead-zone behavior, or vibration success.
4. Public strict names use `Microsoft.Xna.Framework...` and XNA PascalCase.
   Formal Swift projections are measured; manual diagnostic allowlisting is
   forbidden.
5. Native handles and FFI remain internal. Native-backed static input calls may
   throw through the established Swift failure projection. No Swift error
   crosses C.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. Runtime and hardware claims require execution evidence. Package platform
   metadata or a disconnected route is not a positive hardware claim.

## Qualified selected surface

Foundation Milestone 6 adds exactly:

- `Microsoft.Xna.Framework.Input.ButtonState`
- `Microsoft.Xna.Framework.Input.Buttons`
- `Microsoft.Xna.Framework.Input.GamePad`
- `Microsoft.Xna.Framework.Input.GamePadButtons`
- `Microsoft.Xna.Framework.Input.GamePadCapabilities`
- `Microsoft.Xna.Framework.Input.GamePadDPad`
- `Microsoft.Xna.Framework.Input.GamePadDeadZone`
- `Microsoft.Xna.Framework.Input.GamePadState`
- `Microsoft.Xna.Framework.Input.GamePadThumbSticks`
- `Microsoft.Xna.Framework.Input.GamePadTriggers`
- `Microsoft.Xna.Framework.Input.GamePadType`

The regenerated closure contains 132 CLR identities and 128 mapped Swift
identities. Its only external public dependencies are the already-complete
PlayerIndex and Vector2. Four enum `value__` storage fields are formal language
projection exclusions. All eleven types are strict-complete and locally
diagnostic-zero.

Buttons is an exact `Int32` OptionSet. The six XNA value types remain Swift
structs. GamePadCapabilities has exactly 26 read-only properties and no public
constructor. GamePadState has both constructors plus a non-public native
snapshot initializer, real connection/packet fields, exact all-bit physical and
virtual button queries, and reference-derived equality/hash/string behavior.

GamePad is a nonconstructible final static-like class. Its four methods bind
only `cna_gamepad_get_state`, `cna_gamepad_get_state_with_dead_zone`,
`cna_gamepad_get_capabilities`, and `cna_gamepad_set_vibration`. Canonical CNA
supplies a real packet number, controller type, per-control capabilities, voice
field, motor fields, dead-zone processing, and device-accepted vibration
Boolean. Every call resolves the current Game generation and validates its
owner thread before native entry.

Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch remain
the same honest runtime partials. Mouse, Touch, Design, Content/XNB, LZX,
Effects/Model/3D, Audio/XACT, Media/Video, Storage, GamerServices, and runtime
partial cleanup were not started.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members.
- Compiler target: 66 types / 1,375 members; 61 complete, 5 partial, 191
  missing. Total diagnostics are 342. The normal strict verifier remains red
  only for deferred profile work; leak-only is green.
- Verifier: 90 mutation/self-tests pass. Manual/applied allowlists and
  unmeasured structural categories are zero. Projection counters remain 113
  language exclusions, 26 protocol witnesses, 19 array mutations, 1 comparable
  interface, 1 collection interface, 9 enumerator supports, 4 indexed-property
  accessors, and 2 optional global operators.
- Pure behavior: 1,239 XNA-derived observations/assertions with zero failures;
  native GamePad evidence has separate canonical-CNA provenance.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero.
- Current native qualification: real HEADLESS/NULL disconnected state for the
  default and three explicit dead-zone routes, all-false/Unknown disconnected
  capabilities, and false vibration acceptance. Fifty cycles per state mode,
  twenty capability cycles, generation reuse, and wrong-thread preflight pass.
- Positive controller state, capability diversity, controller type diversity,
  voice, motor support, and physical vibration are `HARDWARE_PENDING`; repeated
  rumble stress is not run without hardware.

## Platform and release policy

Linux x86-64 with Swift 6.0.3 and exact CNA 0.7.0 HEADLESS/NULL is the only
qualified runtime. HEADLESS has no visible window, and this host has no attached
controller. Apple, Windows, and Web/Wasm remain unqualified.

Completion requires debug/release builds and tests, warnings-as-errors, Symbol
Graph, verifier self-tests/strict/leak-only, pure behavior, full ABI, separate
GamePad native evidence, Keyboard regression, native stress, Swift ASan,
unchanged template 60/600, clean exact source archive, isolated consumer,
`git diff --check`, commit/push synchronization, and no CNA/template source
change. Work stops after this family.
