# CNA-Swift continuation handoff

**Foundation Milestone 16 final status:** COMPLETE.

Foundation 16 is `PURE_MANAGED_BATCH_B`: `Input.MouseState`,
`Media.MediaState`, `Media.MediaSourceType` and `Audio.MicrophoneState` — four
entirely missing pure-managed types carrying 21 mapped Swift XNA identities,
all from the two already-pinned assemblies. `Microsoft.Xna.Framework.Media`
gained its namespace marker. Completing them claims no mouse device, cursor,
microphone, capture, media player, media library, or video capability, and
`MouseState` has no producer because `Input.Mouse` is not implemented. Evidence
is in `docs/foundation-16-pure-managed-batch-evidence.md`.

Foundation 15 was `PRESENTATION_PARAMETERS`. It completes exactly one entirely
missing pure-managed XNA type,
`Microsoft.Xna.Framework.Graphics.PresentationParameters`, carrying **13 mapped
Swift XNA identities**, and promotes the pre-existing `System.IntPtr -> Swift
Int` entry to a documented **general** language rule with verifier support and
ten negative controls. No CNA source, C ABI, native binding, renderer, device,
adapter, buffer, texture, sprite-batch, effect, audio-engine, callback,
thread-affinity, or filesystem work is included, and none of the five
runtime-partial types was touched.

Full evidence is in `docs/foundation-15-presentation-parameters-evidence.md`.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=168 PASS
RELEASE_TESTS=168 PASS
MANAGED_TESTS=158 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS
SYMBOL_GRAPH=PASS
API_SELF_TESTS=1606 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1493/1493/0
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=103
TARGET_MEMBERS=1594
TOTAL_DIAGNOSTICS=305
MISSING_TYPE=154
MISSING_MEMBER=131
COMPLETE_TYPES=98
PARTIAL_TYPES=5
MISSING_TYPES=154
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
LANGUAGE_PROJECTION_EXCLUSIONS=115
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=9
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

`MISSING_MEMBER` stays at 131 and `PARTIAL_TYPES` at 5: the four diagnostics
whose subject mentions `PresentationParameters` are all owned by the protected
partial `GraphicsDevice` and predate this milestone.

## General mapping rule formalised

`System.IntPtr -> Swift Int`: the opaque pointer-width signed numeric value of
the CLR IntPtr, `IntPtr.Zero -> 0`. Not a Swift pointer, a dereferenceable
address, a CNA native handle, an SDL window, a `GraphicsDevice`, or proof of
validity. Never counted as `RAW_HANDLE_LEAK`; that exemption covers only the
mapped XNA IntPtr value and never a CNA FFI or native implementation handle.
Ten negative controls, each proved against a synthetic owner and again against
the real `PresentationParameters.DeviceWindowHandle` identity, plus three
fixtures rejecting invented boundary-crossing members. See
`docs/xna-swift-mapping.md`.

## Retained native evidence

Foundation 15 has zero native surface. The full ABI is unchanged and was
re-derived against the retained ABI-0.7.0 artifact:

```text
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
```

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

## Pinned-assembly scope, investigated

The regenerated graph contains 42 missing types whose XNA public-signature
dependencies are complete. Every one of the 257 pinned contract types was
machine-attributed to its declaring assembly this milestone. The result:

```text
118  Microsoft.Xna.Framework.dll          PINNED (hash re-verified)
 99  Microsoft.Xna.Framework.Graphics.dll PINNED (hash re-verified)
 17  Microsoft.Xna.Framework.Game.dll     present, NOT yet registered
  8  Microsoft.Xna.Framework.Input.Touch.dll   present, NOT yet registered
  7  Microsoft.Xna.Framework.Xact.dll     present, NOT yet registered
  3  Microsoft.Xna.Framework.Video.dll    present, NOT yet registered
  3  Microsoft.Xna.Framework.Storage.dll  present, NOT yet registered
```

All seven are the same XNA 4.0.0.0 redistributable build, and the two already
pinned re-hashed to their retained records exactly. Registering the remaining
five as authoritative reference inputs is a separate, deliberate provenance
step and was **not** performed in this milestone; no type outside the two
pinned assemblies was completed.

## Next milestone

