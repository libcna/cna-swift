# CNA-Swift continuation handoff

**Foundation Milestones 26, 27, 28 and 29 status:** COMPLETE.

The Foundation 26–29 implementation/evidence sequence consists of the six
source/evidence commits listed below. Handoff-only correction commits may
follow them, so this document records **no** count of unpublished commits and
**no** current `HEAD`: any such number invalidates itself the moment the next
documentation commit is made. Resolve both from live Git instead:

```text
git rev-list --count origin/develop..HEAD     # how many are unpublished
git log --oneline --decorate origin/develop..HEAD
git status --short --branch
```

| Commit | What it is |
|---|---|
| `f1c5370` | `BCL_AUTHORITY` — a separate, non-vacuous registry that admits the exact Microsoft `mscorlib`. Evidence: `docs/foundation-26-bcl-authority-evidence.md`. |
| `eec4604` | The BCL base rule, `CNACollection`/`CNAReadOnlyCollection`/`CNAList`, and `GameComponentCollection` as its first XNA proof. Evidence: `docs/foundation-27-bcl-base-projection-evidence.md`. |
| `bb10ba2` | `VisualizationData`, and the audited **stop** on `Game.Components`. Evidence: `docs/foundation-29-collection-consumer-evidence.md`. |
| `b37911b` | The developer-path leak the package qualification caught in the generated BCL report. |
| `abd4baf` | The README BCL section and these numbers. |
| `d58b563` | The qualified source-archive digest, measured on the tree of `abd4baf`. |

Everything at and before `b1abe20` is untouched.

## START

```text
BRANCH=develop
HEAD == origin/develop == b1abe202a2eb239482d08a1a9f761f35e41cae4c
WORKTREE_CLEAN=true
TEMPLATE=86687f62c3a13ee2b59798f338fc083f7399f447
```

Verified live before any work. The starting scoreboard matched the stated
baseline exactly (257/2964, 124 target types, 286 diagnostics, 133 missing).

## The two decisions this session made

### 1. BCL authority is a separate mechanism, not another registered assembly

`pinned_assembly_audit.py` earns an XNA assembly its authority by reproducing
**every contract entry it declares**. `mscorlib` declares **zero**, so that gate
would have compared nothing and passed vacuously. It is untouched;
`registered-assemblies.json` is unchanged and still reproduces 257 types and
2,964 members exactly.

The BCL gets `tools/api_compat/bcl-authorities.json`, audited by
`tools/api_compat/bcl_authority_audit.py` against
`tools/api_compat/reference/bcl40-selected-shape.json`. Admission requires all
of:

```text
BCL_IDENTITY_CHECKS=21        exact name/version/key/token/size/sha256,
                              the strong-name token RECOMPUTED from the
                              assembly's own public key rather than read
BCL_MANIFEST_CHECKS=8         reproduction of the pinned selected-shape manifest
BCL_SENTINEL_CHECKS=125       facts stated independently of the extractor
BCL_MUTATION_SELF_TESTS=97    mutations that must each be detected
BCL_CROSS_CHECKS=41           monodis, an independent metadata reader
BCL_NEGATIVE_CONTROLS=4       binaries that must be REFUSED
BCL_AUTHORITY_STATUS=PASS
```

Admitted, and only because it earned it:

```text
mscorlib 4.0.0.0  token b77a5c561934e089 (recomputed)
  sha256 5634668d4775b0113f08ea31093b281fea69bfc4e99227f5ca761b4ed98acc63
  FileVersion 4.0.30319.1 (RTMRel.030319-0100), CompanyName Microsoft Corporation
  strong-name key f:\dd\Tools\devdiv\ecmapublickey.snk, imports clr.dll + mscoree.dll
  zero Mono./System.Private.CoreLib/MonoTODO markers
BCL_AUTHORITY_ASSEMBLIES=1 BCL_AUTHORITY_TYPES=8 BCL_AUTHORITY_MEMBERS=94
  bcl40-selected-shape.json
  SHA256=ef5f2428a546b677d797b5def4c07c44e04419844418b13de9a20f61aa323f0e
  regenerates BYTE-IDENTICALLY with and without an IL cache
```

