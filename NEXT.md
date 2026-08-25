# CNA-Swift continuation handoff

**Foundation Milestone 14 final status:** COMPLETE.

Foundation 14 is `PURE_MANAGED_BATCH_A`: a multi-type autonomous batch, not a
single-type closure. It completes **25 entirely missing pure-managed XNA types**
carrying **144 mapped Swift XNA identities**, and stops on batch limit **A —
25 newly complete types**. The 150-identity limit B was not reached. No CNA
source, C ABI, native binding, renderer, device, adapter, buffer, texture,
sprite-batch, effect, audio-engine, callback, thread-affinity, or filesystem
work is included, and none of the five runtime-partial types was touched.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=147 PASS
RELEASE_TESTS=147 PASS
MANAGED_TESTS=137 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=1259 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1348/1348/0
GAMEPAD_NATIVE_FAILURES=0
SWIFT_ASAN=PASS_PURE_CORPUS_DETECT_LEAKS_DISABLED
SWIFT_TSAN=PASS_MANAGED_CORPUS
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
TARGET_TYPES=98
TARGET_MEMBERS=1560
TOTAL_DIAGNOSTICS=310
MISSING_TYPE=159
MISSING_MEMBER=131
COMPLETE_TYPES=93
PARTIAL_TYPES=5
MISSING_TYPES=159
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
LANGUAGE_PROJECTION_EXCLUSIONS=114
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=8
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

`NAMESPACE_MARKERS` and therefore `LANGUAGE_PROJECTION_EXCLUSIONS` each rose by
one because `SoundState` and `AudioChannels` are the first implemented types in
`Microsoft.Xna.Framework.Audio`. A namespace marker is a formally measured
language projection, not an allowlist entry, and adds no XNA identity. Every
other projection counter carried over unchanged.

All 151 non-`MISSING_TYPE` diagnostics remain owned exclusively by the five
partials, with a per-type split byte-identical to Foundation 13: `Game` 22 (21
missing members), `GraphicsDeviceManager` 29 (27), `GraphicsDevice` 57 (54),
`SpriteBatch` 27 (16), `Texture2D` 16 (13). The 25 batch types carry zero
diagnostics between them.

## Completed batch

```text
 1 Graphics.GraphicsProfile        enum        2 identities
 2 Graphics.PresentInterval        enum        4
 3 Graphics.VertexElementFormat    enum       12
 4 Graphics.VertexElementUsage     enum       13
 5 Graphics.CompareFunction        enum        8
 6 Graphics.CubeMapFace            enum        6
 7 Graphics.IndexElementSize       enum        2
 8 Graphics.Blend                  enum       13
 9 Graphics.BlendFunction          enum        5
10 Graphics.ColorWriteChannels     OptionSet   6
11 Graphics.CullMode               enum        3
12 Graphics.StencilOperation       enum        8
13 Graphics.TextureAddressMode     enum        3
14 Graphics.TextureFilter          enum        9
15 Graphics.ClearOptions           OptionSet   3
16 Graphics.GraphicsDeviceStatus   enum        3
17 Graphics.PrimitiveType          enum        4
18 Graphics.EffectParameterClass   enum        5
19 Graphics.EffectParameterType    enum       10
20 Graphics.SetDataOptions         OptionSet   3
21 Graphics.VertexElement          struct     10
22 Graphics.IEffectFog             protocol    4
23 Graphics.IEffectMatrices        protocol    3
24 Audio.SoundState                enum        3
25 Audio.AudioChannels             enum        2
                                   TOTAL     144
```

`[Flags]` is an observed absence in the pinned binaries for the 19 ordinary
enums and an observed presence for exactly `ColorWriteChannels`,
`ClearOptions`, and `SetDataOptions`. Full literal tables, IL transcription,
skipped-candidate reasons, verifier fixture coverage, and negative controls are
in `docs/foundation-14-pure-managed-batch-evidence.md`.

## Tooling corrections made this milestone

`tools/api_compat/dependency_graph.py` keyed its graph nodes by raw CLR type
names while type status came from the strict report, which uses mapped names. A
CLR nested name (`A+B`) or generic-collision name never matched a key, so the
type reported zero dependencies and was ranked as trivially dependency-complete.
Six candidates were advertised that way — `ContentTypeReaderOfT` and the
`ModelBoneCollection`, `ModelEffectCollection`, `ModelMeshCollection`,
`ModelMeshPartCollection` and `TouchCollection` enumerators — and every one of
them has an unmapped dependency. Nodes are now mapped exactly as the verifier
maps them. Against the unchanged Foundation-13 report this moves
`DEPENDENCY_COMPLETE_MISSING_TYPES` from 71 to 65 and does not change the
Foundation-13 selection.

