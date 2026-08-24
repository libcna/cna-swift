# CNA-Swift continuation handoff

**Foundation Milestone 3 final status:** COMPLETE.

The milestone closes exactly three compiler-measured identities:

- `Microsoft.Xna.Framework.Color`;
- `Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVector`;
- `Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVectorOfT<TPacked>`.

Pinned Color signatures and its direct generic interface force those two
protocols. Vector3 and Vector4 were already complete. No concrete PackedVector
type occurs in the regenerated dependency graph, and none was started. All new
behavior is managed Swift; CNA source, the CNA C ABI, and the maintained
template source are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=39 PASS
RELEASE_TESTS=39 PASS
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=41 PASS
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
TARGET_TYPES=32
TARGET_MEMBERS=1030
TOTAL_DIAGNOSTICS=376
MISSING_TYPE=225
MISSING_MEMBER=131
COMPLETE_TYPES=27
PARTIAL_TYPES=5
MISSING_TYPES=225
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
LANGUAGE_PROJECTION_EXCLUSIONS=88
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=7
INHERITED_MEMBER_PROJECTIONS=3
PROTOCOL_WITNESS_MEMBER_PROJECTIONS=1
ARRAY_MUTATION_MAPPINGS=18
```

The remaining base mismatches belong to SpriteBatch and Texture2D; the
remaining interface mismatch belongs to GraphicsDeviceManager; the property
mismatch belongs to GraphicsDevice.Viewport; and the 16 overload mismatches
belong to deferred runtime partials. Color owns none of the remaining
diagnostics.

## Complete Milestone-3 matrix

| Type | Kind | Generic parameters | Inheritance/conformance | Expected | Target | Local diagnostics |
|---|---|---|---|---:|---:|---:|
| `Color` | struct | none | `IPackedVectorOfT<UInt32>` | 165 | 165 | 0 |
| `IPackedVector` | protocol | none | none | 2 | 2 | 0 |
| `IPackedVectorOfT` | protocol | `TPacked` | `IPackedVector` | 1 | 1 | 0 |

`IPackedVector.PackFromVector4` is a mutating value-type requirement;
`ToVector4` returns the completed Framework Vector4; and the generic protocol's
`PackedValue: TPacked` is get/set. The compiler Symbol Graph exposes the exact
protocol kinds, inheritance, primary associated-type identity, and Color's
UInt32 witness. Color moved from 21/165 to 165/165; its interface mismatch moved
from one to zero and its two constructor overload mismatches moved to zero.

Color now has independently qualified integer, Float, Vector3, and Vector4
packing; mutating `PackFromVector4`; exact binary32 `ToVector3`/`ToVector4`;
both `FromNonPremultiplied` forms; packed-value/channel mutation; fixed-point
`Lerp`; saturating `Multiply`; packed equality/hash behavior; exact string
formatting; and every one of the 141 pinned predefined properties. The full
palette test uses a separate XNA-derived golden table and checks packed value
plus every channel.

## Behavior and native evidence

```text
AUTHORITY=PURE_XNA_DERIVED
PURE_OBSERVATIONS=415
PURE_ASSERTIONS=415
PURE_FAILURES=0
COLOR_GROUP=13
COLOR_PALETTE_GOLDEN_ENTRIES=141
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

The maintained template remains at its unchanged source revision. Its debug
60-frame run reports 60 updates/60 draws and its release 600-frame run reports
600 draws, viewport 800x480, and texture 128x128. Exact final-commit archive
identity and isolated-consumer results are release handoff artifacts rather
than self-referential source content.

Implementation and authority evidence are retained in
`docs/color-packed-protocol-evidence.md`; current compiler and behavior reports
are under `docs/generated/`.

## Exactly one next dependency-complete milestone

The regenerated scoreboard identifies the managed concrete PackedVector format
family as one dependency-complete next milestone: Alpha8, Bgr565, Bgra4444,
Bgra5551, Byte4, HalfSingle, HalfVector2, HalfVector4, NormalizedByte2,
NormalizedByte4, NormalizedShort2, NormalizedShort4, Rg32, Rgba1010102, Rgba64,
Short2, and Short4. Their public dependencies are the now-complete packed
protocols and already-complete Vector2/Vector3/Vector4 value types.

That family is **not started** in Foundation Milestone 3. Do not combine it
with Curve, runtime partial cleanup, Content/XNB, Effects/Model, Audio, Media,
Storage, Touch, GamerServices, Design, or CNA ABI work.
