# CNA-Swift normative plan and status

**Milestone:** Foundation 8 — complete exactly the standalone
`Microsoft.Xna.Framework.Graphics.BufferUsage` managed flags type over the
completed Foundation 1–7 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata and reference IL are the
   public shape and managed behavior authorities.
2. Native runtime work follows Swift XNA facade → internal CNA-Swift runtime →
   canonical CNA C ABI 0.7.0 → CNA. BufferUsage is managed-only and introduces
   no native route, constant, or graphics resource operation.
3. A type declaration does not imply runtime capability. Vertex/Index buffers,
   dynamic buffers, vertex declarations, SetData/GetData, and GraphicsDevice
   buffer/draw operations remain absent.
4. Public strict names use `Microsoft.Xna.Framework...` and XNA PascalCase.
   Formal Swift projections are measured; manual diagnostic allowlisting is
   forbidden.
5. CLR `[Flags]` enums map through the established Swift `OptionSet` policy and
   retain arbitrary fixed-width raw bits. BufferUsage uses exact `Int32`.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. Runtime and hardware claims require execution evidence. A managed
   BufferUsage value is not evidence of GPU buffer support.

## Qualified selected surface

Foundation Milestone 8 adds exactly
`Microsoft.Xna.Framework.Graphics.BufferUsage`: one CLR type with three CLR
identities and two mapped Swift XNA identities. The synthetic `value__` storage
field remains the existing formal enum-storage language exclusion.

The CLR `[Flags]` enum maps to a Swift `OptionSet` with exact `Int32` storage.
Its only XNA literals are `None=0` and `WriteOnly=1`. Raw construction, union,
intersection, arbitrary positive/negative raw bits, and value copying are
qualified as Swift projection behavior without creating XNA member identities.
No custom string or helper surface is added.

No VertexBuffer, DynamicVertexBuffer, IndexBuffer, DynamicIndexBuffer,
VertexBufferBinding, VertexDeclaration, IVertexType, built-in vertex struct,
GraphicsDevice member, GraphicsDeviceManager member, CNAShim declaration,
native manifest row, native function, C layout, callback, or constant was
added. Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch
remain the same honest runtime partials.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members.
- Compiler target: 68 types / 1,381 members; 63 complete, five partial, 189
  missing. Total diagnostics are 340. Normal strict remains red only for the
  deferred profile; leak-only is green.
- Verifier: 114 mutation/self-tests pass. BufferUsage is locally 2/2 with zero
  diagnostics. Manual/applied allowlists and unmeasured structural categories
  are zero. Every formal projection counter remains unchanged.
- Pure behavior: 1,245 XNA-derived observations/assertions with zero failures.
  The `BUFFER_USAGE` record contains the pinned contract literals and keeps
  Swift OptionSet conveniences in a separate mapping qualification.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero.
- Unchanged flags regressions cover SpriteEffects, Buttons, and
  DisplayOrientation. Unchanged native qualification retains real
  HEADLESS/NULL disconnected state for the default and three explicit
  dead-zone routes, all-false/Unknown capabilities, false vibration acceptance,
  fifty cycles per state mode, twenty capability cycles, generation reuse, and
  wrong-thread preflight.
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