This is **not** the historical 71/72 `GameComponent` nuance, which concerns
whether declared direct interfaces count as dependencies. That question remains
closed: `IGameComponent` and `IUpdateable` are still missing, so `GameComponent`
is still correctly dependency-incomplete.

`tools/behavior/run.py` had a `Color` behavior-group pattern that silently
absorbed `ColorWriteChannels`. The pattern is now `Color(?!WriteChannels)` and
the `Color` group stays at 13.

## Retained native evidence

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b (pinned; not
    re-derivable from the local artifact)
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

Foundation 14 has zero native surface, so every count above is byte-identical
to Foundation 13 and the regenerated native ABI report is unchanged on disk.
`CNA_SOURCE_REVISION` remains pinned-but-not-re-derivable: the retained
ABI-0.7.0 artifact still carries no provenance marker. What is verified is the
contract — encoded ABI 1792 (0.7.0), zero missing header symbols, zero missing
library symbols, zero ABI mismatches.

The retained GamePad and Keyboard results are unchanged. This HEADLESS/NULL
host has no attached controller and no audio device, so positive controller
observations and physical rumble remain `HARDWARE_PENDING`; no result is
fabricated. The maintained template remains at commit
`86687f62c3a13ee2b59798f338fc083f7399f447` and passes debug 60 / release 600
with exact callback counts, viewport 800x480, and texture 128x128. Exact source
archive identity and isolated-consumer results are final handoff artifacts, not
self-referential source content.

## Reference provenance

Public shape comes from the pinned contract SHA-256
`7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`. All 25
completed types were independently re-derived this milestone from the pinned
assemblies and machine-compared against that contract:
`Microsoft.Xna.Framework.Graphics.dll` SHA-256
`560080fc39021c611ca9d076dcebed312faf6d7d1413c2dc523683ea635e9f55` for 23 of
them, and `Microsoft.Xna.Framework.dll` SHA-256
`38e7093f52d7474bbc6256906519781a1210d7da50a1c667b52716fcf49ca130` for
`Audio.SoundState` and `Audio.AudioChannels`. Both are mixed-mode C++/CLI
images whose metadata is readable on the Linux qualification host. Candidates
declared outside these two assemblies were deferred rather than completed on
weaker provenance. No Microsoft binary or extracted proprietary source is in
the repository or the archive.

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Exactly one next milestone

The regenerated graph contains 43 missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 15 selects exactly
`Microsoft.Xna.Framework.Graphics.PresentationParameters`.

The top-ranked candidate is `DisplayModeCollection` at transitive missing
reverse reach 53, but it is not actionable: its only members enumerate
`DisplayMode`, whose instances exist solely through `GraphicsAdapter` mode
enumeration, so any implementation is permanently empty or fabricates adapter
data. `PresentationParameters` is next at reach 52 and is actionable. All six
of its XNA dependencies — `DisplayOrientation`, `DepthFormat`, `PresentInterval`,
`RenderTargetUsage`, `SurfaceFormat`, `Rectangle` — are strict-complete, four of
them only becoming so across Foundation 11–14. It has one direct missing reverse
consumer, `GraphicsDeviceInformation`, and one direct partial reverse consumer,
`GraphicsDevice`, which must remain an untouched partial.

It is deliberately a harder milestone than any Foundation-14 type. The pinned IL
is fully readable managed code: a nested `assembly` `Settings` value struct
holds every field, the property accessors are plain loads and stores, `Clone()`
news a fresh instance and copies `settings` wholesale, `IsFullScreen` is stored
as an `int32` 0/1, the public constructor sets `IsFullScreen` and nothing else,
and `Bounds` is `Rectangle(0, 0, BackBufferWidth, BackBufferHeight)`. The real
decision it forces is `DeviceWindowHandle`, a `native int` that maps to Swift
`Int` under the existing `System.IntPtr` rule — whether a managed descriptor may
expose a platform window handle at all, and where the descriptor stops and
device creation begins.

It must not be combined with `GraphicsDevice` member expansion, device creation,
reset or loss handling, `GraphicsAdapter`, `GraphicsDeviceInformation`,
swap-chain, MSAA, or renderer work.

```text
SELECTED_ONLY=true
STARTED=false
```
