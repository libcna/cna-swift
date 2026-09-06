# CNA-Swift normative plan and status

**Current state.** The native boundary is CNA C ABI **major 0, minor 21 or
later**, qualified against `0.21.0`. Foundation Milestones 1 through 76 are
complete: the native migration off the historical `0.7.0` boundary, the
projected CLR/XNA exception payloads, the graphics resource hierarchy with
`RenderTarget2D`, `Game`'s timing/host members and four host events, the
`IGraphicsDeviceService` producer with `DrawableGameComponent`, the four
graphics state objects, `System.ObjectDisposedException` as the seventh
admitted BCL exception authority, `VertexDeclaration` with the validator behind
it, `IVertexType` with the four vertex structs, the graphics device's
own state members over real CNA routes, its viewport writer, scissor
rectangle and status, and — since Foundation 48 — the whole of what reading the
pinned IL member by member has turned up: `Clear`'s depth buffer, the viewport
and scissor validation, the message-coverage gate itself, the manager's
preferences and its disposal, `SpriteBatch`'s five `Draw` overloads and its
state-taking `Begin`s, `Texture2D`'s constructors, the method-generic mapping
the verifier could not previously express, `SetData`/`GetData`, the vertex and
index buffer family with its dynamic pair, the extracted `ProfileCapabilities`
table and the nine messages that were waiting on it, the vertex- and
index-buffer binders, `TextureCube` with `Texture3D`, and the render-target
family closed with `RenderTargetCube`, `RenderTargetBinding` and the device's
three remaining render-target members, `TextureCollection` with the three
bound-state checks that had nothing to check until it existed, the `Effect`
core's nine types, and the draw family the whole graphics chain was leading to.

This file states what is true **now**, and a gate keeps that literal:
`tools/status_gate/verify.py` derives the current Foundation from the highest
`docs/foundation-<N>-*-evidence.md` on disk and every policed count from the
generated reports, then refuses any normative sentence here, in `README.md` or
in `NEXT.md` that disagrees. The milestone-by-milestone progression lives in
`NEXT.md` and in the per-milestone `docs/foundation-*-evidence.md` files, which
are not summarised away here; where this document once carried a milestone's own
prose, that milestone's evidence file carries it still.

## Normative rules

1. **XNA authority.** Pinned Microsoft XNA 4.0 Windows runtime metadata is the
   public shape authority, and the hash-matched assembly IL is the behaviour
   authority. An assembly earns behaviour authority only by **registration**:
   its SHA-256 is recorded and `tools/api_compat/pinned_assembly_audit.py`
   machine-compares its public metadata against every retained contract entry it
   declares. The audit is calibrated on the assemblies whose provenance predates
   it and carries its own mutation self-tests, so it cannot pass vacuously.
   Seven assemblies are registered and together reproduce the contract's 257
   types and 2,964 members exactly. FNA and MonoGame are engineering
   comparators only. **CNA is never XNA behaviour authority**: a value observed
   from the native runtime is native evidence and is recorded separately.
2. **A user-visible XNA message is read, not transcribed.** XNA loads a
   resource key and the runtime resolves it against the assembly's own string
   table, so every reproduced message is read out of the registered binary,
   pinned in `tools/api_compat/reference/xna40-selected-resource-strings.json`,
   and compared against the Swift source by the verifier. Foundation 49 made
   that literally true: five messages were byte-identical to the assembly's own
   and yet unpinned, so nothing was comparing them. All 29 are pinned now.
