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
complete six-type Curve family. It also includes the exact eleven-type XNA
GamePad family through real canonical CNA state, capability, packet, dead-zone,
and vibration routes. It also includes the standalone managed
`DisplayOrientation` flags type without claiming platform rotation or window
orientation functionality, plus the standalone managed `BufferUsage` flags
type without claiming buffer or GPU resource support, plus the standalone
managed non-flags `DepthFormat` enum without claiming depth/stencil buffers or
renderer support, plus the standalone
managed non-flags `FillMode` enum without claiming rasterizer or wireframe
rendering support, plus the standalone managed non-flags `SurfaceFormat` enum
without claiming texture, render-target, display, DXT, HDR, or GPU format
support, plus the standalone managed `DisplayMode` descriptor class without
claiming monitor enumeration, display-mode discovery, or resolution switching,
plus the standalone managed non-flags `RenderTargetUsage` enum without claiming
render targets or any content discard/preserve behavior.

Foundation 14 adds a further 25 pure-managed types in one batch — 22 exact
enums, the `VertexElement` value struct, and the `IEffectFog` and
`IEffectMatrices` protocols — covering graphics profile, presentation, device
status, primitive, clear, render-state, vertex-declaration, cube-face, effect
parameter and audio metadata. None of them claims any renderer, device, buffer,
effect or audio runtime support.

The old flat API and known fake behaviors are absent.

## Measured surface

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=98
TARGET_MEMBERS=1560
TOTAL_DIAGNOSTICS=310
COMPLETE_TYPES=93
PARTIAL_TYPES=5
MISSING_TYPES=159
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
Curve, CurveKey, CurveKeyCollection, CurveContinuity, CurveLoopType,
CurveTangent, all eleven GamePad-family types, DisplayOrientation, BufferUsage,
DepthFormat, FillMode, SurfaceFormat, DisplayMode, RenderTargetUsage, and the
25 Foundation-14 pure-managed types listed below. Every implemented member has
qualified behavior; missing members remain absent.

## Foundation 14 pure managed batch

Foundation 14 is a multi-type batch rather than a single-type closure. It
completes 25 entirely missing pure-managed types carrying 144 mapped XNA
identities, and stops on the 25-type batch limit.

```text
Graphics.GraphicsProfile        Reach=0, HiDef=1
Graphics.PresentInterval        Default=0, One=1, Two=2, Immediate=3
Graphics.VertexElementFormat    Single=0 .. HalfVector4=11
Graphics.VertexElementUsage     Position=0 .. TessellateFactor=12
Graphics.CompareFunction        Always=0 .. NotEqual=7
Graphics.CubeMapFace            PositiveX=0 .. NegativeZ=5
Graphics.IndexElementSize       SixteenBits=0, ThirtyTwoBits=1
Graphics.Blend                  One=0 .. SourceAlphaSaturation=12
Graphics.BlendFunction          Add=0 .. Max=4
Graphics.ColorWriteChannels     [Flags] None=0, Red=1, Green=2, Blue=4,
                                Alpha=8, All=15
Graphics.CullMode               None=0, CullClockwiseFace=1,
                                CullCounterClockwiseFace=2
Graphics.StencilOperation       Keep=0 .. Invert=7
Graphics.TextureAddressMode     Wrap=0, Clamp=1, Mirror=2
Graphics.TextureFilter          Linear=0 .. MinPointMagLinearMipPoint=8
Graphics.ClearOptions           [Flags] Target=1, DepthBuffer=2, Stencil=4
Graphics.GraphicsDeviceStatus   Normal=0, Lost=1, NotReset=2
Graphics.PrimitiveType          TriangleList=0 .. LineStrip=3
Graphics.EffectParameterClass   Scalar=0 .. Struct=4
Graphics.EffectParameterType    Void=0 .. TextureCube=9
Graphics.SetDataOptions         [Flags] None=0, Discard=1, NoOverwrite=2
Graphics.VertexElement          value struct, 10 identities
Graphics.IEffectFog             protocol, 4 read/write properties
Graphics.IEffectMatrices        protocol, 3 read/write properties
Audio.SoundState                Playing=0, Paused=1, Stopped=2
Audio.AudioChannels             Mono=1, Stereo=2
```

`[Flags]` is an observed property of the pinned binaries: it is present on
exactly `ColorWriteChannels`, `ClearOptions`, and `SetDataOptions` and absent
from the other 19 enums, so those three are Swift `OptionSet` structs and the
rest are ordinary `enum: Int32`. No `None`, `Default`, or `All` literal was
invented, and no enum gained a `description`, `ToString`, predicate, alias, or
native-conversion helper.

