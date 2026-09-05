# CNA-Swift continuation handoff

> **Current as of Foundation 74.** The Foundation 30–36 handoff that used to be
> this file is kept below, under its own heading, because the measurements it
> records were real when it was written. `plan.md` remains the authority for
> project rules; this file is the *state of the work* and *what is left*.

## Where the work stands

Reproduce the numbers rather than trust them — and note that
`tools/status_gate/verify.py` now compares every one of them, in this file and
in `plan.md` and `README.md`, against the generated reports:

```bash
git rev-list --count origin/develop..HEAD
python3 tools/api_compat/verify.py --symbol-graph \
  .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json
python3 tools/status_gate/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --cna-include /path/to/cnanext/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
```

```text
791 tests, 0 failures (debug; release, ASan and TSan re-run at handoff)
TOTAL_DIAGNOSTICS=105   COMPLETE_TYPES=182   PARTIAL_TYPES=6
MISSING_TYPE=69  MISSING_MEMBER=32  OVERLOAD_MAPPING_MISMATCH=4
every category that would mean DISAGREEMENT with XNA: 0
BOUND_FUNCTIONS=317  PROTOTYPE_TYPE_POSITIONS=1081  LAYOUTS=54  ABI_MISMATCHES=0
PROJECTION_MUTATIONS=290 (last full run 137, CAUGHT=135)
5 withdrawn with the reason written where they stood, 1 no-op replaced
NATIVE_ABI_MUTATIONS=14 CAUGHT=14
MESSAGE_COVERAGE_FINDINGS=0 over 1,614 implemented members
API_COMPAT_SELF_TESTS=2443  AUDIT_SELF_TESTS=80  BCL_MUTATION_SELF_TESTS=462
RESOURCE_STRINGS_REPRODUCED=73  ACCESSOR_SELF_TESTS=41
```

**Every remaining diagnostic is an absence.** Nothing implemented disagrees
with the pinned metadata.

## Five facts that bound everything below

Measured, not assumed. A plan that ignores one of these will produce work that
cannot be verified.

1. **No pixel readback exists.** `cna_graphics_device_get_backbuffer_data_window`
   and `cna_texture2d_get_data_rgba8` both answer `CNA_RESULT_NOT_SUPPORTED` on
   a render target and the back buffer alike — `build-probe/f53_readback.c`,
   `build-probe/f53_rtread.c`. **No test here can assert that a pixel ended up
   anywhere.** Geometry, blending, sampling and sort order are unverifiable in
   this environment and must be recorded as such, never asserted from a call
   that returned zero.
2. **Texture *data* is observable.** A typed transfer round-trips exactly
   (`build-probe/f56_texdata.c`), which is why Foundation 57's tests assert
   texel values. This is the one place pixel-level evidence exists.
3. **Only `SurfaceFormat.Color` can be created.** Nineteen of the twenty
   formats answer `NOT_SUPPORTED` — `build-probe/f55_grants.c`. Anything
   depending on another format is unreachable here.
4. **A `GraphicsDevice` is a per-callback capability token**, not an identity
   (`build-probe/f42b_identity.c`). Device-owned state belongs on
   `RuntimeState`; a stored facade goes stale between callbacks. Foundation 54
   learned this again the hard way.
5. **CNA's device is only real inside a lifecycle callback.** Outside one,
   `cna_graphics_device_manager_get_device` answers `INVALID_STATE`.

## What is left, classified

### The 32 missing members, which the roadmap does not show at all

Every milestone above is named after a missing *type*. Thirty-two members are
missing from types that **already stand**, and nothing in this document lists
them, so they are invisible to milestone planning:

| owner | members |
|---|---:|
| `GraphicsDevice` | 20 |
| `GraphicsDeviceManager` | 5 |
| `Game` | 2 (`Window`, `Content`) |
| `SpriteBatch` | 2 (the two longest `Begin` overloads) |
| three serialization constructors | 3 |

**`GraphicsDevice`'s twenty are a coherent milestone on their own**, and most of
it is already measured as unblocked. Foundation 60's re-measurement recorded
`Present` and `Reset` as *"both accepted"* — they were never implemented, and
the entry has read "not blocked, and now ordinary work" for fourteen milestones.
With them come `PresentationParameters`, `DisplayMode`, `Adapter`, `IsDisposed`,
the disposal pair and six events (`Disposing`, `ResourceCreated`,
`ResourceDestroyed`, `DeviceLost`, `DeviceReset`, `DeviceResetting`).

Three of the twenty stay blocked and are the same three as ever: the
`GetBackBufferData` overloads, which `cna_graphics_device_get_backbuffer_data_window`
still answers `NOT_SUPPORTED`. That is Foundation 53's first bounding fact and
nothing here weakens it.

**Ordering.** `Reset(_:presentationParameters:graphicsAdapter:)` and
`GraphicsDevice.__ctor(adapter:graphicsProfile:presentationParameters:)` both
name `GraphicsAdapter`, and `GraphicsDeviceManager`'s five all name
`GraphicsDeviceInformation`. So the adapter trio comes first and unblocks
twenty-five members across two standing types — which is a better return than
its own eighteen suggest, and the reason to take it before `Model`.

The three serialization constructors take `SerializationInfo` and
`StreamingContext`, so they are a `System.Runtime.Serialization` admission and
belong with whatever milestone first needs that namespace, not on their own.

### How much is actually left, counted

| family | types | members |
|---|---:|---:|
| `Media` | 19 | 204 |
| `Audio` | 10 | 127 |
| `Graphics`/`Framework` | 10 | 62 |
| `Design` | 13 | 53 |
| `Content` | 6 | 39 |
| `Model` | 8 | 36 |
| `Storage` | 2 | 31 |
| `GamerServices` | 1 | 3 |
| **total** | **69** | **555** |

Plus **32 missing members in types that already stand**, so 587 members in all.

Against 2,313 members across 182 complete types already projected, that is
**roughly four fifths of the surface done by member count** — and the remainder
is far from evenly spread: `Media` and `Audio` alone are 331 of the 555, while
`Storage`, `GamerServices` and `Model` together are 70.

### The shape of every remaining family, before any of them starts

Foundation 74 lost time designing `Mouse.WindowHandle` as a throwing forward
before the gate pointed at the pinned fallibility table and refused it. That
table can be asked the question **for everything left at once**, and the answer
decides each milestone's architecture before a line of it is written:

| family | missing types | accessors | fallible getters | shape |
|---|---:|---:|---:|---|
| `Media` | 19 | 94 | **68** | throwing forwards |
| `Design` | 13 | 0 | 0 | methods only — no accessor at all |
| `Audio` | 10 | 40 | 7 | mostly snapshot |
| `Model` | 8 | 25 | 2 | **snapshot** |
| `Content` | 6 | 7 | 0 | **snapshot** |
| `Graphics` (rest) | 6 | 17 | 1 | mostly snapshot |
| `Framework` | 4 | 16 | 1 | mostly snapshot |
| `Storage` | 2 | 6 | 4 | throwing forwards |
| `GamerServices` | 1 | 0 | 0 | methods only |

**An infallible getter cannot call a CNA route**, because every route can fail
and a Swift getter cannot throw. So a family whose accessors are infallible has
to read its values from CNA **once** — at construction or refresh — and cache
them, with every getter a plain field read. That is what `GraphicsAdapter` (15
of 15 infallible) and `Model` (23 of 25) both require, and it is the opposite of
what `Media` requires, where two thirds of the getters throw and forwarding is
the faithful shape.

Two things this table is not. It reads **getters** only, so a fallible setter on
an otherwise infallible property still needs the deferred-write treatment
`Mouse.WindowHandle` got. And it counts accessors, not difficulty: `Design` has
none at all and is still the milestone that drags in `System.dll`.


### ACTIONABLE_LOCAL — upstream support exists, the managed side is the work

CNA declares **4,076** distinct `cna_*` symbols. Mapping all 72 still-missing
types onto their route families — `docs/generated/cna-route-map.txt`, and the
reasoning in `docs/frontier-remeasurement-foundation-60.md` — leaves **no family
without native support** except the ones that need none. Route existence is not
capability; but nothing below is blocked upstream, and the blocker in every row
is that the managed type is not projected yet, which is ordinary work:

**The near-term order**, which is finer than the single row below. Grouping the
seventy-two by what makes one coherent milestone:

| milestone | types | note |
|---|---:|---|
| `ContentManager` + `ContentReader` family | 6 | sized below; `.cnj` fixture path known |
| the `Model` family | 13 | `Model`, `ModelBone`, `ModelMesh`, `ModelMeshPart`, four collections and their four enumerators — one coherent unit, and the four collections already have `CNAReadOnlyCollection` as their base |
| `GraphicsAdapter` + `GraphicsDeviceInformation` + `PreparingDeviceSettingsEventArgs` | 3 | one cluster: the adapter and the settings event that carries it |
| `GameWindow`, `TitleContainer`, `FrameworkDispatcher` | 3 | small and standalone; `GameWindow` is under the no-visible-window rule |
| `OcclusionQuery` | 1 | standalone |
| `Storage` | 2 | `StorageDevice`, `StorageContainer` — project-controlled temporary roots only, never user documents |
| `Audio` | 10 | the XACT five, the `SoundEffect` three, `Microphone`, `RendererDetail` — see the microphone rule above |
| `Design` | 13 | costed below; no CNA route at all |
| `Media` | 19 | sized below; probe first |

