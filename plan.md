# CNA-Swift normative plan and status

**Milestone:** Foundation 13 — complete exactly the standalone
`Microsoft.Xna.Framework.Graphics.RenderTargetUsage` managed enum over the
completed Foundation 1–12 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata is the public shape
   authority, and the hash-matched assembly IL is the behavior authority. FNA
   and MonoGame are engineering comparators only. For a type whose entire
   contract is metadata, the pinned contract alone is sufficient and no
   behavior surrogate or reference probe is created.
2. RenderTargetUsage is managed-only and introduces no native route, constant,
   layout, callback, render target, presentation parameter, adapter, device
   member, or renderer operation.
3. A complete enum does not imply runtime capability. Render-target creation,
   content discard, content preservation, platform-defined content policy,
   depth attachments, MSAA, and native usage mapping remain unclaimed.
4. Public strict names use `Microsoft.Xna.Framework...` and exact XNA
   PascalCase. Formal Swift projections are measured; manual diagnostic
   allowlisting is forbidden.
5. A public non-flags CLR enum maps to a Swift `enum` with the CLR underlying
   type as its raw type and one explicitly valued case per CLR literal. It is
   never an `OptionSet`, a `struct`, an `Int` alias, or a differently signed
   raw type, and it gains no string, predicate, alias, or conversion helper.
   The synthetic `value__` storage identity is the existing enum-storage
   language mapping and never appears in the public Swift surface. This rule is
   general and already formally measured; Foundation 13 adds no new mapping
   rule.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. Foundation 13 does not consume RenderTargetUsage from RenderTarget2D,
   RenderTargetCube, RenderTargetBinding, PresentationParameters,
   GraphicsDevice, or CNA.

## Qualified selected surface

Foundation Milestone 13 adds exactly
`Microsoft.Xna.Framework.Graphics.RenderTargetUsage`: one CLR enum with four
declared identities and three mapped Swift XNA identities. It is sealed and
non-flags with `System.Int32` underlying storage, `System.Enum` base, and no
direct interfaces.

The Swift projection is a `public enum RenderTargetUsage: Int32` in the exact
`Microsoft.Xna.Framework.Graphics` namespace with `DiscardContents = 0`,
`PreserveContents = 1`, and `PlatformContents = 2`. Every raw value is
explicit. There is no Framework-root alias, no `RenderTarget` subnamespace, and
no native or interop namespace.

The CLR storage identity `value__` is not exposed. Compiler-provided
`rawValue`, `init?(rawValue:)`, equality, and value copying are Swift language
surface and add no XNA identity. Valid raw initializers 0, 1, and 2 return
their exact cases; 3, -1, `Int32.max`, and `Int32.min` return `nil`.

No `OptionSet` conformance, union, intersection, `contains`, bitwise operation,
`HasFlag`, `CustomStringConvertible`, `description`, `ToString`, `String`,
`isDiscard`, `preservesContents`, `platformDefault`, `requiresPreservation`,
`nativeUsage`, `Default`, `None`, `KeepContents`, `Discard`, or `Preserve`
member is added.

No RenderTarget2D, RenderTargetCube, RenderTargetBinding,
PresentationParameters, `GraphicsDevice.SetRenderTarget`, GraphicsAdapter,
renderer work, CNAShim declaration, native manifest row, native function, C
layout, callback, or constant is added. Game, GraphicsDeviceManager,
GraphicsDevice, Texture2D, and SpriteBatch remain the same honest runtime
partials, and DisplayMode is unchanged.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`. The
  RenderTargetUsage entry was independently re-read for this milestone and
  confirms `SOURCE_MEMBERS=4`.
- Formal projection: 257 Swift types / 2,887 Swift members;
  `EXPECTED_SWIFT_MEMBERS=3` for RenderTargetUsage after the existing
  enum-storage exclusion.
- Compiler target: 73 types / 1,416 members; 68 complete, five partial, 184
  missing. Total diagnostics are 335. Normal strict remains red only for the
  deferred profile; leak-only is green.
- Verifier: 235 mutation/self-tests pass. RenderTargetUsage is locally 3/3 with
  zero diagnostics. Manual/applied allowlists and unmeasured structural
  categories are zero. Every formal projection counter is unchanged, including
  the 49 enum-storage exclusions, which already contained this type's
  `value__`.
- Pure behavior: 1,271 XNA-derived observation/assertion sites with zero
  failures. The `RENDER_TARGET_USAGE` group carries the pinned kind, flags,
  storage, and complete raw table; Swift projection qualification stays in a
  separate test.
- Dependency graph: three missing types are direct reverse dependents, there is
  no direct partial reverse dependent, and 50 missing types plus all five
  partials remain in the transitive reverse closure. No dependent is
  implemented or started.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero and unchanged.
- DisplayMode, SurfaceFormat, Rectangle, Viewport, DepthFormat, FillMode,
  BufferUsage, DisplayOrientation, ordinary enum, flags, PackedVector, GamePad,
  Keyboard, managed value, native lifecycle, template, archive, and
  isolated-consumer gates remain required.

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
