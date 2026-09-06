# CNA-Swift continuation handoff

> **Current as of Foundation 76.** The Foundation 30–36 handoff that used to be
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
  --library "$CNA_NATIVE_LIBRARY" \
  --assembly-dir /path/to/xna/redistributable \
  --il-cache ~/deps/xna-il-cache
```

```text
931 tests, 0 failures (debug; release, ASan and TSan re-run at handoff)
TOTAL_DIAGNOSTICS=51   COMPLETE_TYPES=213   PARTIAL_TYPES=6
MISSING_TYPE=38  MISSING_MEMBER=10  OVERLOAD_MAPPING_MISMATCH=3
every category that would mean DISAGREEMENT with XNA: 0
BOUND_FUNCTIONS=612  PROTOTYPE_TYPE_POSITIONS=2052  LAYOUTS=64  ABI_MISMATCHES=0
PROJECTION_MUTATIONS=375 (last full run 137, CAUGHT=135)
5 withdrawn with the reason written where they stood, 1 no-op replaced
NATIVE_ABI_MUTATIONS=14 CAUGHT=14
MESSAGE_COVERAGE_FINDINGS=0 over 1,614 implemented members
API_COMPAT_SELF_TESTS=2464  AUDIT_SELF_TESTS=80  BCL_MUTATION_SELF_TESTS=462
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
| The five unwired content loaders | 0 types, 0 members | `ContentManager` landed in Foundation 87 with **one** loader bound, `load_texture2d`, because adopting what the other five produce needs machinery those types do not have yet. Each is unblocked by its own type's milestone, not by content work. |
| `ContentManager.OpenStream` / `ReadAsset` | 0 types, 2 members | The two protected members Foundation 87 left absent. `OpenStream` returns a `Stream` over an asset this binding never opens itself, and `ReadAsset` takes `Action<IDisposable>`; both wait on decisions about `System.IO` and delegate projection. |

### Foundation 90 — `DynamicSoundEffectInstance`, and two members Swift cannot spell

Built from a sample rate and a channel count, so it is reachable where the XACT
family is not. Twelve routes, a native `BufferNeeded` subscription, and one
measured refusal.

**Measured: submitting 101 buffers to this runtime leaves 101 pending.** XNA
refuses past 64 -- `OverTheInstancePacketLimit` names the number -- so the limit
is enforced here. A queue that grows without bound fails later and somewhere
else, which is a worse answer than being told the limit.

**`Play` and `IsLooped` stay inherited, and that is a language limit stated
rather than hidden.** XNA declares both on this type again with C#'s `new`, and
the accessor table shows the redeclared `IsLooped` throws in **both** directions
where the base's getter is `IL_NO_FAILURE_PATH`. Swift has neither member hiding
nor a way to override an infallible property with a fallible one, so the
subclass cannot express either. They are counted as MISSING_MEMBER -- which is
what they are, an absence -- and the consequence a caller sees is one refusal
fewer: reading `IsLooped` on a dynamic instance answers false where XNA would
raise. `Play` loses nothing, because CNA dispatches on the handle and the
inherited call reaches the dynamic instance's own behaviour.

One mutation was **withdrawn** with the reason written where it stood.
`dynamic-submit-ignores-the-range` cannot be falsified through the projected
surface: nothing CNA publishes reports how many *bytes* are queued --
`get_pending_buffer_count` counts buffers, and one submit is one buffer whether
it carried two bytes or two hundred. The range does reach the ABI, and the
manifest and native ABI gate check its argument positions; only its effect is
invisible from Swift.

**An observation without a diagnosis:** the mutation harness reported
`PROJECTION_MUTATION_BASELINE=RED` twice in this session on a tree whose full
suite passes seconds later, and both times an immediate re-run was green. It is
recorded rather than explained. If it recurs, the thing to capture is the
baseline run's own output rather than the verdict line.

### Foundation 91 — `RendererDetail`, a type nothing can populate yet

Entirely managed: two strings, value equality over them, a hash and a
`ToString`. It is projected even though `AudioEngine.RendererDetails` -- the
only thing that produces one -- is blocked on a `.xgs` file, because everything
a consumer can *do* with one is managed, and the pinned contract declares it.

Two details are worth keeping. **Equality is over the renderer id alone**: the
friendly name is what a person reads, the id is what identifies the device, so
the same renderer under two labels is one renderer. And `ToString` answers the
friendly name itself rather than a braced field list, unlike every geometry
type in this binding.

The parameterless constructor is **internal**, and the reference metadata is
why: C# gives every struct an implicit one, the contract declares none, and a
public Swift `init()` was reported as `UNEXPECTED_MEMBER` by name -- which is
the strict comparison working exactly as intended.

The hash deliberately does not claim to be Microsoft's. `String.GetHashCode` is
unspecified across CLR runtimes, so the test asserts that equal values hash
equally -- the contract a hash actually has -- and never a particular number.

### Foundation 92 — `Song`, and two guesses the runtime corrected