**Where the seventy-two sit**, so the size of what remains is not guessed:

| namespace | types |
|---|---:|
| `Media` | 19 |
| `Design` | 13 |
| `Audio` | 10 |
| `Graphics` | 10 |
| `Content` | 6 |
| `Microsoft.Xna.Framework` | 5 |
| `Storage` | 2 |
| the four `Model*Collection` enumerators | 4 |
| `GamerServices`, `Input`, `Input.Touch` | 3 |

`Media` and `Design` together are nearly half of it, and neither has been
started. `Design`'s thirteen converters need no CNA route at all — they need
the `System.dll` `ComponentModel` closure admitted, which is recorded below as
its own decision. **`GLOBAL_ACTIONABLE_LOCAL = 0` means all seventy-two**, so
the road is long: this is a per-namespace campaign, not a handful of milestones.

| Next | Closes | Notes |
|---|---|---|
| `ContentManager` (+ `Game.Content`) | 2 types, 1 member | **The next milestone.** 33 routes. It inherits a specific question from Foundation 70: whether a compiled `.xnb`'s character table arrives sorted, which `SpriteFont`'s binary search requires and which `cna_sprite_font_create` does not guarantee. |

### The mutation harness had no deadline, and one mutation hung a full run

`from-type-size-test-reads-the-wrong-size` inflates a registered vertex type's
measured size by four. The suite it produces does not fail — it **hangs**, and
`run_tests` had no timeout, so a 278-mutation run sat on it indefinitely with
the mutation applied and nothing compiling. That is worse than a survivor: a
survivor is at least reported.

The harness now has `TEST_TIMEOUT_SECONDS = 600` and a third verdict. A
timed-out mutation is scored **`HUNG`**, not `CAUGHT`, because the two are
different facts about the projection — one says a test disagreed, the other
says the projection stopped answering — and the deadline is deliberately
generous: it is the line between "slow" and "never", not a performance budget.
`subprocess.run`'s timeout kills the wrapper but not the test binary it
spawned, so that is killed explicitly too.

**One entry in the run that produced this note is misleading, and this says
so.** That run began before the deadline existed; its line for
`from-type-size-test-reads-the-wrong-size` reads `CAUGHT`, and the reason it
does is that the hung binary was killed by hand after about seven minutes, not
that an assertion failed. A run started after this change reports it as `HUNG`.

### The small standalone types, sized

Seven types that no larger family carries, with their member counts and the CNA
routes behind them:

| type | members | routes | note |
|---|---:|---:|---|
| `GameWindow` | 20 | 19 | `abstract`-shaped in XNA, and under the **no-visible-window rule** |
| `GraphicsAdapter` | 18 | 15 |
| `GraphicsDeviceInformation` | 7 | — | pure managed: it carries an adapter, a profile and presentation parameters |
| `OcclusionQuery` | 6 | 8 | standalone |
| `PreparingDeviceSettingsEventArgs` | 2 | — | pure managed; it is the event payload that carries the one above |
| ~~`TitleContainer`~~ | 1 | 1 | **landed, Foundation 73** |
| ~~`FrameworkDispatcher`~~ | 1 | 1 | **landed, Foundation 72** |
| `Input.Mouse` | 3 | 3 | `MouseState` and `ButtonState` already stand |

`TitleContainer` and `FrameworkDispatcher` were sized here as the cheapest two
types left, one member and one route each. **One of those two sizings was
wrong, and the way it was wrong is worth keeping.** `FrameworkDispatcher` was
exactly what it looked like. `TitleContainer` was not: its single public member
is 213 bytes of IL over three private helpers totalling 383 more, it needed an
`System.IO` exception family admitted, and it needed a decision about a branch
CNA cannot distinguish. **A member count is not a milestone size.** Read the IL
of the member before believing the count — that reading is what stopped
`TitleContainer` from being rushed in as an appendix to Foundation 72.

**The next milestone is `Input.Mouse`**, and it is measured rather than
guessed:

* Three members — `GetState()`, `SetPosition(Int32, Int32)` and the static
  `WindowHandle` property — and `cna_mouse_get_state`, `cna_mouse_set_position`
  and `cna_mouse_get_window_handle`/`cna_mouse_set_window_handle` behind them.
* `MouseState` (14 members) and `ButtonState` **already stand**, so this is the
  last piece of its own family rather than the first.
* **There is no managed half at all.** `Mouse.GetState`'s IL is Win32 P/Invoke
  end to end — `GetCursorPos`, then `ScreenToClient` when a window handle is
  hooked, then `GetAsyncKeyState` per button. Nothing in it is a managed
  decision this binding could reproduce, so the milestone's honest claim is the
  narrow one, as Foundation 72's was.
* `WindowHandle` is `System.IntPtr`, which projects the way
  `GraphicsDevice.Present(overrideWindowHandle:)` already projects it.

**The hard part is WHEN the snapshot is taken, not that it is one.** Every one
of the fifteen `cna_graphics_adapter_*` routes takes a `CNA_Handle
graphics_device`, and this project's fifth bounding fact is that CNA's device is
only real inside a lifecycle callback. XNA's `Adapters` and `DefaultAdapter` are
static **and infallible**: they read `pAdapterList`, a static field built once by
enumeration, and they answer anywhere — before a game exists, after it is gone.

Those two cannot both be satisfied. The projection can only populate the list
from inside a callback, so **before any callback has run, `Adapters` answers an
empty collection where XNA answers the machine's adapters.** That is a real
divergence, it is forced, and it has to be written into the type's
documentation and asserted by a test rather than discovered by a consumer.

`CNA_GraphicsAdapterInfo` covers the identity properties in one read —
`adapter_index`, `is_default_adapter`, `is_wide_screen`, `use_null_device`,
`use_reference_device`, `vendor_id`, `device_id`, `revision` — with
`copy_description` and `copy_device_name` for the two strings, so a whole
adapter is four routes plus the display modes. Note that CNA documents
`revision` as **always zero**, which is a value the projection must pass through
rather than treat as missing.

**`GraphicsAdapter` is a SNAPSHOT, and the fallibility table decides that
before a line is written.** All fifteen of its accessors are pinned
`IL_NO_FAILURE_PATH` — every one, including both static ones — so not a single
Swift getter here may throw. The IL is plain field reads: `get_VendorId` is
`ldfld _vendorId`, `get_Adapters` is `ldsfld pAdapterList`. XNA populates an
adapter once by enumeration and its properties read fields.

So the projection must read every value from CNA **once**, at construction or
refresh, and cache it — exactly the shape `Mouse.WindowHandle` was forced into
in Foundation 74, but for a whole type instead of one property. Designing it as
throwing forwards first and letting the gate reject it would waste the milestone;
this is written down so it is not discovered twice.

The two `Query*` methods are the exception: they are **methods**, not accessors,
so they may throw — and each carries three `out` parameters
(`SurfaceFormat&`, `DepthFormat&`, `Int32&`), which is the ref/out projection
rule's largest case so far.

All four types it depends on already stand — `DisplayModeCollection`,
`DisplayMode`, `PresentationParameters` and `GraphicsProfile` — and CNA
publishes fifteen `cna_graphics_adapter_*` routes covering every member,
`set_device_preferences` included for the two static flags.

`GraphicsDeviceInformation` and `PreparingDeviceSettingsEventArgs` need **no CNA
route at all** — they are managed carriers — but they depend on `GraphicsAdapter`
existing first, which is why the three go together as one milestone.

### `Storage` — small, but its root is derived, not chosen

Two types, 35 routes: `storage_device` 11, `storage_container` 24.

**The constraint is satisfiable, but not the obvious way.** The rule for this
work is project-controlled temporary roots only, never user documents — and the
ABI offers no route that sets a root. It offers
`cna_storage_set_app_name_ext(app_name)`, "expected once at startup, before any
storage access", from which the root is **derived**, plus
`cna_storage_copy_root_ext` to read back what was derived. So the shape a test
must take is: set a test-only application name, read the root back and **assert
where it landed before writing anything**, then delete what it created.

That root is a per-application user-data directory, not `/tmp`. It is not user
documents and the name is ours, which satisfies the rule — but a session that
assumes it can point storage at a scratch directory will not find a route for
it, and a session that writes first and looks later has already broken the rule.

**One projection decision is visible up front.** XNA's storage API is the
fake-async `BeginXxx`/`EndXxx` pair, and CNA "completes synchronously … this
callback is invoked before it returns so the canonical completion contract is
preserved". The `IAsyncResult` shape XNA exposes therefore has to be projected
over a call that has already finished by the time it returns.

