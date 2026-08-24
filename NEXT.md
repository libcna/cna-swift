# CNA-Swift continuation handoff

**Foundation Milestone 7 final status:** COMPLETE.

The milestone closes exactly
`Microsoft.Xna.Framework.DisplayOrientation`: one XNA public type, five CLR
identities, and four mapped Swift identities. It is an exact managed `Int32`
OptionSet with values 0/1/2/4. CNA source, the canonical ABI, every
GraphicsDeviceManager and GameWindow member, the five runtime-partial types,
and maintained template source are unchanged.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=79 PASS
RELEASE_TESTS=79 PASS
MANAGED_TESTS=69 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=102 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1243/1243/0
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
TARGET_TYPES=67
TARGET_MEMBERS=1379
TOTAL_DIAGNOSTICS=341
MISSING_TYPE=190
MISSING_MEMBER=131
COMPLETE_TYPES=62
PARTIAL_TYPES=5
MISSING_TYPES=190
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
GraphicsDevice, Texture2D, and SpriteBatch. Every GamePad-family mismatch
category is zero.

## DisplayOrientation type matrix

| Type | CLR / expected / target | Kind | Raw type | Values | Diagnostics |
|---|---:|---|---|---|---:|
| `DisplayOrientation` | 5 / 4 / 4 | CLR flags enum → Swift `OptionSet` | `Int32` | Default=0, LandscapeLeft=1, LandscapeRight=2, Portrait=4 | 0 |

The synthetic CLR `value__` identity is the existing enum-storage language
mapping. Swift `rawValue`, `init(rawValue:)`, and inherited OptionSet operations
are compiler language surface and produce no unexpected XNA member. Union,
intersection, arbitrary raw bits including 8 and -1, and value-copy behavior
are qualified separately from the four pinned XNA-derived literal
observations. See `docs/display-orientation-evidence.md`.

No runtime orientation capability is claimed. SupportedOrientations,
GameWindow, display detection, SDL/mobile/window rotation, and every native ABI
entry remain deferred.

## Retained GamePad type matrix

| Type | CLR / expected / target | Kind | Behavior | Native | Diagnostics |
|---|---:|---|---|---|---:|
| ButtonState | 3 / 2 / 2 | Int32 enum | verified | N/A | 0 |
| Buttons | 26 / 25 / 25 | Int32 OptionSet | verified | explicit bits | 0 |
| GamePad | 4 / 4 / 4 | final class/private init | verified | route verified | 0 |
| GamePadButtons | 17 / 17 / 17 | struct | verified | copied value | 0 |
| GamePadCapabilities | 26 / 26 / 26 | struct/no public init | verified | route verified | 0 |
| GamePadDPad | 10 / 10 / 10 | struct | verified | copied value | 0 |
| GamePadDeadZone | 4 / 3 / 3 | Int32 enum | verified | explicit modes | 0 |
| GamePadState | 15 / 15 / 15 | struct | verified | route verified | 0 |
| GamePadThumbSticks | 8 / 8 / 8 | struct | verified | copied value | 0 |
| GamePadTriggers | 8 / 8 / 8 | struct | verified | copied value | 0 |
| GamePadType | 11 / 10 / 10 | Int32 enum | verified | explicit mapping | 0 |

Buttons has all 25 explicit raw values and retains arbitrary combinations.
The state implements all physical/DPad/stick-click/BigButton identities, eight
virtual stick directions, both virtual triggers, all-bit combinations, zero,
and unknown-bit behavior. Public constructors set connected=true and packet=0;
native construction alone copies real connection and PacketNumber. Equality and
hash include connection and packet as well as all four public nested values;
the exact string reports only connection.

Triggers use the XNA Min-then-Max clamp and preserve NaN; thumbsticks use the
XNA square Vector2 Min-then-Max clamp. Their special values, signed zero,
equality, hashes, strings, and value copies are qualified. Capabilities expose
all 26 real copied fields and no public initializer.

## Retained native GamePad evidence

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

The only added native routes are canonical `cna_gamepad_get_state`,
`cna_gamepad_get_state_with_dead_zone`, `cna_gamepad_get_capabilities`, and
`cna_gamepad_set_vibration`. Default state is IndependentAxes. None,
IndependentAxes, and Circular route directly to CNA without double processing.
Player slots, all selected button bits, controller type, and fields map
explicitly. Each operation resolves the current Game generation and validates
the owner thread before native entry.

This HEADLESS/NULL host has no connected controller. Real successful
disconnected state and capability snapshots and `SetVibration=false` are
verified. Positive controller state/capabilities/type/voice/motors and physical
rumble remain `HARDWARE_PENDING`; repeated rumble stress was intentionally not
run. No result is fabricated. See `docs/gamepad-evidence.md`,
`docs/gamepad-native-inventory.md`, and generated GamePad native evidence.

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

The regenerated public-signature dependency graph contains multiple independent
closures. Foundation Milestone 8 selects exactly the standalone managed
`Microsoft.Xna.Framework.Graphics.BufferUsage` flags enum: one CLR type with
three CLR identities and two mapped Swift identities (`value__` excluded), no
missing XNA dependency, `System.Int32` storage, and literal values `None=0` and
`WriteOnly=1`.

This choice is based on the regenerated zero-missing-dependency graph and keeps
the next closure minimal. It does not infer GraphicsDeviceManager orientation,
GameWindow, Mouse, Touch, VertexElement, Content, or runtime graphics support
from the completed milestone.

This is selection only. `BufferUsage` has not been started and must not be
combined with a second type, a buffer implementation, runtime-partial cleanup,
or CNA ABI work.

```text
SELECTED_ONLY=true
STARTED=false
```
