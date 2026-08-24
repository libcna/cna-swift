# CNA-Swift normative plan and status

**Milestone:** Foundation 5 — complete managed Microsoft XNA Framework 4.0
Curve family, over the completed Foundation 1–4 baseline.

## Normative rules

1. Microsoft XNA 4.0 Windows runtime metadata and reference behavior are the
   public shape and behavior authorities. CNA and sibling bindings are not XNA
   behavioral authorities.
2. Native runtime work uses strict Swift XNA facade -> internal CNA-Swift
   runtime -> canonical CNA C ABI 0.7.0 -> CNA. The Curve family is wholly
   managed Swift and has no CNA call.
3. Public strict names use `Microsoft.Xna.Framework...` and XNA PascalCase.
   Namespace markers and root support projections are measured infrastructure,
   not additional XNA types.
4. A missing member is preferable to a fake member. Partial types are allowed
   only when the compiler scoreboard identifies every missing identity and
   every implemented member has real behavior.
5. Native handles and functions remain private. No Swift error crosses C.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer path.
7. Runtime support claims require execution evidence. Package platform metadata
   is not a support claim.

## Qualified selected surface

Foundation Milestones 1–4 completed the initial managed/runtime canary, the
binary32 linear-algebra and forced intersection closure, Color and its packed
protocols, and all 17 concrete PackedVector formats.

Foundation Milestone 5 adds exactly:

- `Microsoft.Xna.Framework.Curve`
- `Microsoft.Xna.Framework.CurveKey`
- `Microsoft.Xna.Framework.CurveKeyCollection`
- `Microsoft.Xna.Framework.CurveContinuity`
- `Microsoft.Xna.Framework.CurveLoopType`
- `Microsoft.Xna.Framework.CurveTangent`

These six public types and 49 mapped identities are complete and locally
strict-clean. The three CLR classes are open Swift reference classes. Exact
reference IL governs construction, cloning, equality/hash/ordering, sorted key
storage, mutation-sensitive live enumeration, tangents, Hermite evaluation,
and all five loop modes. `CurveKey.CompareTo` deliberately uses the direct XNA
branch sequence: both `NaN/finite` and `finite/NaN` return +1, and `NaN/NaN`
also returns +1.

The collection mapping adds no fake BCL namespace and no automatic Swift
Collection conformance. `ICollection<T>` maps to the concrete member contract;
`IEnumerator<CurveKey>` returns root support type `CNAEnumerator<CurveKey>`;
and read/write CLR `Item[Int32]` maps to throwing `Item`/`SetItem` accessors so
bad indices never trap. `CopyTo` mutates caller-owned `inout` array storage.

Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch remain
the same honest runtime partials. No deferred Design, Content/XNB, LZX,
Effects/Model/3D, Audio/XACT, Media/Video, Storage, Touch, GamerServices, or
runtime-partial surface was started.

## Measurement status

- Pinned contract: 257 types / 2,964 members; retained SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members after deterministic
  language storage/lifetime projections.
- Compiler target: 55 types / 1,247 mapped members; 50 complete, 5 partial,
  202 missing. Normal strict is red only for deferred work; leak-only is green.
- Verifier: 66 mutation/self-tests pass. Manual and applied allowlists are zero;
  unmeasured structural categories are zero. Whole-profile counters include 26
  protocol witnesses, 19 caller-owned array mutations, 1 comparable-interface,
  1 collection-interface, 9 enumerator-support, 4 indexed-property-accessor,
  and 2 optional global-operator projections.
- Pure behavior: 986 XNA-derived observations/assertions, zero failures. Curve
  groups cover enums, key semantics, collection/enumerator behavior, tangents,
  evaluation, and loops without `CNA_NATIVE_LIBRARY`.
- Native ABI remains exactly 25 functions, 72 prototype positions, 72
  C/Swift measurements, 15 layouts, 2 callbacks, and 168 constants, with zero
  header/library/mismatch failures.
- Debug/release builds and tests, warnings-as-errors, Symbol Graph, native
  lifecycle stress, Swift ASan pure corpus, unchanged template, exact source
  archive, and isolated consumer gates are required release evidence.

## Platform policy

Linux x86-64 with Swift 6.0.3 and CNA 0.7.0 HEADLESS/NULL is the only qualified
runtime. HEADLESS has no visible window, so visible output remains
BACKEND_BLOCKED. Apple, Windows, and Web/Wasm remain unqualified.

## Completion policy

Foundation Milestone 5 is complete only when all six Curve types are 49/49,
locally diagnostic-zero, and exact for class identity, collection interfaces,
throwing indexing, live mutation-invalidated enumeration, sorted insertion,
cloning, comparison/hash, tangent generation, interpolation precision, and
negative loop cycles. The full 257-type strict verifier remains red by design;
zero fake behavior, zero manual suppression, zero unmeasured category, zero ABI
mismatch, clean archive/consumer qualification, and unchanged CNA/template
source remain mandatory. Work stops after the Curve family.