The Media leaf, and the only member of that family with a public factory.
`System.Uri` maps to **`Foundation.URL`**, recorded beside `System.IDisposable`
with its reason: it is the same move `System.IO.Stream` already makes, and
admitting the whole `Uri` family for one parameter would earn authority nothing
else consumes.

Every getter but `IsDisposed` is `IL_REACHABLE_THROW` with
`ObjectDisposedException`, so all ten are throwing getters. `Artist`, `Album`
and `Genre` are **not** projected: they answer three missing types that carry
collections back to songs, so the cycle lands together or not at all, and this
type is partial by exactly those three members until it does.

**Two guesses the runtime corrected, both worth keeping.**

`cna_song_create_from_uri` **requires the file to exist** -- a URL naming
nothing comes back `Could not find file`. So the test writes a minimal 8 kHz
mono PCM16 WAV, opens a real song through it and removes it afterwards. No
asset ships with this repository and none needs to.

And two `FromUri` calls on one file are **equal but not the same instance**.
`cna_song_equals` answers true, and disposing one leaves the other reporting
alive -- so equality means "the same track", not "the same object". The first
draft assumed the opposite and documented a divergence that does not exist;
the test now pins what was measured instead. Anything that later caches songs
by equality needs this fact.

`IsDisposed` reads CNA rather than a local flag, which is what gives
`cna_song_get_is_disposed` a consuming member -- it was bound and unused in the
first draft, which is the Foundation 67 rule broken by a type's own author.

One mutation is **withdrawn with its reason in place**: dropping
`cna_song_dispose` and keeping only `cna_song_destroy` is unobservable here,
because the only reference that could see the disposal mark is the one being
released in the same call. It becomes observable when `SongCollection` can hold
a song the caller also disposes directly, and should be reinstated then.

### Foundation 93 — the Media cycle, and three defects the gates caught

Eight types: `Artist`, `Album`, `Genre`, the four collections, and the half of
`MediaLibrary` that reaches them. They are one cycle -- every entity reaches
songs and albums, every collection answers an entity -- so they landed together,
and `Song` is complete at last.

`MediaLibrary` is **partial on purpose**: its picture half reaches `Picture`,
`PictureCollection` and `PictureAlbum`, `Playlists` reaches
`PlaylistCollection`, and `MediaSource` is a fifth missing type. What is here is
the half that makes the rest of the family reachable *and testable* -- without
a library nothing on this host can obtain an artist at all.

**Three defects, and two gates caught what a build could not.**

The relation routes take **three** parameters, not two: `out_artist` and an
`out_available` flag. Calling a three-parameter C function through a
two-parameter Swift signature segfaulted at the first call, and the native ABI
gate named all of them precisely once it was run. The lesson is the running
order: the ABI gate belongs immediately after binding routes, not after writing
the type.

Then `Song.Artist` refused. That is correct: CNA says a song built from a file
path has no library context, "an ordinary answer, not a failure", and all three
returns are `PROVEN_NONNULL_SUCCESS` -- so the absence is reported on the
runtime channel rather than fabricated as an empty artist.

And the borrowed-handle rule: CNA hands out a **borrowed** entity when a song
names one, so a facade that called destroy on it would release something it
never took. The three entity types carry a `borrowed` flag for exactly that.

**A design that had to be rewritten twice.** The collections share one
implementation, and the first version passed the five routes as a struct of
closures. That segfaulted -- passing a `@convention(c)` pointer as a Swift
closure argument produces a broken re-abstraction thunk in this toolchain, the
same shape that crashed SILGen in `SoundEffect`. The family is selected by an
enum now and every route is called directly. **Do not put a C function pointer
behind a Swift closure parameter in this project.**

**Measured, and it corrects a guess from Foundation 92 in the other
direction.** A collection's disposal is *shared*: two facades over the library's
songs name one collection and releasing either is visible from the other -- the
opposite of `Song`, where two equal songs are separate objects. What is not
established is which native half does it; removing
`cna_..._collection_dispose` leaves the observation unchanged, so `destroy`
alone suffices, and the mutation on it is withdrawn with that reason.

### Foundation 94 — the picture branch, and a test that had to be deleted

`Picture`, `PictureAlbum` and their two collections, plus the picture half of
`MediaLibrary`. `System.DateTime` maps to **`Foundation.Date`**, the same move
`System.TimeSpan` makes to `Duration`: CNA answers a Unix instant, which is what
a `Date` carries. XNA's `DateTime` also has a `Kind` and there is nothing here
to reproduce it from.

**A test was written, passed, and then deleted — with the file it created.**
`MediaLibrary.SavePicture` works on this host, so the obvious round trip was to
save a picture and read it back. It did, and it left `canary picture.png` in
`~/Pictures/Saved Pictures/` -- the **user's own photo album** -- beside files
earlier probes from other bindings had left there. CNA publishes no route to
remove one. The file was deleted and the test with it.

