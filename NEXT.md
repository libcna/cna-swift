# CNA-Swift continuation handoff

**Foundation Milestone 17 final status:** COMPLETE.

Foundation 17 is `REFERENCE_ASSEMBLY_REGISTRATION` plus `PURE_MANAGED_BATCH_C`.
It registers five additional Microsoft XNA assemblies as authoritative
reference inputs and consumes the first seven types that unblocks, carrying 26
mapped Swift XNA identities. Evidence is in
`docs/foundation-17-reference-assembly-registration-evidence.md`.

Foundation 16 was `PURE_MANAGED_BATCH_B` (`MouseState`, `MediaState`,
`MediaSourceType`, `MicrophoneState`); Foundation 15 was
`PRESENTATION_PARAMETERS` and the general `System.IntPtr -> Swift Int` rule.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=176 PASS
RELEASE_TESTS=176 PASS
MANAGED_TESTS=166 PASS_WITHOUT_CNA_NATIVE_LIBRARY
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS
SYMBOL_GRAPH=PASS
API_SELF_TESTS=1822 PASS
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS
AUDIT_SELF_TESTS=60 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1523/1523/0
```

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=110
TARGET_MEMBERS=1620
TOTAL_DIAGNOSTICS=298
MISSING_TYPE=147
MISSING_MEMBER=131
COMPLETE_TYPES=105
PARTIAL_TYPES=5
MISSING_TYPES=147
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
LANGUAGE_PROJECTION_EXCLUSIONS=116
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=10
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

All 151 non-`MISSING_TYPE` diagnostics remain owned exclusively by the five
runtime partials, which are untouched.

## Registered reference assemblies

```text
120 types  Microsoft.Xna.Framework.dll           38e7093f52d7474bbc6256906519781a1210d7da50a1c667b52716fcf49ca130
 99 types  Microsoft.Xna.Framework.Graphics.dll  560080fc39021c611ca9d076dcebed312faf6d7d1413c2dc523683ea635e9f55
 17 types  Microsoft.Xna.Framework.Game.dll      b5dffdd8125abef2a4507ba4e1d2f11062143f0a63d48fe4f298b95ad746a1f0
  8 types  Microsoft.Xna.Framework.Input.Touch.dll b0585224c18022c3661057ae79544644c10f33f1dc529678364f3d6b25151c25
  7 types  Microsoft.Xna.Framework.Xact.dll      a14d5364dca7cf49fb90639e87ba04d52b59a700dc9198efa5707ce8eae28f0a
  3 types  Microsoft.Xna.Framework.Video.dll     17538b1ca9d48a993e2cd88c96b436df08e7abb4aec5d4758eb21feb580d6e06
  3 types  Microsoft.Xna.Framework.Storage.dll   798f678e9ae3d9afc3bed66c30123bc9634fb923b6d200188344b618e608cbb8
```

Together these seven files reproduce the retained contract's 257 types and
2,964 members exactly. **No XNA reference input is missing.** The pinned-scope
blocker recorded by Foundation 14 and 16 is closed.

## Retained native evidence

Foundation 17 has zero native surface. The full ABI is unchanged:

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

## Next milestone

The regenerated graph contains **39** missing types whose XNA public-signature
dependencies are complete. Foundation Milestone 18 is **not yet selected**.
With the pinned-assembly blocker closed, every remaining frontier is now a
**general BCL language-mapping decision** or a **runtime capability**, not a
provenance gap.

**A. General BCL language projections that do not exist yet.** Each needs one
principled general rule, not a per-type exception. In rough value order:

1. **`System.EventHandler<T>` / CLR events.** Unblocks `IUpdateable`,
   `IDrawable` and, behind them, `GameComponent` and
   `DrawableGameComponent`. `EVENT_MAPPING_MISMATCH` is a measured category
   that has never been exercised: all 49 contract events live in missing or
   partial types. This is the single highest-value general rule remaining.
2. **`System.EventArgs`.** `ResourceCreatedEventArgs` and
   `ResourceDestroyedEventArgs` (reach 50 each),
   `GameComponentCollectionEventArgs`, `PreparingDeviceSettingsEventArgs`.
   Both resource types are sealed, have no public constructor, and derive from
   `System.EventArgs`, which currently maps to the **`CNAEventArgs` struct**.
   The strict verifier does not measure non-XNA bases, so they could be
   completed today as plain Swift classes with internal construction, exactly
   following the `DisplayMode` precedent — but that models the CLR base as
   absent rather than as a struct/class conflict. Making `CNAEventArgs` a class
   would change an existing public API type's kind and value semantics, and it
   appears in `Game.OnExiting`, a member of a protected partial. **This is a
   genuine architecture decision and is deliberately left open.**
3. **`System.Exception`.** Eight sealed exception types across Audio, Content,
   Graphics and Storage, each with `()`, `(message)`, `(message, inner)`. Swift
   has no CLR unchecked exceptions; the binding projects failure paths as
   `throws` and carries `CNAError` outside the XNA namespace. Whether an XNA
   exception *type* becomes a Swift `Error`-conforming type, and how `inner`
   chains, is open.
4. **`System.String.GetHashCode`.** Blocks `Audio.RendererDetail`. The CLR
   function is explicitly unspecified and implementation-defined, so it is not
   derivable from IL. Either the type stays blocked or the project decides that
   an unspecified BCL hash may be projected onto a documented substitute — a
   fidelity decision, not a mapping mechanic.
5. **`System.Attribute`** — five `ContentSerializer*Attribute` types.
6. **`System.Type` / `System.IServiceProvider`** — `GameServiceContainer`.
7. **`System.Collections.Generic.Dictionary<K,V>` as a base** —
   `LaunchParameters`.
8. **`System.Collections.ObjectModel.ReadOnlyCollection<T>`** —
   `Media.VisualizationData`.
9. **`System.ComponentModel.TypeConverter`** — `Design.MathTypeConverter`
   (reach 12) and its eleven concrete subclasses.

**B. Blocked on runtime capability, not on mapping.**

- `DisplayModeCollection` (reach 53) — enumerates `DisplayMode`, whose
  instances exist only through `GraphicsAdapter` mode enumeration. Any
  implementation is permanently empty or fabricates adapter data.
- `EffectAnnotation` (reach 25) — effect runtime semantics are missing.
- `ContentManager` (reach 8) — filesystem plus disposal lifecycle.
- `AudioEmitter` / `AudioListener` — native XACT emitter data and handedness.
- `Input.Touch.TouchLocation` (reach 3), `TouchPanel`, `VideoPlayer`,
  `StorageDevice`, `AudioEngine` — real hardware or platform capability.

The recommended next frontier is **the general CLR event/delegate projection**,
because it is the only remaining general rule that unblocks a whole cluster
(`IUpdateable`, `IDrawable`, `GameComponent`, `DrawableGameComponent`) and it
exercises a measured diagnostic category that has never been exercised. If two
materially different event mappings prove equally plausible and repository
policy does not decide between them, that is a legitimate architecture stopping
condition.

```text
SELECTED_ONLY=false
STARTED=false
```
