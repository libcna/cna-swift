# CNA-Swift continuation handoff

**Foundation Milestone 18 final status:** COMPLETE.

Foundation 18 is `PURE_MANAGED_BATCH_D`: `Input.Touch.TouchLocation`,
`Input.Touch.GestureSample` and `Graphics.DisplayModeCollection` — three
entirely missing pure-managed types carrying 21 mapped Swift XNA identities.
Evidence is in `docs/foundation-18-pure-managed-batch-evidence.md`.

Foundation 17 was `REFERENCE_ASSEMBLY_REGISTRATION` plus `PURE_MANAGED_BATCH_C`.
It registers five additional Microsoft XNA assemblies as authoritative
reference inputs and consumes the first seven types that unblocks, carrying 26
mapped Swift XNA identities. Evidence is in
`docs/foundation-17-reference-assembly-registration-evidence.md`.

Foundation 16 was `PURE_MANAGED_BATCH_B` (`MouseState`, `MediaState`,
`MediaSourceType`, `MicrophoneState`); Foundation 15 was
`PRESENTATION_PARAMETERS` and the general `System.IntPtr -> Swift Int` rule.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=186 PASS
RELEASE_TESTS=186 PASS
MANAGED_TESTS=176 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS
SYMBOL_GRAPH=PASS
API_SELF_TESTS=1994 PASS
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS
AUDIT_SELF_TESTS=60 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1595/1595/0
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=113
TARGET_MEMBERS=1641
TOTAL_DIAGNOSTICS=295
MISSING_TYPE=144
MISSING_MEMBER=131
COMPLETE_TYPES=108
PARTIAL_TYPES=5
MISSING_TYPES=144
UNEXPECTED_TYPE=0
UNEXPECTED_MEMBER=0
TYPE_KIND_MISMATCH=0
BASE_MAPPING_MISMATCH=2
INTERFACE_MAPPING_MISMATCH=1
FIELD_MAPPING_MISMATCH=0
PROPERTY_MAPPING_MISMATCH=1
METHOD_SIGNATURE_MAPPING_MISMATCH=0
PARAMETER_MAPPING_MISMATCH=0
RETURN_MAPPING_MISMATCH=0
OVERLOAD_MAPPING_MISMATCH=16
GENERIC_MAPPING_MISMATCH=0
ENUM_VALUE_MISMATCH=0
FLAGS_MAPPING_MISMATCH=0
EVENT_MAPPING_MISMATCH=0
OPERATOR_MAPPING_MISMATCH=0
REF_OUT_MAPPING_MISMATCH=0
LANGUAGE_MAPPING_MISMATCH=0
INTERNAL_TYPE_LEAK=0
RAW_HANDLE_LEAK=0
PUBLIC_NATIVE_FFI_LEAK=0
UNMEASURED_STRUCTURAL_CATEGORY=0
ALLOWLIST_ENTRIES=0
APPLIED_ALLOWLIST_ENTRIES=0
LANGUAGE_PROJECTION_EXCLUSIONS=116
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=10
INHERITED_MEMBER_PROJECTIONS=3
PROTOCOL_WITNESS_MEMBER_PROJECTIONS=26
ARRAY_MUTATION_MAPPINGS=19
COMPARABLE_INTERFACE_PROJECTIONS=1
COLLECTION_INTERFACE_PROJECTIONS=1
ENUMERATOR_SUPPORT_PROJECTIONS=9
INDEXED_PROPERTY_ACCESSOR_PROJECTIONS=4
GLOBAL_OPTIONAL_OPERATOR_PROJECTIONS=2
NONPUBLIC_CONSTRUCTION_PROJECTIONS=5
```

All 151 non-`MISSING_TYPE` diagnostics remain owned exclusively by the five
runtime partials, which are untouched.

## Registered reference assemblies

```text
120 types  Microsoft.Xna.Framework.dll           38e7093f52d7474bbc6256906519781a1210d7da50a1c667b52716fcf49ca130
 99 types  Microsoft.Xna.Framework.Graphics.dll  560080fc39021c611ca9d076dcebed312faf6d7d1413c2dc523683ea635e9f55
 17 types  Microsoft.Xna.Framework.Game.dll      b5dffdd8125abef2a4507ba4e1d2f11062143f0a63d48fe4f298b95ad746a1f0
  8 types  Microsoft.Xna.Framework.Input.Touch.dll b0585224c18022c3661057ae79544644c10f33f1dc529678364f3d6b25151c25
  7 types  Microsoft.Xna.Framework.Xact.dll      a14d5364dca7cf49fb90639e87ba04d52b59a700dc9198efa5707ce8eae28f0a
  3 types  Microsoft.Xna.Framework.Video.dll     17538b1ca9d48a993e2cd88c96b436df08e7abb4aec5d4758eb21feb580d6e06
  3 types  Microsoft.Xna.Framework.Storage.dll   798f678e9ae3d9afc3bed66c30123bc9634fb923b6d200188344b618e608cbb8