A suite may not leave things in a person's photo album. Four mutations are
withdrawn as a result, each with the reason in place: three need a real picture
to reach `SavedPictures`, `GetThumbnail` and `Picture.Date`, and the fourth
needs a media store with **no** pictures, which is equally the user's business.
They wait for a host whose media store already holds pictures the suite did not
have to create.

**The normalizer gap was fixed properly this time.** `InputStream`, then `URL`,
then `Date` each turned a correct projection into a reported mismatch, and each
had been patched with another `elif`. It is a set now, so the fourth Foundation
type will not repeat it.

`MediaLibrary` is still partial, by less: `Playlists` needs
`PlaylistCollection`, `MediaSource` is its own type with the constructor that
takes one, and the `SavePicture` overload taking a `Stream` is blocked
differently -- `cna_media_library_save_picture_from_stream` wants a CNA stream
handle, which this binding cannot make from a `Foundation.InputStream`.

### Foundation 95 — `Playlist`, `MediaSource`, and `MediaLibrary` finished bar one

Three types, and `MediaLibrary` is now one member short of complete: the
`SavePicture` overload that takes a `Stream` needs a CNA stream handle this
binding cannot make from a `Foundation.InputStream`.

**`MediaSource` carries an index, not a handle.** CNA publishes no media-source
object -- every route is `_at(game, index)` -- so a source *is* its position in
the runtime's enumeration, and the name and type are read once when the list is
built rather than on each access, because a later enumeration need not be the
one an index came from. `System.Collections.Generic.IList<T>` maps to `CNAList`,
its first and only use in the whole contract.

**`MediaLibrary.MediaSource` is always nil, and that is CNA's shape rather than
a gap.** The runtime publishes a library's source only as a *name*, and a name
is not a `MediaSource` -- the type carries an enumeration index this binding
would have to guess at. The return is proven nullable, so nil is a state XNA
itself produces; inventing a source from a matching name would be a different
object that merely looked right. The getter still refuses on a disposed
library, because the CLR getter is fallible.

**Measured, and it corrected the test rather than the code:** disposing a
`MediaLibrary` does **not** cascade to the collections it handed out. They are
separate runtime children, alive until the game tears down -- which is XNA's
shape too, where a library's `Dispose` disposes the library and not the objects
it published.

Two mutations are withdrawn with their reasons: one needs a machine with two
media sources, and this host publishes one, so index zero is the right answer
and the mutant is indistinguishable.

### Foundation 96 — `MediaPlayer` and `MediaQueue`: the music half is done

Eighteen of the nineteen Media types are projected. Only `VideoPlayer` remains,
and `MediaLibrary` is one member short.

`MediaPlayer` is a **`final class` with only static members**, not an enum: the
CLR seals the type and declares it a class, and the strict comparison named the
difference. `Queue` is non-Optional and traps when there is no runtime -- the
third member decided by that pair of facts, after `DefaultAdapter` and
`Game.Content`.

**Measured, and it cost a red test to learn: the media queue is process-wide.**
It outlives the game that filled it, exactly as
`cna_media_player_get_queue`'s own words say ("a view of the process-wide media
queue"). A test that played a song left it queued for the next test, whose game
was a different one -- and whose fixture file had already been deleted, so the
failure arrived as `Could not find file`. Nothing in that suite asserts an empty
queue now.

**And a third crash from the same forbidden shape.** A helper taking
`{ $0.someRoute }` crashed SILGen again -- a `@convention(c)` pointer behind a
Swift closure parameter. It has now crashed `SoundEffect` at compile time,
segfaulted the media collections at run time, and crashed `MediaPlayer` at
compile time. **Write the call out.** Every such site in this binding is now
spelled in full, and the rule is in three doc comments so the fourth author
meets it before the compiler does.

Three mutations are withdrawn with their reasons, all limits of the host rather
than of the code: the three-argument `Play` needs a collection with two songs,
the visualisation swap needs a renderer that produces data (this one answers 256
zeros in both buffers, which the test records), and the queue's availability
flag needs an empty queue the suite cannot arrange.

The ABI gate's struct parser learned one thing too: an array bound may be a
**macro** rather than a literal, which `CNA_VisualizationData` is the first to
use.

### Foundation 97 — `VideoPlayer`, and the Media namespace is complete

**All nineteen Media types are projected**, from `Song` to `VideoPlayer`. The
namespace went from entirely absent to entirely present in six milestones, and
the thing that made it possible was measured at the start: Media needs no asset
where XACT and `Model` do.

`Video` now carries a **handle as well as its values**, and both shapes are
real. XNA's videos come out of a content pipeline this binding cannot load, so
the value-built form is what the type was; a player answers a handle and
`Play` needs one back, so a video that came from a player carries it. A
value-built one **cannot** be played, and that is said in the refusal rather
than passed to the ABI as a zero.

`VideoPlayer` is also the only Media type that reaches back into Graphics:
`GetTexture` answers the current frame as a `Texture2D`, adopted through the
same path `Texture2D.fromStream` uses. With nothing playing there is no frame,
and CNA reports that with an availability flag -- so the absence is reported
rather than a texture built from an out-parameter nobody wrote.

