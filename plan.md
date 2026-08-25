# CNA-Swift normative plan and status

**Milestone:** Foundation 16 — Pure Managed Batch B. Four entirely missing
pure-managed XNA types carrying 21 mapped Swift XNA identities, over the
completed Foundation 1–15 baseline.

## Normative rules

1. Pinned Microsoft XNA 4.0 Windows runtime metadata is the public shape
   authority, and the hash-matched assembly IL is the behavior authority. FNA
   and MonoGame are engineering comparators only. For a type whose entire
   contract is metadata, the pinned contract alone is sufficient and no
   behavior surrogate or reference probe is created. Every type completed in
   this batch was additionally re-derived from a pinned, hash-matched assembly;
   a candidate whose declaring assembly lies outside the pinned set is deferred
   rather than completed on weaker provenance.
2. The batch is managed-only. It introduces no native route, constant, layout,
   callback, device, adapter, buffer, texture, render target, effect, audio
   engine, or renderer operation.
3. A complete type does not imply runtime capability. Profile selection,
   presentation, device status, primitives, clear paths, blend/depth/stencil/
   rasterizer/sampler state, vertex and index buffers, cube textures, effects,
   fog, and audio playback all remain unclaimed.
4. Public strict names use `Microsoft.Xna.Framework...` and exact XNA
   PascalCase. Formal Swift projections are measured; manual diagnostic
   allowlisting is forbidden.
5. Mapping rules are unchanged and no new mapping policy was created to make a
   candidate convenient. Foundation 15 promoted the pre-existing
   `System.IntPtr -> Swift Int` entry to a documented **general** language rule
   with verifier support and ten negative controls; it invented nothing,
   because the rule was already in `mapping-rules.json` and the mapping
   document before this milestone. The expected projection is never
   `RAW_HANDLE_LEAK`; that exemption covers only the mapped XNA IntPtr value
   and never a CNA FFI or native implementation handle. Earlier rules:
   - a public non-flags CLR enum maps to a Swift `enum` with the CLR underlying
     type as its raw type and one explicitly valued case per CLR literal;
   - a public `[Flags]` CLR enum maps to a Swift `OptionSet` struct with the CLR
     underlying type as `rawValue`, one `static let` per CLR literal, and a
     zero-valued literal spelled as the empty set;
   - a public CLR interface maps to a Swift `protocol` with one requirement per
     declared member and no invented conformance;
   - the synthetic `value__` storage identity remains the existing enum-storage
     language mapping and never appears in the public Swift surface;
   - `[Flags]` presence is read out of the pinned binary, never assumed.
   A namespace marker is added when a namespace gains its first implemented
   type; `Microsoft.Xna.Framework.Audio` gained its marker this milestone.
6. Exact CNA ABI 0.7.0 only. Native selection is an absolute environment
   override or installed soname, never a developer-tree fallback.
7. The five runtime-partial types — `Game`, `GraphicsDeviceManager`,
   `GraphicsDevice`, `Texture2D`, `SpriteBatch` — are off limits. A candidate
   that would require modifying one of them is skipped and recorded, and
   `MISSING_MEMBER` stays at 131 with `PARTIAL_TYPES=5`.
8. The batch consumes candidates by regenerated dependency rank, one at a time,
   regenerating the graph after every completion. An unsafe highest-ranked
   candidate is skipped with a recorded reason; it does not stop the batch.

## Qualified selected surface

Foundation 16 adds exactly these four types, all previously entirely missing:

- `Microsoft.Xna.Framework.Input.MouseState`, a sealed sequential value struct
  mapping to a Swift struct with 14 identities: the constructor, eight get-only
  properties, `GetHashCode`, `ToString`, `Equals(object)`, and the two equality
  operators. Its pinned constructor order places `middleButton` before
  `rightButton`; because both share a mapped type and a `_` label, the
  transposition is caught only by the registered
  `internalParameterOrderChecks` entry, which the self-test exercises for every
  adjacent pair. `GetHashCode` is a plain `Int32` XOR with **no**
  `SmartGetHashCode` zero substitution, and `ToString` emits buttons in the
  order Left, Right, Middle, XButton1, XButton2. No typed `Equals`, no
  `Equatable`/`Hashable` conformance, and no mutable property is added.
- Three ordinary CLR `Int32` enums with no `[Flags]` attribute in the pinned
  binary: `Media.MediaState`, `Media.MediaSourceType`, and
  `Audio.MicrophoneState`. `MediaSourceType`'s literals are non-contiguous
  (0 and 4) and no literal was invented to close the gap;
  `MicrophoneState.Started` is the zero literal.

`Microsoft.Xna.Framework.Media` gained its namespace marker.

Completing these four types claims no mouse device, cursor, microphone,
capture, media player, media library, or video capability.

