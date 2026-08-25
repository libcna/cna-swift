# CNA-Swift continuation handoff

**Foundation Milestones 19, 20 and 21 status:** COMPLETE.

Three local commits were made this session, none pushed.

| Milestone | Commit | What it is |
|---|---|---|
| Foundation 19 | `6658ed9` | `CLR_EVENT_ARCHITECTURE` — the general event/delegate projection, the `System.EventArgs` class migration, and the first five types that depend on them. Evidence: `docs/foundation-19-clr-event-architecture-evidence.md`. |
| Foundation 20 | `89663b3` | `PURE_MANAGED_BATCH_E` — `AudioListener`, `TouchCollection`, `TouchCollection.Enumerator`. Evidence: `docs/foundation-20-pure-managed-batch-evidence.md`. |
| Foundation 21 | `98f9273` | `Media.Video`, completing the same batch and exhausting the safe managed frontier. Recorded in the Foundation 20 evidence. |

Foundation 18 (`c40cb57`) and everything before it are untouched.

## Qualified environment and gates

Run at the end of the session, on the committed tree.

```text
SWIFT_VERSION=6.0.3
SWIFT_TARGET=x86_64-pc-linux-gnu
SWIFT_TOOLS_VERSION=5.9
DEBUG_BUILD=PASS
RELEASE_BUILD=PASS
DEBUG_TESTS=231 PASS
RELEASE_TESTS=231 PASS
MANAGED_TESTS=231 PASS_WITHOUT_CNA_NATIVE_LIBRARY (10 native tests skipped)
WARNINGS_AS_ERRORS=PASS_DEBUG_AND_RELEASE_INCLUDING_TESTS (forced full rebuild)
SYMBOL_GRAPH=PASS
API_SELF_TESTS=2126 PASS
PINNED_ASSEMBLY_AUDIT=257_TYPES/2964_MEMBERS CALIBRATION=PASS
AUDIT_SELF_TESTS=60 PASS
NORMAL_STRICT=EXPECTED_RED_DEFERRED_PROFILE_ONLY
LEAK_ONLY=PASS
PURE_XNA_DERIVED=1717/1717/0
SWIFT_ASAN=PASS_PURE_CORPUS_137_TESTS_DETECT_LEAKS_DISABLED
SWIFT_TSAN=PASS_MANAGED_CORPUS_231_TESTS_0_RACES
NATIVE_ABI=29/91/91/18/2/214 MISSING=0/0 MISMATCHES=0
NATIVE_STRESS=GAME_CYCLES=20 GAME_RECREATION_CYCLES=20 TEXTURE2D_CYCLES=20
    SPRITEBATCH_CYCLES=20 CALLBACK_ERROR_CYCLES=20 GAMEPAD_GET_STATE_CYCLES=50
    GAMEPAD_CAPABILITIES_CYCLES=20 NATIVE_CRASHES=0 OBSERVED_UAF=0
    OBSERVED_DOUBLE_FREE=0 MODE_FAILURES=0
GAMEPAD_NATIVE=0 FAILURES HARDWARE_AVAILABLE=NO
SOURCE_ARCHIVE=239 entries FORBIDDEN=0 NATIVE_LIBRARIES=0
    MICROSOFT_REFERENCE_BINARIES=0 DEVELOPER_PATH_LEAKS=0 DETERMINISTIC=YES
    SHA256=e6197e7f6417fd760655ff19edf7504814d8011acdf41fab7db711a62f42a69a
ISOLATED_CONSUMER=DEBUG_BUILD=PASS RELEASE_BUILD=PASS RUN_60=PASS RUN_600=PASS
TEMPLATE=86687f62c3a13ee2b59798f338fc083f7399f447 UNCHANGED WORKTREE_CLEAN
    debug 60 -> updates=60 draws=60 viewport=800x480 texture=128x128
    release 600 -> updates=600 draws=600 viewport=800x480 texture=128x128
GIT_DIFF_CHECK=CLEAN
```

