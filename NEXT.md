# CNA-Swift continuation handoff

**Foundation Milestone 1 status:** complete for the applicable Linux x86-64
HEADLESS boundary. The full XNA profile is intentionally incomplete; preserve
the strict red scoreboard.

## Repository and toolchain evidence

```text
CNA_SWIFT_INITIAL_HEAD=db329d8358e21420952bf4dd7318302a3cd3c81c
CNA_SWIFT_TEMPLATE_INITIAL_HEAD=ae8c8d38d3dee4a4a47b3515ef65989b7f36812a
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
TESTS=15
TEST_FAILURES=0
WARNINGS_AS_ERRORS=PASS
SYMBOL_GRAPH=PASS
SWIFT_ASAN=PASS_PURE_CORPUS_DETECT_LEAKS_DISABLED_PTRACE
NATIVE_CNA_SANITIZER=NOT_INSTRUMENTED
```

The environment had no Swift on PATH. Qualification used the locally extracted
Debian swiftlang 6.0.3 toolchain without adding a package dependency. The first
ASan launch hit LeakSanitizer's ptrace limitation; rerunning with leak detection
disabled passed the pure suite. This is Swift-side memory-misuse evidence, not
native CNA sanitizer or leak-freedom evidence.

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=19
TARGET_MEMBERS=365
TOTAL_DIAGNOSTICS=575
MISSING_TYPE=238
MISSING_MEMBER=307
COMPLETE_TYPES=11
PARTIAL_TYPES=8
MISSING_TYPES=238
UNEXPECTED_TYPE=0
UNEXPECTED_MEMBER=0
TYPE_KIND_MISMATCH=0
BASE_MAPPING_MISMATCH=2
INTERFACE_MAPPING_MISMATCH=2
FIELD_MAPPING_MISMATCH=0
PROPERTY_MAPPING_MISMATCH=1
METHOD_SIGNATURE_MAPPING_MISMATCH=0
PARAMETER_MAPPING_MISMATCH=0
RETURN_MAPPING_MISMATCH=0
OVERLOAD_MAPPING_MISMATCH=25
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
ALLOWLIST_ENTRIES=86
```

The 86 formal mapping entries are 49 `value__` backing fields, 28 finalizers,
six namespace markers, and three inherited/System.IDisposable `Dispose()`
projections. They are explicit language mappings, not unmeasured API.
Twenty-two verifier mutation/self-tests pass. Normal strict exits red; leak-only exits
green.

Complete types:

- Microsoft.Xna.Framework.MathHelper
- Microsoft.Xna.Framework.Point
- Microsoft.Xna.Framework.Rectangle
- Microsoft.Xna.Framework.GameTime
- Microsoft.Xna.Framework.PlayerIndex
- Microsoft.Xna.Framework.Graphics.SpriteSortMode
- Microsoft.Xna.Framework.Graphics.SpriteEffects
- Microsoft.Xna.Framework.Input.Keys
- Microsoft.Xna.Framework.Input.KeyState
- Microsoft.Xna.Framework.Input.KeyboardState
- Microsoft.Xna.Framework.Input.Keyboard

Partial types are Color, Vector2, Game, GraphicsDeviceManager, GraphicsDevice,
Viewport, Texture2D, and SpriteBatch. Their exact missing identities are in
`docs/generated/missing-type-inventory.md`; do not replace those diagnostics
with catch-alls or no-ops.

## Native evidence

```text
CNA_SOURCE_REVISION=a09196a6477f69a7a57c8364f990658d31531a5b
CNA_ABI_VERSION=0.7.0
NATIVE_LIBRARY_SHA256=42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
PLATFORM=Linux x86-64
RENDERER=HEADLESS
AUDIO_BACKEND=NULL
BOUND_FUNCTIONS=25
PROTOTYPE_TYPE_POSITIONS=72
C_SWIFT_MEASUREMENTS=72
LAYOUTS=15
CALLBACKS=2
CONSTANTS=168
MISSING_HEADER_SYMBOLS=0
MISSING_LIBRARY_SYMBOLS=0
ABI_MISMATCHES=0
```

Current CNA HEAD `1bb2145d99ed572dd4eb15009c34e2e5f410fcf0`
remains read-only and its clean out-of-tree C API build is blocked on the
missing `GameUpdateRequiredException.hpp`. Do not patch CNA from this binding.
The retained compatible artifact was independently reverified here.

## Behavior, lifecycle, and stress

```text
PURE_OBSERVATIONS=47
PURE_ASSERTIONS=47
PURE_FAILURES=0
GAME_CYCLES=20
GAME_RECREATION_CYCLES=20
TEXTURE2D_CYCLES=20
SPRITEBATCH_CYCLES=20
CALLBACK_ERROR_CYCLES=20
NATIVE_CRASHES=0
OBSERVED_UAF=0
OBSERVED_DOUBLE_FREE=0
```

Real callback containment covers Initialize, LoadContent, Update, Draw, and
UnloadContent. Wrong-thread Game and Texture destruction refuse without
clearing the handle; owner-thread retry succeeds. Parent-before-child,
child-before-parent, double dispose, failed PNG create, retained borrowed
device, and generation invalidation are covered.

The maintained template completed 60 and 600 exact native Update/Draw callback
counts, decoded its project-owned logo as 128x128, and read the HEADLESS native
viewport as 800x480. It uses real Clear, SpriteBatch, rotation, scale,
movement, and Keyboard. Visible output remains BACKEND_BLOCKED by HEADLESS.

## Deferred boundaries

Content/XNB is DEFERRED and fake ContentManager is absent. Effects/3D is
DEFERRED and fake BasicEffect, cube, `GraphicsCapability`, and capability guess
are absent. Audio, Media, Storage, Touch, Design, PackedVector, and all remaining
families are unimplemented. macOS, iOS, tvOS, visionOS, Windows, and Web/Wasm
are unqualified.

## One next dependency-complete milestone

Implement the strict binary32 linear-algebra closure as one milestone:
Vector2, Vector3, Vector4, Quaternion, and Matrix, including every constructor,
operator, value/ref overload, transform array overload, field/property, equality,
hash, and string mapping required by the pinned contract. Extend the
PURE_XNA_DERIVED corpus with exact Float edge observations and complete Matrix
creation/multiplication semantics. Then finish the newly unblocked Viewport
Project/Unproject and Color vector-dependent members only if that closes those
whole types.

Do not start Content, Effects/Model, Audio, or another broad family during that
milestone.