### `Audio` splits in two, and only one half is reachable here

Ten types, and the line between them is whether the asset can be
project-authored.

**Reachable, and testable from bytes this repository can write.**
`cna_sound_effect_create_pcm16(game, create_info, pcm_bytes, byte_count, out)`
builds a `SoundEffect` from **raw PCM** — no bank, no proprietary file, nothing
to download. With it come `SoundEffect` (42 routes), `SoundEffectInstance`
(16) and `DynamicSoundEffectInstance` (12). There is also
`create_from_encoded_ext` for a WAV. Three of the ten types, and the natural
first Audio milestone.

**Blocked on an asset that must not be downloaded.**
`cna_audio_engine_create(game, settings_file, out_engine)` opens an XACT engine
**from a path to an `.xgs` settings file**, answering `CNA_RESULT_IO` for a
missing one. `AudioEngine`, `SoundBank`, `WaveBank`, `Cue` and `AudioCategory`
— five of the ten — need `.xgs`/`.xsb`/`.xwb` files, and the standing rule is
that proprietary XACT banks are not to be downloaded. Whether this project can
*author* a legal `.xgs` triple from scratch is **an open question nobody has
asked yet**; it is the whole blocker for that half, and it should be asked
before the half is planned, not during it.

`Microphone` (18 routes) is under the do-not-record rule at the top of this
section. `RendererDetail` is enumeration and should come free with the engine.

**And the capability question is unasked for all of it.** Whether this HEADLESS
host has any audio backend at all — whether `create_pcm16` even succeeds — is
unmeasured, exactly as it is for `Media`. One probe answers both namespaces and
should precede either.

### The `Model` family, sized — and buildable without content

**Twelve types and 48 members in the family, of which 8 types and 36 members
remain** — corrected at Foundation 74. The earlier count, "thirteen types, 36
members", had the type count wrong and the member count right for the wrong
reason: it missed the four `+Enumerator` nested types at three members each, and
those four **already stand**, so 48 − 12 = the 36 still to do. `Model` 8, `ModelMesh` 7,
`ModelBone` 5, `ModelMeshPart` 8, the four collections 3+3+1+1, four
enumerators 3 apiece. Still small for its place on the roadmap, because most of
it is properties.

**And those properties decide the architecture, exactly as `GraphicsAdapter`'s
do.** Of the family's 29 accessors, **27 are pinned infallible** and only two
getters may throw: `ModelBoneCollection.Item` and `ModelMeshCollection.Item`,
both `IL_DIRECT_THROW` raising `KeyNotFoundException` — the name-keyed lookups.
So `Model`, `ModelMesh`, `ModelBone` and `ModelMeshPart` are **snapshots**: read
from CNA once at construction and cached, with every getter a plain field read.
Only the two name lookups are throwing members. Do not design this family as
throwing forwards; the gate will reject it, as it did for `Mouse.WindowHandle`
in Foundation 74.

**It can be built in memory.** `cna_model_create(graphics_device, bones,
bone_count, meshes, mesh_count, out_model)` takes arrays of bone and mesh
handles, with `cna_model_bone_collection_create` and siblings alongside — so a
`Model` needs no `.xnb` and no content pipeline, exactly as
`cna_sprite_font_create` freed `SpriteFont`. There are also
`cna_model_create_default` and `cna_model_create_with_parents`. That makes the
whole family testable here, and it is the reason to take it early rather than
after `ContentManager`.

CNA publishes **231 routes** across the four families — `model` 134,
`model_mesh` 50, `model_mesh_part` 30, `model_bone` 17 — many of them `_ext`.
`cna_model_draw` exists; what a returning draw means is Foundation 68's answer
and no more.

**The BCL work is already done.** All four collections derive from
`ReadOnlyCollection<T>`, which is admitted and projected as
`CNAReadOnlyCollection`, and `ModelBoneCollection` and `ModelMeshCollection`
add a `TryGetValue(name:value:)` each — the `ref`/`out` shape this project
already maps. `ModelMeshPart.Effect` is the only settable reference among them
and lands on the `Effect` that Foundation 67 built.

### `Media`, the largest block, sized enough to start

Nineteen types — `MediaPlayer`, `MediaLibrary`, `MediaQueue`, `MediaSource`,
`Song`, `Video`/`VideoPlayer`, `Picture`, and the `Album`/`Artist`/`Genre`/
`Playlist` families with a collection apiece. Nearly all of them read.

**Upstream support is not the blocker.** Counted from the pinned 0.21.0
headers:

```text
picture 45   song 33   media_player 31   album 25   video_player 23
media_library 21   artist 18   genre 18   playlist 18   media_queue 10
song_collection 8   media_source 6
```

Something over 250 routes, and the documentation reads like an implementation
rather than a declaration: `cna_media_library_create_from_source` describes
borrowing a source, copying its kind and name, and refusing a non-local-device
source with `NOT_SUPPORTED` "exactly as the canonical constructor refuses it".
No placeholder language anywhere in `media_player.h` — unlike
`cna_content_manager_create_resource`, which says outright that every load
through it fails.

**The unknown is capability, not existence, and it is unmeasured.** Route
existence is not capability — this file's own rule — and nothing has yet asked
whether a `MediaLibrary` on this HEADLESS host enumerates any source, whether
it holds any song or picture, or whether `MediaPlayer` can play to a device
that has no audio output. **A probe answers all three and is the milestone's
first step**, before a line of Swift. If the library comes back empty, the
namespace is still projectable but its tests measure refusals rather than
playback, which is a different milestone from the one the route count suggests.

Do not record `Media` as blocked on the strength of "HEADLESS has no output" —
that inference was carried into eight entries once before and three of them had
never been asked. See the BLOCKED list below.

### `ContentManager`, sized

Measured while Foundation 71's mutations ran, so the next session starts from
facts rather than from the roadmap's one-line guess.

**The type.** Ten members: two constructors, `Dispose()`, `Dispose(Boolean)`,
`Unload()`, the generic `Load<T>`, the protected `ReadAsset<T>` and
`OpenStream`, and `ServiceProvider` / `RootDirectory`. CNA publishes **34**
`cna_content_manager_*` routes, six of them typed loaders — `texture2d`,
`texture_cube`, `sprite_font`, `effect`, `model`, `sound_effect`. Four of those
six have their XNA type projected today; `Model` and `SoundEffect` do not.