**A warnings-as-errors caveat worth carrying forward.** An incremental
`swift build -Xswiftc -warnings-as-errors --build-tests` reports success while a
real diagnostic sits in the tree, because SwiftPM reuses artifacts built without
the flag. The gate is only meaningful after `find Sources Tests -name '*.swift'
-exec touch {} +`. Release additionally needs `-Xswiftc -enable-testing` to build
the test target at all. One real warning was found and fixed this way.

## Structural scoreboard

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=122
TARGET_MEMBERS=1684
TOTAL_DIAGNOSTICS=286
MISSING_TYPE=135
MISSING_MEMBER=131
COMPLETE_TYPES=117
PARTIAL_TYPES=5
MISSING_TYPES=135
UNEXPECTED_TYPE=0
UNEXPECTED_MEMBER=0
TYPE_KIND_MISMATCH=0
BASE_MAPPING_MISMATCH=2
INTERFACE_MAPPING_MISMATCH=1
FIELD_MAPPING_MISMATCH=0
PROPERTY_MAPPING_MISMATCH=1
METHOD_SIGNATURE_MAPPING_MISMATCH=0
PARAMETER_MAPPING_MISMATCH=0
RETURN_MAPPING_MISMATCH=0
OVERLOAD_MAPPING_MISMATCH=16
GENERIC_MAPPING_MISMATCH=0
ENUM_VALUE_MISMATCH=0
FLAGS_MAPPING_MISMATCH=0
EVENT_MAPPING_MISMATCH=0
OPERATOR_MAPPING_MISMATCH=0
REF_OUT_MAPPING_MISMATCH=0
LANGUAGE_MAPPING_MISMATCH=0
INTERNAL_TYPE_LEAK=0
RAW_HANDLE_LEAK=0
PUBLIC_NATIVE_FFI_LEAK=0
UNMEASURED_STRUCTURAL_CATEGORY=0
ALLOWLIST_ENTRIES=0
APPLIED_ALLOWLIST_ENTRIES=0
EVENT_PROJECTIONS=49
EVENT_SUPPORT_TYPE_MEASUREMENTS=4
MEASURED_SUPPORT_BASE_PROJECTIONS=4
ARRAY_MUTATION_MAPPINGS=20
NONPUBLIC_CONSTRUCTION_PROJECTIONS=8
```

All 151 non-`MISSING_TYPE` diagnostics remain owned exclusively by the five
runtime partials — `Game`, `GraphicsDeviceManager`, `GraphicsDevice`,
`Texture2D`, `SpriteBatch` — which are untouched. `MISSING_MEMBER` held at 131
through all three milestones. The ABI is unchanged.

## Types completed this session

Nine types, 43 mapped Swift XNA identities.

```text
Microsoft.Xna.Framework.IUpdateable                              5
Microsoft.Xna.Framework.IDrawable                                5
Microsoft.Xna.Framework.GameComponentCollectionEventArgs         2
Microsoft.Xna.Framework.Graphics.ResourceCreatedEventArgs        1
Microsoft.Xna.Framework.Graphics.ResourceDestroyedEventArgs      2
Microsoft.Xna.Framework.Audio.AudioListener                      5
Microsoft.Xna.Framework.Input.Touch.TouchCollection             15
Microsoft.Xna.Framework.Input.Touch.TouchCollection.Enumerator   3
Microsoft.Xna.Framework.Media.Video                              5
```

## The event architecture, as built

`System.EventHandler<TArgs>` → one get-only property per event, keeping the XNA
name, of type `CNAEvent<TArgs>`. No `add_`/`remove_`/`raise_` XNA identity; any
such name in the strict surface is reported as a leaked CLR accessor.

| Support type | Role |
|---|---|
| `CNAEvent<TArgs>` | Consumer view. Exactly `Add` and `Remove`. Cannot raise. |
| `CNAEventSource<TArgs>` | Declaring side. Owns storage, exposes `Event` and `Raise`. |
| `CNAEventSubscription` | Opaque token returned by `Add`. |

`CNAEventSource` is **composed** with `CNAEvent`, never derived from it — both
are `final` with no superclass — so a consumer handed the view has no downcast
to `Raise`; the compiler rejects the attempt outright. It is public so an
external package can conform to `IUpdateable`/`IDrawable` and raise its own
events. The same shape is what a future native-raised event will use: a
protected runtime type owns the source privately and a native callback calls
`Raise`.

Token semantics, recorded honestly as a `LANGUAGE_PROJECTION` rather than as
equivalence: CLR matches handlers by delegate identity and Swift closures have
none, so adding one closure twice creates two independently removable
registrations. Removing twice, or removing another event's token, is harmless.
The token does not unsubscribe on `deinit`. Dispatch walks a snapshot in
registration order; a throwing handler propagates its own error, stops the
dispatch, and leaves the list intact.

`CNAEventArgs` is now an `open class`, deliberately not `Sendable`, with `Empty`
as one shared instance — derived from all 46 `ldsfld System.EventArgs::Empty`
raise sites and zero `newobj` in the registered assemblies. Its base is
**measured**: `System.EventArgs → CNAEventArgs` is checked exactly as an XNA
base is.

## Verifier work

- `EVENT_MAPPING_MISMATCH` was a measured category that had never been
  exercised. It now covers 49 event projections plus the four support types,
  measured against a pinned shape in `mapping-rules.json`.
- **Undecided BCL bases are no longer silently droppable.** A non-XNA base that
  is neither a CLR root nor a decided support projection reports
  `UNMEASURED_STRUCTURAL_CATEGORY` if a type carrying it is implemented. This
  guards 21 still-missing types, `GameComponentCollection` among them.
- `IList<T>` is a measured direct interface, and the `CopyTo` caller-owned
  destination rule accepts it as well as `ICollection<T>`.
- Swift's `any P` existential spelling normalizes away; `some P` deliberately
  does not.
- `CNAError` gained `notSupported`.
- Self-tests 1,994 → 2,126. Every new rule was confirmed to bite by disabling it
  and observing the specific failures.

## Why this session stopped

**All remaining safe managed work is exhausted, and every remaining frontier
needs a decision, a runtime, or hardware.** The dependency graph reports 32
dependency-complete missing types; each is blocked by one of:

| Blocker | Types | Notes |
|---|---|---|
| Undecided **throwing property writer** | `AudioEmitter`, `GameWindow`, `ContentManager`, `SpriteFont` | See below. The highest-value decision. |
| Undecided BCL base | 13 — 8 exceptions, 5 `ContentSerializer*Attribute`, `MathTypeConverter`, `GameComponentCollection`, `LaunchParameters` | Now machine-guarded. |
| Undecided BCL member type | `VisualizationData`, `SpriteFont` (`ReadOnlyCollection<T>`), `GameServiceContainer` (`System.Type`) | |
| Real hardware | `GraphicsAdapter`, `Input.Mouse`, `TouchPanel`, `Microphone` | |
| Real runtime subsystem | `EffectAnnotation`, `ContentManager`, `TitleContainer`, `FrameworkDispatcher`, `AudioCategory`, `MediaSource` | `FrameworkDispatcher.Update()` pumps audio/media/networking; a no-op would be fabricated. |
| Unspecified BCL hash | `RendererDetail` (`System.String.GetHashCode`) | |
| Protected runtime partial | `SpriteFont` (`Texture2D`) | |

`GameComponent` and `DrawableGameComponent` are not in that list at all: they
depend on the `Game` and `GraphicsDevice` partials, so they are not
dependency-complete. They were **not** forced, and the dependency-complete rule
was not weakened to improve the scoreboard.

## Recommended next frontier

**The general throwing property writer.** This is now the highest-value
remaining decision, and it is quantified rather than guessed. A machine scan of
every public instance setter in the registered `Microsoft.Xna.Framework.dll`,
`Graphics.dll` and `Game.dll` finds **35 of 278 can throw**. Three are indexers
that repository policy already resolves — a read/write CLR indexer becomes a
throwing `Item` plus a throwing `SetItem`. The other **32 are plain
properties**:

```text
 6  GraphicsDevice        BlendState, DepthStencilState, RasterizerState,
                          Viewport, Indices, ScissorRectangle
 5  SoundEffect           Name, MasterVolume, SpeedOfSound, DopplerScale,
                          DistanceScale
 4  SoundEffectInstance   Volume, Pitch, Pan, IsLooped
 3  Game                  InactiveSleepTime, TargetElapsedTime, Content
 2  GraphicsDeviceManager PreferredBackBufferWidth, PreferredBackBufferHeight
 1  each                  AudioEmitter.DopplerScale, Microphone.BufferDuration,
                          ContentManager.RootDirectory, SpriteFont.DefaultCharacter,
                          GameWindow.Title, GraphicsDeviceInformation.Adapter,
                          Effect.CurrentTechnique, SkinnedEffect.WeightsPerVertex,
                          DynamicSoundEffectInstance.IsLooped,
                          ContentSerializerAttribute.CollectionItemName,
                          DecompressStream.Position, ImageStream.Position
