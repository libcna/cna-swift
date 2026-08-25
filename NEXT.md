# CNA-Swift continuation handoff

**Foundation Milestone 13 final status:** COMPLETE.

The milestone closes exactly
`Microsoft.Xna.Framework.Graphics.RenderTargetUsage`: one XNA public non-flags
`Int32` enum with four declared CLR identities and three mapped Swift
identities. It is a pure managed metadata closure with `DiscardContents=0`,
`PreserveContents=1`, and `PlatformContents=2`, no `OptionSet` conformance, no
string or helper surface, and no native mapping. CNA source, the canonical ABI,
RenderTarget2D, RenderTargetCube, RenderTargetBinding, PresentationParameters,
GraphicsDevice, every render-target and content-preservation behavior, the five
runtime-partial types, DisplayMode, and maintained template source are
unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=98 PASS
RELEASE_TESTS=98 PASS
MANAGED_TESTS=88 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=235 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1271/1271/0
GAMEPAD_NATIVE_FAILURES=0
SWIFT_ASAN=PASS_PURE_CORPUS_DETECT_LEAKS_DISABLED
NATIVE_CNA_SANITIZER=NOT_INSTRUMENTED
KEYBOARD_MANAGED_STATE_AND_PINNED_KEYS=PASS
KEYBOARD_NATIVE_DEFAULT_ROUTE=PASS
KEYBOARD_NATIVE_PER_PLAYER_ROUTE=BOUND_AND_ABI_VERIFIED_NOT_EXERCISED
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=73
TARGET_MEMBERS=1416
TOTAL_DIAGNOSTICS=335
MISSING_TYPE=184
MISSING_MEMBER=131
COMPLETE_TYPES=68
PARTIAL_TYPES=5
MISSING_TYPES=184
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
GraphicsDevice, Texture2D, and SpriteBatch, and `MISSING_MEMBER` is unchanged
at 131 because no partial type was touched. Every other mismatch,
unexpected-surface, leak, allowlist, and unmeasured category is zero. Every
formal projection counter carried over unchanged, including the 49
enum-storage exclusions, which already contained this type's `value__`.

## RenderTargetUsage type matrix

| Type | CLR / expected / target | Kind | Raw type | Flags | Diagnostics |
|---|---:|---|---|---|---:|
| `RenderTargetUsage` | 4 / 3 / 3 | CLR enum → Swift `enum` | `Int32` | false | 0 |

| CLR identity | Swift shape |
|---|---|
| `value__` | excluded enum-storage language mapping |
| `DiscardContents = 0` | `case DiscardContents = 0` |
| `PreserveContents = 1` | `case PreserveContents = 1` |
| `PlatformContents = 2` | `case PlatformContents = 2` |

The pinned assembly was disassembled directly this milestone. The type is
`sealed`, extends `[mscorlib]System.Enum`, has no `implements` clause, declares
`int32 value__` plus exactly the three literals above, and carries **no**
`System.FlagsAttribute` — unlike `BufferUsage` in the same image, which does.
So `FLAGS=false` is an observed absence in the pinned binary, not an assumption.

The three literals are mutually exclusive alternatives, so the Swift projection
is an ordinary `enum` and never an `OptionSet`. Valid raw initializers 0, 1, and
2 return their exact cases; 3, -1, `Int32.max`, and `Int32.min` return `nil`.
Assignment is ordinary Swift value copying with no reference ownership, native
lifetime, generation, or initialization side effect. No `description`,
`ToString`, `String`, predicate helper, alias, `OptionSet` operation, or native
conversion exists, and no allowlist entry or new mapping rule was needed —
registering the type in the existing `rawTypeChecks` list is the same per-enum
registration every previously completed enum uses.

See `docs/render-target-usage-evidence.md` for the IL, the strict-zero matrix,
mutation coverage, and the dependency boundary.

## Dependency effect and deferred boundary

The public-signature dependency graph was regenerated with the retained
`tools/api_compat/dependency_graph.py`. RenderTargetUsage has zero XNA
dependencies. It has exactly three still-missing direct reverse consumers —
`PresentationParameters`, `RenderTarget2D`, and `RenderTargetCube` — and no
direct partial reverse consumer. The transitive reverse closure is 50 missing
types plus all five unchanged partials.

