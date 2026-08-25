# Pure behavior corpus

The corpus executes only deterministic `PURE_XNA_DERIVED` observations. CNA is
not a golden source for these value semantics, and no native library is needed.
Selected exact Float results are compared by binary32 bit pattern; semantic
predicates cover NaN and value/object behavior where a single bit pattern is
not the reference contract.

GamePad value groups cover both enums, the Int32 OptionSet, physical button and
DPad values, trigger/thumbstick special floats, both state constructors, every
physical and virtual button query, combinations, connection/packet equality,
all 26 managed capability properties, and XNA vibration input quantization.
Canonical controller observations are intentionally emitted by the separate
`tools/gamepad_native` runner and never counted as pure XNA-derived behavior.

The `DISPLAY_ORIENTATION` group records only the pinned XNA flags, Int32
underlying type, and four literal values. Swift `OptionSet` union,
intersection, arbitrary-bit, and copy qualification lives in a separate test
case and is not counted as XNA runtime behavior.

The `DEPTH_FORMAT` group records only the pinned non-flags enum, Int32
underlying type, and complete four-value literal table. Swift raw-value
initialization, unknown-value rejection, and copy qualification remain in a
separate projection test and are not counted as XNA runtime behavior.

The `SURFACE_FORMAT` group likewise records only the pinned non-flags enum,
Int32 underlying type, and complete twenty-value literal table. Swift raw-value
initialization, unknown-value rejection, and copy qualification remain in a
separate projection test and are not counted as XNA runtime behavior.

The four `DISPLAY_MODE_*` groups record only pinned XNA facts for the managed
`DisplayMode` descriptor: verbatim width/height/format storage through the
non-public constructor, the exact binary32 `AspectRatio` bit patterns including
the zero-dimension short circuit, the unmodified Windows `TitleSafeArea`
rectangle, and the exact `ToString` strings for every pinned SurfaceFormat
literal. Swift class-reference identity, internal-only construction, immutable
public state, and Rectangle value semantics remain in a separate projection
test and are not counted as XNA runtime behavior.