`VertexElement` reproduces the pinned IL exactly: verbatim unvalidated
construction, plain field accessors, four-field `op_Equality` with `!=` as its
negation, `Equals(object)` null/type guards, the internal `SmartGetHashCode`
word XOR with `0x7FFFFFFF` for a zero result, and
`{Offset:O Format:F Usage:U UsageIndex:I}`. The two element enums gain no
public string surface; the name tables stay private to `VertexElement`.

`SoundState` and `AudioChannels` are the first `Microsoft.Xna.Framework.Audio`
types, so that namespace marker was added. They are metadata only: there is no
audio engine, and the audio backend remains NULL.

This batch is managed metadata and managed value logic only. No CNA source, C
ABI, native binding, renderer, device, texture, sprite-batch, callback,
thread-affinity, filesystem or audio-engine work is included, and none of the
five runtime-partial types was touched. See
`docs/foundation-14-pure-managed-batch-evidence.md`.

## Managed RenderTargetUsage

`Microsoft.Xna.Framework.Graphics.RenderTargetUsage` is the exact managed
non-flags `Int32` enum with `DiscardContents=0`, `PreserveContents=1`, and
`PlatformContents=2`. The three literals are mutually exclusive alternatives,
not bit flags, so the type is a Swift `enum` and never an `OptionSet`. The CLR
`value__` storage identity is the existing enum-storage language mapping. Swift
raw-value initialization accepts the complete 0...2 table, rejects
representative unknown positive and negative values with `nil`, and preserves
ordinary value-copy behavior without adding XNA members. There is no
`description`, `ToString`, predicate helper, alias, or native conversion.

This is managed metadata only. RenderTarget2D, RenderTargetCube,
RenderTargetBinding, PresentationParameters, render-target creation, depth
attachments, MSAA, `GraphicsDevice.SetRenderTarget`, and native usage mapping
remain deferred. The names describe XNA's content-preservation policy;
CNA-Swift does not implement or claim discard, preserve, or platform-defined
content semantics. See `docs/render-target-usage-evidence.md`.

## Managed DisplayMode

`Microsoft.Xna.Framework.Graphics.DisplayMode` is the exact managed descriptor
class with the pinned six identities: `ToString`, `Format`, `Height`, `Width`,
`AspectRatio`, and `TitleSafeArea`. The pinned public contract declares **no
constructor**, so the Swift class exposes no public initializer; the CLR's
`assembly`-accessible `.ctor(width, height, format)` maps to an `internal` Swift
initializer that is implementation infrastructure and never public XNA surface.
The class is deliberately neither `open` — no accessible CLR constructor makes
it externally subclassable — nor `final`, because metadata says `sealed=false`.

`Width`, `Height` and `Format` are verbatim get-only stored values with no
validation. `AspectRatio` is the guarded binary32 quotient: positive zero
whenever either dimension is zero, otherwise `Float(Width) / Float(Height)`
computed without Double widening, without clamping and without absolute value.
`TitleSafeArea` is exactly `Rectangle(0, 0, Width, Height)` — the unmodified
Windows result, with no overscan inset, no Xbox policy and no display query.
`ToString` reproduces `{Width:W Height:H Format:F AspectRatio:A}`.

There is no `Equals`, `GetHashCode`, `==`, `!=`, `Equatable`, `Hashable`,
setter, static factory, `description`, or convenience helper, and SurfaceFormat
gains no public string surface.

This is a managed descriptor only. DisplayModeCollection, GraphicsAdapter,
`GraphicsDevice.DisplayMode`, PresentationParameters, monitor enumeration,
display-mode discovery, resolution switching, fullscreen mode management, and
native display support remain deferred. See `docs/display-mode-evidence.md`.

## Managed DepthFormat

`Microsoft.Xna.Framework.Graphics.DepthFormat` is the exact managed non-flags
`Int32` enum with `None=0`, `Depth16=1`, `Depth24=2`, and
`Depth24Stencil8=3`. The CLR `value__` storage identity is the existing
enum-storage language mapping. Swift raw-value initialization accepts the
complete 0...3 table, rejects representative unknown positive and negative
values with `nil`, and preserves ordinary value-copy behavior without adding
XNA members.

This is managed metadata only. GraphicsAdapter, PresentationParameters,
RenderTarget2D, RenderTargetCube, GraphicsDeviceManager depth-format members,
DepthStencilState, depth/stencil allocation or testing, renderer capability,
and native DepthFormat mapping remain deferred. See
`docs/depth-format-evidence.md`.

## Managed SurfaceFormat

