# CNA-Swift continuation handoff

> **Current as of Foundation 63.** The Foundation 30–36 handoff that used to be
> this file is kept below, under its own heading, because the measurements it
> records were real when it was written. `plan.md` remains the authority for
> project rules; this file is the *state of the work* and *what is left*.

## Where the work stands

Reproduce the numbers rather than trust them — and note that
`tools/status_gate/verify.py` now compares every one of them, in this file and
in `plan.md` and `README.md`, against the generated reports:

```bash
git rev-list --count origin/develop..HEAD
python3 tools/api_compat/verify.py --symbol-graph \
  .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json
python3 tools/status_gate/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --cna-include /path/to/cnanext/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
```

```text
662 tests, 0 failures (debug, release, ASan with detect_leaks=0, TSan)
TOTAL_DIAGNOSTICS=152   COMPLETE_TYPES=156   PARTIAL_TYPES=6
MISSING_TYPE=95  MISSING_MEMBER=52  OVERLOAD_MAPPING_MISMATCH=5
every category that would mean DISAGREEMENT with XNA: 0
BOUND_FUNCTIONS=109  PROTOTYPE_TYPE_POSITIONS=386  LAYOUTS=33  ABI_MISMATCHES=0
PROJECTION_MUTATIONS=155 (last full run 137, CAUGHT=135, 2 no-ops replaced)
NATIVE_ABI_MUTATIONS=14 CAUGHT=14
MESSAGE_COVERAGE_FINDINGS=0 over 1,298 implemented members
API_COMPAT_SELF_TESTS=2426  AUDIT_SELF_TESTS=80  BCL_MUTATION_SELF_TESTS=462
RESOURCE_STRINGS_REPRODUCED=56
```

**Every remaining diagnostic is an absence.** Nothing implemented disagrees
with the pinned metadata.

## Five facts that bound everything below

Measured, not assumed. A plan that ignores one of these will produce work that
cannot be verified.

1. **No pixel readback exists.** `cna_graphics_device_get_backbuffer_data_window`
   and `cna_texture2d_get_data_rgba8` both answer `CNA_RESULT_NOT_SUPPORTED` on
   a render target and the back buffer alike — `build-probe/f53_readback.c`,
   `build-probe/f53_rtread.c`. **No test here can assert that a pixel ended up
   anywhere.** Geometry, blending, sampling and sort order are unverifiable in
   this environment and must be recorded as such, never asserted from a call
   that returned zero.
2. **Texture *data* is observable.** A typed transfer round-trips exactly
   (`build-probe/f56_texdata.c`), which is why Foundation 57's tests assert
   texel values. This is the one place pixel-level evidence exists.
3. **Only `SurfaceFormat.Color` can be created.** Nineteen of the twenty
   formats answer `NOT_SUPPORTED` — `build-probe/f55_grants.c`. Anything
   depending on another format is unreachable here.
4. **A `GraphicsDevice` is a per-callback capability token**, not an identity
   (`build-probe/f42b_identity.c`). Device-owned state belongs on
   `RuntimeState`; a stored facade goes stale between callbacks. Foundation 54
   learned this again the hard way.
5. **CNA's device is only real inside a lifecycle callback.** Outside one,
   `cna_graphics_device_manager_get_device` answers `INVALID_STATE`.

## What is left, classified

### ACTIONABLE_LOCAL — upstream support exists, the managed side is the work

CNA declares **4,076** distinct `cna_*` symbols. Mapping all 97 still-missing
types onto their route families — `docs/generated/cna-route-map.txt`, and the
reasoning in `docs/frontier-remeasurement-foundation-60.md` — leaves **no family
without native support** except the ones that need none. Route existence is not
capability; but nothing below is blocked upstream, and the blocker in every row
is that the managed type is not projected yet, which is ordinary work:

| Next | Closes | Notes |
|---|---|---|
| `GraphicsDevice` drawing (`DrawPrimitives`, `DrawIndexedPrimitives`, `DrawUserPrimitives`, …) | ~8 members | 7 CNA routes. **Verifiable only as "the call was accepted"** — see fact 1. Say so in the evidence rather than implying more. |
| `Effect` family (`Effect`, `EffectParameter`, `EffectPass`, `EffectTechnique`, the collections, `BasicEffect` and friends) | ~14 types, 2 `SpriteBatch.Begin` overloads, 1 `GraphicsDevice` member | 138 routes. Large but well supported. `cna_sprite_batch_begin_with_effect` is already there, unbound. |
| `SpriteFont` + `SpriteBatch.DrawString` | 1 type, 6 members | 9 routes, including `cna_sprite_batch_draw_string`. |
| `ContentManager` (+ `Game.Content`) | 2 types, 1 member | 33 routes. Phase 8. |
| `TextureCollection` (`GraphicsDevice.Textures`, `VertexTextures`) | 1 type, 2 members | Previously judged blocked: `CNA_TextureSlotInfo` has no kind discriminator and `TextureCube`/`Texture3D` are unprojected. **Re-measure before believing that** — the same assumption was wrong twice. |

### The BLOCKED list, re-measured at Foundation 60

Most of what stood here was **inference, not measurement**: "HEADLESS has no
window" was carried into eight entries, three of which had never been asked.
`docs/frontier-remeasurement-foundation-60.md` asks them.

Not blocked, and now ordinary work:

* **`GraphicsDevice.GraphicsProfile`** — `cna_graphics_device_get_graphics_profile`
  answers `Reach`. It is the only blocker the six deferred `Texture2D` profile
  messages, and the three new buffer ones, name. What is still needed is the
  pinned `ProfileCapabilities` table, read out of the IL.
* **`GraphicsAdapter`, `DisplayMode`, `PresentationParameters`** — the device
  answers its adapter index, an 800x480 display mode, and its presentation
  parameters. Whether a fallible route can serve `PresentationParameters`'
  `IL_NO_FAILURE_PATH` getter is a question about *when* it is read, not about
  whether the value exists.
* **`GameWindow`** and `Game.Window` — nineteen routes, all taking the game
  handle. Title and `AllowUserResizing` round-trip; the client rectangle is the
  empty one a headless session has, which is what HEADLESS means.
* **`GraphicsDevice.Present`, `Reset`** — both accepted.
* **`TextureCollection`** — CNA's own header prescribes the fix: cache what you
  bind and answer from the cache, using `bound` to tell "something else owns
  this slot" from "the slot is empty". That is what XNA's `DeviceResourceManager`
  cache does.
* **Audio, Media, Touch, Storage, GamerServices** — no longer unmeasured: 20-45
  routes per family, listed in `docs/generated/cna-route-map.txt`.

Still blocked, and now measured rather than inferred:

* **`GraphicsDevice.GetBackBufferData`** — the size query answers 384,000 with
  `CNA_RESULT_CAPACITY` and the read answers `NOT_SUPPORTED`, before and after a
  clear that succeeds. Foundation 53's first bounding fact stands.
* **`GamePad.InvalidController`, `Keyboard.CouldNotReadKeyboard`** — the
  error-channel halves that need a native input failure this environment cannot
  produce. CNA already matches the "not connected" half.

### `Microsoft.Xna.Framework.Design` — no longer out of scope

The thirteen converters are pure managed and need no CNA route at all. What they
need is the minimal authentic `System.dll` `ComponentModel` closure, admitted to
the same non-vacuous standard `mscorlib` was. `System.dll` is on disk and its
identity is established.

## Rules a next session must not quietly break

These are the ones that cost the most to relearn:

1. **A gate not demonstrated to fail is not evidence.** Every mutation must be
   shown to be caught; one that survives is either a missing test or an
   unfalsifiable claim, and an unfalsifiable one is **withdrawn with the reason
   written where it stood**. Foundations 45, 48, 53 and 55 each have one.