**The mutation harness earned its keep again.** `PROJECTION_MUTATION_BASELINE=RED`
came back twice, and this time it was not the flake recorded earlier: the
manifest count in `NativeABIPolicyTests` was one short of the routes actually
bound. A filtered `swift test` had not run that suite. Two identical RED
baselines in a row are a real failure; one is worth re-running first.

### Foundation 98 — `GamerServicesComponent`, and a namespace with one type

The whole of `Microsoft.Xna.Framework.GamerServices` in this profile: one
`GameComponent` whose job is to pump the gamer-services dispatcher. XNA's
`Initialize` calls `GamerServicesDispatcher.Initialize(Game)` and its `Update`
calls `GamerServicesDispatcher.Update()`, and this does exactly those two
things. The `gameTime` is **ignored**, because XNA's own call takes no argument.

`cna_gamer_services_component_create` is deliberately **not bound**. It makes a
*canonical* component whose initialize and update belong to the runtime, which
is right for a C caller assembling a component set and wrong here: this type is
the component, and a consumer overriding `Update` has to be able to decide
whether the base runs.

**Both mutations on it are withdrawn, and the reason is the profile.** The XNA
4.0 Windows contract declares exactly one type in this namespace and no
`GamerServicesDispatcher`. CNA does publish the dispatcher's state --
`cna_gamer_services_dispatcher_get_is_initialized` -- but no projected member
consumes it, so the Foundation 67 rule forbids binding it; and without it a
component that pumps the dispatcher and one that does nothing are
indistinguishable, because both routes simply accept here. The test asserts what
it *can*: that both accept, which is worth failing on if it ever changes.

### Foundation 99 — `TouchPanel`, and the Input namespace is complete

Every supporting type it answers -- `TouchPanelCapabilities`,
`TouchCollection`, `GestureSample`, `TouchLocation` -- had been projected
earlier, so this milestone was the panel alone, and it closed the last gap in
`Microsoft.Xna.Framework.Input`.

**It carries this binding's only settable properties.** `WindowHandle`,
`DisplayWidth` and `DisplayHeight` have setters that are `IL_NO_FAILURE_PATH`,
so the accessor rule keeps them as *properties* where every other fallible
setter became a `Set<Name>` writer. A setter that cannot refuse still has to
reach CNA, so the value is stored and pushed on the same call, and a push that
fails is kept in `lastPushFailure` -- the shape `GraphicsAdapter`'s device
preferences already use. `EnabledGestures` and `DisplayOrientation` have
fallible setters and are writers, so the two shapes sit side by side in one
type, which is the clearest place in the binding to see the rule at work.

`GetState` reads only the **counted prefix** of CNA's fixed eight-slot array;
the rest is whatever the previous frame left there, and a mutation that reads
all eight is caught by a host with no touch device reporting phantom touches.

`CNA_TOUCH_MAX_TOUCHES` is the second macro array bound in a mirrored
structure, after `CNA_VISUALIZATION_DATA_SIZE` -- the parser that learned about
those in Foundation 96 needed no further change.

### Everything left is behind four decisions, and here they are

With Media, Input and GamerServices complete, the remaining **38 types and 10
members** are not a queue of work but four questions. Nothing is left that can
simply be written.

| what | types | what it needs | costed? |
|---|---:|---|---|
| `Design` converters | 13 | **`System.dll`'s ComponentModel closure** admitted to the same non-vacuous standard `mscorlib` met: 7 types, ~151 members, and System.dll's first-time admission | yes, in this file |
| `Model` family | 12 | a way to **produce** a `.xnb`, or shipped fixtures -- `cna_content_manager_load_model` reads one and this repository has none | partly |
| XACT family | 6 | a `.xgs` settings file and `.xsb`/`.xwb` banks, same question one asset kind over | no |
| `Content` readers | 5 | **`System.IO.BinaryReader`** (`ContentReader` derives from it) and `System.Resources.ResourceManager` | no |
| `Storage` | 2 | `System.IAsyncResult`, `System.AsyncCallback`, and the three `System.IO` file enums | no |

The ten missing members are the same four questions in miniature, plus three
that are **measured impossibilities** rather than decisions:
`GraphicsDevice.GetBackBufferData` (both native routes answer `NOT_SUPPORTED`,
now measured rather than assumed), `MediaLibrary.SavePicture(Stream)` (CNA wants
a stream handle this binding cannot make), and
`DynamicSoundEffectInstance.Play`/`IsLooped` (C#'s `new`, which Swift has no
word for).

**The order that costs least.** `Design` is the only one already costed, needs
no CNA route at all, and unblocks the largest single group; the content question
unblocks eighteen types across two families but is a design decision about what
this repository ships. Everything else waits on a BCL admission whose size has
not been measured.

### Media is NOT asset-blocked — it is a deep type graph, and one mapping

