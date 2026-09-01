# Canonical CNA C ABI boundary

## The admitted window

CNA-Swift admits **CNA C ABI major 0 with minor 21 or later**, and is qualified
against exactly `0.21.0` (`0x00001500`). The rule is CNA's own, not this
binding's invention: `docs/c-api/ABI_VERSIONING.md` says a consumer *must reject
a different major and may require a minimum minor*, and the installed CNA
package enforces the same thing with `COMPATIBILITY SameMajorVersion`. Under
`0.x` an incompatible change is what moves the minor, so the minimum minor is
the generation this binding was measured against.

A later minor is admitted by that rule. The protection against a later minor
that removed a route is not a version number: every one of the 63 bound symbols
must resolve by name before the runtime starts, and a missing one throws
`CNAError.missingNativeSymbol`.

A rejection names the admitted window, the reported version, and the file that
was selected:

```text
CNA native library /opt/cna/libcna_c_api.so reports C ABI 0.7.0 (0x00000700);
CNA-Swift admits major 0 with minor 21 or later (qualified against 0.21.0)
```

The loader accepts `CNA_NATIVE_LIBRARY` only when it is an absolute file path;
without it Linux tries only the installed soname `libcna_c_api.so`. There is no
sibling checkout, build directory, developer path, or C++ fallback.

## What is recorded and what is verified

`NativeManifest.swift` records, for each bound route: the canonical C symbol,
the single `NativeFunctions` property that holds it, that route's own
`@convention(c)` type, the canonical return and parameter declarations,
ownership, result lifetime, error lifetime, and callback ABI. `NativeFunctions`
resolves each symbol once into an immutable typed property. No two routes share
a route type, and no strict XNA type exposes a handle or function pointer.

`tools/native_abi/verify.py` independently:

1. compares each manifest declaration **textually** with the canonical
   declaration parsed from the CNA headers, parameter names included, so a
   merely compatible spelling is a mismatch;
2. compiles `__builtin_types_compatible_p` assertions for every manifest
   prototype against `&symbol`;
3. pairs every Swift property with exactly one symbol and one route type, each
   route type being re-derived from its symbol rather than trusted;
4. compares every mirrored `CNASwift_*` structure with its canonical
   counterpart field for field — names, order, offsets and widths;
5. proves every mirrored callback is the canonical callback type;
6. compiles the canonical constants and every selected `Keys` literal;
7. audits ELF exports and calls `cna_get_abi_version` on the explicit library,
   requiring it to be inside the admitted window *and* to agree with the header.

Qualified result on CNA 0.21.0:

```text
BOUND_FUNCTIONS=63  ROUTE_PAIRINGS=63  PROTOTYPE_TYPE_POSITIONS=198
CANONICAL_DECLARATION_CHECKS=198  C_SWIFT_MEASUREMENTS=198
LAYOUTS=25  LAYOUT_FIELDS=209  CALLBACKS=4  CONSTANTS=212  SCALAR_FACTS=3
MISSING_HEADER_SYMBOLS=0  MISSING_LIBRARY_SYMBOLS=0  ABI_MISMATCHES=0
```

Every count is derived from the source the verifier just compiled. None is a
hand-maintained literal.

`tools/native_abi/mutations.py` is the falsifiability gate: fourteen planted
defects — wrong parameter width, a compatible-but-wrong canonical spelling, a
stale symbol, a swapped route symbol, a swapped route type, a shared route type,
a wrong Swift position width, an unsatisfiable ABI window, an omitted structure
field, transposed fields, a narrowed field, a wrong callback signature, a wrong
constant and a wrong `Keys` literal — each of which the verifier must reject.
All fourteen are caught, and the tree is proven byte-identical afterwards.

## The evidence library

```text
CNA_SOURCE_REVISION=0a6158e4ff764907065cd7259e3d29e331a52088 (cnanext, branch next)
CNA_ABI_VERSION=0.21.0
NATIVE_LIBRARY_SHA256=c32bfbd307d695664f906ccf2834ec3f9ebc240fa388d544ac21ee3ebaeb731b
PLATFORM=Linux x86-64
RENDERER=HEADLESS
AUDIO_BACKEND=SDL3
CNA_DEVICES=OFF
CNA_CNAEXT=OFF
EXPORTS=4054
```

It is not shipped. Its headers are byte-identical to live cnanext HEAD's, its
export set is exactly the 4,054 names in cnanext's own checked-in
`tools/c-api/abi_baseline.json`, and the version it reports equals the version
its headers declare. `docs/native-abi-migration-evidence.md` records the full
migration, the route-by-route audit, the one CNA-Swift defect it found, and the
one upstream runtime behaviour that changed.