2. **Run a baseline first.** An ad-hoc mutation check against a tree that does
   not compile reports CAUGHT for everything. That happened in Foundation 51
   and the result was believed for a minute.
3. **The two mutation harnesses take `.mutation-gate.lock`.** They both edit
   files under `Sources/`; running them together makes one compile the other's
   defect and report a CAUGHT it did not earn.
4. **Grep the neighbouring symbols before calling something upstream-blocked.**
   `cna_sprite_batch_begin`'s doc comment describes that route, not the API;
   `begin_with_states` was there all along and Foundation 53 wrote the wrong
   verdict because of it.
5. **A route with no consuming member is not bound**, and a mirrored structure
   with no route is the same unearned count. Three have been *un*bound so far.
6. **Read the IL of every member you implement, including the ones already
   implemented.** Four defects in three milestones were found that way and none
   by a failing test. `tools/api_compat/message_coverage.py` now catches the
   message half of it automatically; nothing yet catches the rest.
7. **`plan.md` and the diagnostic block in `README.md` must move with the
   numbers.** They are updated in the same commit as the work, never after.
   Foundation 58 made that a gate rather than a habit, because it had already
   failed: `plan.md` opened at Foundation 47 while the tree was at 57, and
   `docs/generated/native-abi-report.json` was itself forty-seven routes stale.
   `tools/status_gate/verify.py` derives the current Foundation from the highest
   evidence file, derives every policed count from the generated reports,
   *and* regenerates four of those reports to prove they are what a live run
   still produces.

## The gates, and what each is for

```bash
swift build && swift build -c release && swift test && swift test -c release
ASAN_OPTIONS=detect_leaks=0 swift test --sanitize=address --scratch-path build-asan
swift test --sanitize=thread --scratch-path build-tsan
swift package dump-symbol-graph
python3 tools/api_compat/verify.py --self-test
python3 tools/api_compat/verify.py --graph-self-test --symbol-graph …
python3 tools/api_compat/verify.py --symbol-graph … --output docs/generated/api-compat-report.json
python3 tools/api_compat/dependency_graph.py --report … --output …
python3 tools/native_abi/verify.py     --cna-include … --library "$CNA_NATIVE_LIBRARY"
python3 tools/native_abi/mutations.py  --cna-include … --library "$CNA_NATIVE_LIBRARY"
CNA_NATIVE_LIBRARY=… python3 tools/projection_mutations/run.py     # ~40 min, 114 mutations
python3 tools/api_compat/message_coverage.py --self-test|--mutations|(report)
python3 tools/api_compat/pinned_assembly_audit.py …
python3 tools/api_compat/bcl_authority_audit.py … --cross-check --negative-control …×4
python3 tools/runtime_capabilities/render.py --check
python3 tools/api_compat/profile_capabilities.py --check \
  --assembly-dir /path/to/xna/redistributable --il-cache ~/deps/xna-il-cache
python3 tools/status_gate/verify.py --self-test
python3 tools/status_gate/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --cna-include /path/to/cnanext/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
python3 tools/gamepad_native/run.py --library … --output …
cd ../cna-swift-template && swift run HelloGame --frames 600
```

`README.md`'s *Verification* section is the maintained copy of this list.

Two operational notes worth the seconds they save:

* **Every run must be headless.** `$SCRATCH/env.sh` exports
  `CNA_RENDERER=HEADLESS`, `SDL_VIDEODRIVER=dummy` and a private `DISPLAY`, so
  nothing can paint on the real desktop even if one layer is forgotten.
* **If the template canary fails with compile errors in code that is fine**,
  delete the consumer's `.build/build.db`: SwiftPM caches a path dependency's
  source file list, and a new file in the library is invisible until it is
  cleared. Foundation 57 lost time to this.

## Open items carried forward