```

Together these seven files reproduce the retained contract's 257 types and
2,964 members exactly. **No XNA reference input is missing.** The pinned-scope
blocker recorded by Foundation 14 and 16 is closed.

## Retained native evidence

Foundation 17 has zero native surface. The full ABI is unchanged:

```text
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=c62949d23d3745964f5e557a06665875621ed4cb6e2930e3f282afd5911f2dcb
BOUND_FUNCTIONS=29
PROTOTYPE_TYPE_POSITIONS=91
C_SWIFT_MEASUREMENTS=91
LAYOUTS=18
CALLBACKS=2
CONSTANTS=214
MISSING_HEADER_SYMBOLS=0
MISSING_LIBRARY_SYMBOLS=0
ABI_MISMATCHES=0
```

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Final gate results

Run at the end of the Foundation-18 session, on the committed tree:

```text
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=186 PASS
RELEASE_TESTS=186 PASS
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS
SYMBOL_GRAPH=PASS
API_SELF_TESTS=1994 PASS
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS AUDIT_SELF_TESTS=60 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1595/1595/0
SWIFT_ASAN=PASS_PURE_CORPUS_126_TESTS_DETECT_LEAKS_DISABLED
SWIFT_TSAN=PASS_MANAGED_CORPUS_126_TESTS
NATIVE_ABI=29/91/91/18/2/214 MISSING=0/0 MISMATCHES=0
NATIVE_STRESS=GAME_CYCLES=20 GAME_RECREATION_CYCLES=20 TEXTURE2D_CYCLES=20
    SPRITEBATCH_CYCLES=20 CALLBACK_ERROR_CYCLES=20 GAMEPAD_GET_STATE_CYCLES=50
    GAMEPAD_CAPABILITIES_CYCLES=20 NATIVE_CRASHES=0 OBSERVED_UAF=0
    OBSERVED_DOUBLE_FREE=0 MODE_FAILURES=0
GAMEPAD_NATIVE=0 FAILURES HARDWARE_AVAILABLE=NO
SOURCE_ARCHIVE=225 entries FORBIDDEN=0 NATIVE_LIBRARIES=0
    MICROSOFT_REFERENCE_BINARIES=0 DEVELOPER_PATH_LEAKS=0 DETERMINISTIC=YES
ISOLATED_CONSUMER=DEBUG_BUILD=PASS RELEASE_BUILD=PASS RUN_60=PASS RUN_600=PASS
TEMPLATE=86687f62c3a13ee2b59798f338fc083f7399f447 UNCHANGED
    debug 60 -> updates=60 draws=60 viewport=800x480 texture=128x128
    release 600 -> updates=600 draws=600 viewport=800x480 texture=128x128