Worth stating plainly, because the two neighbouring families are blocked and
this one looks like it should be: **Media needs no asset**. `Song` has a public
factory, `Song.FromUri(String name, Uri uri)`, and CNA publishes
`cna_song_create_from_uri` for it -- a consuming member for a bindable route.
There are 25 `cna_song_*` routes, 32 for `MediaPlayer`, 23 for `MediaLibrary`.

Two things stand between here and it.

**One mapping decision.** `System.Uri` is not projected, and `FromUri` is the
only member that needs it. The cheap answer already has precedent:
`System.IO.Stream` maps to `Foundation.InputStream`, so `System.Uri` mapping to
`Foundation.URL` is the same move -- a platform type standing in for a BCL one,
recorded in `typeMappings` with its reason. Admitting `System.Uri` as a BCL
family instead would be a much larger piece of work for one parameter.

**A graph, not a chain.** `Song.Artist`, `.Album` and `.Genre` answer three
types that are themselves missing, and each of those carries collections back
to songs and albums. `MediaQueue` and `MediaPlayer` then need `Song` and
`SongCollection`. Nineteen Media types are one connected component, and picking
a starting point means deciding how much of it lands in one milestone --
`Song` alone would be PARTIAL by three members, which is honest but leaves the
type closed to nobody.

The order that keeps every commit green: map `System.Uri`, then take
`Artist`/`Album`/`Genre` **with** their collections, then `Song`, then
`SongCollection`, `MediaQueue` and `MediaPlayer` last -- the player is the only
one that needs all of them.

### The XACT family is blocked on a settings file, like `Model` on its `.xnb`

`AudioEngine`, `SoundBank`, `WaveBank`, `Cue` and `AudioCategory` are five of
the eight audio types still missing, and CNA publishes 52 routes for them --
but `cna_audio_engine_create` takes *"Path to the `.xgs` settings file"*, and
`SoundBank` and `WaveBank` take an `.xsb` and an `.xwb`. This repository has
none, and hand-writing an XACT settings binary would be inventing pinned data,
which is the one thing this project does not do.

So the family waits on the **same** question the `Model` family waits on: does
this binding grow a way to produce content, or does it ship fixtures? Answering
it once unblocks twelve model types and five XACT types together.

### `DynamicSoundEffectInstance` is the next reachable audio type

It is **not** blocked: `cna_dynamic_sound_effect_instance_create` takes a sample
rate and a channel count, exactly as XNA's constructor does, and all twelve of
its routes exist including `submit_buffer` and `subscribe_buffer_needed`.

One question is already identified and should not be rediscovered at the
keyboard. XNA declares `IsLooped` and `Play` on this type **again**, hiding the
base's with C#'s `new`, and the accessor table shows why they differ: the base's
`IsLooped` getter is `IL_NO_FAILURE_PATH` while this one is `IL_DIRECT_THROW`
in **both** directions -- a dynamic instance cannot loop, so reading the
property refuses rather than answering false.

**Swift has no member hiding, and cannot override an infallible property with a
fallible one.** So the subclass cannot express either redeclaration. The
projection has to choose between inheriting the base's members (and losing the
stricter refusal) and some rule-level exception, and whichever it is has to be
written down as a language divergence rather than left to look like an
oversight. `Play` is the easier half: CNA dispatches on the handle, so the
inherited call reaches the dynamic instance's own behaviour anyway.

`Microphone` stays out of scope. It is the one remaining audio type this
session will not implement, because it records from a physical device.

### Foundation 89 — `SoundEffect` and `SoundEffectInstance`

Two audio types, thirty-five routes, and **no asset**:
`cna_sound_effect_create_pcm16` takes raw PCM16LE bytes, so the fixture is a
tenth of a second of silence written by the test. That property is why this
family came before `Model`, which is blocked on a compiled `.xnb`.

The qualified HEADLESS renderer **does** have audio: sounds construct, play,
loop, pan and report their state.

**Almost all of the interesting work was the managed half.** Running
`message_coverage.py` after the first green build returned **22 findings** --
every argument and state rule XNA enforces and CNA does not:

* four constructor refusals, because CNA takes the byte count it is given and
  decodes what fits, so an odd-length buffer is a shorter sound rather than an
  error, and a loop region past the end is accepted;
* three stateful rules that all close at the first `Play` -- the loop flag is
  fixed then, `Apply3D` is too late to make a sound 3D, and `Pan` cannot be set
  on a 3D sound because the emitter's position decides where it is heard;
* the disposal text, which XNA's audio types pass themselves rather than
  taking the BCL's generic one.

`InvalidBufferSize`, `InvalidPanCall` and the rest are read out of the pinned
assemblies, never typed from memory.

**One finding closed itself by accident, and that is worth knowing.**
`CallFrameworkDispatcherUpdate` went green the moment its message constant
existed -- `message_coverage.py` matches a message by its **text in the
sources**, so a constant nobody references satisfies it. The constant was
removed and the absence recorded as `unreachable` instead, with the real
reason: a `SoundEffect` is built through `RuntimeRegistry.current()`, so one can
exist only while a game does, and `Game.Tick` calls the dispatcher itself. When
that gate goes green on a new message, check that something actually throws it.