**Every one of those consumers remains deferred.** No RenderTarget2D,
RenderTargetCube, RenderTargetBinding, PresentationParameters,
`GraphicsDevice.SetRenderTarget`, render-target creation, depth attachment,
MSAA, native constant, or native usage mapping was implemented or started.
Capability is limited to
`RenderTargetUsage managed enum contract: VERIFIED_MANAGED`. The literal names
describe XNA's content-preservation policy; a completed enum is not a working
discard, preserve, or platform-defined content path, and none is claimed.

## Retained native evidence

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b (pinned; not
    re-derivable from the local artifact — see below)
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

The retained ABI-0.7.0 artifact at `~/deps/cna-c-abi-0.7.0` keeps the
Foundation-12 binary SHA-256 `c62949d2…` and still carries no retained
provenance marker, so `CNA_SOURCE_REVISION` remains **pinned-but-not-
re-derivable**: it is the value carried forward from earlier handoffs and could
not be independently re-derived from the local artifact this milestone either.
No revision is guessed or fabricated, and provenance movement is not treated as
an ABI delta. What *is* verified is the contract itself: the loaded library
reports encoded ABI 1792 (0.7.0), and every measured count is byte-identical to
Foundation 12, with zero missing header symbols, zero missing library symbols,
and zero ABI mismatches. Nothing in Foundation 13 touches CNA source or the ABI,
and the regenerated native ABI report is unchanged on disk.

One inherited gate line was corrected rather than carried forward. Earlier
handoffs since `459b874` reported
`KEYBOARD_DEFAULT_AND_PLAYERS_ONE_THROUGH_FOUR=PASS`, but no test in this
repository calls `Keyboard.GetState(_ playerIndex:)`, so that PASS was not
reproducible. What is actually verified is stated above: the managed
`KeyboardState`/`Keys` surface passes, and the native default
`Keyboard.GetState()` route executes on the HEADLESS device. The per-player
route is really implemented and really bound — `cna_keyboard_get_state_for_player`
is one of the 29 manifest functions the native ABI verifier checks, with zero
missing library symbols — but it is not exercised by any test, so it is
reported as bound and ABI-verified rather than as a passing behavior gate. No
Keyboard code changed in this milestone; only the claim was made honest.

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
`7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc` and was
independently re-derived this milestone from
`Microsoft.Xna.Framework.Graphics.dll` SHA-256
`560080fc39021c611ca9d076dcebed312faf6d7d1413c2dc523683ea635e9f55`, whose
`Microsoft.Xna.Framework.dll` companion keeps the retained SHA-256
`38e7093f52d7474bbc6256906519781a1210d7da50a1c667b52716fcf49ca130`. Both are
mixed-mode C++/CLI images whose metadata is readable on the Linux qualification
host and was queried there. Foundation 12 established that they cannot execute
directly under Mono on this host; that limitation is irrelevant here, because
RenderTargetUsage declares no executable member and its entire contract is
metadata. No behavior surrogate or reference probe was created for this
milestone. No Microsoft binary or extracted proprietary source is in the
repository or the archive.

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Exactly one next dependency-complete milestone

The regenerated graph contains 71 missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 14 selects exactly
`Microsoft.Xna.Framework.Graphics.GraphicsProfile`.

The ranking was recomputed after RenderTargetUsage completion. Three candidates
tie at the top transitive missing reverse reach of 50: GraphicsProfile,
DisplayModeCollection, and PresentInterval. GraphicsProfile wins the established
tie-break with two direct missing reverse consumers — `GraphicsAdapter` and
`GraphicsDeviceInformation` — against one each for the others; it additionally
has two direct partial reverse consumers, `GraphicsDevice` and
`GraphicsDeviceManager`, which remain untouched partials. It has zero XNA
dependencies, so it is trivially dependency-complete, and it is a standalone
non-flags `Int32` enum with three CLR identities (`value__`, `Reach=0`,
`HiDef=1`) and two mapped Swift identities.

This is selection only. `GraphicsProfile` has not been started and must not be
combined with adapter, device, device-information, capability, or renderer work.

```text
SELECTED_ONLY=true
STARTED=false
```