* One ThreadSanitizer run in Foundation 49 reported a single failure whose
  identity was not captured. Eleven runs since — three under saturating CPU
  load — have been clean. Recorded as unreproduced, not as a pass.
* `GraphicsDevice.PresentationParameters` is deliberately absent: XNA's getter
  is `IL_NO_FAILURE_PATH` because it reads a field cached at device creation,
  and this binding has no infallible source. `IGraphicsDeviceManager.CreateDevice`
  and the native `DeviceCreated`/`DeviceReset` events are the two candidate
  caching points if it is ever wanted.
* `useResizedBackBuffer` is stored by the two dimension setters and read by
  nothing: XNA's readers are inside `ChangeDevice`'s window negotiation, which
  needs `GameWindow`.

---

# Historical: the Foundation 30–36 handoff

> **The handoff written at the end of the Foundation 30-36 session, kept as
> that session's record.** It is not the current state and is not maintained:
> Foundation Milestones 37 through 63 have landed since. Nothing here is
> deleted, because the measurements it records were real when it was written.

<!-- status-gate:historical -->

**Foundation Milestones 30 through 36: COMPLETE.** Eleven local commits, none
pushed.

Resolve HEAD and the unpublished count from live Git rather than from this
file — any number written here invalidates itself the moment the next
documentation commit is made:

```text
git rev-list --count origin/develop..HEAD
git log --oneline --decorate origin/develop..HEAD
git status --short --branch
```

| Commit | What it is |
|---|---|
| `56a72e4` | The CLR exception families as real Swift `Error` classes, and eight XNA exception types. |
| `8171fa7` | `Dictionary<K,V>` as a reference class, and `LaunchParameters`. |
| `68527e7` | The generated report echoed the caller's absolute symbol-graph path. |
| `31a787c` | The nullability analyser did not understand `String.IsNullOrEmpty`. |
| `654ff5c` | `System.Attribute` and the five `ContentSerializer*` types. |
| `eede22b` | `LaunchParameters` parses the command line; `SetItem` does not throw. |
| `9e61538` | The managed `Game` component engine. |
| `d9f2d93` | `GameComponent`. |
| `1db5e83` | XNA's own resource strings pinned; eight messages corrected. |
| `eea67d1` | `System.Type` as the Swift metatype, and `GameServiceContainer`. |
| `8f248aa` | The support-hierarchy checks made runtime tests. |

Everything at and before `7b59ceb` is untouched.

## START — the state this session began from, reproduced exactly

```text
BRANCH=develop   HEAD == origin/develop == 7b59ceb   WORKTREE_CLEAN=true
TARGET 126/1706  TOTAL_DIAGNOSTICS 284  COMPLETE 121  MISSING_TYPE 131
MISSING_MEMBER 130  PARTIAL 5  EXPECTED_SWIFT_MEMBERS 2887
BCL_INHERITED_MEMBER_PROJECTIONS 16  PROPERTY_MAPPING_MISMATCH 4
OVERLOAD_MAPPING_MISMATCH 16  NATIVE_ABI 29/91/91/18/2/214
```

Verified live before any work; every number matched.

## Structural scoreboard

