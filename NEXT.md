# CNA-Swift continuation handoff

**Foundation Milestone 5 final status:** COMPLETE.

The milestone closes exactly `Curve`, `CurveKey`, `CurveKeyCollection`,
`CurveContinuity`, `CurveLoopType`, and `CurveTangent`: six XNA public types
and 49 mapped member identities. All behavior is managed Swift. CNA source,
the CNA C ABI, the five runtime-partial types, and maintained template source
are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=63 PASS
RELEASE_TESTS=63 PASS
MANAGED_TESTS=56 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=66 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
SWIFT_ASAN=PASS_PURE_CORPUS_DETECT_LEAKS_DISABLED
NATIVE_CNA_SANITIZER=NOT_INSTRUMENTED
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=55
TARGET_MEMBERS=1247
TOTAL_DIAGNOSTICS=353
MISSING_TYPE=202
MISSING_MEMBER=131
COMPLETE_TYPES=50
PARTIAL_TYPES=5
MISSING_TYPES=202
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
LANGUAGE_PROJECTION_EXCLUSIONS=113
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=7
INHERITED_MEMBER_PROJECTIONS=3
PROTOCOL_WITNESS_MEMBER_PROJECTIONS=26
ARRAY_MUTATION_MAPPINGS=19
COMPARABLE_INTERFACE_PROJECTIONS=1
COLLECTION_INTERFACE_PROJECTIONS=1
ENUMERATOR_SUPPORT_PROJECTIONS=9
INDEXED_PROPERTY_ACCESSOR_PROJECTIONS=4
GLOBAL_OPTIONAL_OPERATOR_PROJECTIONS=2
```

The two base mismatches, one interface mismatch, one property mismatch, and 16
overload mismatches still belong exclusively to Game, GraphicsDeviceManager,
GraphicsDevice, Texture2D, and SpriteBatch. No Curve type owns a diagnostic.

## Curve type matrix

| Type | Expected/target | Kind | Behavior | Local diagnostics |
|---|---:|---|---|---:|
| `Curve` | 11/11 | open class | XNA-qualified | 0 |
| `CurveKey` | 15/15 | open class | XNA-qualified | 0 |
| `CurveKeyCollection` | 13/13 | open class | XNA-qualified | 0 |
| `CurveContinuity` | 2/2 | Int32 enum | XNA-qualified | 0 |
| `CurveLoopType` | 5/5 | Int32 enum | XNA-qualified | 0 |
| `CurveTangent` | 3/3 | Int32 enum | XNA-qualified | 0 |

The classes are non-sealed in pinned metadata and preserve reference identity.
CurveKey constructors, immutable Position, mutable value/tangents/continuity,
distinct clone, field equality, null-aware operators, deterministic CLR-style
hash, and null-reference failure are exact.

The authoritative XNA IL for `CurveKey.CompareTo` compares Position with direct
`==`, then `<`, then returns +1. Consequently finite order and signed zero are
ordinary; `NaN/finite=+1`, `finite/NaN=+1`, and `NaN/NaN=+1`. This independently
resolves the sibling discrepancy; no sibling repository was modified.

## Collection, tangents, and evaluation

`ICollection<CurveKey>` maps to the concrete seven-member interface contract;
no fake BCL or Swift Collection conformance exists. Transitive enumeration maps
to root `CNAEnumerator<CurveKey>` with throwing `Next`, a fresh live cursor,
source order/reference preservation, and exact version invalidation. Successful
Add/Remove/RemoveAt/Clear and item replacement invalidate; Clear invalidates an
empty collection; failed Remove and CopyTo do not. Indexing is one CLR property
projected as throwing `Item(Int32)` and `SetItem(Int32, CurveKey)` symbols.

Add uses the XNA List binary-search path and inserts normal equal positions
after their run; same references may repeat. Replacement stays in place only
when positions compare equal, otherwise it removes/reinserts. Contains,
IndexOf, and Remove use field equality and first match. CopyTo mutates `inout`
destination storage without cloning keys. Collection and Curve clones own new
collection shape but share contained CurveKey references.

Curve defaults both loops to Constant, preserves one Keys identity, and defines
IsConstant as Count <= 1. Flat tangents are zero; Linear uses raw value
differences; Smooth uses the XNA position-scaled formula and Single epsilon.
Mixed modes are independent, whole-curve computation is forward and stable,
and invalid indices throw.

Evaluate covers empty/single curves, duplicate positions, Step at exactly one,
exact Float Hermite grouping, and the reference Double-widened interpolation
fraction. Constant, Linear, Cycle, CycleOffset, and Oscillate match reference
IL, including exact negative cycle boundaries, negative parity, large values,
and unchecked CLR-like float-to-Int32 behavior.

## Behavior, ABI, native, and template evidence

```text
AUTHORITY=PURE_XNA_DERIVED
PURE_OBSERVATIONS=986
PURE_ASSERTIONS=986
PURE_FAILURES=0
CURVE_ENUMS=1
CURVE_KEY=1
CURVE_COLLECTION=2
CURVE_TANGENTS=1
CURVE_EVALUATE=1
CURVE_LOOPS=1
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
BOUND_FUNCTIONS=25
PROTOTYPE_TYPE_POSITIONS=72
C_SWIFT_MEASUREMENTS=72
LAYOUTS=15
CALLBACKS=2
CONSTANTS=168
MISSING_HEADER_SYMBOLS=0
MISSING_LIBRARY_SYMBOLS=0
ABI_MISMATCHES=0
GAME_CYCLES=20
GAME_RECREATION_CYCLES=20
TEXTURE2D_CYCLES=20
SPRITEBATCH_CYCLES=20
CALLBACK_ERROR_CYCLES=20
NATIVE_CRASHES=0
OBSERVED_UAF=0
OBSERVED_DOUBLE_FREE=0
```

The maintained template remains clean at commit
`86687f62c3a13ee2b59798f338fc083f7399f447`, source tree
`70e6bab6a86db65324a60b04c4cde8aa4bce662e`, and passes maintained 60/600
runs with exact update/draw counts, viewport 800x480, and texture 128x128.
Final source-archive identity and isolated-consumer results are release handoff
artifacts rather than self-referential source content.

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Exactly one next dependency-complete milestone

The regenerated scoreboard selects the XNA GamePad family as the next single
dependency-complete milestone: `ButtonState`, `Buttons`, `GamePad`,
`GamePadButtons`, `GamePadCapabilities`, `GamePadDPad`, `GamePadDeadZone`,
`GamePadState`, `GamePadThumbSticks`, `GamePadTriggers`, and `GamePadType`.
These 11 missing types contain 128 mapped identities and close publicly over
the already-complete PlayerIndex and Vector2 plus Swift/System primitives.

This is selection only. The GamePad family is not started here. Its future run
must independently audit exact native-input requirements and the pinned 0.7
function table; it must not be combined with runtime-partial cleanup, Touch,
Design, Content, Effects/Model, Audio, Media, Storage, or GamerServices.