Authority is demand-driven: `Collection\`1`, `ReadOnlyCollection\`1`, `List\`1`,
`List\`1+Enumerator`, `IList\`1`, `ICollection\`1`, `IEnumerable\`1`,
`IEnumerator\`1` — each with a recorded reason. `System.dll` is registered as
**available but deliberately unadmitted**: nothing implemented consumes it.

**The negative controls are what keep the gate honest.** The Mono 4.0-api
facade is the instructive one: it is *named* `mscorlib`, declares version
`4.0.0.0`, carries the ECMA key and token `b77a5c561934e089`, and even reports
`FileVersion 4.0.30319.1`. It is refused by 12 of 21 checks — `CompanyName`
`Mono development team`, no DevDiv key file, no `clr.dll`/`mscoree.dll`, and
`MonoTODO` 352 times. "Do not use Mono as the authority" is now mechanical.

### 2. A CLR BCL base class projects through real Swift inheritance

```text
System.Collections.ObjectModel.Collection`1          -> CNACollection<Element>
System.Collections.ObjectModel.ReadOnlyCollection`1  -> CNAReadOnlyCollection<Element>
System.Collections.Generic.List`1                    -> CNAList<Element>
```

```swift
public final class GameComponentCollection:
    CNACollection<any Microsoft.Xna.Framework.IGameComponent>
```

Not `Object`, not a flattened `Array`, not composition, and **not**
`CNACollection<Any>`. The three support classes live outside
`Microsoft.Xna.Framework`, are counted in no XNA scoreboard, and no `::System`
namespace is fabricated.

Both families are `open` classes over a reference-typed backing store, because
both CLR wrapping constructors store the caller's list live. `CNACollection`'s
public surface is `final` and only the four hooks are `open`, reproducing
`mscorlib`'s `virtual final` split.

## Four defects this session's own checks caught

Each was found by a gate rather than by inspection, which is the point of
having them:

1. **The BCL extractor dropped every protected member.** It filtered on raw IL
   access tokens (`family`) instead of `Parser`'s mapped spellings
   (`protected`), so all four hooks and both `Items` properties vanished. Caught
   by the sentinels — exactly the failure a self-agreeing manifest hides.
2. **The shared IL cache was keyed by file stem.** Every candidate is named
   `mscorlib.dll`, so a negative control was handed the *admitted* assembly's
   disassembly and the Mono markers never fired. Now keyed by SHA-256, and
   controls do not write to the cache at all.
3. **The cross-check mis-parsed generic method names.** `monodis` renders
   `ConvertAll<TOutput>`; the parser took the whole token. Caught by the
   independent reader disagreeing with `ikdasm`.
4. **The generated BCL report leaked machine-local paths.** Caught by the
   package qualification's `DEVELOPER_PATH_LEAKS` check, which exits nonzero.
   The audit now records only file names and digests. `1 -> 0`.

## Structural scoreboard

```text
REFERENCE_TYPES=257                  unchanged
REFERENCE_MEMBERS=2964               unchanged
EXPECTED_SWIFT_TYPES=257             unchanged
EXPECTED_SWIFT_MEMBERS=2887          unchanged  (see below)
TARGET_TYPES=126                     (124 -> 125 -> 126)
TARGET_MEMBERS=1706                  (1696 -> 1703 -> 1706)
TOTAL_DIAGNOSTICS=284                (286 -> 285 -> 284)
COMPLETE_TYPES=121                   (119 -> 120 -> 121)
MISSING_TYPE=131                     (133 -> 132 -> 131)
MISSING_MEMBER=130                   unchanged
PARTIAL_TYPES=5                      unchanged
BASE_MAPPING_MISMATCH=2              unchanged
INTERFACE_MAPPING_MISMATCH=1         unchanged
PROPERTY_MAPPING_MISMATCH=4          unchanged
OVERLOAD_MAPPING_MISMATCH=16         unchanged
every other mismatch/leak category=0
UNMEASURED_STRUCTURAL_CATEGORY=0
ALLOWLIST_ENTRIES=0
DEPENDENCY_COMPLETE_MISSING_TYPES=31 (32 -> 31)

