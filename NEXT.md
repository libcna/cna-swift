# CNA-Swift continuation handoff

**Foundation Milestone 4 final status:** COMPLETE.

The milestone closes exactly the 17 public concrete XNA PackedVector structs:
Alpha8, Bgr565, Bgra4444, Bgra5551, Byte4, HalfSingle, HalfVector2,
HalfVector4, NormalizedByte2, NormalizedByte4, NormalizedShort2,
NormalizedShort4, Rg32, Rgba1010102, Rgba64, Short2, and Short4. All behavior
is managed Swift. CNA source, the CNA C ABI, the five runtime-partial types,
and maintained template source are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=56 PASS
RELEASE_TESTS=56 PASS
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=47 PASS
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
TARGET_TYPES=49
TARGET_MEMBERS=1198
TOTAL_DIAGNOSTICS=359
MISSING_TYPE=208
MISSING_MEMBER=131
COMPLETE_TYPES=44
PARTIAL_TYPES=5
MISSING_TYPES=208
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
ARRAY_MUTATION_MAPPINGS=18
```

The remaining base mismatches belong to SpriteBatch and Texture2D; the
interface mismatch belongs to GraphicsDeviceManager; the property mismatch
belongs to GraphicsDevice.Viewport; and the 16 overload mismatches belong to
the same deferred runtime partials. No PackedVector type owns a diagnostic.

## Concrete PackedVector matrix

| Type | Expected/target | TPacked | Public converter | Projected witnesses | Local diagnostics |
|---|---:|---|---|---|---:|
| `Alpha8` | 9/9 | `UInt8` | `ToAlpha` | pack + vector4 | 0 |
| `Bgr565` | 10/10 | `UInt16` | `ToVector3` | pack + vector4 | 0 |
| `Bgra4444` | 10/10 | `UInt16` | `ToVector4` | pack | 0 |
| `Bgra5551` | 10/10 | `UInt16` | `ToVector4` | pack | 0 |
| `Byte4` | 10/10 | `UInt32` | `ToVector4` | pack | 0 |
| `HalfSingle` | 9/9 | `UInt16` | `ToSingle` | pack + vector4 | 0 |
| `HalfVector2` | 10/10 | `UInt32` | `ToVector2` | pack + vector4 | 0 |
| `HalfVector4` | 10/10 | `UInt64` | `ToVector4` | pack | 0 |
| `NormalizedByte2` | 10/10 | `UInt16` | `ToVector2` | pack + vector4 | 0 |
| `NormalizedByte4` | 10/10 | `UInt32` | `ToVector4` | pack | 0 |
| `NormalizedShort2` | 10/10 | `UInt32` | `ToVector2` | pack + vector4 | 0 |
| `NormalizedShort4` | 10/10 | `UInt64` | `ToVector4` | pack | 0 |
| `Rg32` | 10/10 | `UInt32` | `ToVector2` | pack + vector4 | 0 |
| `Rgba1010102` | 10/10 | `UInt32` | `ToVector4` | pack | 0 |
| `Rgba64` | 10/10 | `UInt64` | `ToVector4` | pack | 0 |
| `Short2` | 10/10 | `UInt32` | `ToVector2` | pack + vector4 | 0 |
| `Short4` | 10/10 | `UInt64` | `ToVector4` | pack | 0 |

Every row is a Swift struct with one private fixed-width packed value and an
exact get/set `PackedValue`. Equality and operators compare packed bits.
UInt8/UInt16 hashes widen, UInt32 hashes reinterpret, and UInt64 hashes XOR-fold
its 32-bit halves. Strings match the pinned XNA IL paths.

The verifier measures 17 new `PackFromVector4` and eight new reduced-format
`ToVector4` compiler witnesses. With Color, the formal whole-profile count is
26. Its 47 self-tests retain errors for missing/wrong witnesses, a wrong
`TPacked`, and unrelated public members; no general protocol-member suppression
exists.

## Packed-bit behavior

All normalized formats scale in Float, clamp safely for NaN/infinity, widen at
the pinned IL point, and use `System.Math.Round` midpoint-to-even semantics.
SNorm -1 packs to -127/-32767 (`0x81`/`0x8001`); directly assigned minimum
two's-complement codes also decode to -1. Byte4 and Short2/Short4 are raw,
unscaled integer-domain formats.

The half implementation is a bit-level port of XNA `HalfUtils`, not Swift
Float16. It preserves signed zero, subnormals, finite normals, and ties. XNA
canonicalizes positive infinity/NaN to `0x7FFF` and negative infinity/NaN to
`0xFFFF`; these packed exponent-31 patterns decode to finite extended values.
All 65,536 UInt16 patterns decode and repack identically.

Declared zero-failure exhaustive sweeps are Alpha8 256, Bgr565 65,536,
Bgra4444 65,536, Bgra5551 65,536, and HalfSingle 65,536. Exact layouts, fills,
rounding thresholds, non-finite inputs, direct assignment, equality/hash/string,
and independent goldens are documented in `docs/packed-vector-evidence.md`.

## Behavior and native evidence

```text
AUTHORITY=PURE_XNA_DERIVED
PURE_OBSERVATIONS=762
PURE_ASSERTIONS=762
PURE_FAILURES=0
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
PLATFORM=Linux x86-64
RENDERER=HEADLESS
AUDIO_BACKEND=NULL
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

The maintained template remains at unchanged commit
`86687f62c3a13ee2b59798f338fc083f7399f447`; its debug 60-frame and release
600-frame runs both match the requested callback counts, viewport 800x480, and
texture 128x128. Exact final-archive identity and isolated-consumer results are
release handoff artifacts rather than self-referential source content.

## Unchanged partial types

Exactly these five remain partial with their pre-milestone diagnostics:

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Exactly one next dependency-complete milestone

The regenerated scoreboard selects the managed Curve family as the next single
dependency-complete milestone: `Curve`, `CurveKey`, `CurveKeyCollection`,
`CurveContinuity`, `CurveLoopType`, and `CurveTangent`. Their current mapped
member counts are 11, 15, 13, 2, 5, and 3 respectively (49 total); their public
signatures close within that six-type family and Swift/System primitives.

This is a selection only. The Curve family is **not started** here. Do not
combine it with runtime-partial cleanup, Design, Content/XNB, LZX,
Effects/Model, Audio/XACT, Media/Video, Storage, Touch, GamerServices, or CNA
ABI work.
