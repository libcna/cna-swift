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
