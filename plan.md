# CNA-Swift normative plan and status

**Milestone:** Foundation 12 — complete exactly the standalone
`Microsoft.Xna.Framework.Graphics.DisplayMode` managed descriptor class over the
completed Foundation 1–11 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata is the public shape
   authority, and the hash-matched assembly IL is the behavior authority. FNA
   and MonoGame are engineering comparators only.
2. DisplayMode is managed-only and introduces no native route, constant,
   layout, callback, adapter, collection, presentation, monitor, or display
   query.
3. A complete descriptor class does not imply display capability. Monitor
   enumeration, display-mode discovery, resolution switching, fullscreen mode
   management, and native display support remain unclaimed.
4. Public strict names use `Microsoft.Xna.Framework...` and exact XNA
   PascalCase. Formal Swift projections are measured; manual diagnostic
   allowlisting is forbidden.
5. A public CLR class whose declared constructors are all non-public maps to a
   plain Swift `public class` — not `open`, because no accessible constructor
   makes it externally subclassable, and not `final`, because metadata
   `sealed=false` must not be strengthened. Its Swift initializer stays
   `internal` implementation infrastructure and must not appear in the public
   Symbol Graph. This rule is general and formally measured.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. Foundation 12 does not consume DisplayMode from DisplayModeCollection,
   GraphicsAdapter, GraphicsDevice, PresentationParameters, or CNA.

## Qualified selected surface

Foundation Milestone 12 adds exactly
`Microsoft.Xna.Framework.Graphics.DisplayMode`: one CLR class with six declared
public identities and six mapped Swift XNA identities. The pinned contract
declares zero public constructors, so the Swift projection exposes zero public
initializers.

`Width`, `Height` and `Format` are verbatim stored values with get-only public
access. `AspectRatio` is the guarded binary32 quotient — positive zero whenever
either dimension is zero, otherwise `Float(Width) / Float(Height)` with no
Double widening, no clamping and no absolute value. `TitleSafeArea` is exactly
`Rectangle(0, 0, Width, Height)`, the unmodified Windows result of the internal
`Viewport.GetTitleSafeArea`, with independent value semantics and no display
query. `ToString` reproduces
`{Width:W Height:H Format:F AspectRatio:A}` with the CLR literal format name
and the invariant general-float rendering.

No `Equals`, `GetHashCode`, `op_Equality`, `op_Inequality`, `Equatable`,
`Hashable`, setter, public initializer, static factory, `description`, or
convenience helper is added. SurfaceFormat gains no public string surface; the
literal-name table is private to DisplayMode.

No DisplayModeCollection, GraphicsAdapter, `GraphicsDevice.DisplayMode`,
PresentationParameters, monitor query, renderer work, CNAShim declaration,
native manifest row, native function, C layout, callback, or constant is added.
Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch remain
the same honest runtime partials.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
  DisplayMode behavior comes from `Microsoft.Xna.Framework.Graphics.dll`
  SHA-256
  `560080fc39021c611ca9d076dcebed312faf6d7d1413c2dc523683ea635e9f55`.
- Formal projection: 257 Swift types / 2,887 Swift members.
- Compiler target: 72 types / 1,413 members; 67 complete, five partial, 185
  missing. Total diagnostics are 336. Normal strict remains red only for the
  deferred profile; leak-only is green.
- Verifier: 201 mutation/self-tests pass. DisplayMode is locally 6/6 with zero
  diagnostics. Manual/applied allowlists and unmeasured structural categories
  are zero. `NONPUBLIC_CONSTRUCTION_PROJECTIONS` is the one added formal
  counter and reports four implemented reference classes, each with zero public
  Swift initializers.
- Pure behavior: 1,269 XNA-derived observation/assertion sites with zero
  failures. The four `DISPLAY_MODE_*` records carry the retained reference
  tables and keep Swift class/reference/immutability qualification in a
  separate projection test.
- Dependency graph: two missing types and one partial type are direct reverse
  dependents; 51 missing types and all five partials remain in the transitive
  reverse closure. No dependent is implemented or started.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero.
- SurfaceFormat, Rectangle, DepthFormat, FillMode, BufferUsage,
  DisplayOrientation, ordinary enum, flags, PackedVector, GamePad, Keyboard,
  managed value, native lifecycle, template, archive, and isolated-consumer
  gates remain required.

## Platform and release policy

Linux x86-64 with Swift 6.0.3 and exact CNA 0.7.0 HEADLESS/NULL is the only
qualified runtime. HEADLESS has no visible window, and this host has no attached
controller. Apple, Windows, and Web/Wasm remain unqualified.

Completion requires debug/release builds and tests, warnings-as-errors, Symbol
Graph, verifier self-tests/strict/leak-only, pure behavior, unchanged full ABI,
GamePad and Keyboard regression, native stress, Swift ASan, unchanged template
60/600, a clean exact source archive, isolated consumer, `git diff --check`,
the local milestone commit, and the explicit publication boundary. Work stops
after selecting—but not starting—one regenerated next closure.
