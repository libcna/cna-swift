# CNA-Swift normative plan and status

**Milestone:** Foundation 7 — complete the standalone
`Microsoft.Xna.Framework.DisplayOrientation` managed flags type over the
completed Foundation 1–6 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata and reference IL are the
   public shape and managed behavior authorities.
2. Native runtime work follows Swift XNA facade → internal CNA-Swift runtime →
   canonical CNA C ABI 0.7.0 → CNA. DisplayOrientation is managed-only and
   introduces no native or platform route.
3. A type declaration does not imply runtime capability. Display rotation,
   GameWindow orientation, and GraphicsDeviceManager.SupportedOrientations
   remain absent.
4. Public strict names use `Microsoft.Xna.Framework...` and XNA PascalCase.
   Formal Swift projections are measured; manual diagnostic allowlisting is
   forbidden.
5. Native handles and FFI remain internal. Managed flags retain arbitrary
   fixed-width raw bits through ordinary Swift OptionSet semantics.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. Runtime and hardware claims require execution evidence. A managed
   DisplayOrientation value is not evidence of platform orientation support.

## Qualified selected surface

Foundation Milestone 7 adds exactly
`Microsoft.Xna.Framework.DisplayOrientation`: one CLR type with five CLR
identities and four mapped Swift XNA identities. The synthetic `value__`
storage field remains a formal language exclusion.

The CLR `[Flags]` enum maps through the already-established Swift `OptionSet`
rule with exact `Int32` storage. Its only XNA members are `Default=0`,
`LandscapeLeft=1`, `LandscapeRight=2`, and `Portrait=4`. Raw construction,
union, intersection, arbitrary raw bits, and value copies are qualified as
Swift projection behavior without creating XNA member identities.

No GraphicsDeviceManager or GameWindow member, orientation platform API,
CNAShim type, native manifest entry, native function, layout, or constant was
added. Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch
remain the same honest runtime partials. Mouse, Touch, Vertex APIs, Design,
Content/XNB, Effects/Model, Audio, Media, Storage, GamerServices, and runtime
partial cleanup were not started.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members.
- Compiler target: 67 types / 1,379 members; 62 complete, 5 partial, 190
  missing. Total diagnostics are 341. The normal strict verifier remains red
  only for deferred profile work; leak-only is green.
- Verifier: 102 mutation/self-tests pass. DisplayOrientation is locally 4/4
  with zero diagnostics. Manual/applied allowlists and
  unmeasured structural categories are zero. Projection counters remain 113
  language exclusions, 26 protocol witnesses, 19 array mutations, 1 comparable
  interface, 1 collection interface, 9 enumerator supports, 4 indexed-property
  accessors, and 2 optional global operators.
- Pure behavior: 1,243 XNA-derived observations/assertions with zero failures.
  The DISPLAY_ORIENTATION record separates pinned CLR contract facts from
  independently qualified Swift OptionSet conveniences.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero.
- Unchanged native qualification: real HEADLESS/NULL disconnected state for the
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
Graph, verifier self-tests/strict/leak-only, pure behavior, unchanged full ABI,
GamePad and Keyboard regression, native stress, Swift ASan, unchanged template
60/600, a clean exact source archive, isolated consumer, `git diff --check`,
commit/push synchronization, and no CNA/template source change. Work stops
after selecting—but not starting—one regenerated next closure.