```text
REFERENCE_TYPES=257                  unchanged
REFERENCE_MEMBERS=2964               unchanged
EXPECTED_SWIFT_MEMBERS=2887          unchanged
TARGET_TYPES=142                     (126 -> 142)
TARGET_MEMBERS=1767                  (1706 -> 1767)
TOTAL_DIAGNOSTICS=269                (284 -> 269)
COMPLETE_TYPES=135                   (121 -> 135)
PARTIAL_TYPES=7                      (5 -> 7)
MISSING_TYPE=115                     (131 -> 115)
MISSING_MEMBER=129                   (130 -> 129)
BASE_MAPPING_MISMATCH=2              unchanged
INTERFACE_MAPPING_MISMATCH=1         unchanged
PROPERTY_MAPPING_MISMATCH=4          unchanged
OVERLOAD_MAPPING_MISMATCH=18         (16 -> 18, the two deferred serialization ctors)
INHERITANCE_MAPPING_MISMATCH=0       new rule, green
LANGUAGE_MAPPING_MISMATCH=0          new check, green
every other mismatch/leak category=0
UNMEASURED_STRUCTURAL_CATEGORY=0
ALLOWLIST_ENTRIES=0

BCL_SUPPORT_TYPE_MEASUREMENTS=10     (3 -> 10)
BCL_BASE_PROJECTIONS=19              (5 -> 19)
PROJECTED_BCL_BASE_TYPES=15          (1 -> 15)
PENDING_BCL_BASE_TYPES=4             unchanged
BCL_INHERITED_MEMBER_PROJECTIONS=77  (16 -> 77)
MEASURED_SUPPORT_BASE_PROJECTIONS=23 (9 -> 23)
NAMESPACE_MARKERS=11                 (10 -> 11, Storage)

BCL_RESOURCE_STRING_PROJECTIONS=8    new
BCL_STATIC_TABLE_PROJECTIONS=1       new
XNA_RESOURCE_STRING_PROJECTIONS=4    new
XNA_SEALED_CLASS_PROJECTIONS=18      new
BCL_ABSTRACT_BASE_WIDENINGS=1        new, recorded
NONDERIVABLE_UNSEALED_CLASSES=5      new, RECORDED not diagnosed
```

**`EXPECTED_SWIFT_MEMBERS` did not move, and should not have.** Every new
`TARGET_MEMBER` is a declared XNA identity that was already in the pinned
contract and already counted. The surface those types *inherit* is real and
usable and is not an XNA identity, so it is counted once on its own axis.

## Sixteen types completed

```text
Audio.InstancePlayLimitException              Content.ContentSerializerAttribute
Audio.NoAudioHardwareException                Content.ContentSerializerCollectionItemNameAttribute
Audio.NoMicrophoneConnectedException          Content.ContentSerializerIgnoreAttribute
Graphics.DeviceLostException                  Content.ContentSerializerRuntimeTypeAttribute
Graphics.DeviceNotResetException              Content.ContentSerializerTypeVersionAttribute
Graphics.NoSuitableGraphicsDeviceException    LaunchParameters
GameComponent                                 GameServiceContainer
```

Two more are PARTIAL by exactly one member each —
`Content.ContentLoadException` and `Storage.StorageDeviceNotConnectedException`
— see the serialization note below. `Game` gained `Components`,
`LaunchParameters` and `Services`.

## The decisions this session made

### 1. A CLR exception class is a Swift class conforming to `Error`

```text
System.Exception                                 ->  CNAException : Error
System.SystemException                           ->  CNASystemException
System.Runtime.InteropServices.ExternalException ->  CNAExternalException
```

The chain is **three links, not two**: `ExternalException`'s exact direct base
is `SystemException`, whose constructors substitute their own message and set
HResult `0x80131501` before `ExternalException` overwrites it with
`0x80004005`. `CNAError` stays a separate channel, is not a `CNAException`, and
a `catch is CNAException` does not swallow it.

Selected surface: `Message`, `InnerException`, `HResult`, `HelpLink`,
`GetBaseException`, `ExternalException.ErrorCode` — every member reconstructible
from managed state. `StackTrace`, `Source`, `TargetSite`, `Data`,
`GetObjectData`, `GetType` and `ToString` each need a CLR runtime service and
are **forbidden** by the verifier rather than answered with something plausible.

### 2. `Dictionary<K,V>` is a reference class with the CLR's own storage

Buckets, an entry array, a free list and a version counter, so the observable
behaviour follows from the algorithm: a removed slot is reused by the next
insertion, the free list is last-freed-first, and clearing an already empty
dictionary does not invalidate an enumerator.