BCL_BASE_PROJECTIONS=5               contract types with a decided BCL base
PROJECTED_BCL_BASE_TYPES=1           …implemented
PENDING_BCL_BASE_TYPES=4             …still blocked, named not dropped
BCL_INHERITED_MEMBER_PROJECTIONS=16  inherited, NOT declared, NOT an XNA identity
BCL_SUPPORT_TYPE_MEASUREMENTS=3
MEASURED_SUPPORT_BASE_PROJECTIONS=9  (4 -> 9)
```

**`EXPECTED_SWIFT_MEMBERS` was not forced to 2887 — it derived to it.** The ten
new `TARGET_MEMBERS` are the declared XNA identities of the two new types
(`GameComponentCollection`: one constructor, four overrides, two events;
`VisualizationData`: one constructor, two properties), every one of which was
already in the pinned contract and already counted. The surface
`GameComponentCollection` *inherits* is real and usable and is **not** an XNA
identity, so it is counted once, on its own axis, as
`BCL_INHERITED_MEMBER_PROJECTIONS=16`.

## Types completed

```text
Microsoft.Xna.Framework.GameComponentCollection        7 declared + 16 inherited
Microsoft.Xna.Framework.Media.VisualizationData        3
```

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3   SWIFT_TARGET=x86_64-pc-linux-gnu   TOOLS_VERSION=5.9
DEBUG_BUILD=PASS                RELEASE_BUILD=PASS
DEBUG_TESTS=318 PASS            RELEASE_TESTS=318 PASS
NATIVE_TESTS=318 PASS (0 skipped, CNA_NATIVE_LIBRARY set)
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS (forced full rebuild)
SYMBOL_GRAPH=PASS
API_SELF_TESTS=2288 PASS        (2197 -> 2288)
SYMBOL_GRAPH_SELF_TESTS=17 PASS
BCL_AUTHORITY_STATUS=PASS       21/125/8/97/41 checks, 4 controls refused
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS
AUDIT_SELF_TESTS=60 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1861/1861/0    (1768 -> 1861)
PURE_BCL_DERIVED=77/77/0        new, separate authority
SWIFT_ASAN=PASS_318_TESTS_DETECT_LEAKS_DISABLED
SWIFT_TSAN=8_RUNS_0_RACES_0_FAILURES   (see below)
NATIVE_ABI=29/91/91/18/2/214 MISSING=0/0 MISMATCHES=0   unchanged
NATIVE_STRESS=GAME_CYCLES=20 GAME_RECREATION_CYCLES=20 TEXTURE2D_CYCLES=20
    SPRITEBATCH_CYCLES=20 CALLBACK_ERROR_CYCLES=20 GAMEPAD_GET_STATE_CYCLES=50
    GAMEPAD_CAPABILITIES_CYCLES=20 NATIVE_CRASHES=0 OBSERVED_UAF=0
    OBSERVED_DOUBLE_FREE=0 MODE_FAILURES=0
GAMEPAD_NATIVE=0 FAILURES HARDWARE_AVAILABLE=NO
SOURCE_ARCHIVE=274 entries DETERMINISTIC=YES
    SHA256=5c675df6bac26f7d186fccd9db727038bf6dcdc575dcb53b07b5a1badeb04b23
    measured on the tree of commit abd4baf; handoff-only commits after it
    change this file and therefore the digest, so re-measure rather than assume
ISOLATED_CONSUMER=DEBUG_BUILD=PASS RELEASE_BUILD=PASS RUN_60=PASS RUN_600=PASS
    REJECTED_NEGATIVE_CONSUMERS=11  (4 -> 11)
    FORBIDDEN_ENTRIES=0 NATIVE_LIBRARIES=0 MICROSOFT_REFERENCE_BINARIES=0
    DEVELOPER_PATH_LEAKS=0
TEMPLATE=86687f62c3a13ee2b59798f338fc083f7399f447 UNCHANGED WORKTREE_CLEAN
    debug 60 -> updates=60 draws=60 viewport=800x480 texture=128x128
    release 600 -> updates=600 draws=600 viewport=800x480 texture=128x128
GIT_DIFF_CHECK=CLEAN
```