The regenerated graph contains **41** missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 17 is **not yet selected**;
the frontier now splits into three groups, and choosing between them is the
next decision.

**A. Blocked on a general BCL language projection that does not exist yet.**
Each of these needs one new, principled, general rule, not a per-type
exception:

- `System.Exception` — eight sealed exception types across Audio, Content,
  Graphics and Storage, each with the same three constructors
  `()`, `(message)`, `(message, inner)`. Swift has no CLR unchecked
  exceptions; the repository already projects failure paths as `throws` and
  carries a `CNAError` support type outside the XNA namespace. Whether an XNA
  exception *type* becomes a Swift `Error`-conforming type, and how its
  `inner` chains, is an open general decision.
- `System.Attribute` — five `ContentSerializer*Attribute` types. Swift
  attributes are not first-class declarable types, so these would have to map
  to ordinary types that carry no attribute semantics.
- `System.EventArgs` — `ResourceCreatedEventArgs` and
  `ResourceDestroyedEventArgs` (reach 50 each). Both are sealed, have no
  public constructor, and derive from `System.EventArgs`, which currently maps
  to the **`CNAEventArgs` struct**. The strict verifier does not measure
  non-XNA bases, so both could be completed today as plain Swift classes with
  internal construction, exactly following the `DisplayMode` precedent — but
  that models the CLR base as absent rather than as a struct/class conflict.
  Making `CNAEventArgs` a class instead would alter an existing public API
  type's kind and value semantics, and `CNAEventArgs` appears in
  `Game.OnExiting`, a member of a protected partial. That is a genuine
  architecture decision and is recorded here rather than resolved silently.
- `System.Collections.ObjectModel.ReadOnlyCollection<T>` —
  `Media.VisualizationData`.
- `System.ComponentModel.TypeConverter` — `Design.MathTypeConverter`
  (reach 12) and its eleven concrete subclasses.

**B. Blocked on runtime capability, not on mapping.**

- `DisplayModeCollection` (reach 53) — its members enumerate `DisplayMode`,
  whose instances exist only through `GraphicsAdapter` mode enumeration. Any
  implementation is permanently empty or fabricates adapter data.
- `EffectAnnotation` (reach 25) — effect runtime semantics are missing.
- `ContentManager` (reach 8) — filesystem plus disposal lifecycle.
- `AudioEmitter` / `AudioListener` — native XACT emitter data and handedness.

**C. Blocked only on pinned-assembly registration.** See below. This is the
largest single unlock and requires no new mapping rule at all.

## Pinned-assembly scope: investigated, not yet extended

Every one of the 257 pinned contract types was machine-attributed to its
declaring assembly. All seven declaring assemblies are present on the
qualification host as one XNA 4.0.0.0 redistributable set, and the two already
pinned re-hashed to their retained records exactly.

```text
118  Microsoft.Xna.Framework.dll               PINNED, hash re-verified
 99  Microsoft.Xna.Framework.Graphics.dll      PINNED, hash re-verified
 17  Microsoft.Xna.Framework.Game.dll          present, NOT registered
  8  Microsoft.Xna.Framework.Input.Touch.dll   present, NOT registered
  7  Microsoft.Xna.Framework.Xact.dll          present, NOT registered
  3  Microsoft.Xna.Framework.Video.dll         present, NOT registered
  3  Microsoft.Xna.Framework.Storage.dll       present, NOT registered
```

Registering the remaining five as authoritative reference inputs would make
their 38 contract types behavior-provable and would unblock, among others,
`IGameComponent`, `IUpdateable`, `IDrawable`, `IGraphicsDeviceManager`,
`GameServiceContainer`, `GameWindow`, `LaunchParameters`, the eight
`Input.Touch` types, and `Audio.AudioStopOptions` — all previously recorded as
"outside the currently pinned assembly set".

This is a deliberate provenance step, not a side effect of a type milestone.
It requires: re-hashing each assembly, recording the hashes in the mapping
document and the reference README under the existing provenance policy, and
machine-comparing each assembly's public metadata against the already-pinned
contract entries it owns before any type from it is completed. **No type
outside the two pinned assemblies has been completed**, and none should be
until that comparison is done and recorded.

```text
SELECTED_ONLY=false
STARTED=false
```
