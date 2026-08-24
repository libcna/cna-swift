# CNA-Swift normative plan and status

**Milestone:** Foundation 10 — complete exactly the standalone
`Microsoft.Xna.Framework.Graphics.SurfaceFormat` managed non-flags enum over
the completed Foundation 1–9 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata is the public shape and
   managed enum authority.
2. SurfaceFormat is managed-only and introduces no native route, constant,
   layout, texture or render-target operation, display API, or GPU mapping.
3. A complete enum declaration does not imply renderer capability. DXT,
   half-float, HDR, pixel conversion, native format negotiation, and backend
   format support remain unclaimed.
4. Public strict names use `Microsoft.Xna.Framework...` and exact XNA
   PascalCase. Formal Swift projections are measured; manual diagnostic
   allowlisting is forbidden.
5. Ordinary CLR enums use the established Swift raw-enum policy.
   SurfaceFormat is not `[Flags]`, uses exact `Int32`, and unknown Swift raw
   values return `nil`.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. Foundation 10 does not consume SurfaceFormat from DisplayMode,
   GraphicsAdapter, PresentationParameters, a Texture or RenderTarget family,
   GraphicsDeviceManager, GraphicsDevice, or CNA.

## Qualified selected surface

Foundation Milestone 10 adds exactly
`Microsoft.Xna.Framework.Graphics.SurfaceFormat`: one CLR type with 21 CLR
identities and 20 mapped Swift XNA identities. The synthetic `value__` storage
field remains the existing formal enum-storage language exclusion.

The ordinary CLR enum maps to a Swift `enum` with exact `Int32` storage and
twenty explicit cases: Color=0, Bgr565=1, Bgra5551=2, Bgra4444=3, Dxt1=4,
Dxt3=5, Dxt5=6, NormalizedByte2=7, NormalizedByte4=8, Rgba1010102=9, Rg32=10,
Rgba64=11, Alpha8=12, Single=13, Vector2=14, Vector4=15, HalfSingle=16,
HalfVector2=17, HalfVector4=18, and HdrBlendable=19.

All 0...19 raw initializers, unknown positive and negative rejection, and value
copying are qualified as Swift projection behavior without creating XNA member
identities. No OptionSet, custom string, helper, PackedVector association, or
native dependency is added.

No DisplayMode, DisplayModeCollection, GraphicsAdapter,
PresentationParameters, Texture/RenderTarget type or constructor,
GraphicsDeviceManager member, GraphicsDevice member, CNAShim declaration,
native manifest row, native function, C layout, callback, or constant was
added. Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch
remain the same honest runtime partials.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members.
- Compiler target: 70 types / 1,403 members; 65 complete, five partial, 187
  missing. Total diagnostics are 338. Normal strict remains red only for the
  deferred profile; leak-only is green.
- Verifier: 145 mutation/self-tests pass. SurfaceFormat is locally 20/20 with
  zero diagnostics. Manual/applied allowlists and unmeasured structural
  categories are zero. Every formal projection counter remains unchanged.
- Pure behavior: 1,249 XNA-derived observation/assertion sites with zero
  failures. The `SURFACE_FORMAT` record contains the complete pinned literal
  table and keeps Swift raw-initializer/copy semantics in a separate mapping
  qualification.
- Dependency graph: nine missing types remain direct reverse dependents and 56
  missing types remain in the transitive reverse closure. DisplayMode becomes
  dependency-complete but is not implemented or started.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero.
- Ordinary enum, flags, PackedVector, GamePad, Keyboard, managed value, native
  lifecycle, template, archive, and isolated-consumer gates remain required.

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