3. **A complete type does not imply runtime capability.** Profile selection,
   presentation, primitives, vertex and index buffers, cube textures, effects,
   content loading, windows, and audio playback all remain unclaimed. Render
   targets are created, bound and consumed natively. The four state objects are
   applied to a device as of Foundation 45, and device status, the viewport,
   the scissor rectangle and all three `Clear` overloads followed in
   Foundations 47 and 48. Two measured divergences shaped how that was done and
   are recorded rather than worked around: CNA's graphics-device handle is a
   per-callback capability token and not a stable identity, so device-owned
   managed state is anchored to the game; and `BlendFunction.Min`/`.Max` are
   numbered the other way round in CNA than in XNA, so every state enum crosses
   the boundary through an explicit map. Both are stated with the rest of that
   research in
   `docs/frontier-research-graphics-device-state-and-vertex-declaration.md`.

   Foundation 48 is the reminder that this cuts both ways: `Clear(Color)` had
   been *implemented* since the earliest graphics work and was **wrong**,
   clearing colour where XNA also clears depth, on the only device
   configuration a projected game ever gets (`DepthFormat.Depth24`, measured).
   A member being present, tested and green is not evidence that it agrees with
   the pinned IL; only reading the IL is. See
   `docs/foundation-48-clear-evidence.md`.

   Reading every implemented `GraphicsDevice` member's IL by size, which is how
   that was found, immediately found two more: `set_Viewport` and
   `set_ScissorRectangle` were projected with none of their validation
   (Foundation 49). Generalising the reading into a gate found a fourth,
   `DrawableGameComponent.GraphicsDevice` raising its sibling's message, and
   `SpriteBatch`'s whole begin/end rule (Foundation 50).

   Four defects in three milestones, none found by a failing test, is why
   `tools/api_compat/message_coverage.py` exists: for every implemented member,
   every message its pinned IL can raise is either reproduced or recorded with
   a reason and a kind. A member that disagrees with XNA is worse than one that
   is honestly absent, and the gate is what keeps the fifth one from being
   found by a user.
4. **A CLR field's writability is metadata, not convention.** `literal` and
   `initonly` are two different `FieldAttributes`, and neither is assignable, so
   both project to a Swift `let`. `readonly` is recorded on all 557 contract
   fields, proven against the registered binaries by the pinned-assembly audit,
   and independently cross-checked with a second disassembler. See
   `docs/foundation-41-graphics-state-evidence.md`.
5. **Public strict names** use `Microsoft.Xna.Framework...` and exact XNA
   PascalCase. Formal Swift projections are measured; manual diagnostic
   allowlisting is forbidden, and `ALLOWLIST_ENTRIES` is 0.
6. **Mapping rules are measured, never invented for convenience.** The full set
   is in `docs/xna-swift-mapping.md` and `tools/api_compat/mapping-rules.json`.
   The load-bearing ones: a non-flags CLR enum maps to a Swift `enum` with the
   CLR underlying raw type and one explicitly valued case per literal; a
   `[Flags]` enum maps to an `OptionSet`, with `[Flags]` read out of the pinned
   binary rather than assumed; a CLR interface maps to a Swift `protocol` with
   no invented conformance; a CLR class maps to a Swift class, and CLR
   derivability is not strengthened casually; `System.Type` maps to the Swift
   metatype; `Dictionary<K,V>` maps to a reference class with the CLR's own
   storage algorithm; a CLR event maps to the `CNAEvent` architecture;
   `System.IntPtr` maps to Swift `Int` as a documented general language rule
   whose expected projection is never `RAW_HANDLE_LEAK` — an exemption that
   covers the mapped XNA IntPtr value and never a CNA FFI or native handle.
7. **The native boundary.** CNA-Swift admits the ABI window CNA itself
   publishes for a consumer — reject a different major, require a minimum minor
   — which is major `0` exactly and minor `21` or later, qualified against
   `0.21.0`. Native selection is an absolute `CNA_NATIVE_LIBRARY` override or
   the installed soname, never a developer-tree fallback. Every bound symbol
   must resolve by name before the runtime starts. See `docs/native-abi.md` and
   `docs/native-abi-migration-evidence.md`.
8. **Two error channels stay separate, and the split is by cause.** `CNAError`
   is the CNA runtime's own failure channel. Projected CLR/XNA failures are the
   `CNAException` class hierarchy, which conforms to `Error`. `catch is
   CNAException` must not swallow a native CNA runtime failure, and the two are
   never merged for convenience. The line is what *caused* the failure, not
   which layer noticed it: a consumer using a resource it disposed is a CLR
   failure and raises `CNAObjectDisposedException`, while a native object whose
   C lifetime ended has no XNA counterpart and stays on `CNAError`. The same
   Swift enum case can serve both, and four `CNAError.disposedObject` sites do.
