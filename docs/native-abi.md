# Canonical CNA C ABI boundary

Foundation 1 admits exactly CNA C ABI 0.7.0 (`0x00000700`). It rejects ABI 0.8
and every other version before resolving the selected function table. The
loader accepts `CNA_NATIVE_LIBRARY` only when it is an absolute file path;
without it Linux tries only the installed soname `libcna_c_api.so`. There is no
sibling checkout, build directory, developer path, or C++ fallback.

`NativeManifest.swift` records for each selected symbol its C return and
parameters, pointer depth, fixed-width signedness, ownership, result lifetime,
error lifetime, and callback ABI. `NativeFunctions` resolves each symbol once
into an immutable typed `@convention(c)` property. No strict XNA type exposes a
handle or function pointer.

`tools/native_abi/verify.py` independently:

1. compiles C type-compatibility assertions for all manifest prototypes against
   canonical CNA headers;
2. compares every Swift function position with the manifest;
3. compiles size/alignment/offset assertions between canonical structures and
   `CNAShim`;
4. compiles callback and all `Keys`/selected flag constants;
5. audits ELF exports and calls `cna_get_abi_version` on the explicit library.

Qualified result: 25 functions, 72 prototype positions, 72 C/Swift
measurements, 15 layouts, 2 callbacks, 168 constants, zero missing header
symbols, zero missing library symbols, and zero mismatches.

The external evidence library is not shipped:

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
PLATFORM=Linux x86-64
RENDERER=HEADLESS
AUDIO_BACKEND=NULL
```

Current canonical CNA HEAD
`1bb2145d99ed572dd4eb15009c34e2e5f410fcf0` was inspected read-only. A clean
out-of-tree C API build with HEADLESS/NULL reached CNA's existing missing
`Microsoft/Xna/Framework/GamerServices/GameUpdateRequiredException.hpp`
include. CNA was not patched. The compatible retained artifact was therefore
independently reverified rather than inheriting another binding's verdict.