The fact that settles the hash question: **an entry's index comes from `count++`
or the free list, never from its hash**, so enumeration order is reproducible
without reproducing a single CLR hash code. A caller-supplied comparer is exact,
including that one whose hash disagrees with its equality cannot find its own
entries.

### 3. `System.Attribute` — the base carries identity, not members

Its public surface is overwhelmingly reflection and is forbidden. The one
widening is recorded: Swift has neither `abstract` nor `protected`, so
`CNAAttribute()` compiles where `new Attribute()` does not.

### 4. `System.Type` is the Swift metatype

The contract names it in **twenty-four positions and calls a member on it in
none**, so the selected surface is identity and assignability — and
`_openExistential` reproduces `Type.IsAssignableFrom` exactly, including
protocol conformance and class inheritance. Probed before the decision, not
after.

### 5. The `Game` base bodies own the managed component semantics

`Initialize`, `Update` and `Draw` are no longer empty. The `LoadContent`
dispatch question was answered by **measuring the host**:

```text
RunOneFrame  Initialize, LoadContent, Update, Draw, UnloadContent
Run          Initialize, LoadContent, BeginRun, Update, EndRun, UnloadContent
```

which is XNA's `RunGame` sequence exactly, so the native `load_content`
callback **is** the projection of the `LoadContent()` call inside
`Game.Initialize()`. One occurrence, one invocation. The measurement is a
permanent test.

## Defects this session's own gates caught

1. **The IL parser silently merged two types.** `skip_block` stopped only on
   `ikdasm`'s commented method close, but a `pinvokeimpl … preservesig` body
   closes with a bare `}` — so `System.Exception` absorbed all of
   `System.ValueType`. Now brace-depth aware, with a minimised fixture.
   `AUDIT_SELF_TESTS` 60 → 64; the XNA contract still reproduces 257/2964.
2. **The nullability analyser did not understand `String.IsNullOrEmpty`.** A
   field read on the branch reachable only when the field is *not* null was
   reported nullable. Six verdicts moved, every one checked against the CIL by
   hand. `RETURN_NULLABILITY_SELF_TESTS` 115 → 118.
3. **`LaunchParameters` did not parse the command line.** The first version of
   Foundation 31 implemented `.ctor()` as a bare `base..ctor()` and recorded
   "nothing here fabricates launch data" as a virtue — but an empty collection
   *is* the fabrication. Caught by its own new test under the real runner.
4. **Eight XNA messages were transcribed rather than read.** One differed by a
   whole clause and a double space. XNA's resource strings are now pinned and
   compared exactly as the BCL ones are.
5. **A generated report echoed the caller's absolute path.** Normalised.
6. **Two mutation helpers were no-ops on `System.Attribute`**, substituting
   `System.Object` for `System.Object`. Fixed for every subject.
7. **Nine `is` tests the compiler could answer statically**, caught by
   warnings-as-errors. Now runtime checks through `Any`.

## Deliberately deferred, with named blockers

| What | Blocked by |
|---|---|
| `ContentLoadException` / `StorageDeviceNotConnectedException` protected `(SerializationInfo, StreamingContext)` ctor | `System.Type`, `IDictionary` and a deserialization runtime; Swift has no `protected`, so a projection would be publicly callable and would return an exception carrying none of the serialized state |
| `DrawableGameComponent` | `IGraphicsDeviceService` resolved out of `Game.Services`; nothing fabricates a graphics service producer |
| `Game.Content`, `Game.Window`, timing and activation members | `ContentManager`, `GameWindow`, unbound host state |
| `Data`, `StackTrace`, `Source`, `TargetSite`, `ToString`, `GetObjectData` on the exception family | CLR runtime services; forbidden by the verifier, not merely absent |
| XNA's `LoadContent` conditions | `IGraphicsDeviceService`; see below |

### The `LoadContent` differences, and the guard that was removed

Two remain, both needing `IGraphicsDeviceService`:

- XNA calls `LoadContent` only when a graphics device service and device exist;
  here the host decides, so a game with no `GraphicsDeviceManager` still gets it;