9. **Native ownership is explicit.** Every native handle has a recorded
   ownership — `OWNED`, `BORROWED`, `PARENT_OWNED`, `PROCESS_GLOBAL` or
   `MANAGED_VALUE` — and disposal is deterministic. A Swift `deinit` is a
   backstop, never the only correctness mechanism, and no callback may outlive
   the rooted Swift state.
10. **Every gate must be shown to fail.** A verifier, audit or runtime gate is
    evidence only once a planted, realistic defect has been proven to break it.
    `tools/native_abi/mutations.py`, `tools/projection_mutations/run.py`, the
    API verifier's self-tests and graph fixtures, the pinned-assembly audit's
    mutations and the BCL authority's negative controls are all of this kind.
11. **A normative status claim is derived, never remembered.** The current
    Foundation is the highest `docs/foundation-<N>-*-evidence.md` on disk and
    every policed count comes out of a generated report;
    `tools/status_gate/verify.py` refuses any sentence in this file, `README.md`
    or `NEXT.md` that disagrees, and additionally regenerates the strict report,
    the missing-type inventory, the dependency graph and the native ABI report
    to prove each committed copy is still what a live run produces. Historical
    prose is exempt only inside an explicit `<!-- status-gate:historical -->`
    region and is never deleted to make a claim true. Both failures this rule
    exists for had already happened: see
    `docs/foundation-58-normative-status-gate-evidence.md`.

## Measurement status

Reproduced live on CNA 0.21.0 at the current HEAD.

```text
REFERENCE_TYPES=257            REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257       EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=219               TARGET_MEMBERS=2645
COMPLETE_TYPES=213             PARTIAL_TYPES=6      MISSING_TYPE=38
MISSING_MEMBER=10              TOTAL_DIAGNOSTICS=51
ALLOWLIST_ENTRIES=0            UNMEASURED_STRUCTURAL_CATEGORY=0
NONDERIVABLE_UNSEALED_CLASSES=0    PENDING_BCL_BASE_TYPES=4
XNA_RESOURCE_STRING_PROJECTIONS=79 API_COMPAT_SELF_TESTS=2464
```

**Every remaining diagnostic is an absence.** Three categories are non-zero —
`MISSING_TYPE=38`, `MISSING_MEMBER=10`, and `OVERLOAD_MAPPING_MISMATCH=3`,
whose every entry reads *required overload is absent*: `SpriteBatch.Begin` (2,
both taking an `Effect`) and the two serialization constructors of
`ContentLoadException` and `StorageDeviceNotConnectedException`.
`GraphicsDevice.SetRenderTarget`'s cube overload left this list in Foundation
65. `GraphicsDeviceManager.Dispose` left this
list in Foundation 52, all five `SpriteBatch.Draw` entries in Foundation 53, two
of the four `SpriteBatch.Begin` entries in Foundation 54, and
`Texture2D.FromStream`'s resizing overload in Foundation 59.

Every category that would mean the projection **disagrees** with XNA is 0:
`TYPE_KIND_MISMATCH`, `BASE_MAPPING_MISMATCH`, `INTERFACE_MAPPING_MISMATCH`,
`FIELD_MAPPING_MISMATCH`, `PROPERTY_MAPPING_MISMATCH`,
`METHOD_SIGNATURE_MAPPING_MISMATCH`, `PARAMETER_MAPPING_MISMATCH`,
`RETURN_MAPPING_MISMATCH`, `GENERIC_MAPPING_MISMATCH`, `ENUM_VALUE_MISMATCH`,
`FLAGS_MAPPING_MISMATCH`, `EVENT_MAPPING_MISMATCH`, `OPERATOR_MAPPING_MISMATCH`,
`REF_OUT_MAPPING_MISMATCH`, `LANGUAGE_MAPPING_MISMATCH`,
`INHERITANCE_MAPPING_MISMATCH`, `UNEXPECTED_TYPE`, `UNEXPECTED_MEMBER`,
`UNMEASURED_STRUCTURAL_CATEGORY`, `INTERNAL_TYPE_LEAK`, `RAW_HANDLE_LEAK` and
`PUBLIC_NATIVE_FFI_LEAK`. Wherever this binding has projected an XNA member it
agrees with the pinned metadata; what remains is what has not been written.

