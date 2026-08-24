# Formal XNA 4.0 to Swift mapping

The public API authority is the pinned Microsoft XNA Framework 4.0 Windows
runtime metadata contract, not CNA and not a sibling binding. The selected
reference contains 257 public types and 2,964 declared members. The retained
contract SHA-256 is
`7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`.
Its primary `Microsoft.Xna.Framework.dll` input has SHA-256
`38e7093f52d7474bbc6256906519781a1210d7da50a1c667b52716fcf49ca130`.
The snapshot was extracted from the Microsoft XNA 4.0 Windows runtime metadata
by mature-binding tooling and copied byte-for-byte; `tools/api_compat` verifies
the retained snapshot hash before projecting it.

## Names and kinds

- Namespace marker enums produce `Microsoft.Xna.Framework`, `.Graphics`,
  `.Input`, and `.Content`. Markers are mapping infrastructure, not XNA types,
  and the verifier excludes the six marker symbols.
- CLR class -> Swift class; an externally subclassable CLR class -> `open`
  Swift class where required.
- CLR struct -> Swift struct.
- CLR interface -> Swift protocol.
- CLR enum -> Swift enum with the reviewed fixed-width raw type.
- CLR `[Flags]` enum -> Swift `OptionSet` when raw flag behavior is preserved.
- CLR delegate -> a typed Swift closure at the native boundary; public delegate
  types will receive deterministic named closure projections when selected.
- Nested CLR `+` identity -> nested Swift `.` identity.
- Public XNA spelling remains PascalCase whenever Swift syntax permits it.
  There are no lowercase strict-surface compatibility aliases.

## Members and overloads

- CLR `.ctor` -> overloaded Swift `init`.
- Value-type constructor external labels are `_`; class constructor labels
  preserve metadata parameter names.
- A normal method's first external label is `_`; later labels preserve XNA
  metadata names. Operator parameters all use `_`.
- Fields and properties preserve static/instance identity, type, and
  mutability. XNA static value properties remain Swift static properties.
- CLR operators map to Swift operator functions. The verifier measures each
  overload separately.
- CLR `ref`/`out` -> Swift `inout`; direction, type, label, and mutability are
  measured.
- CLR protected virtual lifecycle members -> `open` methods. Their additional
  Swift visibility is `LANGUAGE_MAPPING`, not an unexpected XNA member.
- A selected inherited public member may temporarily be declared on a partial
  subtype until its XNA base exists. It must exactly match a selected ancestor.
  `System.IDisposable` maps to public `Dispose()`. These are counted mapping
  entries, not silently ignored members.

## Generics and nullability

Swift cannot place `Foo` and `Foo<T>` in one scope. The non-generic type keeps
its canonical name. The two collisions in this profile map deterministically:

- `ContentTypeReader<T>` -> `ContentTypeReaderOfT<T>`
- `IPackedVector<TPacked>` -> `IPackedVectorOfT<TPacked>`

No aliases collapse the identities. Reference nullability maps to Swift
Optional only where the selected XNA signature permits null. Native create
failure is an Error, not an Optional result. Value types remain non-optional
unless the signature itself is nullable.

## Errors

Swift `throws` is the language projection for runtime/XNA failure paths because
Swift has no CLR unchecked exceptions. It does not add a reference member and
is ignored only as a measured `LANGUAGE_MAPPING` signature detail. Ordinary
failures never use `fatalError`, process exit, silent defaults, or no-ops.
`CNAError` is support API outside the strict XNA namespace.

## BCL mappings started in Foundation 1

| CLR type | Swift projection | Rule |
|---|---|---|
| `System.TimeSpan` | `Duration` | CNA supplies exact signed 100-nanosecond ticks; Swift constructs seconds/attoseconds without a floating-point interval. |
| `System.IO.Stream` | `Foundation.InputStream` | The strict `Texture2D.FromStream` projection reads the stream to contiguous bytes internally before CNA decode. |
| `System.IntPtr` | `Int` | Pointer-width signed integer; the native ABI verifier validates the host width where a selected route first uses it. |
| `System.Object` | `Any?` | Optional preserves CLR null. |
| `System.EventArgs` | `CNAEventArgs` | Empty public support value outside the XNA namespace. |

The verifier derives `EXPECTED_SWIFT_TYPES=257`. It derives
`EXPECTED_SWIFT_MEMBERS=2887` by excluding exactly 49 enum backing fields named
`value__` and 28 CLR finalizers. Swift raw-value storage and non-public `deinit`
are language mappings. No missing functional API is hidden by those omissions.
