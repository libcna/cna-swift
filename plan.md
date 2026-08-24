# CNA-Swift normative plan and status

**Milestone:** Foundation 1 — compiler-measured Swift -> canonical CNA C ABI
foundation.

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

## Foundation-1 selected surface

The first strict-complete pure/value closure is MathHelper, Point, Rectangle,
GameTime, and PlayerIndex. The coherent input value closure Keys, KeyState,
KeyboardState, and Keyboard is also complete. SpriteSortMode and SpriteEffects
are complete exact dependencies of the canary.

Vector2 and Color are honest canary dependencies but remain partial. Game,
GraphicsDeviceManager, GraphicsDevice, Viewport, Texture2D, and SpriteBatch are
honest runtime partials. Broad Content, Effects/Model, Audio, Media, Storage,
Touch, Design, and PackedVector families are not started.

## Measurement status

- Pinned contract: 257 types / 2,964 members; retained SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
- Formal projection: 257 Swift types / 2,887 Swift members after 49 raw enum
  backing fields and 28 finalizers map to language storage/lifetime syntax.
- Compiler target: 19 types / 365 emitted members; 11 complete, 8 partial,
  238 missing. Normal strict is red by design; leak-only is green.
- Verifier: every requested structural category has executable comparison code;
  22 mutation/self-tests pass, including native-handle, internal-helper, and
  unmeasured-category mutations.
- Native ABI: 25 functions, 72 type positions, 15 layouts, 2 callbacks, 168
  constants; zero header/library/mismatch failures.
- Pure behavior: 47 observations/assertions, zero failures.
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

Foundation 1 is complete when the exact final source archive and isolated
consumer gates recorded in `NEXT.md` remain green. The full 257-type strict
verifier is not a Foundation-1 completion condition; zero fake behavior, zero
unmeasured structural categories, zero ABI mismatch, and real selected native
routes are.