Native boundary:

```text
BOUND_FUNCTIONS=612  ROUTE_PAIRINGS=612  PROTOTYPE_TYPE_POSITIONS=2052
CANONICAL_DECLARATION_CHECKS=2052  C_SWIFT_MEASUREMENTS=2052
LAYOUTS=64  LAYOUT_FIELDS=494  CALLBACKS=8  CONSTANTS=228  SCALAR_FACTS=3
MISSING_HEADER_SYMBOLS=0  MISSING_LIBRARY_SYMBOLS=0  ABI_MISMATCHES=0
NATIVE_ABI_MUTATIONS=14  NATIVE_ABI_MUTATIONS_CAUGHT=14
NATIVE_ABI_MUTATION_SURVIVORS=0
PROJECTION_MUTATIONS=375  PROJECTION_MUTATIONS_LAST_FULL_RUN=137
PROJECTION_MUTATIONS_CAUGHT=135
WITHDRAWN_IN_SOURCE=26  REPLACED_NO_OPS_IN_SOURCE=2
```

The projection-mutation count is what the harness holds; `CAUGHT` is what a
**full run** last proved. The two differ while a milestone is in flight, and the
difference is stated rather than rounded up: the last full run covered 137
mutations and caught 135, the two survivors were no-op mutations that measured
nothing and were replaced with observable ones, and every mutation added since —
the two replacements and Foundation 61's six — was planted individually and
caught. A full run over all 143 is repeated before the final handoff, and only
then does `CAUGHT` equal the count.

The projection-mutation harness refuses to run without a selected
`CNA_NATIVE_LIBRARY`: sixteen of its mutations are caught only by suites that
start a CNA runtime, and those suites *skip* rather than fail when no library
is selected, which would report a coverage loss as sixteen projection defects.

The seven registered reference assemblies reproduce 257 contract types and 2,964
contract members exactly; calibration and the audit's mutation self-tests pass
(`AUDIT_SELF_TESTS=80`, `RESOURCE_STRINGS_REPRODUCED=79`). The BCL authority
carries `BCL_SENTINEL_CHECKS=585`, `BCL_MUTATION_SELF_TESTS=497`,
`BCL_CROSS_CHECKS=197` against a second disassembler, and four negative
controls that are still refused. The four are not the same four binaries as in
earlier sessions -- this machine's Mono packages were upgraded since, and none
of the previously recorded control digests exists on disk any more, so the set
was rebuilt from what is here now. One of the four is the strongest control the
gate has had: a **genuine Microsoft** `mscorlib.dll` from another .NET 4.0
install, refused by 2 of 21 checks rather than by 12 to 16. A control that only
just fails is worth more than three that fail obviously.
Two BCL assemblies are admitted, 39 types and 487 members between them.
`mscorlib` `5634668d…acc63` supplies 34 types and 389 members across seven
raised exception families and thirteen support types. `System.dll`
`c3182e40…` was admitted at Foundation 100 for the five-type
`System.ComponentModel` closure the thirteen `Microsoft.Xna.Framework.Design`
converters are built from — `TypeConverter`, `ExpandableObjectConverter`,
`ITypeDescriptorContext`, `PropertyDescriptor` and
`PropertyDescriptorCollection`, 98 members — together with
`Globalization.CultureInfo` and `Collections.IDictionary` from mscorlib, which
those signatures reach for. The converters themselves are design-time IDE
types unreachable from a running game — and the admitted authority then showed
they are not projectable at all without a disagreement: `MathTypeConverter`
advertises exactly one conversion target of its own,
`ComponentModel.Design.Serialization.InstanceDescriptor`, which the base type
also accepts as its only source. That type is a reflected `ConstructorInfo`
plus an argument list, for a design-time source emitter. Swift has neither.
`NEXT.md` records the measurement; the choice between projecting a reflection
surface and answering `false` where XNA answers `true` is the project owner's,
because the second trades away "nothing implemented disagrees".