`Microsoft.Xna.Framework.Graphics.SurfaceFormat` is the exact managed
non-flags `Int32` enum with all twenty pinned literals from `Color=0` through
`HdrBlendable=19`. The CLR `value__` storage identity is the existing
enum-storage language mapping. Swift raw-value initialization accepts the
complete 0...19 table, rejects representative unknown positive and negative
values with `nil`, and preserves ordinary value-copy behavior without adding
XNA members.

This is managed metadata only. DisplayModeCollection,
GraphicsAdapter, PresentationParameters, texture and render-target APIs,
GraphicsDeviceManager format properties, GraphicsDevice format operations,
pixel/DXT conversion, HDR capability, GPU format negotiation, and native
SurfaceFormat mapping remain deferred. See
`docs/surface-format-evidence.md`.

## Managed FillMode

`Microsoft.Xna.Framework.Graphics.FillMode` is the exact managed non-flags
`Int32` enum with `Solid=0` and `WireFrame=1`. The CLR `value__` storage
identity is the existing enum-storage language mapping. Swift raw-value
initialization accepts 0 and 1, rejects representative unknown values with
`nil`, and preserves ordinary value-copy behavior without adding XNA members.

This is only a managed enum. `RasterizerState`,
`GraphicsDevice.RasterizerState`, drawing, wireframe rendering, polygon-mode
switching, and native renderer support remain deferred. See
`docs/fill-mode-evidence.md`.

## Managed BufferUsage

`Microsoft.Xna.Framework.Graphics.BufferUsage` is the exact managed `Int32`
OptionSet with `None=0` and `WriteOnly=1`. The CLR `value__` storage identity
is the existing enum-storage language mapping; Swift raw-value and OptionSet
surface adds no XNA identity. Unknown positive and negative raw patterns,
ordinary union/intersection, and value-copy semantics are qualified separately
from the two pinned literal observations.

This is only a managed flags value. VertexBuffer, IndexBuffer, dynamic buffers,
VertexDeclaration, IVertexType, SetData/GetData, and all GraphicsDevice buffer
and draw operations remain deferred. See `docs/buffer-usage-evidence.md`.

## Managed DisplayOrientation

`Microsoft.Xna.Framework.DisplayOrientation` is the exact root-framework
`Int32` OptionSet with `Default=0`, `LandscapeLeft=1`, `LandscapeRight=2`, and
`Portrait=4`. The CLR `value__` storage field and the Swift raw-value/OptionSet
surface remain formal language projections, so the type has exactly four XNA
identities and zero local diagnostics. Arbitrary raw bits are preserved.

This is only a managed flags value. GraphicsDeviceManager orientation members,
GameWindow, display detection, and platform rotation remain deferred. See
`docs/display-orientation-evidence.md`.

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

## Qualified GamePad family

`Buttons` is an exact `Int32` OptionSet with all 25 XNA flags. The six public
GamePad value types remain Swift structs; capabilities expose 26 read-only
properties and no public initializer. State constructors, physical and virtual
button queries, all-bit combination behavior, packet/connection fields,
binary32 clamps, equality, hashing, and strings follow the pinned XNA IL.

The four static GamePad methods bind only existing canonical CNA 0.7.0 C ABI
routes. Native snapshots carry real packet numbers and per-control capabilities;
vibration returns CNA's device-accepted Boolean. The current HEADLESS/NULL host
has no controller, so disconnected routes are verified while positive state,
capability diversity, and physical rumble remain `HARDWARE_PENDING`. See
`docs/gamepad-evidence.md`, `docs/gamepad-native-inventory.md`, and the separate
generated native qualification report.

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
and no native binary ships in the source package. Managed Curve and GamePad
value tests require no native library.

HEADLESS executes real viewport, clear, PNG decode, SpriteBatch, keyboard, and
GamePad disconnected routes but has no visible window or attached controller.
Visible output and positive controller behavior are not claimed. macOS, iOS,
tvOS, visionOS, Windows, and Web/Wasm are unqualified.

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
python3 tools/api_compat/dependency_graph.py \
  --report docs/generated/api-compat-report.json \
  --output docs/generated/dependency-graph.json
python3 tools/native_abi/verify.py \
  --cna-include /path/to/cna/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
python3 tools/gamepad_native/run.py \
  --library "$CNA_NATIVE_LIBRARY" \
  --output docs/generated/gamepad-native-report.json
```

The normal API verifier exits nonzero until the full selected profile is
complete; use `--leak-only` for the green encapsulation gate. Architecture,
mapping, ABI provenance, capabilities, evidence, and the exact continuation
handoff are retained under `docs/`, `plan.md`, and `NEXT.md`.