- XNA's `LoadContent` fires from *inside* the base `Initialize`, so an override
  that skips `super` never receives it; here it always does.

A flag gating the callback on the base body having run **was implemented and
then removed**. It fixes the second and would also suppress the device-reset
reload XNA issues through the handlers `HookDeviceEvents` installs — behaviour
this host has not been measured for. Trading a known divergence for an
unmeasured one is not an improvement. Worth knowing: the flag *worked*, and
broke the 60-frame canary, whose probe overrides `Initialize` without calling
`super` — precisely the XNA footgun it reproduces.

## Recommended next frontier, in value order

### 1. The BCL exception payload conversion — named three times, still open

`CNAList`, `CNACollection`, `CNADictionary`, `GameComponentCollection` and
`GameServiceContainer` all report CLR-shaped failures through `CNAError`. The
**messages** are now exact; the exception **classes** are not. Foundation 30
made `ArgumentException`, `ArgumentNullException`,
`ArgumentOutOfRangeException`, `NotSupportedException`,
`InvalidOperationException` and `KeyNotFoundException` projectable, and
converting one support type while leaving the others would make the layer
inconsistent — so it is one milestone across all of them.

`CNAError` has accreted `argumentNull` and `keyNotFound` in the meantime; that
conversion is where they come back out.

### 2. `NONDERIVABLE_UNSEALED_CLASSES=5`

```text
GameTime  GraphicsDevice  SpriteBatch  Texture2D  GraphicsDeviceManager
```

XNA leaves all five derivable and this projection has sealed them.
**`Texture2D` is the one that matters: `RenderTarget2D` derives from it**, so
that type is inexpressible while it is `final`. Unsealing a public class is an
API decision of its own, which is why the rule records this direction rather
than diagnosing it.

### 3. `System.ComponentModel.TypeConverter` and the fourteen `Design` converters

`System.Type` is now decided, which was half the blocker.
`ExpandableObjectConverter` and `System.dll` — still registered as available
but deliberately unadmitted — are the other half. `System.dll`'s admission
needs the same non-vacuous standards `mscorlib` met.

### 4. `Game`'s remaining partial members

`Tick`, `SuppressDraw`, `ResetElapsedTime`, `IsFixedTimeStep`,
`TargetElapsedTime`, `IsMouseVisible`, `InactiveSleepTime`, `IsActive`,
`Dispose(bool)`, `ShowMissingRequirementMessage` and the four events. Several
need host state that is not bound; several are pure managed state.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3   SWIFT_TARGET=x86_64-pc-linux-gnu   TOOLS_VERSION=5.9
DEBUG_BUILD=PASS                RELEASE_BUILD=PASS
DEBUG_TESTS=406 PASS            RELEASE_TESTS=406 PASS
NATIVE_TESTS included (CNA_NATIVE_LIBRARY set); 0 skipped
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS (forced full rebuild)
SYMBOL_GRAPH=PASS               SYMBOL_GRAPH_SELF_TESTS=17 PASS
API_SELF_TESTS=2390 PASS        (2288 -> 2390)
AUDIT_SELF_TESTS=64 PASS        (60 -> 64)
RETURN_NULLABILITY_SELF_TESTS=118 PASS   (115 -> 118)
BCL_AUTHORITY_STATUS=PASS
    21 identity / 314 sentinel / 28 manifest / 346 mutation / 91 cross-check
    8 resource / 1 static table / 4 negative controls, all refused
    19 types, 205 members   (8 types, 94 members)
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS
    RESOURCE_STRING_CHECKS=8 RESOURCE_STRINGS_REPRODUCED=4
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=2002/2002/0    (1861 -> 2002)
PURE_BCL_DERIVED=210/210/0      (77 -> 210)
SWIFT_ASAN=PASS_406_TESTS_DETECT_LEAKS_DISABLED
SWIFT_TSAN=3_RUNS_0_RACES_0_FAILURES   tsan-1..3.log captured unfiltered
NATIVE_ABI=29/91/91/18/2/214 MISSING=0/0 MISMATCHES=0   unchanged
NATIVE_STRESS=GAME_CYCLES=20 GAME_RECREATION_CYCLES=20 TEXTURE2D_CYCLES=20
    SPRITEBATCH_CYCLES=20 CALLBACK_ERROR_CYCLES=20 GAMEPAD_GET_STATE_CYCLES=50
    GAMEPAD_CAPABILITIES_CYCLES=20 NATIVE_CRASHES=0 OBSERVED_UAF=0
    OBSERVED_DOUBLE_FREE=0 MODE_FAILURES=0