`Apply3D` needed the first two **mirrored structures** in the audio namespace:
CNA takes the listener and emitter by value, not by handle, which is why those
two managed types now have native descriptors and the ABI layout gate covers
them.

### The status gate now re-runs the message-coverage report too

The eleven findings above were invisible for a specific, fixable reason: the
status gate **reads** `docs/generated/message-coverage.json` for derived facts
but never re-ran the tool, so the committed copy could record zero findings
indefinitely while a live run returned eleven. That is exactly the drift the
gate's own header describes for the native ABI report, one report over.

It now regenerates and byte-compares that report as well, given
`--assembly-dir` and `--il-cache`, and both arguments are in the documented
invocation in `README.md` and above. `REPORTS_COMPARED` is 5 → 6. Proved by
editing one number in the committed copy and watching the gate fail on it.

### Foundation 88 — `OcclusionQuery`, and a gate nobody had been running

`tools/api_compat/message_coverage.py` reported **eleven findings** the first
time it was run this session, against a recorded state of zero. Every one was a
message an implemented member can raise that was neither reproduced nor
recorded, and several belonged to milestones from earlier the same day. The
gate is not in the default loop; running it is now part of finishing a
milestone, not part of a handoff.

Eight were reproduced and three recorded, and the interesting half is what
happened to the ones that could not be:

**`NullWindowHandleNotAllowed` was implemented and withdrawn.** The qualified
HEADLESS renderer reports `DeviceWindowHandle = 0` for every device it makes --
the consumer canary prints `window=handle=0` -- so XNA's check refused *every*
device creation and reset on this binding's own qualified boundary. Three green
suites failed on it, which is the measurement. Recorded as `deferred`, naming
the work: make it conditional on a renderer that has a window.

**`ProfileInvalidDevice` was implemented and withdrawn.** Reproducing it over
`GraphicsAdapter.IsProfileSupported` refused a reset CNA accepts -- proof the
two conditions are not the same one. Whether a profile can be served is CNA's
decision. Recorded as `native-owned`.

**`ContentManagerCannotChangeRootDirectory` was a real defect shipped in
Foundation 87.** The accessor table records TWO exceptions for
`set_RootDirectory` and only the null one was reproduced; once anything has
been loaded the root is frozen. The rule needed an internal test hook to be
provable at all, because this host has no `.xnb` to load -- without it the
mutation that removes the rule survives.

`OcclusionQuery` itself closes one missing type. The type is small and its two
managed rules are the whole of it: a second `Begin` is refused until the
previous result has been *looked at* (reading `IsComplete` rearms it), and
`PixelCount` refuses a query that has not finished -- **measured: CNA answers a
count for a query that was never begun, so both refusals are the binding's**.

One decision is worth keeping. `IsComplete` is `IL_NO_FAILURE_PATH` over a
route that can fail, and a failed read answers **true**, not false. The member
exists to be spun on; answering false on a route that keeps failing hangs that
loop forever with nothing to report, while answering true ends it and hands the
question to `PixelCount`, which can raise. An infallible getter should not be
the member that traps a caller -- it should defer to the one that can explain.
The failure is kept in `lastStatusFailure` so the choice is provable rather than
described.

### The `Model` family is blocked on a fixture, and the reason was measured

Two facts turned up before a line of it was written, both from
`build-probe/f88a_bone_identity.c` and the 0.21.0 headers.

**CNA bone handles carry no object identity.** Every accessor that answers a
bone or a collection returns a *fresh* handle: two `get_at(c, 0)` calls answer
different values, `get_parent` answers a different value each time, `find`
answers a third, and none equals the handle the bone was created with. What CNA
does expose is `cna_model_bone_collection_contains`, which answers true for
**both** a created handle and a view handle -- so the identity exists inside the
runtime and simply has no comparison in the ABI.

The consequence for the projection is concrete: XNA's `Bones[0] === Bones[0]`
and `bone.Parent === theParent` are reference identities, and they cannot be
reproduced from handle values. They have to come from materialising each bone
facade **once per model** and resolving `Parent` through
`cna_model_bone_get_index` into that array -- which is what XNA's own object
graph does. Every accessor in the family is `IL_NO_FAILURE_PATH`, so the
snapshot shape was already indicated; this is the measurement that makes it the
only correct shape rather than the convenient one. Note also that each of those
per-call views is an **owned** handle: a facade that read `Parent` on every
access would leak one per read.

