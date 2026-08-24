# CNA-Swift continuation handoff

**Foundation Milestone 11 final status:** COMPLETE.

The milestone closes exactly
`Microsoft.Xna.Framework.Graphics.DepthFormat`: one XNA public type, five CLR
identities, and four mapped Swift identities. It is an exact managed non-flags
`Int32` enum with `None=0`, `Depth16=1`, `Depth24=2`, and
`Depth24Stencil8=3`. CNA source, the canonical ABI, adapter/presentation and
render-target APIs, every depth/stencil runtime feature, every
GraphicsDeviceManager member, the five runtime-partial types, and maintained
template source are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=87 PASS
RELEASE_TESTS=87 PASS
MANAGED_TESTS=77 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=161 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1251/1251/0
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
TARGET_TYPES=71
TARGET_MEMBERS=1407
TOTAL_DIAGNOSTICS=337
MISSING_TYPE=186
MISSING_MEMBER=131
COMPLETE_TYPES=66
PARTIAL_TYPES=5
MISSING_TYPES=186
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

## DepthFormat type matrix

| Type | CLR / expected / target | Kind | Raw type | Flags | Diagnostics |
|---|---:|---|---|---|---:|
| `DepthFormat` | 5 / 4 / 4 | CLR enum → Swift `enum` | `Int32` | false | 0 |

| Case | Raw |
|---|---:|
| `None` | 0 |
| `Depth16` | 1 |
| `Depth24` | 2 |
| `Depth24Stencil8` | 3 |

The synthetic CLR `value__` identity is the existing enum-storage language
mapping. Swift `rawValue`, `init?(rawValue:)`, equality, and value copying are
compiler language surface and produce no unexpected XNA member. All raw values
0...3 construct the exact cases; 4, -1, and `Int32.max` return `nil`.

DepthFormat is not an OptionSet and has no custom string or helper surface.
`Depth24Stencil8` is a single ordinary literal, not flags composition. See
`docs/depth-format-evidence.md` for the exact contract, strict-zero matrix,
mutation coverage, and dependency boundary.

## Dependency effect and deferred boundary

The regenerated public-signature graph retains four still-missing direct
reverse consumers: GraphicsAdapter, PresentationParameters, RenderTarget2D,
and RenderTargetCube. GraphicsDeviceManager is the one direct partial consumer
and remains unchanged. The transitive reverse closure is 54 missing types plus
all five unchanged partial types.

No GraphicsAdapter, PresentationParameters, RenderTarget2D, RenderTargetCube,
GraphicsDeviceManager.PreferredDepthStencilFormat, DepthStencilState,
depth/stencil buffer, attachment, clear, test, renderer capability, native
constant, or native format mapping was implemented or started. Capability is
limited to `DepthFormat: VERIFIED_MANAGED`; the enum does not prove GPU support
for Depth16, Depth24, or Depth24Stencil8.

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

The regenerated graph contains 66 missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 12 selects exactly
`Microsoft.Xna.Framework.Graphics.DisplayMode`.

This is not an automatic choice based on its earlier eligibility. The ranking
was recomputed after DepthFormat completion: DisplayMode has the highest
transitive missing reverse reach at 54, with two direct missing reverse
consumers and one direct partial consumer. The next candidate,
RenderTargetUsage, has reverse reach 53. DisplayMode's dependencies,
SurfaceFormat and Rectangle, are both strict-complete.

This is selection only. `DisplayMode` has not been started and must not be
combined with DisplayModeCollection, GraphicsAdapter, presentation, device, or
renderer work.

```text
SELECTED_ONLY=true
STARTED=false
```
