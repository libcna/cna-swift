# CNA-Swift continuation handoff

**Foundation Milestone 12 final status:** COMPLETE.

The milestone closes exactly
`Microsoft.Xna.Framework.Graphics.DisplayMode`: one XNA public class with six
declared public identities and six mapped Swift identities. It is an exact
managed descriptor with **no public constructor**, verbatim `Width`/`Height`/
`Format` storage, a guarded binary32 `AspectRatio`, the unmodified Windows
`TitleSafeArea` rectangle, and the exact XNA `ToString`. CNA source, the
canonical ABI, DisplayModeCollection, GraphicsAdapter,
`GraphicsDevice.DisplayMode`, presentation and render-target APIs, every
monitor/display feature, the five runtime-partial types, and maintained
template source are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=96 PASS
RELEASE_TESTS=96 PASS
MANAGED_TESTS=86 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=201 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1269/1269/0
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
TARGET_TYPES=72
TARGET_MEMBERS=1413
TOTAL_DIAGNOSTICS=336
MISSING_TYPE=185
MISSING_MEMBER=131
COMPLETE_TYPES=67
PARTIAL_TYPES=5
MISSING_TYPES=185
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
NONPUBLIC_CONSTRUCTION_PROJECTIONS=4
```

The two base mismatches, one interface mismatch, one property mismatch, and 16
overload mismatches remain owned exclusively by Game, GraphicsDeviceManager,
GraphicsDevice, Texture2D, and SpriteBatch. Every other mismatch,
unexpected-surface, leak, allowlist, and unmeasured category is zero. Every
formal projection counter carried over unchanged;
`NONPUBLIC_CONSTRUCTION_PROJECTIONS` is the one new measured counter.

## DisplayMode type matrix

| Type | CLR / expected / target | Kind | Public ctors | Diagnostics |
|---|---:|---|---:|---:|
| `DisplayMode` | 6 / 6 / 6 | CLR class → Swift `class` | 0 | 0 |

| Identity | Swift shape |
|---|---|
| `ToString` | `public func ToString() -> String` |
| `Format` | `public var Format: SurfaceFormat { get }` |
| `Height` | `public var Height: Int32 { get }` |
| `Width` | `public var Width: Int32 { get }` |
| `AspectRatio` | `public var AspectRatio: Float { get }` |
| `TitleSafeArea` | `public var TitleSafeArea: Rectangle { get }` |

The reference declares exactly one `assembly`-accessible
`.ctor(int32 width, int32 height, valuetype SurfaceFormat format)` that stores
its three arguments verbatim with no validation. It maps to
`internal init(width:height:format:)`, which never appears in the public Symbol
Graph and therefore adds no XNA identity. The Swift class is deliberately
neither `open` (no accessible CLR constructor makes it externally subclassable)
nor `final` (metadata says `sealed=false`).

`AspectRatio` short-circuits to positive zero when either stored dimension is
zero and is otherwise the binary32 quotient of two `conv.r4` conversions, so no
infinity, NaN, negative zero, or integer division can occur, and negative
dimensions are neither clamped nor absolute-valued. `TitleSafeArea` is exactly
`Rectangle(0, 0, Width, Height)` with independent value semantics and no
display query. `ToString` emits
`{Width:W Height:H Format:F AspectRatio:A}` with the CLR literal format name.

No `Equals`, `GetHashCode`, `op_Equality`, `op_Inequality`, `Equatable`,
`Hashable`, setter, public initializer, static factory, `description`, or
convenience helper exists. SurfaceFormat is untouched at 21 CLR / 20 Swift
identities with zero local diagnostics and no public string surface.

Qualifying `ToString` exposed and fixed one genuine general defect: the shared
invariant general-float formatter matched CLR "G7" in notation, digits and
exponent width but spelled the exponent marker in lower case. DisplayMode is
the first qualified type whose ordinary `Int32` inputs reach exponent range.
The fix is general, changes nothing in the fixed-point domain every previously
qualified type uses, and is covered by retained `1.677722E+07`,
`2.147484E+09`, and `4.656613E-10` observations.

See `docs/display-mode-evidence.md` for the IL, the retained reference tables,
the strict-zero matrix, mutation coverage, and the dependency boundary.

## Dependency effect and deferred boundary

The public-signature dependency graph is now a retained, reproducible tool
(`tools/api_compat/dependency_graph.py`, generated into
`docs/generated/dependency-graph.json`). Its edge rule is: `A -> B` when `A`'s
pinned public signature — base type, direct interface, member return type,
property or field type, or parameter type — mentions XNA type `B`, with
generic arguments and array/by-ref decorations unwrapped.

DisplayMode has two still-missing direct reverse consumers,
`DisplayModeCollection` and `GraphicsAdapter`, and one direct partial consumer,
`GraphicsDevice`, whose missing `DisplayMode()` member is unchanged. The
transitive reverse closure is 51 missing types plus all five unchanged
partials. Earlier handoffs reported this reach as 54 from a non-retained ad-hoc
computation; 51 is the regenerated value under the now-retained edge rule, and
the direct-consumer counts match the earlier record exactly.

No DisplayModeCollection, GraphicsAdapter, `GraphicsDevice.DisplayMode`,
PresentationParameters, monitor query, display enumeration, resolution switch,
renderer capability, native constant, or native display mapping was implemented
or started. Capability is limited to
`DisplayMode managed descriptor contract: VERIFIED_MANAGED`; a managed
descriptor class is not platform display integration.

## Retained native evidence

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b (pinned; not
    re-verifiable from the local artifact — see below)
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

The retained ABI-0.7.0 artifact at `~/deps/cna-c-abi-0.7.0` was replaced since
Foundation 11: its binary SHA-256 is now
`c62949d2…` rather than the previously recorded `42e09914…`, and the directory
carries no retained provenance marker, so `CNA_SOURCE_REVISION` above is the
pinned value from the prior handoff and could not be re-derived from the local
artifact this milestone. What *is* verified is the contract itself: the loaded
library reports encoded ABI 1792 (0.7.0), and every measured count — 29 bound
functions, 91 prototype type positions, 91 C/Swift measurements, 18 layouts,
two callbacks, 214 constants — is identical to Foundation 11, with zero missing
header symbols, zero missing library symbols, and zero ABI mismatches. Nothing
in Foundation 12 touches CNA source or the ABI.

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

## Reference provenance

Public shape comes from the pinned contract SHA-256
`7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`. DisplayMode
structure and behavior come from `Microsoft.Xna.Framework.Graphics.dll` SHA-256
`560080fc39021c611ca9d076dcebed312faf6d7d1413c2dc523683ea635e9f55`, whose
`Microsoft.Xna.Framework.dll` companion keeps the retained SHA-256
`38e7093f52d7474bbc6256906519781a1210d7da50a1c667b52716fcf49ca130`. Both are
mixed-mode C++/CLI images: their metadata is readable on the Linux
qualification host and was queried there, while the value-producing evidence was
obtained by executing the disassembled IL's exact instruction sequence through
the retained, independently authored surrogate. No Microsoft binary or
extracted proprietary source is in the repository or the archive.

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Exactly one next dependency-complete milestone

The regenerated graph contains 72 missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 13 selects exactly
`Microsoft.Xna.Framework.Graphics.RenderTargetUsage`.

The ranking was recomputed after DisplayMode completion. Four candidates tie at
the top transitive missing reverse reach of 50: RenderTargetUsage,
GraphicsProfile, DisplayModeCollection, and PresentInterval. RenderTargetUsage
wins the established tie-break with three direct missing reverse consumers —
`PresentationParameters`, `RenderTarget2D`, and `RenderTargetCube` — against two
for GraphicsProfile and one each for the others. It has zero XNA dependencies,
so it is trivially dependency-complete, and it is a standalone non-flags `Int32`
enum with four CLR identities (`value__`, `DiscardContents=0`,
`PreserveContents=1`, `PlatformContents=2`) and three mapped Swift identities.

DisplayModeCollection is deliberately *not* selected despite becoming
dependency-complete through this milestone; it ranks below RenderTargetUsage on
the same recomputed criteria.

This is selection only. `RenderTargetUsage` has not been started and must not be
combined with render-target, presentation, adapter, device, or renderer work.

```text
SELECTED_ONLY=true
STARTED=false
```