## Historical record: the retired CNA 0.7.0 boundary

Foundation Milestone 1 admitted exactly CNA C ABI `0.7.0` (`0x00000700`) and
rejected every other version. That measurement happened and is retained here;
it is no longer the boundary.

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
PLATFORM=Linux x86-64   RENDERER=HEADLESS   AUDIO_BACKEND=NULL
NATIVE_ABI=29 functions / 91 prototype positions / 91 C-Swift measurements /
           18 layouts / 2 callbacks / 214 constants / 0 missing / 0 mismatches
```

That binary no longer exists on this machine; the reproduced, ABI- and
behaviour-equivalent build documented in
`~/deps/cna-c-abi-0.7.0-pinned-foundation11/PROVENANCE.md`
(`c62949d23d3745964f5e557a06665875621ed4cb6e2930e3f282afd5911f2dcb`) reproduced
every one of those numbers exactly. `214` was a hand-maintained literal; the
derived count for the same assertions is 212 — see the migration document.

Foundation Milestone 6 added only the four required existing GamePad functions,
three exact copied-POD layouts, and 46 player/dead-zone/threshold/button/type
constants. Every field offset and function position was compiler-measured; no
adjacent CNA controller extension route was bound. All of it still holds on
0.21.0, unchanged.

## The render-target routes

Foundation 38 added the first native surface since the migration: seven routes
(`cna_texture_get_info`, `cna_render_target2d_create`,
`cna_render_target_get_info`, `cna_render_target_destroy`,
`cna_graphics_device_set_render_target2d` and the ContentLost
subscribe/unsubscribe pair), three mirrored structures and one mirrored
callback. Their first verification run failed on two positions the verifier
could not yet spell — `CNA_RenderTargetEventRegistrationHandle` and `void*` —
which is the canonical-declaration check working on the first surface added
since it existed.

## The game-host and device-service routes

Foundations 39 and 40 took the count from 43 to 55. Foundation 39 bound the
`Game` host members — timing writers, `Tick`, `SuppressDraw`,
`ResetElapsedTime`, `ShowMissingRequirementMessage`, the activation state and
the host-event subscribe/unsubscribe pair — with a fourth mirrored callback,
`CNA_GameEventCallback`, whose shape is the parameterless
`void (*)(void* context)`. Foundation 40 bound the graphics device manager's
own creation, `BeginDraw`/`EndDraw`, its device-event subscription pair, and the
callback-scoped device accessor.

The device accessor is the one route whose *refusal* is part of the measured
contract: outside a CNA callback `cna_graphics_device_manager_get_device`
answers `CNA_RESULT_INVALID_STATE` with a zero handle. The Swift guard that
returns `nil` there is documented defence in depth over a native refusal, not
the only thing preventing a dangling handle — which is why the mutation that
removed it was withdrawn as unfalsifiable rather than left in the harness
claiming coverage it did not have.

## The device-state routes

Foundation 41 added the four graphics state objects and bound **no** route for
them, because the milestone projected the managed types and did not implement
`GraphicsDevice.BlendState`. Binding a route for count, without a member that
uses it, is the thing this boundary exists to prevent.

Foundation 45 added the members and, with them, eight routes: get and set for
blend, depth-stencil and rasterizer state, and get and set for one sampler slot
of one shader stage. Four more mirrored structures came with them, taking the
layout wall from 21 structures and 157 fields to 25 and 209.

`cna_blend_state_init` and its three neighbours are still **not** bound. They
are CNA's own preset descriptors, and the Swift presets come from the pinned
`.cctor`; binding them would add a route no member consumes and would put a
native value where XNA authority belongs.

The first verification run of the eight failed on two positions:

```text
cna_graphics_device_get_sampler_state: parameters
  ['uint64_t', 'uint32_t', 'uint32_t', 'CNA_SamplerState*'] !=
  ['uint64_t', 'CNA_ShaderStage', 'uint32_t', 'CNA_SamplerState*']
```

`CNA_ShaderStage` — `typedef uint32_t` at `graphics_state.h:214` — was missing
from the alias table the type-compatibility comparison uses. The textual
canonical-declaration check had already passed on all 198 positions, because the
manifest keeps CNA's own spelling, and an alias never weakens that check. Same
class of gap as the two `RenderTarget2D` positions in Foundation 38, and the
same conclusion: the check working on the first surface added since it existed.
