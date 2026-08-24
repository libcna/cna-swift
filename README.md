# CNA-Swift

CNA-Swift is now a real, deliberately partial Swift projection of Microsoft
XNA Framework 4.0 over the canonical CNA C ABI. It is not a 257-type binding
yet, and it does not claim that it is.

The strict public identity is `Microsoft.Xna.Framework...`. The qualified
foundation has a
compiler-Symbol-Graph scoreboard, exact ABI-0.7 admission, a reviewed typed
function table, owner-thread/generation/ownership enforcement, callback error
containment, a native Game/2D/input canary, and a complete managed binary32
linear-algebra plus public-signature geometry dependency closure. The managed
Color and its two forced packed-vector protocols are also complete. The old
flat one-file API and every known fake behavior were removed.

## Measured surface

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=32
TARGET_MEMBERS=1030
COMPLETE_TYPES=27
PARTIAL_TYPES=5
MISSING_TYPES=225
```

Normal strict verification remains red because future XNA types and members
are genuinely absent. Leak-only verification is green: no internal type, raw
pointer, native handle, or public FFI declaration leaks into the XNA surface.
See `docs/generated/api-compat-report.json` and
`docs/generated/missing-type-inventory.md` for the current exact diagnostics.

Strict-complete types are MathHelper, Point, Rectangle, GameTime, PlayerIndex,
Vector2, Vector3, Vector4, Quaternion, Matrix, Viewport, Plane,
PlaneIntersectionType, Ray, BoundingBox, BoundingSphere, BoundingFrustum,
ContainmentType, SpriteSortMode, SpriteEffects, Keys, KeyState, KeyboardState,
Keyboard, Color, Graphics.PackedVector.IPackedVector, and
Graphics.PackedVector.IPackedVectorOfT. Game, GraphicsDeviceManager,
GraphicsDevice, Texture2D, and SpriteBatch are explicitly measured partial
types. Every implemented member is real; missing members are absent.

The geometry types are not a separate follow-on milestone: pinned Matrix
signatures require Plane, whose own public signatures recursively require the
exact intersection closure above. No broader geometry, rendering, or native ABI
surface was added. BasicEffect, ContentManager, GraphicsCapability, and the old top-level
`Run(game:)` do not exist. Content/XNB and Effects/3D are deferred. See
`docs/linear-algebra-evidence.md` and
`docs/geometry-intersection-evidence.md` for the binary32, convention, and
dependency evidence.

Color exposes the complete 165-member pinned surface, including exact UInt32
packing, Vector3/Vector4 conversion, premultiplication, fixed-point
interpolation, and all 141 predefined colors. Its authoritative direct
interface forces only `IPackedVector` and the mapped generic
`IPackedVectorOfT<TPacked>` protocol. No concrete PackedVector format was
started. See `docs/color-packed-protocol-evidence.md` for the dependency,
compiler, and behavior evidence.

## Qualified runtime

The qualified host is Linux x86-64 with Swift 6.0.3
(`x86_64-pc-linux-gnu`) and an external CNA C ABI 0.7.0 HEADLESS/NULL library.
Supply it explicitly:

```bash
export CNA_NATIVE_LIBRARY=/absolute/path/to/libcna_c_api.so
swift test
```

`CNA_NATIVE_LIBRARY` must be absolute. Without it Linux tries only an installed
`libcna_c_api.so`; there is no developer-tree fallback. ABI 0.8 is rejected.
No native binary ships in the source package.

The HEADLESS renderer executes real viewport, clear, PNG decode, SpriteBatch,
and keyboard routes, but has no visible window. Visible output is therefore
backend-blocked, not claimed. macOS, iOS, tvOS, visionOS, Windows, and Web/Wasm
are future/unqualified.

## Verification

The core commands are:

```bash
swift build
swift build -c release
swift test
swift package dump-symbol-graph
python3 tools/api_compat/verify.py --self-test
python3 tools/api_compat/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --output docs/generated/api-compat-report.json
python3 tools/native_abi/verify.py \
  --cna-include /path/to/cna/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
```

The normal API verifier exits nonzero until the selected XNA profile is
complete; use `--leak-only` for the green encapsulation gate.
Architecture, mapping, ABI provenance, scaffold audit, capabilities, and exact
handoff evidence are retained under `docs/`, `plan.md`, and `NEXT.md`.