The native evidence library is the pinned
`NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086`.
Its matching ABI 0.7.0 headers are `~/deps/cna-c-abi-0.7.0/include` — the
`cnanext` working tree has moved past 0.7.0 and its header now fails the
probe's `_Static_assert`. The Foundation 20 warnings-as-errors caveat still
holds: the gate is meaningful only after
`find Sources Tests -name '*.swift' -exec touch {} +`, and release additionally
needs `-Xswiftc -enable-testing`.

### TSan — the historical flake did NOT recur, and was hunted for

Eight full-suite ThreadSanitizer executions, **all output captured unfiltered**
to `tsan-1..8.log`. Every one: 318 tests, `0 failures`, and zero
`WARNING: ThreadSanitizer` lines. Runs 5 and 6 were executed under **deliberate
concurrent native load** — six back-to-back 600-frame release template canaries
in a second process — which is the condition under which the previous session's
single unidentified XCTest failure appeared. It did not reproduce. The previous
session's caveat is not being rewritten: that run happened, its output was
filtered, and its failing case was never captured. This session simply failed to
reproduce it in eight tries, two of them adversarial.

## What was audited and deliberately NOT done

### `Game.Components` — authorized, audited, and stopped

The limited authorization was taken up. `Game::get_Components` is a bare field
read and the field is assigned once, in `Game..ctor` at `IL_009b`. That much is
trivially safe. **Its reachable contract is not.**

The same constructor immediately subscribes two private handlers to the
collection's events, and those handlers are the machinery:

```text
GameComponentAdded    inRun ? component.Initialize() : notYetInitialized.Add(c)
                      IUpdateable -> BinarySearch updateableComponents by
                                     UpdateOrderComparer.Default, insert sorted,
                                     subscribe UpdateableUpdateOrderChanged
                      IDrawable   -> the same for drawableComponents
GameComponentRemoved  reverses all three
```

and `updateableComponents` / `drawableComponents` are exactly what the **base
bodies** of `Game.Update` and `Game.Draw` iterate, while `Game.Initialize`'s
base body drains `notYetInitialized` and then calls `LoadContent()`.

In CNA-Swift those three members are **already implemented**, as
`open func … throws {}` — empty — over a native-owned loop. So:

- `Components` alone would let a consumer write `game.Components.Add(c)` and get
  no `Initialize`, no `Update`, no `Draw` and no error. A silent lie, and the
  same class of fabrication the Foundation 25 audit rejected 28 members for;
- making it honest means changing the base bodies of three **already-implemented
  public members**, which is outside the authorization and is a new public
  decision of its own: `super.Update(gameTime)` would change meaning for every
  existing CNA subclass;
- `Game.Initialize`'s body ends in `LoadContent()`, which CNA's native host
  already drives through its own callback — transcribing it would double-call.

`inRun` is *not* the blocker: `begin_run`/`end_run` are wired, so the flag is
observable. The blocker is the three empty base bodies and native loop
ownership.

`GameComponent` follows it unchanged: its own IL is pure managed, but
`Dispose(bool)` unregisters from `Game.Components`. Neither was implemented,
and `DrawableGameComponent` was not touched.

### Undecided BCL families — deliberately still undecided