The identity work found a defect worth recording: the audit read an assembly's
own name with a regex that matched the FIRST `.assembly` line, which in any
assembly that references another is `.assembly extern mscorlib`. It was right
for `mscorlib` — which references nothing — and wrong for everything else. A
negative lookahead fixed it. Admitting a second assembly is what exposed it.

## Platform and release policy

Linux x86-64 with Swift 6.0.3 and an external CNA C ABI 0.21.0 HEADLESS library
(SDL3 audio backend, `CNA_DEVICES=OFF`, `CNA_CNAEXT=OFF`) is the qualified
runtime. HEADLESS has no visible window and this host has no attached
controller, so no visible output and no positive controller behaviour is
claimed. Apple platforms, Windows, and Web/Wasm remain unqualified.

## The frontier

`docs/frontier-research-graphics-device-state-and-vertex-declaration.md` records
what has been measured about the next two frontiers and not implemented.
`docs/generated/dependency-graph.json` ranks the 17 dependency-complete missing
types; the widest reach after Foundation 45 is `GraphicsAdapter` (35), then
`TextureCollection` (32), `EffectAnnotation` (25), `MathTypeConverter` (12) and
`ContentManager` (6). The rest are audio and media types of reach 3 or less.

`TextureCollection` is the natural successor to Foundation 45 and is a larger
job than `SamplerStateCollection` was. Its `get_Item` queries the live device
for the bound texture rather than reading a managed array, and its `set_Item`
accepts null. Two facts about it were read out of the IL and the CNA headers
rather than assumed:

* **The identity map is not an invention.** `Texture2D.GetManagedObject` calls
  `pDevice.Resources.GetCachedObject(pInterface)` — XNA keeps its own
  native-pointer-to-managed-object cache in `DeviceResourceManager`, the same
  internal type `GraphicsResource.set_Name` already routes through. Reproducing
  a handle-keyed equivalent is faithful, not an addition, and it would be
  complete by construction here because `set_Item` is the only way a texture
  becomes bound.
* **CNA cannot say which kind a bound handle is.** `CNA_TextureSlotInfo` carries
  `bound` and a raw `CNA_Handle` and no discriminator, where XNA's getter
  QueryInterfaces the COM pointer against `IID_IDirect3DTexture9`,
  `IID_IDirect3DCubeTexture9` and `IID_IDirect3DVolumeTexture9` to choose
  between `Texture2D`, `TextureCube` and `Texture3D`. The latter two are not
  projected, so a getter written today could serve only one of three branches,
  and reporting a `Texture2D` for a bound cube map would be worse than not
  answering.

The remaining member diagnostics belong to `GraphicsDevice` (44),
`GraphicsDeviceManager` (21), `SpriteBatch` (16), `Texture2D` (12) and `Game`
(2), and every one of them waits on an XNA type that is not yet projected.

Completion of a milestone requires debug and release builds and tests,
warnings-as-errors including tests, Symbol Graph and its self-tests, the
verifier's self-tests, strict and leak-only runs, pure XNA and BCL behaviour,
the pinned assembly audit, the BCL authority audit, the native ABI verifier and
its mutation controls, GamePad and Keyboard regression, native stress, Swift
ASan and TSan, an unchanged template at 60 and 600 frames, a deterministic exact
source archive, the isolated consumer and its rejected negative consumers,
`git diff --check`, and one coherent commit. Publication is a separate explicit
boundary and is never crossed without instruction.