GIT_DIFF_CHECK=CLEAN
```

The isolated external consumer now additionally qualifies the Foundation
15-18 public surface. That matters because the in-module tests use
`@testable import`: only the external canary can prove what the genuinely
public surface allows — public construction and derivation of
`PresentationParameters`, the unlabelled `MouseState` constructor in its pinned
order, external conformance to `IGameComponent` and `IGraphicsDeviceManager`,
the `TouchLocation` equality asymmetry and `out` parameter — and what it
forbids.

`swift package archive-source` **is byte-deterministic**: three consecutive
invocations on an unchanged tree produced the identical SHA-256. It does,
however, silently decline to overwrite an existing output file while still
printing "Created", so a stale archive must be deleted before re-archiving or
the audit will report on the previous one.

The archive audit found one real leak this session and it is fixed: a
`verify.cpython-311.pyc` had been committed, because the pre-existing
`.gitignore` pattern `./tools/api_compat/__pycache__` is malformed — a leading
`./` is not valid gitignore syntax — and a `git add -A` picked the bytecode up
once the verifier was run as an importable module. The tracked bytecode is
removed and the pattern replaced with `__pycache__/` and `*.pyc`. The final
archive has 225 entries with zero forbidden entries, zero native libraries,
zero Microsoft reference binaries and zero developer path leaks.

## Why this session stopped

Two legitimate stopping conditions are met together.

**A material architecture decision is required that this prompt and repository
policy do not resolve.** Every remaining general BCL mapping frontier is a
genuine fork, not a mechanical gap. In value order:

1. **`System.EventHandler<T>` and CLR events.** All 49 contract events are the
   single shape `System.EventHandler<TArgs>`, and `EVENT_MAPPING_MISMATCH` is a
   measured category that has never been exercised because every one of them
   lives in a missing or partial type. Repository policy *does* decide the
   outer shape — the `CNAEnumerator<T>` precedent, the documented rule that
   "public delegate types will receive deterministic named closure
   projections", and the verifier already accepting `event -> property` all
   point at a `CNAEvent<TArgs>` support type outside the XNA namespace, exposed
   as a get-only property. What policy does **not** decide is the part that
   matters most, and it is not cosmetic:
   - CLR removes a handler by *delegate identity*. Swift closures have no
     identity, so removal needs either an opaque subscription token that XNA
     does not have, or an `AnyObject` owner, or it must be dropped.
   - CLR lets only the declaring type raise an event. A Swift protocol
     requirement such as `IUpdateable.EnabledChanged` must be satisfiable by a
     *user's* type outside this module, so raising has to be publicly
     reachable — either a public `Raise` on `CNAEvent` (weaker encapsulation
     than CLR) or a `CNAEvent`/`CNAEventSource` split (two support types for
     one concept).
   Whichever is chosen becomes a permanent public support API used by all 49
   events, including those on the protected partials `Game`,
   `GraphicsDevice` and `GraphicsDeviceManager`, where the *native* side will
   eventually raise. That last coupling is the decisive reason not to settle it
   inside a managed-only milestone.
2. **`System.EventArgs`.** `ResourceCreatedEventArgs` and
   `ResourceDestroyedEventArgs` (reach 50 each),
   `GameComponentCollectionEventArgs`, `PreparingDeviceSettingsEventArgs`. All
   derive from `System.EventArgs`, which currently maps to the **`CNAEventArgs`
   struct**. The strict verifier does not measure non-XNA bases, so they could
   be completed today as plain Swift classes with internal construction,
   exactly following the `DisplayMode` precedent — but that models the CLR base
   as *absent* rather than as a struct/class conflict. Making `CNAEventArgs` a
   class instead changes an existing public API type's kind and value
   semantics, and it appears in `Game.OnExiting`, a member of a protected
   partial. An `open class CNAEventArgs` also cannot keep its current
   `Sendable` conformance without `@unchecked`.
3. **`System.Exception`.** Eight exception types across Audio, Content,
   Graphics and Storage. Beyond deciding whether an XNA exception type becomes
   a Swift `Error`-conforming type, two of them extend
   `System.Runtime.InteropServices.ExternalException` rather than
   `System.Exception`, and four declare a
   `(SerializationInfo, StreamingContext)` constructor — a whole BCL
   serialization subsystem. And because the contract lists only *declared*
   members, a strict projection yields types that store a message no consumer
   can read; making them useful means extending the inherited-member projection
   rule to a BCL base and deciding which of `System.Exception`'s members to
   include. Both readings are defensible.
4. **`System.String.GetHashCode`** blocks `Audio.RendererDetail`. The CLR
   function is explicitly unspecified and implementation-defined, so it is not
   derivable from IL; Swift's own `String` hashing is per-process seeded and
   would not even be stable within the binding. Either the type stays blocked
   or the project decides an unspecified BCL hash may be projected onto a
   documented substitute. That is a fidelity decision, not a mapping mechanic.
5. **`System.Attribute`** (five `ContentSerializer*Attribute` types, one of
   which has seven properties and a `Clone`), **`System.Type` /
   `System.IServiceProvider`** (`GameServiceContainer`),
   **`Dictionary<K,V>` as a base** (`LaunchParameters`),
   **`ReadOnlyCollection<T>`** (`Media.VisualizationData`), and
   **`System.ComponentModel.TypeConverter`** (`Design.MathTypeConverter` and
   its eleven concrete subclasses).

**All other remaining candidates require native, runtime or hardware work
beyond the managed scope.** `GraphicsAdapter` (reach 52) and `Input.Mouse` both
became dependency-complete during this session — because
`DisplayModeCollection` and `MouseState` completed — and both are blocked on
real adapter and device enumeration that would have to be fabricated.
`EffectAnnotation` needs effect runtime semantics; `ContentManager` and
`TitleContainer` need the filesystem; `AudioEmitter`, `AudioListener`,
`AudioCategory`, `Microphone`, `AudioEngine`, `SoundBank`, `WaveBank` and `Cue`
need the XACT engine; `TouchPanel`, `VideoPlayer`, `StorageDevice` and
`StorageContainer` need the platform; `SpriteFont` depends on the `Texture2D`
partial; `FrameworkDispatcher.Update()` pumps audio, media and networking and a
no-op would be a fabricated answer; `Media.Video`'s pinned internal constructor
takes a `GraphicsDevice` partial and its only producer is `ContentManager`.

**No XNA reference input is missing.** The pinned-scope blocker recorded by
Foundation 14 and 16 was closed in Foundation 17: all seven declaring
assemblies are registered and together reproduce the retained contract's 257
types and 2,964 members exactly. **No missing software or Debian package is
required** — `swift` 6.0.3, `ikdasm`, `monodis` and `mono` are all present and
were all used.

## Recommended next frontier

**The general CLR event/delegate projection**, taken as a deliberate
architecture decision rather than inside a type milestone. It is the only
remaining general rule that unblocks a whole cluster — `IUpdateable`,
`IDrawable`, and behind them `GameComponent` and `DrawableGameComponent` — and
it exercises a measured diagnostic category that has never been exercised.
Decide the removal-identity and raise-encapsulation questions in section 1
above first, ideally together with how a native-raised event on
`GraphicsDevice` will eventually work, then implement the rule, add verifier
support and negative mutations, and prove it on `IUpdateable` and `IDrawable`.

`System.EventArgs` (section 2) should be decided in the same pass, because the
four `*EventArgs` types and the events that carry them are the same design.

```text
SELECTED_ONLY=false
STARTED=false
```