```text
System.Exception / ExternalException    8 XNA exception types
System.Attribute                        5 ContentSerializer* types
System.Collections.Generic.Dictionary`2 LaunchParameters
System.ComponentModel.ExpandableObjectConverter  MathTypeConverter
System.IO.BinaryReader                  ContentReader
```

Each still reports `UNMEASURED_STRUCTURAL_CATEGORY` if anything implements it,
and a self-test enforces that every *measured* generic support base has an
admitted BCL family behind it — so a base cannot be declared decided without an
authority. Admitting the binary that declares `System.Exception` decided nothing
about whether projected XNA exceptions conform to Swift `Error`, inherit from a
support class, or interact with `CNAError`.

### Re-audited collection consumers, still deferred

| Type | Now blocked by |
|---|---|
| `Graphics.GraphicsAdapter` | display enumeration (hardware) |
| `Audio.Microphone` | capture-device enumeration (hardware) |
| `Graphics.SpriteFont` | loaded content |
| `Audio.RendererDetail` | a `GetHashCode` the CLR leaves unspecified |
| the four `Model*Collection` | element types bottoming out at `Effect`/`GraphicsResource`/`GraphicsDevice` |

In each the BCL base is no longer the blocker. No producer was fabricated.

## Recommended next frontier, in value order

### 1. `System.Exception` — the largest remaining decision, 8 types

The mechanism is built and general; this is purely a **public API decision**,
and it is genuinely cross-cutting:

- do projected XNA exception classes conform to Swift `Error`?
- do they inherit from a `CNAException` support class the way collections
  inherit `CNACollection`, and if so does that class conform to `Error`?
- how do they interact with the existing `CNAError` enum, which is what every
  implemented member throws today?
- does anything already-implemented change its `throws` payload?

The last question is the sharp one: making `DeviceLostException` a real thrown
type would change what existing members throw. Register the family in
`bcl-authorities.json` (the registry is designed to take it), then decide.

### 2. `Dictionary<K,V>` — one type, but its own semantics

`LaunchParameters` is the only consumer. Needs comparer, enumerator, nested
collection and exception-behaviour decisions of its own.

### 3. `Game.Components` + the component dispatch loop

Not a BCL question any more — a **`Game` runtime** question. It needs explicit
authorization to change the base bodies of `Game.Initialize`, `Game.Update` and
`Game.Draw`, and a decision about `LoadContent` double-dispatch against the
native host. `GameComponent` and `DrawableGameComponent` follow immediately
once it is decided.

### 4. CLR abstract class members

`GameWindow` has nine `abstract` public members. Swift has no abstract member,
and every one of them also needs a real window system. Doubly blocked.

## Registered inputs

Unchanged. The seven XNA assemblies still reproduce 257 types / 2,964 members
exactly and live in
`/rv/tmp/samples/SAMPLE-017-CollisionSample_4_0/xna4-build/bin` (Framework,
Graphics, Game, Input.Touch) and
`/rv/tmp/samples/_tools/xna-game-studio-4-refresh/admin/Program Files/Microsoft XNA/XNA Game Studio/v4.0/References/Windows/x86`
(Xact, Video, Storage). The BCL binaries are in the `~/.wine-cna-xna40` prefix.
`ikdasm`, `monodis`, `mono` and `swift` 6.0.3 (at
`/tmp/cna-swift-toolchain-6.0.3`) are all present. **No required input or
package is missing.**

`~/deps/xna-il-cache/` is shared with other sessions and is a convenience, never
an authority: the BCL audit re-hashes what it is pointed at, keys its cache by
digest, and the byte-identical manifest regeneration was also run with no cache.

One archiving detail worth knowing, because it looks like non-determinism and
is not: `swift package archive-source` names the archive's **root directory
after the output file**, so `--output a1.zip` and `--output a2.zip` of the same
tree differ in every entry path and therefore in digest. Archive to a fixed
`CNA.zip` name (in different directories if you need two) and the bytes are
identical — verified twice this session, same tree, same 274 entries, same
digest.

```text
SELECTED_ONLY=false
STARTED=false
```
