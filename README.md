# CNA-Swift

CNA-Swift is a real, deliberately partial Swift projection of Microsoft XNA
Framework 4.0 over the canonical CNA C ABI. It does not claim completion of the
full 257-type profile.

The strict public identity is `Microsoft.Xna.Framework...`. The qualified
foundation has a compiler Symbol Graph scoreboard, exact ABI-0.7 admission, a
reviewed typed function table, owner-thread/generation/ownership enforcement,
callback error containment, and a native Game/2D/input canary. Its managed
surface includes exact binary32 linear algebra and intersection types, Color,
both packed-vector protocols, all 17 concrete PackedVector formats, and the
complete six-type Curve family. The old flat API and known fake behaviors are
absent.

## Measured surface

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=55
TARGET_MEMBERS=1247
TOTAL_DIAGNOSTICS=353
COMPLETE_TYPES=50
PARTIAL_TYPES=5
MISSING_TYPES=202
MISSING_MEMBER=131
```

Normal strict verification remains red because deferred XNA types are genuinely
absent. Leak-only is green: no internal type, pointer, native handle, or public
FFI declaration leaks into the XNA surface. All remaining member diagnostics
belong to Game, GraphicsDeviceManager, GraphicsDevice, Texture2D, and
SpriteBatch. See `docs/generated/api-compat-report.json` and
`docs/generated/missing-type-inventory.md` for the exact inventory.

The strict-complete managed foundation includes MathHelper, Point, Rectangle,
GameTime, PlayerIndex, Vector2/3/4, Quaternion, Matrix, Viewport, Plane, Ray,
BoundingBox/Sphere/Frustum and their enums, keyboard values, SpriteSortMode,
SpriteEffects, Color, the packed protocols, all concrete PackedVector formats,
and Curve, CurveKey, CurveKeyCollection, CurveContinuity, CurveLoopType, and
CurveTangent. Every implemented member has qualified behavior; missing members
remain absent.

## Managed Curve family

Curve, CurveKey, and CurveKeyCollection are open reference classes, matching
the non-sealed CLR types. CurveKey has exact field equality/hash and the XNA
direct-branch CompareTo behavior, including `NaN/finite=+1`,
`finite/NaN=+1`, and `NaN/NaN=+1`.

CurveKeyCollection preserves XNA sorted insertion and reference identity. Its
CLR collection interfaces map without fake Microsoft collection types or
automatic Swift Collection conformance. `GetEnumerator` returns the root
support type `CNAEnumerator<CurveKey>` so mutation invalidation throws; the
read/write CLR indexer maps to throwing Item/SetItem accessors so invalid
indices cannot become Swift Array traps. Tangents, Hermite evaluation, Double
position widening, Step continuity, and Constant/Cycle/CycleOffset/Oscillate/
Linear loops reproduce the pinned XNA IL, including negative cycles.

See `docs/curve-evidence.md` for exact formulas, clone depth, collection
versioning, null policy, projection rules, and authority provenance. Earlier
managed families are documented in the other evidence files under `docs/`.

## Qualified runtime

The qualified host is Linux x86-64 with Swift 6.0.3
(`x86_64-pc-linux-gnu`) and an external CNA C ABI 0.7.0 HEADLESS/NULL library.
Supply it explicitly:

```bash
export CNA_NATIVE_LIBRARY=/absolute/path/to/libcna_c_api.so
swift test
```

`CNA_NATIVE_LIBRARY` must be absolute. Without it Linux tries only an installed
`libcna_c_api.so`; there is no developer-tree fallback. ABI 0.8 is rejected,
and no native binary ships in the source package. Managed Curve tests require
no native library.

HEADLESS executes real viewport, clear, PNG decode, SpriteBatch, and keyboard
routes but has no visible window. Visible output is backend-blocked, not
claimed. macOS, iOS, tvOS, visionOS, Windows, and Web/Wasm are unqualified.

## Verification

```bash
swift build
swift build -c release
swift test
swift test -c release
swift package dump-symbol-graph
python3 tools/api_compat/verify.py --self-test
python3 tools/api_compat/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --output docs/generated/api-compat-report.json \
  --inventory-output docs/generated/missing-type-inventory.md
python3 tools/native_abi/verify.py \
  --cna-include /path/to/cna/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
```

The normal API verifier exits nonzero until the full selected profile is
complete; use `--leak-only` for the green encapsulation gate. Architecture,
mapping, ABI provenance, capabilities, evidence, and the exact continuation
handoff are retained under `docs/`, `plan.md`, and `NEXT.md`.
