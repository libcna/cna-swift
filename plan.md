# CNA-Swift normative plan and status

**Current state.** The native boundary is CNA C ABI **major 0, minor 21 or
later**, qualified against `0.21.0`. Foundation Milestones 1 through 43 are
complete: the native migration off the historical `0.7.0` boundary, the
projected CLR/XNA exception payloads, the graphics resource hierarchy with
`RenderTarget2D`, `Game`'s timing/host members and four host events, the
`IGraphicsDeviceService` producer with `DrawableGameComponent`, the four
graphics state objects, `System.ObjectDisposedException` as the seventh
admitted BCL exception authority, and `VertexDeclaration` with the validator
behind it.

This file states what is true **now**. The milestone-by-milestone progression
lives in `NEXT.md` and in the per-milestone `docs/foundation-*-evidence.md`
files, which are not summarised away here; where this document once carried a
milestone's own prose, that milestone's evidence file carries it still.

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
   and compared against the Swift source by the verifier.
3. **A complete type does not imply runtime capability.** Profile selection,
   presentation, device status, primitives, clear paths, vertex and index
   buffers, cube textures, effects, content loading, windows, and audio
   playback all remain unclaimed. Render targets are now created, bound and
   consumed natively. The four state objects are complete managed types whose
   values have never been **applied to a device**: no
   `GraphicsDevice.BlendState` or sampler-collection route is bound yet, so
   `isBound` is reachable only from inside the module. Two measured
   divergences stand in the way of binding them and are recorded rather than
   worked around: CNA's graphics-device handle is a per-callback capability
   token and not a stable identity, so device-owned managed state must be
   anchored to the game; and `BlendFunction.Min`/`.Max` are numbered the other
   way round in CNA than in XNA, so every state enum must cross the boundary
   through an explicit map. Both are measured, and both are stated with the
   rest of that research in
   `docs/frontier-research-graphics-device-state-and-vertex-declaration.md`.
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

## Measurement status

Reproduced live on CNA 0.21.0 at the current HEAD.

```text
REFERENCE_TYPES=257            REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257       EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=151               TARGET_MEMBERS=1890
COMPLETE_TYPES=144             PARTIAL_TYPES=7      MISSING_TYPE=106
MISSING_MEMBER=106             TOTAL_DIAGNOSTICS=229
ALLOWLIST_ENTRIES=0            UNMEASURED_STRUCTURAL_CATEGORY=0
NONDERIVABLE_UNSEALED_CLASSES=0    PENDING_BCL_BASE_TYPES=4
XNA_RESOURCE_STRING_PROJECTIONS=20 API_COMPAT_SELF_TESTS=2420
```

Mismatch categories that are not zero, each a recorded decision rather than an
oversight: `PROPERTY_MAPPING_MISMATCH=1` (`GraphicsDevice.SetViewport`) and
`OVERLOAD_MAPPING_MISMATCH=16` (the `SpriteBatch.Begin` and
`GraphicsDeviceManager.Dispose` overloads that wait on types not yet
projected). Every other mismatch and leak category is 0, including
`UNEXPECTED_TYPE`, `BASE_MAPPING_MISMATCH`, `FIELD_MAPPING_MISMATCH`,
`INTERFACE_MAPPING_MISMATCH`, `INHERITANCE_MAPPING_MISMATCH`,
`INTERNAL_TYPE_LEAK`, `RAW_HANDLE_LEAK` and `PUBLIC_NATIVE_FFI_LEAK`.

Native boundary:

```text
BOUND_FUNCTIONS=55  ROUTE_PAIRINGS=55  PROTOTYPE_TYPE_POSITIONS=170
CANONICAL_DECLARATION_CHECKS=170  C_SWIFT_MEASUREMENTS=170
LAYOUTS=21  LAYOUT_FIELDS=157  CALLBACKS=4  CONSTANTS=212  SCALAR_FACTS=3
MISSING_HEADER_SYMBOLS=0  MISSING_LIBRARY_SYMBOLS=0  ABI_MISMATCHES=0
NATIVE_ABI_MUTATIONS=14  CAUGHT=14  SURVIVORS=0
PROJECTION_MUTATIONS=46  CAUGHT=46  SURVIVORS=0
```

The projection-mutation harness refuses to run without a selected
`CNA_NATIVE_LIBRARY`: sixteen of its mutations are caught only by suites that
start a CNA runtime, and those suites *skip* rather than fail when no library
is selected, which would report a coverage loss as sixteen projection defects.

The seven registered reference assemblies reproduce 257 contract types and 2,964
contract members exactly; calibration and the audit's mutation self-tests pass
(`AUDIT_SELF_TESTS=80`, `RESOURCE_STRINGS_REPRODUCED=20`). The BCL authority
carries `BCL_SENTINEL_CHECKS=433`, `BCL_MUTATION_SELF_TESTS=462`,
`BCL_CROSS_CHECKS=141` against a second disassembler, and four negative
controls that are still refused.
`mscorlib` `5634668d…acc63` is the sole admitted BCL authority — 28 types and
254 members across seven raised exception families and eleven support types.
`System.dll` is available, its identity is established, and it is deliberately
unadmitted: no family it declares is required by any implemented projection,
and admitting it would register authority nothing consumes. What it would
unlock is the thirteen `Microsoft.Xna.Framework.Design` converters, which are
design-time IDE types unreachable from a running game.

## Platform and release policy

Linux x86-64 with Swift 6.0.3 and an external CNA C ABI 0.21.0 HEADLESS library
(SDL3 audio backend, `CNA_DEVICES=OFF`, `CNA_CNAEXT=OFF`) is the qualified
runtime. HEADLESS has no visible window and this host has no attached
controller, so no visible output and no positive controller behaviour is
claimed. Apple platforms, Windows, and Web/Wasm remain unqualified.

## The frontier

`docs/frontier-research-graphics-device-state-and-vertex-declaration.md` records
what has been measured about the next two frontiers and not implemented.
`docs/generated/dependency-graph.json` ranks the 19 dependency-complete missing
types; the widest reach after Foundation 43 is `GraphicsAdapter` (41), then
`SamplerStateCollection` and `TextureCollection` (38 each), `EffectAnnotation`
(25), `MathTypeConverter` (12), `ContentManager` (6) and `IVertexType` (4) —
the last of which `VertexDeclaration` unblocked.

The remaining member diagnostics belong to `GraphicsDevice` (52),
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