```

Swift has no throwing property setter. The project has already met this and has
**not** resolved it: `GraphicsDevice.Viewport` is projected get-only and its
`PROPERTY_MAPPING_MISMATCH` is one of the four deferred partial-owned
diagnostics. Eleven of the 32 live on the protected runtime partials, whose
eventual native implementations must follow whatever is chosen — which is the
decisive reason not to settle it inside a managed batch, exactly as the event
projection was not.

Concrete alternatives, none of which repository policy picks:

1. **Generalize the indexed rule** — a get-only property plus a throwing
   `SetName(_:)` method. Consistent with the existing `Item`/`SetItem`
   precedent and already measured machinery, but it renames 32 public writers
   and makes them not look like properties.
2. **Read/write property whose setter traps** on invalid input. Keeps property
   syntax; converts a catchable CLR exception into a fatal error, which the
   documented error policy forbids ("Ordinary failures never use `fatalError`").
3. **Read/write property that stores without validating**, with a separate
   throwing validator. Fabricates acceptance of values XNA rejects.
4. **Leave them get-only** and carry a measured `PROPERTY_MAPPING_MISMATCH` per
   property, as `GraphicsDevice.Viewport` does today. Honest, but it would move
   `PROPERTY_MAPPING_MISMATCH` from 1 to 33 and block 4 types from ever being
   complete.

Option 1 is the closest fit to existing policy; the choice is still a material
public-API decision, so it is left to the user.

After that, in value order: `System.Exception` (8 types, 2 via
`ExternalException`, 4 with a `(SerializationInfo, StreamingContext)`
constructor), `System.Collections.ObjectModel.Collection<T>` and
`ReadOnlyCollection<T>` (which together unblock `GameComponentCollection`,
`VisualizationData` and 4 model types), `System.Attribute` (5 types),
`System.Type`/`IServiceProvider` (`GameServiceContainer`), and
`Dictionary<K,V>` (`LaunchParameters`).

## Unchanged partial types

- `Microsoft.Xna.Framework.Game`
- `Microsoft.Xna.Framework.GraphicsDeviceManager`
- `Microsoft.Xna.Framework.Graphics.GraphicsDevice`
- `Microsoft.Xna.Framework.Graphics.Texture2D`
- `Microsoft.Xna.Framework.Graphics.SpriteBatch`

No event was added to any of them. Those events need real lifecycle and native
raising, and an event that never fires is not implemented.

## Registered reference assemblies

Unchanged; all seven still reproduce the contract's 257 types and 2,964 members
exactly. They live in
`/rv/tmp/samples/SAMPLE-017-CollisionSample_4_0/xna4-build/bin` (Framework,
Graphics, Game, Input.Touch) and
`/rv/tmp/samples/_tools/xna-game-studio-4-refresh/admin/Program Files/Microsoft
XNA/XNA Game Studio/v4.0/References/Windows/x86` (Xact, Video, Storage), and
were hash-matched before use. **No XNA reference input is missing, and no
missing software or Debian package is required** — `swift` 6.0.3 (at
`/tmp/cna-swift-toolchain-6.0.3`), `ikdasm`, `monodis` and `mono` are all
present and were all used.

```text
SELECTED_ONLY=false
STARTED=false
```
