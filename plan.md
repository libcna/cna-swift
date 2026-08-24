# CNA-Swift normative plan and status

**Milestone:** Foundation 3 — compiler-measured managed Color and exactly the
two packed-vector protocols forced by Color's pinned direct interface, over the
completed Foundation-2 geometry closure.

## Normative rules

1. Microsoft XNA 4.0 Windows runtime metadata and reference behavior are the
   public shape/behavior authorities. CNA is an implementation, not the XNA
   reference.
2. The only runtime path is strict Swift XNA facade -> internal CNA-Swift
   runtime -> canonical CNA C ABI 0.7.0 -> CNA. C++ and sibling bindings are
   forbidden runtime dependencies.
3. Public strict names use `Microsoft.Xna.Framework...` and XNA PascalCase.
   Namespace markers are excluded mapping infrastructure.
4. A missing member is preferable to a fake member. Partial types are allowed
   only when the compiler scoreboard lists every missing identity and every
   implemented member has real behavior.
5. Native handles/functions remain private. Owned destruction is explicit,
   transactional, generation-checked, and owner-thread checked. Deinit is only
   safe best effort.
6. No Swift error crosses C. Callback trampolines store failure and return CNA
   callback status; controlled Swift boundaries rethrow.
7. Exact ABI 0.7.0 only. Native selection is an absolute environment override
   or an installed soname, never a developer path.
8. Runtime support claims require execution evidence. Package platform metadata
   is not a support claim.

## Qualified selected surface

The first strict-complete pure/value closure is MathHelper, Point, Rectangle,
GameTime, and PlayerIndex. The coherent input value closure Keys, KeyState,
KeyboardState, and Keyboard is also complete. SpriteSortMode and SpriteEffects
are complete exact dependencies of the canary.

Foundation Milestone 2 completed two inseparable parts:

- A: the complete binary32 linear-algebra closure: Vector2, Vector3, Vector4,
  Quaternion, Matrix, and Viewport.
- B: only the public-signature dependency closure forced by Matrix through
  Plane: Plane, PlaneIntersectionType, Ray, BoundingBox, BoundingSphere,
  BoundingFrustum, and ContainmentType.

Pinned metadata proved B unavoidable because complete Matrix exposes Plane and
complete Plane recursively exposes the other six types. This is the corrected
Foundation-2 closure, not Foundation Milestone 3 and not discretionary geometry
scope. All 13 types remain complete and locally strict-clean.

Foundation Milestone 3 adds exactly:

- `Microsoft.Xna.Framework.Color`;
- `Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVector`;
- the deterministic Swift collision mapping
  `Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVectorOfT<TPacked>`.

Pinned public signatures and direct interfaces prove this closure. Vector3 and
Vector4 were already complete; no concrete packed-vector format is referenced.
All three Milestone-3 types are complete and locally strict-clean. Their new
behavior is managed Swift with no CNA calls or C ABI expansion. Game,
GraphicsDeviceManager, GraphicsDevice, Texture2D, and SpriteBatch remain honest
runtime partials. Curve, Content, Effects/Model, Audio, Media, Storage, Touch,
Design, and all concrete PackedVector formats are not started.

## Measurement status

- Pinned contract: 257 types / 2,964 members; retained SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members after 49 raw enum
  backing fields and 28 finalizers map to language storage/lifetime syntax.
- Compiler target: 32 types / 1,030 emitted members; 27 complete, 5 partial,
  225 missing. Normal strict is red by design; leak-only is green.
- Verifier: every requested structural category has executable comparison code;
  41 mutation/self-tests pass. Manual diagnostic suppressions are zero. The 88
  deterministic language projections are measured separately, including
  enum-storage, finalizer, namespace-marker, inherited-member, and the one
  compiler-required explicit-protocol-witness rule. The 18 caller-owned array
  mutation projections are separately measured.
- Native ABI: 25 functions, 72 type positions, 15 layouts, 2 callbacks, 168
  constants; zero header/library/mismatch failures.
- Pure behavior: 415 observations/assertions, zero failures, including exact
  binary32 vector, quaternion, matrix, viewport, plane, ray, bounds, and frustum
  observations plus the dedicated Color group and independent 141-entry
  predefined palette.
- Native lifecycle: real 60/600 frame loops, real exit, callback containment,
  20 recreations, resources, and callback-error cycles.
- Graphics/input: native viewport 800x480, clear, PNG decode, SpriteBatch scaled
  submission, and keyboard query on HEADLESS.

## Platform policy

Linux x86-64 is the only qualified runtime. HEADLESS/NULL is the only qualified
backend combination. The absence of a visible window is BACKEND_BLOCKED. Apple,
Windows, and Web/Wasm remain PLATFORM_PENDING and have no manifest declarations
that could be mistaken for runtime evidence.

## Completion policy

The Milestone-3 closure is complete only when both protocols have their exact
kind, inheritance, generic identity, mutating method, and mutable property;
Color is 165/165 with its exact UInt32 conformance; all 141 named values have
independent golden evidence; and all compiler, behavior, ABI, native, template,
archive, and isolated-consumer gates pass. The full 257-type strict verifier
remains red by design; zero fake behavior, zero unmeasured structural
categories, zero manual suppression, zero ABI mismatch, and real selected
native routes remain mandatory. Work stops after these three types: no concrete
packed-vector format belongs to this milestone.
