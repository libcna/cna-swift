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
  `.Graphics.PackedVector`, `.Input`, and `.Content`. Markers are mapping
  infrastructure, not XNA types, and the verifier excludes the seven marker
  symbols.
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
- A reference-typed operator whose null behavior must remain observable may
  require Optional operands. Swift cannot declare an operator as a type member
  when both operands are Optional, so the configured global compiler symbol is
  assigned back to its XNA owner and measured as that same operator identity.
- CLR `ref`/`out` -> Swift `inout`; direction, type, label, and mutability are
  measured.
- A CLR caller-owned destination array named `destinationArray` or `corners`
  maps to Swift `inout Array`. Source arrays remain value snapshots. This
  preserves writes through Swift value semantics and gives overlapping
  source/destination calls an explicit copy-on-write snapshot rule. The verifier
  measures every selected destination-array mapping independently.
- The `array` parameter of `ICollection<T>.CopyTo` is identified from the
  pinned direct interface plus member semantics and likewise maps to `inout
  Array`. This is a general caller-owned mutation rule, not a diagnostic
  allowlist.
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

`System.Nullable<T>` maps independently to Swift `T?` when `T` is a faithfully
represented value type. Thus XNA geometry intersection distances return
`Float?`, and `out Nullable<Single>` maps to `inout Float?`; `nil` means XNA
`HasValue=false` and is not an error or sentinel value. Selected
`IEnumerable<Vector3>` point inputs map to `[Vector3]`, the established finite
Swift collection projection, without introducing a synthetic Microsoft
collection type.

Reference parameters become Optional only where null is an observable selected
operation rather than merely an immediate invalid argument. CurveKey therefore
maps typed `Equals`, `CompareTo`, and both operator operands to Optional;
CurveKeyCollection maps `IndexOf`, `Contains`, and `Remove` items to Optional.
`CompareTo(nil)` throws the mapped null-reference error. `Add(nil)` and an
indexed setter value of nil are immediate XNA argument failures, so those
strict parameters remain non-Optional.

`IPackedVectorOfT<TPacked>` uses Swift's primary-associated-type protocol
syntax and explicitly declares `associatedtype TPacked`. The compiler Symbol
Graph must expose that exact name and the verifier measures it, not merely the
number of generic parameters. A concrete conformance supplies a same-named
typealias; Color and all 17 concrete PackedVector structs expose the exact
fixed-width compiler witness, producing the corresponding mapped
`IPackedVectorOfT<TPacked>` interface.

Interface mutation maps to a `mutating` Swift protocol requirement when the CLR
operation changes packed struct storage. Thus `IPackedVector.PackFromVector4`
is mutating, while `ToVector4` is not. XNA's private explicit-interface methods
do not count among a concrete struct's public declared CLR members, but Swift
requires public conformance witnesses. The verifier excludes a witness only
when the concrete CLR type has the direct generic packed interface, the
non-generic interface declares the requirement, the concrete public contract
lacks it, the compiler emits a matching `sourceOrigin`, and the full witness
signature/mutating identity matches. It records all such deterministic
language projections separately rather than using a diagnostic allowlist.
Unrelated public members and malformed witnesses remain errors.

## Errors

Swift `throws` is the language projection for runtime/XNA failure paths because
Swift has no CLR unchecked exceptions. It does not add a reference member and
is ignored only as a measured `LANGUAGE_MAPPING` signature detail. Ordinary
failures never use `fatalError`, process exit, silent defaults, or no-ops.
`CNAError` is support API outside the strict XNA namespace.

## Comparison and collection interfaces

`System.IComparable<T>` maps to the exact concrete `CompareTo(T)` member. It
does not imply Swift `Comparable` conformance or synthesize ordering operators.
The pre-existing `System.IEquatable<T>` mapping remains the XNA `Equals(T)` and
operator members without Swift `Equatable` conformance.

`System.Collections.Generic.ICollection<T>` maps to the concrete XNA public
members that implement it: `Add`, `Clear`, `Contains`, `CopyTo`, `Remove`,
`Count`, and `IsReadOnly`. The verifier records the pinned direct-interface
identity and requires those compiler symbols, but there is no fake Microsoft
protocol and no automatic Swift `Collection`, `MutableCollection`, `Sequence`,
or `RandomAccessCollection` conformance.

`System.Collections.Generic.IEnumerator<T>` return values map to the public
support type `CNAEnumerator<T>` outside the XNA namespace. Its throwing
`Next() -> T?` preserves a live cursor and mutation invalidation. It does not
conform to nonthrowing `IteratorProtocol`. The related generic and non-generic
`IEnumerable` identities add no automatic Swift conformance.

A read/write CLR indexed property maps to a throwing getter named `Item` and a
throwing setter named `SetItem`. Swift has no throwing setter accessor. The
verifier validates both compiler symbols and recombines them into one source
property identity; missing/wrong getters, setters, index types, element types,
and mutability remain diagnostics. Read-only indexed properties may continue
to use a normal Swift subscript where their selected error contract permits.

## BCL mappings started in Foundation 1

| CLR type | Swift projection | Rule |
|---|---|---|
| `System.TimeSpan` | `Duration` | CNA supplies exact signed 100-nanosecond ticks; Swift constructs seconds/attoseconds without a floating-point interval. |
| `System.IO.Stream` | `Foundation.InputStream` | The strict `Texture2D.FromStream` projection reads the stream to contiguous bytes internally before CNA decode. |
| `System.IntPtr` | `Int` | Pointer-width signed integer; the native ABI verifier validates the host width where a selected route first uses it. |
| `System.Object` | `Any?` | Optional preserves CLR null. |
| `System.EventArgs` | `CNAEventArgs` | Empty public support value outside the XNA namespace. |
| `System.Collections.Generic.IEnumerator<T>` | `CNAEnumerator<T>` | Throwing live enumeration preserves CLR mutation invalidation without a fake Microsoft type. |

The verifier derives `EXPECTED_SWIFT_TYPES=257`. It derives
`EXPECTED_SWIFT_MEMBERS=2887` by excluding exactly 49 enum backing fields named
`value__` and 28 CLR finalizers. Swift raw-value storage and non-public `deinit`
are language mappings. No missing functional API is hidden by those omissions.

The report reserves `ALLOWLIST_ENTRIES` for genuine manual diagnostic
suppressions; it is currently zero. Deterministic projection transformations
are reported separately as `LANGUAGE_PROJECTION_EXCLUSIONS` (49 enum storage
fields, 28 finalizer mappings, seven namespace markers, three inherited member
projections, and 26 explicit-interface protocol witnesses). Comparison,
collection, enumerator, indexed-property, optional-operator-placement, and
caller-owned-array mappings have their own precise counters. A verifier
self-test proves that a real suppression counts
as an allowlist entry and that a missing geometry member cannot be reclassified
as a projection rule.