Foundation 15 added exactly one type, previously entirely missing:

- `Microsoft.Xna.Framework.Graphics.PresentationParameters`, a public
  non-sealed CLR class with a public parameterless constructor, mapping to an
  `open` Swift class with 13 identities: `init()`, non-virtual `Clone()`, ten
  read/write properties, and the get-only `Bounds`. Its internal nested
  `Settings` value struct and `settings` field mirror the pinned `assembly`
  storage and stay out of the public Swift surface. `IsFullScreen` defaults to
  `true` per the pinned `ldc.i4.1`; nothing validates, clamps, or rejects any
  value; `Clone` is a wholesale value-struct copy that yields a base instance
  even from a derived one; there is no `Clear` member to implement.
  `DeviceWindowHandle` is pure managed descriptor state and is never
  dereferenced, validated against a window, resolved through SDL, or handed to
  CNA.

Foundation 14 added exactly these 25 types, all previously entirely missing:

- 19 ordinary CLR `Int32` enums → Swift `enum: Int32`: `GraphicsProfile`,
  `PresentInterval`, `VertexElementFormat`, `VertexElementUsage`,
  `CompareFunction`, `CubeMapFace`, `IndexElementSize`, `Blend`,
  `BlendFunction`, `CullMode`, `StencilOperation`, `TextureAddressMode`,
  `TextureFilter`, `GraphicsDeviceStatus`, `PrimitiveType`,
  `EffectParameterClass`, `EffectParameterType`, `Audio.SoundState`,
  `Audio.AudioChannels`.
- 3 `[Flags]` CLR `Int32` enums → Swift `OptionSet` structs:
  `ColorWriteChannels`, `ClearOptions`, `SetDataOptions`.
- 1 sealed sequential value struct: `VertexElement`.
- 2 pure abstract interfaces → Swift protocols: `IEffectFog`,
  `IEffectMatrices`.

No enum gained a `description`, `ToString`, `String`, predicate, alias,
`OptionSet` convenience, or native-conversion member, and no `None`, `Default`,
or `All` literal was invented. `VertexElement` gained no typed `Equals`
overload, no `Equatable`/`Hashable` conformance, and no static factory; its two
element-name tables are `private`, so neither element enum gained a public
string surface. The two protocols gained no default implementation, no
extension, and no XNA conformer.

No CNAShim declaration, native manifest row, native function, C layout,
callback, or constant was added, and the five runtime partials are untouched.

## Measurement status

- Pinned contract: 257 types / 2,964 members; contract SHA-256
  `7207908eb7926cc90a156d0370c907add4dda465421cea1cbec51afba2f97fdc`. The
  Foundation-15 entry was independently re-read and machine-compared against
  the pinned assembly IL for this milestone, as were all 25 Foundation-14
  entries before it.
- Formal projection: 257 Swift types / 2,887 Swift members.
- Compiler target: 103 types / 1,594 members; 98 complete, five partial, 154
  missing. Total diagnostics are 305. Normal strict remains red only for the
  deferred profile; leak-only is green.
- Verifier: 1,606 mutation/self-tests pass, up from 1,396. Every completed type
  is locally complete with zero diagnostics. Manual/applied allowlists and
  unmeasured structural categories are zero.
- Pure behavior: 1,493 XNA-derived observation/assertion sites with zero
  failures, up from 1,443. Swift projection qualification stays in separate
  tests and is not counted as XNA behavior.
- Dependency graph: node names are now mapped exactly as the strict verifier
  maps them, which removed six false-positive dependency-complete candidates
  caused by CLR nested and generic-collision names.
- Native ABI: 29 functions, 91 prototype positions, 91 C/Swift measurements,
  18 layouts, 2 callbacks, and 214 constants; header, library, and ABI mismatch
  counters are zero and unchanged.
- All earlier managed, GamePad, Keyboard, PackedVector, native lifecycle,
  template, archive, and isolated-consumer gates remain required and pass.

## Platform and release policy

Linux x86-64 with Swift 6.0.3 and exact CNA 0.7.0 HEADLESS/NULL is the only
qualified runtime. HEADLESS has no visible window, this host has no attached
controller, and the audio backend is NULL. Apple, Windows, and Web/Wasm remain
unqualified.

Completion requires debug/release builds and tests, warnings-as-errors, Symbol
Graph, verifier self-tests/strict/leak-only, pure behavior, unchanged full ABI,
GamePad and Keyboard regression, native stress, Swift ASan and TSan, unchanged
template 60/600, a clean exact source archive, isolated consumer,
`git diff --check`, one milestone commit for the whole batch, and the explicit
publication boundary. Work stops after selecting—but not starting—one
regenerated next closure.