GAMEPAD_NATIVE=0 FAILURES HARDWARE_AVAILABLE=NO
SOURCE_ARCHIVE=307 entries DETERMINISTIC=YES
    SHA256=fdcfe7f4c280a0f9dc7021e9836660924747684ff99653c8a3e38e2ad4cb94b8
    measured on the tree of 8f248aa; handoff-only commits after it change this
    file and therefore the digest, so re-measure rather than assume
ISOLATED_CONSUMER=DEBUG_BUILD=PASS RELEASE_BUILD=PASS RUN_60=PASS RUN_600=PASS
    REJECTED_NEGATIVE_CONSUMERS=11
    FORBIDDEN_ENTRIES=0 NATIVE_LIBRARIES=0 MICROSOFT_REFERENCE_BINARIES=0
    DEVELOPER_PATH_LEAKS=0
GIT_DIFF_CHECK=CLEAN
```

### Pinned reference digests

```text
bcl40-selected-shape.json               52b98a96a506b132…
xna40-selected-resource-strings.json    699aab9e8d3de992…   new this session
xna40-reference-return-nullability.json 1b95bce92cd67e02…   regenerated
```

### The ASan leak observation, stated rather than buried

Leak detection is disabled in the gate, as it was before. With it **enabled**,
LeakSanitizer reports allocations from `libXCTest` and from the native library,
scaling exactly with the test count (406 objects). **No leak trace enters a CNA
source frame**, including the `GameComponent` parent cycle, which the tests
break through `Dispose`. That is an observation, not a claim that the binding
leaks nothing.

### The native evidence library is NOT the previously pinned one

```text
used     ~/deps/cna-c-abi-0.7.0/libcna_c_api.so
         c62949d23d3745964f5e557a06665875621ed4cb6e2930e3f282afd5911f2dcb
pinned   42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
```

**The previously pinned binary no longer exists anywhere on this machine** — it
lived under the system temporary directory and was lost. The library used is
the shared reproduced build documented in
`~/deps/cna-c-abi-0.7.0-pinned-foundation11/PROVENANCE.md` as ABI- and
behaviour-equivalent on the exercised surface but **not** byte-identical to the
admitted artifact. It reproduces the pinned ABI numbers exactly
(29/91/91/18/2/214, zero missing, zero mismatches) and every stress and gamepad
number. `docs/native-abi.md` still records the old digest and has not been
rewritten, because that measurement did happen; this note is the correction.

## Registered inputs

Unchanged. The seven XNA assemblies still reproduce 257 types / 2,964 members
exactly. `mscorlib` `5634668d…acc63` is still the sole admitted BCL authority;
`System.dll` is still available and deliberately unadmitted. `ikdasm`,
`monodis`, `mono` and Swift 6.0.3 at `/tmp/cna-swift-toolchain-6.0.3` are all
present. **No required input or package is missing.**

`~/deps/xna-il-cache/` now holds digest-keyed disassemblies alongside the older
stem-keyed ones. Prefer the digest-keyed form: two different `mscorlib.dll`
files have the same stem, and a name-keyed cache once handed a negative control
the admitted assembly's IL.

```text
SELECTED_ONLY=false
STARTED=false
```
