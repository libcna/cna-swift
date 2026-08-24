# CNA-Swift continuation handoff

**Foundation Milestone 2 final status:** COMPLETE. This is the final status of
Milestone 2, not Foundation Milestone 3.

Pinned XNA metadata proved that complete Matrix requires Plane and that
complete Plane recursively requires the geometry/intersection types. The
corrected milestone therefore closes exactly the following two parts:

- binary32 linear algebra: Vector2, Vector3, Vector4, Quaternion, Matrix,
  Graphics.Viewport;
- Matrix's forced public-signature closure: Plane, PlaneIntersectionType, Ray,
  BoundingBox, BoundingSphere, BoundingFrustum, ContainmentType.

Every one of these 13 types is complete and locally zero-diagnostic. No other
geometry, Color, Content, Effects, renderer, or CNA ABI work was included.

## Qualified environment

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=27 PASS
RELEASE_TESTS=27 PASS
WARNINGS_AS_ERRORS=PASS
SYMBOL_GRAPH=PASS
SWIFT_ASAN=PASS_PURE_CORPUS_DETECT_LEAKS_DISABLED
NATIVE_CNA_SANITIZER=NOT_INSTRUMENTED
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=30
TARGET_MEMBERS=883
TOTAL_DIAGNOSTICS=525
MISSING_TYPE=227
MISSING_MEMBER=275
COMPLETE_TYPES=24
PARTIAL_TYPES=6
MISSING_TYPES=227
UNEXPECTED_TYPE=0
UNEXPECTED_MEMBER=0
TYPE_KIND_MISMATCH=0
BASE_MAPPING_MISMATCH=2
INTERFACE_MAPPING_MISMATCH=2
FIELD_MAPPING_MISMATCH=0
PROPERTY_MAPPING_MISMATCH=1
METHOD_SIGNATURE_MAPPING_MISMATCH=0
PARAMETER_MAPPING_MISMATCH=0
RETURN_MAPPING_MISMATCH=0
OVERLOAD_MAPPING_MISMATCH=18
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
LANGUAGE_PROJECTION_EXCLUSIONS=86
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=6
INHERITED_MEMBER_PROJECTIONS=3
ARRAY_MUTATION_MAPPINGS=18
```

Twenty-nine verifier mutation/self-tests pass. Normal strict exits red only
because 227 future types and 275 members of deferred partial runtime/value types
are genuinely absent; leak-only is green. The remaining global mismatch owners
are unchanged: SpriteBatch/Texture2D bases, Color/GraphicsDeviceManager
interfaces, GraphicsDevice.Viewport mutability, and overloads on Color, Game,
GraphicsDevice, SpriteBatch, Texture2D, and GraphicsDeviceManager.

## Complete Milestone-2 matrix

| Type | Expected | Target | Local diagnostics | Kind | Behavior |
|---|---:|---:|---:|---|---|
| Vector2 | 77 | 77 | 0 | struct | PASS |
| Vector3 | 88 | 88 | 0 | struct | PASS |
| Vector4 | 85 | 85 | 0 | struct | PASS |
| Quaternion | 55 | 55 | 0 | struct | PASS |
| Matrix | 107 | 107 | 0 | struct | PASS |
| Graphics.Viewport | 14 | 14 | 0 | struct | PASS |
| Plane | 30 | 30 | 0 | struct | PASS |
| PlaneIntersectionType | 3 | 3 | 0 | enum | PASS |
| Ray | 16 | 16 | 0 | struct | PASS |
| BoundingBox | 33 | 33 | 0 | struct | PASS |
| BoundingSphere | 33 | 33 | 0 | struct | PASS |
| BoundingFrustum | 33 | 33 | 0 | class | PASS |
| ContainmentType | 3 | 3 | 0 | enum | PASS |

`Nullable<Single>` and nullable out results are formally measured as `Float?`
and `inout Float?`. Plane dot, Matrix/Quaternion transforms, and all
intersections are present. Box corner order and caller-owned destination
mutation are exact. Sphere point construction, merge, and largest-basis-scale
Matrix transform are qualified. BoundingFrustum preserves class semantics,
recomputes planes/corners on Matrix mutation, uses exact XNA plane/corner
ordering, and contains only a private scalar GJK helper.

## Behavior and native evidence

```text
AUTHORITY=PURE_XNA_DERIVED
PURE_OBSERVATIONS=360
PURE_ASSERTIONS=360
PURE_FAILURES=0
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b
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

The implementation and conventions are documented in
`docs/linear-algebra-evidence.md` and
`docs/geometry-intersection-evidence.md`. All new closure behavior is managed
Swift; no native symbol, handle, library, or public helper identity was added.
The template source is unchanged and its maintained debug-60 and release-600
canaries pass with exact Update/Draw counts, viewport 800x480, and texture
128x128.

## Deferred boundaries

Color remains deliberately unchanged at 21/165 with 144 missing identities.
The six runtime partials are otherwise unchanged. Content/XNB, Effects,
rendering, Audio, Media, Storage, Touch, GamerServices, Design, and concrete
PackedVector formats remain deferred. Do not modify CNA.

## Exactly one next dependency-complete milestone

The next milestone should be the managed Color/protocol closure:

`Color`, `Graphics.PackedVector.IPackedVector`, and
`Graphics.PackedVector.IPackedVector<TPacked>` plus only language mapping needed
for those exact interfaces. Pinned Color signatures and direct interfaces force
only those two PackedVector protocols; they do not force the concrete packed
format structs. Complete all three locally before considering a broader
PackedVector family.

Do not combine that milestone with runtime partials, Content, Effects,
rendering, or concrete PackedVector formats unless a regenerated public
signature graph proves an additional dependency.