**The other five `Content` types, sized.** `ContentReader` is 20 members and
`sealed`, deriving from `System.IO.BinaryReader` — a BCL base that is **not
admitted** and is the family's largest unknown. `ContentTypeReader` is 6,
`ContentTypeReader<T>` 3 (a generic class, which the verifier can express since
Foundation's generic-method repair), `ContentTypeReaderManager` **1**, and
`ResourceContentManager` 2.

`ResourceContentManager` should be taken **last or not at all for now**: its
constructor takes a `System.Resources.ResourceManager` (21 members, mscorlib,
unadmitted), and the route behind it — `cna_content_manager_create_resource` —
is the declared placeholder whose every load returns `CNA_RESULT_IO`. Projecting
it would mean admitting a BCL family to reach a type that cannot load anything.

So the first milestone is really **`ContentManager` alone**, with
`ContentTypeReaderManager` (one member) beside it if convenient; `ContentReader`
is a second milestone gated on deciding what to do about `BinaryReader`.

**And that gate is measured too.** `System.IO.BinaryReader` is **28 members**,
a class, unsealed — comparable to `TypeConverter`'s 39 and well under
`StringBuilder`'s 65. Its own base dependency, `System.IO.Stream`, is 28
members and **abstract**, and the project already maps `Stream` globally to
`Foundation.InputStream` for value positions. So the decision is not "is
`BinaryReader` too big" — it is whether a CLR *base class* that Swift must
inherit from can sit on a Foundation stream, which is a different question from
the value mapping that already exists and the one this milestone actually has
to answer. `measuredSupportBaseProjections` is where a base like that is
declared, and it currently holds eight entries, none of them a stream.

**Two things must be decided before any code.**

* **`System.IServiceProvider` has no mapping**, and it is needed in three
  places: both `ContentManager` constructors, its `ServiceProvider` property,
  and `ResourceContentManager`'s constructor. Measured from mscorlib, it is a
  **one-member interface** — `GetService(Type) -> Object` — and under this
  project's existing `System.Type -> Any.Type` and `System.Object -> Any?`
  mappings that is exactly the signature `GameServiceContainer.GetService`
  already has:

  ```swift
  public final func GetService(_ type: Any.Type) -> Any?
  ```

  So the admission is one protocol with one requirement and a conformance that
  needs no new code. It still goes through the measured act `StringBuilder`
  did — authority, pinned shape, `bclSupportContract` — but it is a small one,
  and `GameServiceContainer` conforming to it is the check that it was
  projected right.
* **`System.IO.Stream` needs nothing new.** It maps globally to
  `Foundation.InputStream`, and the split Foundation imposes is already handled
  where it bites: `streamDirectionParameters` overrides the global mapping for
  `Texture2D.SaveAsPng` and `SaveAsJpeg`, whose `stream` is written and so must
  be an `OutputStream`. `ContentManager.OpenStream` **returns** a stream and
  opens an asset for reading, so the global mapping serves it unchanged and no
  override is needed. Worth knowing that the override mechanism is
  parameter-only — a return position that needed the write direction would have
  nowhere to say so — but nothing here does.

**Content exists to test against, and it is not `.xnb`.** There is no `.xnb`
file anywhere on this machine, and `cna_content_manager_create_resource` — the
`ResourceContentManager` mapping — is a declared placeholder whose every load
returns `CNA_RESULT_IO`. But `load_sprite_font` "reads both the `.xnb` font
container and CNA's own `.cnj` font descriptor", and `.cnj` is JSON that
`cna_content_manager_load_foreign_ext` builds an object from. **A
project-authored `.cnj` is a legal fixture** and is how this milestone gets
tested.

**The fixture's shape, and where the shape came from.** A SpriteFont `.cnj` is
JSON of the form `{"cnjVersion":1,"type":"SpriteFont", …}` — the envelope is
sampled by `tests/assets/.../curve.cnj` — carrying `textureName` (a sidecar
image), `lineSpacing`, `spacing`, `defaultCharacter` and a `glyphs` array whose
entries are `character`, `source`, `crop` and `kerning`. That maps one-for-one
onto `CNA_SpriteFontGlyph`, so the fixture is a small PNG plus a descriptor.

**That schema is engineering guidance, not authority, and was read from a
moving tree.** It comes from `CnjContentPipeline.cpp`'s `ImportSpriteFont` in
`cnanext` — which is the BUILD-TIME pipeline, while the runtime loader is
whatever `cna_content_manager_load_sprite_font` uses. The pinned header says
that route reads `.cnj` directly; whether it shares
`ReadCnjSpriteFontDescription` is likely and **unverified**. Confirm against a
real load before trusting a field name, and remember `cnanext` moved under this
session once already.

**It answers Foundation 70's open question.** Whether a loaded font's character
map arrives sorted — which `SpriteFont`'s binary search requires and
`cna_sprite_font_create` does not guarantee — becomes answerable the moment a
`.cnj` font loads. The invariant check added in Foundation 70 will say so
loudly either way.

**One projection decision is already visible.** `load_sprite_font` hands back
**two owned handles**, font and atlas, because "handing back only the font
would leave the atlas alive but unnameable". XNA's `Load<SpriteFont>` returns
one object, so the atlas attaches to the `SpriteFont` — which is exactly the
`texture` field it already holds, and the destroy-order rule CNA imposes is the
one Foundation 70 already reproduces.

### What `StringBuilder` cost, and what it left behind

Admitted in Foundation 71. The sizing recorded here beforehand held up: 65
visible members pinned as the authority record, 14 projected, the `[UInt16]`
store, and the two IL asymmetries — the indexer's two accessors raising
different exception types, and `set_Length` naming `"value"` for both refusals
with two different keys.

**Two things it taught that the sizing did not predict.** Every growing member
is fallible for a reason its own body does not show: `ExpandByABlock` raises
`ArgumentOutOfRangeException("requiredLength", …)` past `MaxCapacity`, so a
plain `Append` throws and the parameter name is one no caller ever passes. And
two of the messages were transcribed wrong in the first draft — mscorlib says
"MaxCapacity must be one or greater.", not "…greater than zero." Extract every
message; never write the plausible one.

### The BLOCKED list, re-measured at Foundation 60 — status at Foundation 74

**Read the "not blocked" half as a to-do list, not as a report.** Fourteen
milestones on, four of its seven entries have landed and three have not, and the
wording did not distinguish "we measured that it works" from "we built it":

| entry | status at Foundation 74 |
|---|---|
| `GraphicsDevice.GraphicsProfile` | **landed**, Foundation 62, with the pinned `ProfileCapabilities` table |
| `DisplayMode`, `PresentationParameters` | **landed** — both types stand |
| `TextureCollection` | **landed**, Foundation 66 |
| Audio, Media, Touch, Storage, GamerServices routes | measured only; **none of the five families is projected** |
| `GraphicsAdapter` | **not built** — 18 members, and the next milestone |
| `GameWindow`, `Game.Window` | **not built** — 20 members under the no-visible-window rule |
| `GraphicsDevice.Present`, `Reset` | **not built** — measured "both accepted" and left there for fourteen milestones |

That last row is the one worth remembering. *"Both accepted"* is a statement
about the runtime, and it was silently read as though the members existed. They
are in the 32-member list above.


Most of what stood here was **inference, not measurement**: "HEADLESS has no
window" was carried into eight entries, three of which had never been asked.
`docs/frontier-remeasurement-foundation-60.md` asks them.

Not blocked, and now ordinary work:

* **`GraphicsDevice.GraphicsProfile`** — `cna_graphics_device_get_graphics_profile`
  answers `Reach`. It is the only blocker the six deferred `Texture2D` profile
  messages, and the three new buffer ones, name. What is still needed is the
  pinned `ProfileCapabilities` table, read out of the IL.
* **`GraphicsAdapter`, `DisplayMode`, `PresentationParameters`** — the device
  answers its adapter index, an 800x480 display mode, and its presentation
  parameters. Whether a fallible route can serve `PresentationParameters`'
  `IL_NO_FAILURE_PATH` getter is a question about *when* it is read, not about
  whether the value exists.
* **`GameWindow`** and `Game.Window` — nineteen routes, all taking the game
  handle. Title and `AllowUserResizing` round-trip; the client rectangle is the
  empty one a headless session has, which is what HEADLESS means.
* **`GraphicsDevice.Present`, `Reset`** — both accepted.
* **`TextureCollection`** — landed in Foundation 66, exactly as CNA's header
  prescribed: cache what you bind and answer from the cache, using `bound` to
  tell "something else owns this slot" from "the slot is empty".
* **Audio, Media, Touch, Storage, GamerServices** — no longer unmeasured: 20-45
  routes per family, listed in `docs/generated/cna-route-map.txt`.

Still blocked, and now measured rather than inferred:

* **`GraphicsDevice.GetBackBufferData`** — the size query answers 384,000 with
  `CNA_RESULT_CAPACITY` and the read answers `NOT_SUPPORTED`, before and after a
  clear that succeeds. Foundation 53's first bounding fact stands, and
  Foundation 68 landed the draws **without** weakening it: a draw that returns
  is a draw the device accepted, and no test claims a pixel arrived anywhere.
* **`GamePad.InvalidController`, `Keyboard.CouldNotReadKeyboard`** — the
  error-channel halves that need a native input failure this environment cannot
  produce. CNA already matches the "not connected" half.

### `Microsoft.Xna.Framework.Design` — no longer out of scope, and now costed

The thirteen converters are pure managed and need no CNA route at all. What they
need is the minimal authentic `System.dll` `ComponentModel` closure, admitted to
the same non-vacuous standard `mscorlib` was. `System.dll` is on disk and its
identity is established.

**The closure, measured** — every non-trivial type the thirteen converters
mention in a signature, with its visible-member count:

| type | assembly | members |
|---|---|---:|
| `ComponentModel.TypeConverter` | System.dll | 39 |
| `ComponentModel.PropertyDescriptor` | System.dll | 30 |
| `ComponentModel.PropertyDescriptorCollection` | System.dll | 21 |
| `ComponentModel.ITypeDescriptorContext` | System.dll | 5 |
| `ComponentModel.ExpandableObjectConverter` | System.dll | 3 |
| `Globalization.CultureInfo` | mscorlib | 43 |
| `Collections.IDictionary` | mscorlib | 10 |

About 151 members over seven types in two assemblies — roughly two and a half
`StringBuilder`s, plus **System.dll's first-time admission**, which `mscorlib`
already went through and `System.dll` has not.

One thing makes it smaller than that sounds: admission pins the full shape as
the authority record and projects a **measured subset**, as `CNAList` is sixteen
of `List<T>`'s fifty-two.

**And one thing makes it bigger, corrected at Foundation 74.** This section used
to claim that `CultureInfo` is *"only ever an opaque parameter here: every
converter takes it as `ConvertFrom(context, culture, value)` and none reads
it"*. **That is false**, and it was the load-bearing half of the estimate. The
IL reads it eight times:

```text
CultureInfo::get_TextInfo()      x4  -> TextInfo::get_ListSeparator()
CultureInfo::get_CurrentCulture() x4  -> and then the same TextInfo path
```

Every converter that parses or formats a multi-component value — a `Vector3`
from `"1, 2, 3"`, a `Matrix` from sixteen — splits and joins on the **culture's
list separator**, and falls back to `CurrentCulture` when the caller passes
none. So `Globalization.TextInfo` joins the closure, `ListSeparator` is
behaviour that must be reproduced rather than a type that must exist, and the
milestone carries a genuine culture dependency instead of an opaque parameter.

The lesson is the same one `TitleContainer` taught in Foundation 73 and it is
now recorded twice: **a signature does not tell you what a member reads.** Grep
the IL for calls *on* the parameter type before believing any sizing that calls
it opaque.

`ITypeDescriptorContext` is mentioned 38 times and is a five-member interface;
`CultureInfo` 21 times; `IDictionary` 12. XNA's own `MathTypeConverter` is the
shared base of all thirteen and is eight members.

## Rules a next session must not quietly break

**Before the engineering rules, the three standing safety constraints**, which
are binding regardless of what a milestone would be convenient. They were given
for this work and are recorded here because a type name in a list does not
carry them:

* **Do not record a physical microphone.** `Microphone` is among the ten
  missing `Audio` types, and projecting it must not open the default capture
  device — not to test it, not to "see what happens". That needs a NEW explicit
  authorization from the user, per instance. Do not modify PulseAudio or
  PipeWire host configuration either.
* **No visible windows on the user's physical desktop.** `GameWindow` is among
  the five missing root types and is exactly the temptation. Xvfb, a private
  `DISPLAY`, or the SDL dummy video driver — the environment this session has
  used throughout.
* **Do not push.** Commit freely; pushing needs a new explicit instruction.

And one that is not about safety but about authority: **do not download
proprietary XACT banks** for the `AudioEngine`/`SoundBank`/`WaveBank` work.
Project-authored legal fixtures only, as Foundation 70's `.cnj` font will be.

These are the engineering ones that cost the most to relearn:

1. **A gate not demonstrated to fail is not evidence.** Every mutation must be
   shown to be caught; one that survives is either a missing test or an
   unfalsifiable claim, and an unfalsifiable one is **withdrawn with the reason
   written where it stood**. Foundations 45, 48, 53 and 55 each have one.
2. **Run a baseline first.** An ad-hoc mutation check against a tree that does
   not compile reports CAUGHT for everything. That happened in Foundation 51
   and the result was believed for a minute.
3. **The two mutation harnesses take `.mutation-gate.lock`.** They both edit
   files under `Sources/`; running them together makes one compile the other's
   defect and report a CAUGHT it did not earn. **The lock does not protect an
   ordinary build**, and nothing else does either: running `swift build -c
   release` beside `tools/native_abi/mutations.py` in Foundation 65 produced
   `input file 'NativeFunctions.swift' was modified during the build` and a
   `signal 6`. Nothing was corrupted, but a whole release-and-sanitizer pass was
   wasted. Run a mutation harness alone.

   The same contention shows up a second way, and it looks worse than it is:
   `NativeLifecycleTests`' two frame-count assertions are **wall-clock**, and a
   loaded machine drops frames. Running the suite beside a mutation harness in
   Foundation 66 produced 597 frames where 599 are required, and 58 where 59
   are. Both passed immediately on an idle machine. A red frame count is the
   first thing to re-run before believing it.
4. **Grep the neighbouring symbols before calling something upstream-blocked.**
   `cna_sprite_batch_begin`'s doc comment describes that route, not the API;
   `begin_with_states` was there all along and Foundation 53 wrote the wrong
   verdict because of it.
5. **A route with no consuming member is not bound**, and a mirrored structure
   with no route is the same unearned count. Three have been *un*bound so far.
6. **Read the IL of every member you implement, including the ones already
   implemented.** Eight defects in four milestones were found that way and none
   by a failing test — the four newest are Foundation 64's, all in a `Texture2D`
   that had been green since Foundation 59. `tools/api_compat/message_coverage.py`
   catches the message half of it automatically; nothing yet catches the rest.
   And note what Foundation 64 also found: that gate's call walk could not see a
   call to a **generic** method, so the whole `CopyData<T>` family was invisible
   to it while it reported `PASS`. A gate that reads less than it claims is the
   same failure one level up, and the same remedy applies — a mutation that
   makes the reading fail.
7. **`plan.md` and the diagnostic block in `README.md` must move with the
   numbers.** They are updated in the same commit as the work, never after.
   Foundation 58 made that a gate rather than a habit, because it had already
   failed: `plan.md` opened at Foundation 47 while the tree was at 57, and
   `docs/generated/native-abi-report.json` was itself forty-seven routes stale.
   `tools/status_gate/verify.py` derives the current Foundation from the highest
   evidence file, derives every policed count from the generated reports,
   *and* regenerates four of those reports to prove they are what a live run
   still produces.

## The gates, and what each is for

```bash
swift build && swift build -c release && swift test && swift test -c release
ASAN_OPTIONS=detect_leaks=0 swift test --sanitize=address --scratch-path build-asan
swift test --sanitize=thread --scratch-path build-tsan
swift package dump-symbol-graph
python3 tools/api_compat/verify.py --self-test
python3 tools/api_compat/verify.py --graph-self-test --symbol-graph …
python3 tools/api_compat/verify.py --symbol-graph … --output docs/generated/api-compat-report.json
python3 tools/api_compat/dependency_graph.py --report … --output …
python3 tools/native_abi/verify.py     --cna-include … --library "$CNA_NATIVE_LIBRARY"
python3 tools/native_abi/mutations.py  --cna-include … --library "$CNA_NATIVE_LIBRARY"
CNA_NATIVE_LIBRARY=… python3 tools/projection_mutations/run.py     # ~65 min, 215 mutations
python3 tools/api_compat/message_coverage.py --self-test|--mutations|(report)
python3 tools/api_compat/pinned_assembly_audit.py …
python3 tools/api_compat/bcl_authority_audit.py … --cross-check --negative-control …×4
python3 tools/runtime_capabilities/render.py --check
python3 tools/api_compat/profile_capabilities.py --check \
  --assembly-dir /path/to/xna/redistributable --il-cache ~/deps/xna-il-cache
python3 tools/status_gate/verify.py --self-test
python3 tools/status_gate/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --cna-include /path/to/cnanext/modules/c-api/include \
  --library "$CNA_NATIVE_LIBRARY"
python3 tools/gamepad_native/run.py --library … --output …
cd ../cna-swift-template && swift run HelloGame --frames 600
```

`README.md`'s *Verification* section is the maintained copy of this list.

Two operational notes worth the seconds they save:

* **Every run must be headless, and there must be a real virtual screen.**
  `$SCRATCH/env.sh` exports `CNA_RENDERER=HEADLESS`, `SDL_VIDEODRIVER=dummy`
  and `DISPLAY=:99`.

  **`DISPLAY=:99` alone was not a virtual screen.** Checked at Foundation 73:
  no X server was running on `:99` at all, so the only real protection was
  `SDL_VIDEODRIVER=dummy` — one layer, with nothing behind it. A private
  `DISPLAY` pointing at nothing is not defence in depth; it is a single point
  of failure that reads like two.

  `env.sh` now starts one if it is not already up, and a session that does not
  source `env.sh` must start it by hand before running anything:

  ```bash
  xdpyinfo -display :99 >/dev/null 2>&1 || \
    setsid Xvfb :99 -screen 0 1280x800x24 -nolisten tcp -noreset &
  ```

  `env.sh` lives in the per-session scratchpad and is thrown away with it,
  which is why the requirement is written down **here** rather than only
  there. The user's physical desktop is `:0` and nothing in this project may
  ever address it.
* **If the template canary fails with compile errors in code that is fine**,
  delete the consumer's `.build/build.db`: SwiftPM caches a path dependency's
  source file list, and a new file in the library is invisible until it is
  cleared. Foundation 57 lost time to this.

## Open items carried forward

### `git add -A` during a mutation run has now corrupted history twice

**Never stage `Sources/` while `.mutation-gate.lock` is held.** A run plants a
mutation, `git add -A` captures it, and the run restores the file a minute
later — so the working tree looks right and the damage lands only in history,
where nothing looks for it.

It happened once at `5513b94`. It happened again on 2026-09-05, to **nine
consecutive commits**: `fd58b3e` through `d7c45a5`, each a documentation commit
that also carried one line of a planted mutation in a Graphics source it never
mentions. They largely cancel — each captured a mutation and the next captured
its restore — but the net left `TextureCollection.swift` missing
`slots[resolved] = value` in `HEAD` while the working tree had it.

**`--audit-tree` structurally cannot catch this.** By the time anyone runs it
the harness has restored the tree; the audit is looking at the right file and
the wrong place. The check belongs at the commit, and there is now a
`.githooks/pre-commit` that refuses a staged `Sources/` path while the lock is
held, wired up with `core.hooksPath`. A fresh clone needs
`git config core.hooksPath .githooks` before it is protected — that is the
hook's one weakness and it is worth doing first.

The habit to keep even with the hook: while a run is in flight, commit the paths
you actually edited (`git add NEXT.md docs/`), never `-A`.


### What a mutation run costs the SSD, measured

**116 MB per mutation. About 33 GB for a full 290-mutation run.** Measured on
2026-09-05 by sampling `/proc/diskstats` across 300 s of a run in flight: 928 MB
for 8 mutations.

Two full runs happened that day, so mutation runs alone accounted for roughly
66 GB of the ~1.2 TB written across all sessions. The cost is not the tests --
it is the **rebuild and relink of the test binary once per mutation**, which no
amount of test filtering avoids.

`--changed-since <git-ref>` exists for this. It selects only the mutations whose
target file changed since a ref, which is the honest narrowing:

* A change confined to `Sources/` can only move the verdicts of mutations in the
  files it touched.
* **A change anywhere under `Tests/` refuses to narrow at all** and the tool says
  so, because a mutation is caught by whatever test happens to assert the
  behaviour -- so any verdict can move. The 31-file `defer` repair on
  2026-09-05 is exactly that case, and the full run after it was warranted.

Use `--changed-since` for a milestone; keep the full run for a handoff and for
any change that reaches the tests.

**The same arithmetic applies to plain `swift test`**, which pays the same
rebuild-and-relink. Iterate with `--filter` and run the whole suite once before
committing, rather than after every edit.


### A cascade hang in the full suite — NOT diagnosed

Three mutations came back `HUNG` from the full 287-run. All three are now
confirmed **`CAUGHT`** — the harness was scoring only the exit status, which a
timeout never produces, and it reads the captured failures now — so nothing is
unmeasured. What remains is the hang itself, and it is **still unexplained**.

What is known, measured rather than supposed:

* It only happens in the **whole suite**. With
  `from-type-size-test-reads-the-wrong-size` planted, `swift test` stops at test
  **346 of 809**, inside
  `Foundation62ProfileCapabilityTests.testAVertexBufferLargerThanTheProfileIsRefused`.
* **That test is not the defect.** Run alone with the same mutation it *fails*,
  correctly, in **0.046 s**.
* Filtering to `Foundation6[012]` — 32 tests including that one — does **not**
  hang either. So something in the classes that run before it (53, 54, 55, 57,
  59 all drive games) is required to reproduce it.
* By then the mutation has already failed **28 assertions**, so the hang is
  downstream of the detection, not instead of it.

**A hypothesis was tested and is wrong.** Every probe helper ran
`try game.Run()` then `try game.Dispose()`, so a throwing `Run()` skipped
disposal and leaked what CNA calls *"the process's active C-owned CNA game"* —
a plausible way for a later `Game.Run()` to block forever. Disposal is
unconditional now (`defer`) in all 31 helpers, and **the hang is unchanged**.
The change is kept because the leak was real, but it must not be recorded as
the fix, and the next attempt should start by ruling out this explanation
rather than re-deriving it.

Worth knowing for whoever picks it up: the first draft of that repair moved
`Dispose()` *after* the assertions everywhere, which broke
`Foundation38RenderTargetTests.testParentGameDisposalReleasesTheTarget` — a test
whose entire subject is what the parent's disposal does to the child. It now
keeps its explicit `Dispose()` before its assertions with the `defer` as a net.


### The package-qualification gate was red for forty-one commits — closed

`tools/package_qualification/verify.py` carries its own `ArchiveCanary`, and it
had not compiled since `805b4cd` *"raise the exact projected CLR and XNA
exceptions"* removed the four `CNAError` cases it asserted refusals through:
**111 compile errors**. The report on disk was last written by that same commit,
so it recorded `DEBUG_BUILD=PASS RELEASE_BUILD=PASS RUN_60=PASS RUN_600=PASS`
for forty-one commits against an archive whose SHA matched nothing.

Repaired in `1c651f4`. Twenty-three sites were the canary's own "I found a
mismatch" signal and now throw a canary-local `QualificationFailure`, so a
qualification verdict can never be confused with the package's behaviour; the
seven real behavioural assertions were re-aimed by reading each projection.
A second drift surfaced underneath — `Game.GraphicsDevice` is Optional now —
and is bound with a guard that **throws** on nil, because a canary that quietly
returned would report PASS for a run that drew nothing.

**The proposal this section used to make was wrong, and the reason is worth
keeping.** It said to compare the report's recorded archive SHA against a fresh
`git archive` of `HEAD`. That is circular: the report is itself committed, so
the archive of the commit carrying the report can never match the archive the
report was generated from — the check would have been permanently red, which is
no better than permanently green. What actually shipped is
`QUALIFIED_INPUTS_SHA256`, a digest over `Sources/`, `Package.swift` and the
canary tool, recomputed by the status gate. Committing a regenerated report
changes none of those three, so there is no circularity, and it needs no
consumer build. Both directions are demonstrated: a report with no digest and a
report whose digest disagrees each produce `FINDINGS=1 STATUS=FAIL`.

**What this costs going forward.** Any change under `Sources/` makes the report
stale, so package qualification has to be re-run once per handoff — which is
the cadence it was always supposed to have, and the reason the staleness went
unnoticed is that it never had it.

### `CNAStringBuilder.Capacity` is a lower bound, and now says so

**Decided in Foundation 71's follow-up.** .NET computes `Capacity` as
`m_ChunkOffset + m_ChunkChars.Length` and sizes each new chunk as
`Max(requiredAdditionalLength, Min(Length, 8000))`; this class holds one flat
`[UInt16]` and grows to exactly what was asked for, so it reports a smaller
number after a growth.

The difference is **admitted rather than removed**, because reproducing the
number means reproducing the chunk chain — allocation strategy, not observable
text — and no XNA member reads `Capacity`. A half-modelled chain would produce a
plausible wrong number, which is worse than an honest smaller one.

What is now promised and pinned by a test: `Capacity >= Length` always,
`Clear()` leaves it alone, and `SetCapacity` is exact because that path is
XNA's. What is not promised is the value .NET would have chosen after a growth.
The property's own documentation carries the same, so the next reader meets it
where the code is.

### 1. A CLR exception class is a Swift class conforming to `Error`

```text
System.Exception                                 ->  CNAException : Error
System.SystemException                           ->  CNASystemException
System.Runtime.InteropServices.ExternalException ->  CNAExternalException
```

The chain is **three links, not two**: `ExternalException`'s exact direct base
is `SystemException`, whose constructors substitute their own message and set
HResult `0x80131501` before `ExternalException` overwrites it with
`0x80004005`. `CNAError` stays a separate channel, is not a `CNAException`, and
a `catch is CNAException` does not swallow it.

Selected surface: `Message`, `InnerException`, `HResult`, `HelpLink`,
`GetBaseException`, `ExternalException.ErrorCode` — every member reconstructible
from managed state. `StackTrace`, `Source`, `TargetSite`, `Data`,
`GetObjectData`, `GetType` and `ToString` each need a CLR runtime service and
are **forbidden** by the verifier rather than answered with something plausible.

### 2. `Dictionary<K,V>` is a reference class with the CLR's own storage

Buckets, an entry array, a free list and a version counter, so the observable
behaviour follows from the algorithm: a removed slot is reused by the next
insertion, the free list is last-freed-first, and clearing an already empty
dictionary does not invalidate an enumerator.

The fact that settles the hash question: **an entry's index comes from `count++`
or the free list, never from its hash**, so enumeration order is reproducible
without reproducing a single CLR hash code. A caller-supplied comparer is exact,
including that one whose hash disagrees with its equality cannot find its own
entries.

### 3. `System.Attribute` — the base carries identity, not members

Its public surface is overwhelmingly reflection and is forbidden. The one
widening is recorded: Swift has neither `abstract` nor `protected`, so
`CNAAttribute()` compiles where `new Attribute()` does not.

### 4. `System.Type` is the Swift metatype

The contract names it in **twenty-four positions and calls a member on it in
none**, so the selected surface is identity and assignability — and
`_openExistential` reproduces `Type.IsAssignableFrom` exactly, including
protocol conformance and class inheritance. Probed before the decision, not
after.

### 5. The `Game` base bodies own the managed component semantics

`Initialize`, `Update` and `Draw` are no longer empty. The `LoadContent`
dispatch question was answered by **measuring the host**:

```text
RunOneFrame  Initialize, LoadContent, Update, Draw, UnloadContent
Run          Initialize, LoadContent, BeginRun, Update, EndRun, UnloadContent
```

which is XNA's `RunGame` sequence exactly, so the native `load_content`
callback **is** the projection of the `LoadContent()` call inside
`Game.Initialize()`. One occurrence, one invocation. The measurement is a
permanent test.

# Historical: the Foundation 30–36 handoff

> **The handoff written at the end of the Foundation 30-36 session, kept as
> that session's record.** It is not the current state and is not maintained:
> Foundation Milestones 37 through 74 have landed since. Nothing here is
> deleted, because the measurements it records were real when it was written.

<!-- status-gate:historical -->

**Foundation Milestones 30 through 36: COMPLETE.** Eleven local commits, none
pushed.

Resolve HEAD and the unpublished count from live Git rather than from this
file — any number written here invalidates itself the moment the next
documentation commit is made:

```text
git rev-list --count origin/develop..HEAD
git log --oneline --decorate origin/develop..HEAD
git status --short --branch
```

| Commit | What it is |
|---|---|
| `56a72e4` | The CLR exception families as real Swift `Error` classes, and eight XNA exception types. |
| `8171fa7` | `Dictionary<K,V>` as a reference class, and `LaunchParameters`. |
| `68527e7` | The generated report echoed the caller's absolute symbol-graph path. |
| `31a787c` | The nullability analyser did not understand `String.IsNullOrEmpty`. |
| `654ff5c` | `System.Attribute` and the five `ContentSerializer*` types. |
| `eede22b` | `LaunchParameters` parses the command line; `SetItem` does not throw. |
| `9e61538` | The managed `Game` component engine. |
| `d9f2d93` | `GameComponent`. |
| `1db5e83` | XNA's own resource strings pinned; eight messages corrected. |
| `eea67d1` | `System.Type` as the Swift metatype, and `GameServiceContainer`. |
| `8f248aa` | The support-hierarchy checks made runtime tests. |

Everything at and before `7b59ceb` is untouched.

## START — the state this session began from, reproduced exactly

```text
BRANCH=develop   HEAD == origin/develop == 7b59ceb   WORKTREE_CLEAN=true
TARGET 126/1706  TOTAL_DIAGNOSTICS 284  COMPLETE 121  MISSING_TYPE 131
MISSING_MEMBER 130  PARTIAL 5  EXPECTED_SWIFT_MEMBERS 2887
BCL_INHERITED_MEMBER_PROJECTIONS 16  PROPERTY_MAPPING_MISMATCH 4
OVERLOAD_MAPPING_MISMATCH 16  NATIVE_ABI 29/91/91/18/2/214
```

Verified live before any work; every number matched.

## Structural scoreboard

```text
REFERENCE_TYPES=257                  unchanged
REFERENCE_MEMBERS=2964               unchanged
EXPECTED_SWIFT_MEMBERS=2887          unchanged
TARGET_TYPES=142                     (126 -> 142)
TARGET_MEMBERS=1767                  (1706 -> 1767)
TOTAL_DIAGNOSTICS=269                (284 -> 269)
COMPLETE_TYPES=135                   (121 -> 135)
PARTIAL_TYPES=6                      (5 -> 7)
MISSING_TYPE=115                     (131 -> 115)
MISSING_MEMBER=129                   (130 -> 129)
BASE_MAPPING_MISMATCH=2              unchanged
INTERFACE_MAPPING_MISMATCH=1         unchanged
PROPERTY_MAPPING_MISMATCH=4          unchanged
OVERLOAD_MAPPING_MISMATCH=18         (16 -> 18, the two deferred serialization ctors)
INHERITANCE_MAPPING_MISMATCH=0       new rule, green
LANGUAGE_MAPPING_MISMATCH=0          new check, green
every other mismatch/leak category=0
UNMEASURED_STRUCTURAL_CATEGORY=0
ALLOWLIST_ENTRIES=0

BCL_SUPPORT_TYPE_MEASUREMENTS=10     (3 -> 10)
BCL_BASE_PROJECTIONS=19              (5 -> 19)
PROJECTED_BCL_BASE_TYPES=15          (1 -> 15)
PENDING_BCL_BASE_TYPES=4             unchanged
BCL_INHERITED_MEMBER_PROJECTIONS=77  (16 -> 77)
MEASURED_SUPPORT_BASE_PROJECTIONS=23 (9 -> 23)
NAMESPACE_MARKERS=11                 (10 -> 11, Storage)

BCL_RESOURCE_STRING_PROJECTIONS=8    new
BCL_STATIC_TABLE_PROJECTIONS=1       new
XNA_RESOURCE_STRING_PROJECTIONS=4    new
XNA_SEALED_CLASS_PROJECTIONS=18      new
BCL_ABSTRACT_BASE_WIDENINGS=1        new, recorded
NONDERIVABLE_UNSEALED_CLASSES=5      new, RECORDED not diagnosed
```

**`EXPECTED_SWIFT_MEMBERS` did not move, and should not have.** Every new
`TARGET_MEMBER` is a declared XNA identity that was already in the pinned
contract and already counted. The surface those types *inherit* is real and
usable and is not an XNA identity, so it is counted once on its own axis.

## Sixteen types completed

```text
Audio.InstancePlayLimitException              Content.ContentSerializerAttribute
Audio.NoAudioHardwareException                Content.ContentSerializerCollectionItemNameAttribute
Audio.NoMicrophoneConnectedException          Content.ContentSerializerIgnoreAttribute
Graphics.DeviceLostException                  Content.ContentSerializerRuntimeTypeAttribute
Graphics.DeviceNotResetException              Content.ContentSerializerTypeVersionAttribute
Graphics.NoSuitableGraphicsDeviceException    LaunchParameters
GameComponent                                 GameServiceContainer
```

Two more are PARTIAL by exactly one member each —
`Content.ContentLoadException` and `Storage.StorageDeviceNotConnectedException`
— see the serialization note below. `Game` gained `Components`,
`LaunchParameters` and `Services`.

## The decisions this session made

### 1. A CLR exception class is a Swift class conforming to `Error`

```text
System.Exception                                 ->  CNAException : Error
System.SystemException                           ->  CNASystemException
System.Runtime.InteropServices.ExternalException ->  CNAExternalException
```

The chain is **three links, not two**: `ExternalException`'s exact direct base
is `SystemException`, whose constructors substitute their own message and set
HResult `0x80131501` before `ExternalException` overwrites it with
`0x80004005`. `CNAError` stays a separate channel, is not a `CNAException`, and
a `catch is CNAException` does not swallow it.

Selected surface: `Message`, `InnerException`, `HResult`, `HelpLink`,
`GetBaseException`, `ExternalException.ErrorCode` — every member reconstructible
from managed state. `StackTrace`, `Source`, `TargetSite`, `Data`,
`GetObjectData`, `GetType` and `ToString` each need a CLR runtime service and
are **forbidden** by the verifier rather than answered with something plausible.

### 2. `Dictionary<K,V>` is a reference class with the CLR's own storage

Buckets, an entry array, a free list and a version counter, so the observable
behaviour follows from the algorithm: a removed slot is reused by the next
insertion, the free list is last-freed-first, and clearing an already empty
dictionary does not invalidate an enumerator.

The fact that settles the hash question: **an entry's index comes from `count++`
or the free list, never from its hash**, so enumeration order is reproducible
without reproducing a single CLR hash code. A caller-supplied comparer is exact,
including that one whose hash disagrees with its equality cannot find its own
entries.

### 3. `System.Attribute` — the base carries identity, not members

Its public surface is overwhelmingly reflection and is forbidden. The one
widening is recorded: Swift has neither `abstract` nor `protected`, so
`CNAAttribute()` compiles where `new Attribute()` does not.

### 4. `System.Type` is the Swift metatype

The contract names it in **twenty-four positions and calls a member on it in
none**, so the selected surface is identity and assignability — and
`_openExistential` reproduces `Type.IsAssignableFrom` exactly, including
protocol conformance and class inheritance. Probed before the decision, not
after.

### 5. The `Game` base bodies own the managed component semantics

`Initialize`, `Update` and `Draw` are no longer empty. The `LoadContent`
dispatch question was answered by **measuring the host**:

```text
RunOneFrame  Initialize, LoadContent, Update, Draw, UnloadContent
Run          Initialize, LoadContent, BeginRun, Update, EndRun, UnloadContent
```

which is XNA's `RunGame` sequence exactly, so the native `load_content`
callback **is** the projection of the `LoadContent()` call inside
`Game.Initialize()`. One occurrence, one invocation. The measurement is a
permanent test.

## Defects this session's own gates caught

1. **The IL parser silently merged two types.** `skip_block` stopped only on
   `ikdasm`'s commented method close, but a `pinvokeimpl … preservesig` body
   closes with a bare `}` — so `System.Exception` absorbed all of
   `System.ValueType`. Now brace-depth aware, with a minimised fixture.
   `AUDIT_SELF_TESTS` 60 → 64; the XNA contract still reproduces 257/2964.
2. **The nullability analyser did not understand `String.IsNullOrEmpty`.** A
   field read on the branch reachable only when the field is *not* null was
   reported nullable. Six verdicts moved, every one checked against the CIL by
   hand. `RETURN_NULLABILITY_SELF_TESTS` 115 → 118.
3. **`LaunchParameters` did not parse the command line.** The first version of
   Foundation 31 implemented `.ctor()` as a bare `base..ctor()` and recorded
   "nothing here fabricates launch data" as a virtue — but an empty collection
   *is* the fabrication. Caught by its own new test under the real runner.
4. **Eight XNA messages were transcribed rather than read.** One differed by a
   whole clause and a double space. XNA's resource strings are now pinned and
   compared exactly as the BCL ones are.
5. **A generated report echoed the caller's absolute path.** Normalised.
6. **Two mutation helpers were no-ops on `System.Attribute`**, substituting
   `System.Object` for `System.Object`. Fixed for every subject.
7. **Nine `is` tests the compiler could answer statically**, caught by
   warnings-as-errors. Now runtime checks through `Any`.

## Deliberately deferred, with named blockers

| What | Blocked by |
|---|---|
| `ContentLoadException` / `StorageDeviceNotConnectedException` protected `(SerializationInfo, StreamingContext)` ctor | `System.Type`, `IDictionary` and a deserialization runtime; Swift has no `protected`, so a projection would be publicly callable and would return an exception carrying none of the serialized state |
| `DrawableGameComponent` | `IGraphicsDeviceService` resolved out of `Game.Services`; nothing fabricates a graphics service producer |
| `Game.Content`, `Game.Window`, timing and activation members | `ContentManager`, `GameWindow`, unbound host state |
| `Data`, `StackTrace`, `Source`, `TargetSite`, `ToString`, `GetObjectData` on the exception family | CLR runtime services; forbidden by the verifier, not merely absent |
| XNA's `LoadContent` conditions | `IGraphicsDeviceService`; see below |

### The `LoadContent` differences, and the guard that was removed

Two remain, both needing `IGraphicsDeviceService`:

- XNA calls `LoadContent` only when a graphics device service and device exist;
  here the host decides, so a game with no `GraphicsDeviceManager` still gets it;
- XNA's `LoadContent` fires from *inside* the base `Initialize`, so an override
  that skips `super` never receives it; here it always does.

A flag gating the callback on the base body having run **was implemented and
then removed**. It fixes the second and would also suppress the device-reset
reload XNA issues through the handlers `HookDeviceEvents` installs — behaviour
this host has not been measured for. Trading a known divergence for an
unmeasured one is not an improvement. Worth knowing: the flag *worked*, and
broke the 60-frame canary, whose probe overrides `Initialize` without calling
`super` — precisely the XNA footgun it reproduces.

## Recommended next frontier, in value order

### 1. The BCL exception payload conversion — named three times, still open

`CNAList`, `CNACollection`, `CNADictionary`, `GameComponentCollection` and
`GameServiceContainer` all report CLR-shaped failures through `CNAError`. The
**messages** are now exact; the exception **classes** are not. Foundation 30
made `ArgumentException`, `ArgumentNullException`,
`ArgumentOutOfRangeException`, `NotSupportedException`,
`InvalidOperationException` and `KeyNotFoundException` projectable, and
converting one support type while leaving the others would make the layer
inconsistent — so it is one milestone across all of them.

`CNAError` has accreted `argumentNull` and `keyNotFound` in the meantime; that
conversion is where they come back out.

### 2. `NONDERIVABLE_UNSEALED_CLASSES=5`

```text
GameTime  GraphicsDevice  SpriteBatch  Texture2D  GraphicsDeviceManager
```

XNA leaves all five derivable and this projection has sealed them.
**`Texture2D` is the one that matters: `RenderTarget2D` derives from it**, so
that type is inexpressible while it is `final`. Unsealing a public class is an
API decision of its own, which is why the rule records this direction rather
than diagnosing it.

### 3. `System.ComponentModel.TypeConverter` and the fourteen `Design` converters

`System.Type` is now decided, which was half the blocker.
`ExpandableObjectConverter` and `System.dll` — still registered as available
but deliberately unadmitted — are the other half. `System.dll`'s admission
needs the same non-vacuous standards `mscorlib` met.

### 4. `Game`'s remaining partial members

`Tick`, `SuppressDraw`, `ResetElapsedTime`, `IsFixedTimeStep`,
`TargetElapsedTime`, `IsMouseVisible`, `InactiveSleepTime`, `IsActive`,
`Dispose(bool)`, `ShowMissingRequirementMessage` and the four events. Several
need host state that is not bound; several are pure managed state.

## Qualified environment and gates

```text
SWIFT_VERSION=6.0.3   SWIFT_TARGET=x86_64-pc-linux-gnu   TOOLS_VERSION=5.9
DEBUG_BUILD=PASS                RELEASE_BUILD=PASS
DEBUG_TESTS=406 PASS            RELEASE_TESTS=406 PASS
NATIVE_TESTS included (CNA_NATIVE_LIBRARY set); 0 skipped
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS (forced full rebuild)
SYMBOL_GRAPH=PASS               SYMBOL_GRAPH_SELF_TESTS=17 PASS
API_SELF_TESTS=2390 PASS        (2288 -> 2390)
AUDIT_SELF_TESTS=64 PASS        (60 -> 64)
RETURN_NULLABILITY_SELF_TESTS=118 PASS   (115 -> 118)
BCL_AUTHORITY_STATUS=PASS
    21 identity / 314 sentinel / 28 manifest / 346 mutation / 91 cross-check
    8 resource / 1 static table / 4 negative controls, all refused
    19 types, 205 members   (8 types, 94 members)
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS
    RESOURCE_STRING_CHECKS=8 RESOURCE_STRINGS_REPRODUCED=4
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=2002/2002/0    (1861 -> 2002)
PURE_BCL_DERIVED=210/210/0      (77 -> 210)
SWIFT_ASAN=PASS_406_TESTS_DETECT_LEAKS_DISABLED
SWIFT_TSAN=3_RUNS_0_RACES_0_FAILURES   tsan-1..3.log captured unfiltered
NATIVE_ABI=29/91/91/18/2/214 MISSING=0/0 MISMATCHES=0   unchanged
NATIVE_STRESS=GAME_CYCLES=20 GAME_RECREATION_CYCLES=20 TEXTURE2D_CYCLES=20
    SPRITEBATCH_CYCLES=20 CALLBACK_ERROR_CYCLES=20 GAMEPAD_GET_STATE_CYCLES=50
    GAMEPAD_CAPABILITIES_CYCLES=20 NATIVE_CRASHES=0 OBSERVED_UAF=0
    OBSERVED_DOUBLE_FREE=0 MODE_FAILURES=0
GAMEPAD_NATIVE=0 FAILURES HARDWARE_AVAILABLE=NO
SOURCE_ARCHIVE=307 entries DETERMINISTIC=YES
    SHA256=fdcfe7f4c280a0f9dc7021e9836660924747684ff99653c8a3e38e2ad4cb94b8
    measured on the tree of 8f248aa; handoff-only commits after it change this
    file and therefore the digest, so re-measure rather than assume
ISOLATED_CONSUMER=DEBUG_BUILD=PASS RELEASE_BUILD=PASS RUN_60=PASS RUN_600=PASS
    REJECTED_NEGATIVE_CONSUMERS=11
    FORBIDDEN_ENTRIES=0 NATIVE_LIBRARIES=0 MICROSOFT_REFERENCE_BINARIES=0
    DEVELOPER_PATH_LEAKS=0
GIT_DIFF_CHECK=CLEAN
```

### Pinned reference digests

```text
bcl40-selected-shape.json               52b98a96a506b132…
xna40-selected-resource-strings.json    699aab9e8d3de992…   new this session
xna40-reference-return-nullability.json 1b95bce92cd67e02…   regenerated
```

### The ASan leak observation, stated rather than buried

Leak detection is disabled in the gate, as it was before. With it **enabled**,
LeakSanitizer reports allocations from `libXCTest` and from the native library,
scaling exactly with the test count (406 objects). **No leak trace enters a CNA
source frame**, including the `GameComponent` parent cycle, which the tests
break through `Dispose`. That is an observation, not a claim that the binding
leaks nothing.

### The native evidence library is NOT the previously pinned one

```text
used     ~/deps/cna-c-abi-0.7.0/libcna_c_api.so
         c62949d23d3745964f5e557a06665875621ed4cb6e2930e3f282afd5911f2dcb
pinned   42e099146bf3b470f82fd963a516f8bdd7ff0406da8c37dd53747699117db086
```

**The previously pinned binary no longer exists anywhere on this machine** — it
lived under the system temporary directory and was lost. The library used is
the shared reproduced build documented in
`~/deps/cna-c-abi-0.7.0-pinned-foundation11/PROVENANCE.md` as ABI- and
behaviour-equivalent on the exercised surface but **not** byte-identical to the
admitted artifact. It reproduces the pinned ABI numbers exactly
(29/91/91/18/2/214, zero missing, zero mismatches) and every stress and gamepad
number. `docs/native-abi.md` still records the old digest and has not been
rewritten, because that measurement did happen; this note is the correction.

## Registered inputs

Unchanged. The seven XNA assemblies still reproduce 257 types / 2,964 members
exactly. `mscorlib` `5634668d…acc63` is still the sole admitted BCL authority;
`System.dll` is still available and deliberately unadmitted. `ikdasm`,
`monodis`, `mono` and Swift 6.0.3 at `/tmp/cna-swift-toolchain-6.0.3` are all
present. **No required input or package is missing.**

`~/deps/xna-il-cache/` now holds digest-keyed disassemblies alongside the older
stem-keyed ones. Prefer the digest-keyed form: two different `mscorlib.dll`
files have the same stem, and a name-keyed cache once handed a negative control
the admitted assembly's IL.

```text
SELECTED_ONLY=false
STARTED=false
```