**Nothing on this host can produce a `Model`.**
`cna_content_manager_load_model` loads a compiled `.xnb`, and this repository
has none; the header says so plainly ("before it, every `CNA_ModelHandle` was
built by hand from `cna_model_create_*`"). Building one by hand would bind
`cna_model_create`, `cna_model_bone_create` and `cna_model_bone_add_child`,
and **no projected member consumes any of them** -- XNA has no public `Model`
or `ModelBone` constructor -- so the Foundation 67 rule forbids exactly that.
The other door is `cna_cnb_compile_cnj` plus `cna_cnb_build_model_from_cnj`,
which would let a test compile a tiny model at run time; that is a separate
binding surface and its own decision, not a detour inside this milestone.

So the family waits on **one** question: does this binding project the CNB/CNJ
compiler, so that a model asset can be produced rather than shipped? Until that
is answered, implementing `Model` would add four types no test could reach.

### When the fixture question is answered — the `Model` family design

Twelve of the sixty-four missing types are one family: `Model`, `ModelBone`,
`ModelMesh`, `ModelMeshPart` and their four read-only collections with four
nested enumerators. It is also the family that unblocks
`cna_content_manager_load_model`, one of the five loaders Foundation 87 left
unbound.

**The design is already decided, from the tables rather than from taste.**
Every `ModelBone` accessor is `IL_NO_FAILURE_PATH`, so the family takes the
snapshot shape `GraphicsAdapter`, `GraphicsDevice` and `GameWindow` already
use: read from CNA once, cache, and answer from fields. `ModelBone.Transform`
is the one accessor with an infallible **setter** that crosses the boundary, so
it is a deferred write -- store, and push at the next throwing member --
exactly as the accessor rule requires. `ModelBone.Parent` is
`PROVEN_NULLABLE_SUCCESS` on `IL_FIELD_LIFECYCLE` evidence (no constructor
assigns `parent`), so it is Optional; the collections derive from
`CNAReadOnlyCollection`, which is already projected.

Start at the leaves -- `ModelBone` and `ModelBoneCollection` -- because
everything above them holds one.

`ResourceContentManager` is NOT the next step despite being a Content type with
its own CNA route: its constructor takes `System.Resources.ResourceManager` and
its one method returns `System.IO.Stream`, so it is blocked on two decisions
this binding has not made.

### A consumer's stale build plan cost an hour, and would cost anyone else one

Building `cna-swift-template` against the new `ContentManager` failed with
`'ContentManager' is not a member type of enum ...Content` and
`cannot find type 'CNAServiceProvider'` -- while the same sources built cleanly
in this repository. The cause was neither: SwiftPM had cached a **build plan**
in the template's `.build/debug.yaml` that predated the two new files, so they
were never handed to the compiler. `grep -c CNAServiceProvider .build/debug.yaml`
answered `0`, which is the fastest way to see it. Touching `Package.swift` did
not regenerate the plan; removing `.build/debug.yaml` and `.build/build.db` did,
and it keeps every object file, so nothing is rebuilt that did not change.

This is the second staleness trap in one milestone -- the other was SwiftPM not
recompiling the CNA module when only a C header changed. **When a symbol that
demonstrably exists is reported missing, check what the build plan contains
before reading the source again.**

### Foundation 87 — `ContentManager`, `Game.Content`, and one BCL family

**The shape of the divergence.** XNA reads the asset's type out of the `.xnb`
header and builds whatever it finds. CNA publishes one route per asset kind
instead, so here the *type argument selects the route*. A type with no route is
refused by name rather than reported as a missing file, because those are
different facts and a caller can act on only one of them.

Five of the six loaders are deliberately **not bound**: a route with no
consuming member is not bound, and adopting a sprite font, an effect, a sound
effect, a cube or a model needs adoption paths those types do not have. Only
`Texture2D` could be received, so only its route is wired.

**Three decisions that the fallibility table, not taste, settled.**
`Game.Content`'s getter is `IL_NO_FAILURE_PATH` and its return is proven
non-null, which leaves a non-Optional property that must **trap** when there is
no runtime — the answer `GraphicsAdapter.DefaultAdapter` reached from the same
two facts. `set_Content` is `IL_DIRECT_THROW`, so it is a throwing writer, and
because a writer takes the property's own type the null it tests for cannot be
spelled in Swift at all: the type system closes the hole the setter existed to
guard. `ContentManager.RootDirectory` goes the other way — proven nullable, so
Optional.

**`System.IServiceProvider` was admitted as a BCL family**, the smallest one
here: one method. Spelling `ContentManager`'s constructors over
`GameServiceContainer` compiled, passed every test, and was still a narrowing —
a consumer's own service provider could not be handed to a manager at all. The
narrowing was invisible from inside the binding, which is why it was worth a
protocol. Admitted through `bcl-authorities.json`, pinned from the real
`mscorlib.dll`, and covered by nine new sentinel facts (433 → 442).

### Two gates were blind, and a run caught what they missed

`CNASwift_ContentManagerCreateInfo` shipped one field short: CNA's structure
ends in a reserved `uint64` that is part of `sizeof`, so `struct_size` was eight
bytes too small and **every** create call was refused as an invalid
configuration. `tools/native_abi/verify.py` never looked at it —
`MIRRORED_STRUCTS` did not name it. It does now (LAYOUTS 54 → 55), and removing
the field again is a compile error in the generated static assertions.

The second blindness cost an hour: SwiftPM did not recompile the CNA module
when only the C header changed, so the corrected header sat on disk while the
tests kept failing against a stale object. The fix that looked wrong was right.
Anything that edits `Sources/CNAShim/include/` should touch a Swift file in
`Sources/CNA/` too, or verify the value the *binding* sees rather than the one
a test module computes from its own copy of the header.

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

  **Re-measured at Foundation 99 against the OTHER route.** CNA publishes two:
  `cna_graphics_device_get_backbuffer_data_window` and
  `..._data_rgba8`, and only the first had ever been tried. The second was bound
  on purpose, measured -- size query 384,000 with result 14, read with result 6,
  `NOT_SUPPORTED` again -- and **unbound**, because nothing consumes it. Both
  doors are shut, and that is now a fact rather than an assumption about one.
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
  --library "$CNA_NATIVE_LIBRARY" \
  --assembly-dir /path/to/xna/redistributable \
  --il-cache ~/deps/xna-il-cache
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

### `FindBestDevice` and `RankDevices` — sized, and bigger than they look

The last two of `GraphicsDeviceManager`'s five missing members. Both are eight
bytes of IL and both forward to a private platform half, which is where the work
is:

* `RankDevices` → `RankDevicesPlatform`, thirteen bytes:
  `foundDevices.Sort(new GraphicsDeviceInformationComparer(this))`. The whole
  behaviour is that comparer, whose `Compare` is **638 bytes** with two private
  helpers of 48 and 37. It is XNA's device-preference ordering — profile,
  multisampling, format ranks, resolution distance — and it is exactly the kind
  of thing that must be transcribed rather than approximated, because a
  consumer's device choice depends on the order.
* `FindBestDevice` → `FindBestPlatformDevice`, 132 bytes: build a list, call
  `AddDevices` (about a hundred lines of IL), retry once with
  `PreferMultiSampling` flipped, raise `NoCompatibleDevices` if the list is
  empty, `RankDevices`, raise `NoCompatibleDevicesAfterRanking` if it is still
  empty, return `[0]`.

So the pair needs the comparer, `AddDevices`, and two resource strings — a
milestone of its own, not an appendix to the three members Foundation 80
landed. The three that did land are the ones whose IL is fully determined and
short: `CanResetDevice` (23 bytes), `OnPreparingDeviceSettings` (22) and the
event they belong to.

Everything the pair needs already exists: `GraphicsAdapter` enumerates,
`SupportedDisplayModes` is populated, and `GraphicsDeviceInformation` compares
and clones.


### `GraphicsAdapter` — built once, reverted, and what it cost to learn

A complete first implementation was written and then **reverted on purpose**: it
compiled, its six tests passed, and it raised `TOTAL_DIAGNOSTICS` from 105 to
116. A type that leaves the surface less conformant than it found it is not
progress, and the fixes it needs are shape decisions rather than typing.

Everything below is measured. None of it needs re-deriving.

**The routes work and the bindings are right.** Twelve `cna_graphics_adapter_*`
routes bind cleanly; enumeration through them answers **one adapter** on this
host, default and wide-screen, with a real vendor (4098) and device id (5567),
`Revision` and `SubSystemId` zero as CNA documents, a non-empty device name and
description, and **both `Reach` and `HiDef` supported**.

**Three shim structures must be exact**, and two were wrong on the first
attempt: `CNA_DisplayMode` is **24 bytes** and carries an `aspect_ratio` between
`height` and `format` that a first reading missed; `CNA_GraphicsFormatSelection`
is **24** with a `reserved[3]`; `CNA_GraphicsAdapterInfo` is **48**. Each is
passed with an explicit `struct_size` the runtime validates, so a missing field
fails the call with *"The DisplayMode output structure is invalid"* rather than
corrupting anything — a good failure, but only if the sizes are asserted, which
a test now does.

**`cna_graphics_adapters_refresh` can never be called from here.** It refuses
while a device exists — *"The active C GraphicsDevice retains its adapter;
refreshing the global native adapter cache would invalidate that reference"* —
and a device is exactly what enumeration needs. It rebuilds a global cache,
which reading the current adapters does not require. Not a route to bind.

**What the gate demands, and the one open question.** `Adapters` must be
`CNAReadOnlyCollection<GraphicsAdapter>?`, `CurrentDisplayMode` and
`SupportedDisplayModes` must be Optional, the two `Query*` members must take
their three results as `inout` parameters the way `TryGetValue` does rather than
returning a tuple, and **no public member may exist that XNA lacks** — so the
`Refresh()` that fills the snapshot cannot be public and must be driven from
device creation instead.

The open question is `DefaultAdapter`. Its nullability is *not proven from the
registered CIL*, so the rule makes it **non-Optional** — but before any
enumeration there is no adapter to return, and its getter may not throw. XNA
reads `pAdapterList[0]`, which traps on an empty list; whether this projection
should trap likewise, or whether `Refresh` must be guaranteed to have run before
the type is reachable at all, is a public-API decision and is the first thing the
next attempt has to settle.


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
> Foundation Milestones 37 through 76 have landed since. Nothing here is
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
NAMESPACE_MARKERS=12                 (10 -> 11, Storage)

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
