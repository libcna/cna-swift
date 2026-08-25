# CNA-Swift continuation handoff

**Foundation Milestone 15 final status:** COMPLETE.

Foundation 15 is `PRESENTATION_PARAMETERS`. It completes exactly one entirely
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
DEBUG_TESTS=158 PASS
RELEASE_TESTS=158 PASS
MANAGED_TESTS=148 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE
SYMBOL_GRAPH=PASS
API_SELF_TESTS=1396 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1443/1443/0
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=99
TARGET_MEMBERS=1573
TOTAL_DIAGNOSTICS=309
MISSING_TYPE=158
MISSING_MEMBER=131
COMPLETE_TYPES=94
PARTIAL_TYPES=5
MISSING_TYPES=158
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

Foundation Milestone 16 selects a pure managed batch drawn **only** from the
two already-pinned assemblies:

```text
Microsoft.Xna.Framework.Input.MouseState      struct, 14 identities
Microsoft.Xna.Framework.Media.MediaState      enum,    3
Microsoft.Xna.Framework.Media.MediaSourceType enum,    2
Microsoft.Xna.Framework.Audio.MicrophoneState enum,    2
```

`MouseState` is the sealed sequential value struct Foundation 14 flagged as
pinned-derivable and safe; its only XNA dependency, `ButtonState`, is already
strict-complete. The three enums are plain `Int32` CLR enums with no `[Flags]`
attribute in the pinned binary.

Deliberately not selected, with reasons:

- `DisplayModeCollection` (reach 53) — its members enumerate `DisplayMode`,
  whose instances exist only through `GraphicsAdapter` mode enumeration. Any
  implementation is permanently empty or fabricates adapter data.
- `ResourceCreatedEventArgs` / `ResourceDestroyedEventArgs` (reach 50 each) —
  both derive from `System.EventArgs`, which currently maps to the
  `CNAEventArgs` **struct**. A faithful class hierarchy needs a general
  `System.EventArgs` projection decision; see the blocker note below.
- `EffectAnnotation` (reach 25) — effect runtime semantics are missing.
- `MathTypeConverter` (reach 12) — needs the `System.ComponentModel`
  `TypeConverter` BCL subsystem.
- `ContentManager` (reach 8) — filesystem plus disposal lifecycle.
- Exception types and `ContentSerializer*Attribute` types — both need a
  general CLR-exception and CLR-attribute language projection that does not
  exist yet.
- `VisualizationData` — needs a `System.Collections.ObjectModel.ReadOnlyCollection<T>`
  mapping.

```text
SELECTED_ONLY=false
STARTED=true
```
