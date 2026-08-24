# CNA-Swift continuation handoff

**Foundation Milestone 10 final status:** COMPLETE.

The milestone closes exactly
`Microsoft.Xna.Framework.Graphics.SurfaceFormat`: one XNA public type, 21 CLR
identities, and 20 mapped Swift identities. It is an exact managed non-flags
`Int32` enum with the complete pinned 0...19 literal table. CNA source, the
canonical ABI, display/adapter/presentation APIs, texture and render-target
APIs, every GraphicsDevice/GraphicsDeviceManager member, the five runtime-
partial types, and maintained template source are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=85 PASS
RELEASE_TESTS=85 PASS
MANAGED_TESTS=75 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=145 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1249/1249/0
GAMEPAD_NATIVE_FAILURES=0
SWIFT_ASAN=PASS_PURE_CORPUS_DETECT_LEAKS_DISABLED
NATIVE_CNA_SANITIZER=NOT_INSTRUMENTED
KEYBOARD_DEFAULT_AND_PLAYERS_ONE_THROUGH_FOUR=PASS
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=70
TARGET_MEMBERS=1403
TOTAL_DIAGNOSTICS=338
MISSING_TYPE=187
MISSING_MEMBER=131
COMPLETE_TYPES=65
PARTIAL_TYPES=5
MISSING_TYPES=187
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
overload mismatches remain owned exclusively by Game, GraphicsDeviceManager,
GraphicsDevice, Texture2D, and SpriteBatch. Every other mismatch,
unexpected-surface, leak, allowlist, and unmeasured category is zero.

## SurfaceFormat type matrix

| Type | CLR / expected / target | Kind | Raw type | Flags | Diagnostics |
|---|---:|---|---|---|---:|
| `SurfaceFormat` | 21 / 20 / 20 | CLR enum → Swift `enum` | `Int32` | false | 0 |

| Case | Raw | Case | Raw |
|---|---:|---|---:|
| Color | 0 | Rg32 | 10 |
| Bgr565 | 1 | Rgba64 | 11 |
| Bgra5551 | 2 | Alpha8 | 12 |
| Bgra4444 | 3 | Single | 13 |
| Dxt1 | 4 | Vector2 | 14 |
| Dxt3 | 5 | Vector4 | 15 |
| Dxt5 | 6 | HalfSingle | 16 |
| NormalizedByte2 | 7 | HalfVector2 | 17 |
| NormalizedByte4 | 8 | HalfVector4 | 18 |
| Rgba1010102 | 9 | HdrBlendable | 19 |

The synthetic CLR `value__` identity is the existing enum-storage language
mapping. Swift `rawValue`, `init?(rawValue:)`, equality, and value copying are
compiler language surface and produce no unexpected XNA member. All raw values
0...19 construct the exact cases; 20, -1, and `Int32.max` return `nil`.

SurfaceFormat is not an OptionSet and has no custom string/helper surface or
PackedVector dependency. See `docs/surface-format-evidence.md` for the exact
contract, strict-zero matrix, mutation coverage, and dependency evidence.

## Dependency effect and deferred boundary

The regenerated public-signature graph retains nine still-missing direct
reverse dependents: DisplayMode, DisplayModeCollection, GraphicsAdapter,
PresentationParameters, RenderTarget2D, RenderTargetCube, Texture, Texture3D,
and TextureCube. Texture2D and GraphicsDeviceManager are two additional direct
partial consumers and remain unchanged. The transitive reverse closure is 56
missing types plus the same five partial types.

DisplayMode now has only complete public-signature XNA dependencies
(SurfaceFormat and Rectangle), but neither DisplayMode nor any other dependent
was implemented or started. There is no DisplayModeCollection, GraphicsAdapter,
PresentationParameters, Texture constructor, Texture/RenderTarget family,
GraphicsDeviceManager format property, GraphicsDevice format operation, pixel
conversion, DXT implementation, HDR support, GPU negotiation, or CNA-native
SurfaceFormat mapping.

Capability is limited to `SurfaceFormat: VERIFIED_MANAGED`. Enum completeness
is not evidence of actual renderer/GPU support for any format.

## Retained native evidence

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
BOUND_FUNCTIONS=29
PROTOTYPE_TYPE_POSITIONS=91
C_SWIFT_MEASUREMENTS=91
LAYOUTS=18
CALLBACKS=2
CONSTANTS=214
MISSING_HEADER_SYMBOLS=0
MISSING_LIBRARY_SYMBOLS=0
ABI_MISMATCHES=0
GAME_CYCLES=20
GAME_RECREATION_CYCLES=20
TEXTURE2D_CYCLES=20
SPRITEBATCH_CYCLES=20
CALLBACK_ERROR_CYCLES=20
GAMEPAD_GET_STATE_CYCLES_PER_MODE=50
GAMEPAD_GET_STATE_CALLS=200
GAMEPAD_CAPABILITIES_CYCLES=20
NATIVE_CRASHES=0
OBSERVED_UAF=0
OBSERVED_DOUBLE_FREE=0
```

The retained GamePad default/None/IndependentAxes/Circular state routes,
capabilities, disconnected SetVibration, generation, wrong-thread, and stress
qualification all pass. This HEADLESS/NULL host has no attached controller, so
positive controller observations and physical rumble remain
`HARDWARE_PENDING`; no result is fabricated.

The unchanged maintained template remains at commit
`86687f62c3a13ee2b59798f338fc083f7399f447` and passes debug 60 / release 600
with exact callback counts, viewport 800x480, and texture 128x128. Exact source
archive identity and isolated-consumer results are final handoff artifacts, not
self-referential source content.

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Exactly one next dependency-complete milestone

The regenerated graph contains 67 missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 11 selects exactly the
standalone managed `Microsoft.Xna.Framework.Graphics.DepthFormat` enum. It has
no XNA dependency and four mapped Swift literals (`value__` excluded).

DepthFormat and DisplayMode each lead to 54 still-missing types by transitive
reverse reach. The consistent tie-break selects DepthFormat because it has four
direct missing reverse dependents versus DisplayMode's two, while remaining a
bounded dependency-free managed enum. DisplayMode was evaluated after becoming
dependency-complete; it was not selected automatically merely because
SurfaceFormat unlocked it. Design-time converter closures remain outside this
runtime ranking because their external System.ComponentModel projection is not
established.

This is selection only. `DepthFormat` has not been started and must not be
combined with PresentationParameters, render targets, depth-stencil state,
format negotiation, or CNA ABI work.

```text
SELECTED_ONLY=true
STARTED=false
```
