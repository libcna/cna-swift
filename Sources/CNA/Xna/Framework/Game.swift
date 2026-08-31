// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework {
    /// The XNA Game class projected with subclassable lifecycle methods. CNA's
    /// native loop owns frame scheduling and invokes every override through the
    /// reviewed C callback trampolines.
    open class Game {
        internal let runtime: RuntimeState
        private let callbackContext: CallbackContext
        private var disposed = false
        private var callbackFailureWasSurfaced = false

        // ------------------------------------------------------------------
        // The managed component engine.
        //
        // `Game..ctor` allocates one `GameComponentCollection` and five
        // `List<T>`s and subscribes two private handlers to the collection's
        // events. Those handlers ARE the engine: `Components` on its own would
        // be a collection a consumer could add to and never see updated, which
        // is why Foundation 29 refused to ship it alone. All of it is managed
        // XNA behaviour -- the native host owns frame scheduling and nothing
        // else -- so all of it is projected here.
        //
        // The five lists are private state, not projections: `mscorlib`'s
        // `List<T>` is what the CLR uses for them, but nothing public exposes
        // them, so a Swift array is the same thing observed from outside.
        // ------------------------------------------------------------------

        private let gameComponents = GameComponentCollection()
        private var updateableComponents: [any IUpdateable] = []
        private var currentlyUpdatingComponents: [any IUpdateable] = []
        private var drawableComponents: [any IDrawable] = []
        private var currentlyDrawingComponents: [any IDrawable] = []
        private var notYetInitialized: [any IGameComponent] = []

        // `Game::inRun`. XNA sets it true between `BeginRun` and `EndRun`, and
        // `GameComponentAdded` branches on it: a component added before the
        // run is queued for initialization, one added during it is initialized
        // immediately. The CNA host issues both hooks, so the flag is real.
        private var inRun = false

        // Subscriptions the CLR expresses as `-=` on a delegate. Swift
        // closures have no identity, so the token the event returns is kept
        // beside the component it belongs to and matched back with the same
        // default equality every collection member uses.
        private var updateOrderSubscriptions:
            [(component: any IUpdateable, token: CNAEventSubscription)] = []
        private var drawOrderSubscriptions:
            [(component: any IDrawable, token: CNAEventSubscription)] = []

        /// `Game.LaunchParameters`.
        ///
        /// `Game..ctor` allocates exactly one and `get_LaunchParameters` is a
        /// bare field read, so this is the same object on every read and it
        /// carries this process's parsed arguments.
        public let LaunchParameters = Microsoft.Xna.Framework.LaunchParameters()

        /// `Game.Components`.
        ///
        /// `get_Components` is a bare field read of the single collection
        /// `Game..ctor` allocates, so this is the same object on every read.
        /// Adding to it drives the engine below through the collection's own
        /// events, exactly as it does in XNA.
        public var Components: GameComponentCollection { gameComponents }

        public init() throws {
            let functions = try NativeFunctions.load()
            let runtime = RuntimeState(functions: functions)
            self.runtime = runtime
            callbackContext = CallbackContext(runtime: runtime)

            var callbacks = CNASwift_GameCallbacks()
            callbacks.struct_size = UInt32(MemoryLayout<CNASwift_GameCallbacks>.size)
            callbacks.struct_version = 1
            callbacks.load_content = gameLoadContentCallback
            callbacks.update = gameUpdateCallback
            callbacks.draw = gameDrawCallback
            callbacks.unload_content = gameUnloadContentCallback
            callbacks.exiting = gameExitingCallback
            callbacks.context = callbackContext.pointer

            var handle: UInt64 = 0
            let createResult = withUnsafePointer(to: &callbacks) { callbacksPointer -> UInt32 in
                var createInfo = CNASwift_GameCreateInfo()
                createInfo.struct_size = UInt32(MemoryLayout<CNASwift_GameCreateInfo>.size)
                createInfo.struct_version = 1
                createInfo.is_fixed_time_step = 1
                createInfo.target_elapsed_time_ticks = 166_667
                createInfo.window_title = CNASwift_StringView(data: nil, byte_length: 0)
                createInfo.callbacks = callbacksPointer
                return withUnsafePointer(to: &createInfo) {
                    functions.gameCreate($0, &handle)
                }
            }
            do {
                try functions.check(createResult, operation: "cna_game_create")
            } catch {
                callbackContext.releaseAfterNativeStopsCalling()
                throw error
            }
            runtime.installGameHandle(handle)

            var hooks = CNASwift_GameFrameHooks()
            hooks.struct_size = UInt32(MemoryLayout<CNASwift_GameFrameHooks>.size)
            hooks.struct_version = 1
            hooks.initialize = gameInitializeCallback
            hooks.begin_run = gameBeginRunCallback
            hooks.end_run = gameEndRunCallback
            hooks.begin_draw = gameBeginDrawCallback
            hooks.end_draw = gameEndDrawCallback
            hooks.context = callbackContext.pointer
            let hookResult = withUnsafePointer(to: &hooks) {
                functions.gameSetFrameHooks(handle, $0)
            }
            do {
                try functions.check(hookResult, operation: "cna_game_set_frame_hooks_ext")
            } catch {
                _ = functions.gameDestroy(handle)
                runtime.invalidateAfterNativeShutdown()
                callbackContext.releaseAfterNativeStopsCalling()
                throw error
            }
            runtime.game = self

            // `Game..ctor` subscribes these two immediately after allocating
            // the collection. `self` is captured weakly: the CLR delegate
            // holds a strong reference and its cycle is a garbage collector's
            // problem, while here the collection is owned BY the game, so a
            // strong capture would keep every game alive forever.
            _ = gameComponents.ComponentAdded.Add { [weak self] _, args in
                try self?.gameComponentAdded(args.GameComponent)
            }
            _ = gameComponents.ComponentRemoved.Add { [weak self] _, args in
                self?.gameComponentRemoved(args.GameComponent)
            }
        }

        deinit {
            guard !disposed, runtime.owner.isCurrent else { return }
            try? Dispose()
        }

        public func Run() throws {
            let handle = try validatedHandle("Game.Run")
            runtime.clearCallbackError()
            callbackFailureWasSurfaced = false
            let result = runtime.functions.gameRun(handle)
            if let callbackError = runtime.takeCallbackError() {
                callbackFailureWasSurfaced = true
                throw callbackError
            }
            try runtime.functions.check(result, operation: "cna_game_run")
        }

        public func RunOneFrame() throws {
            let handle = try validatedHandle("Game.RunOneFrame")
            runtime.clearCallbackError()
            callbackFailureWasSurfaced = false
            let result = runtime.functions.gameRunOneFrame(handle)
            if let callbackError = runtime.takeCallbackError() {
                callbackFailureWasSurfaced = true
                throw callbackError
            }
            try runtime.functions.check(result, operation: "cna_game_run_one_frame")
        }

        public func Exit() throws {
            let handle = try validatedHandle("Game.Exit")
            try runtime.functions.check(
                runtime.functions.gameRequestExit(handle),
                operation: "cna_game_request_exit"
            )
        }

        public func Dispose() throws {
            if disposed { return }
            try runtime.owner.validate("Game.Dispose")
            try runtime.disposeChildren()
            runtime.clearCallbackError()
            let handle = try validatedHandle("Game.Dispose")
            let result = runtime.functions.gameDestroy(handle)
            if result != 0 && result != 9 {
                try runtime.functions.check(result, operation: "cna_game_destroy")
            }
            disposed = true
            runtime.invalidateAfterNativeShutdown()
            callbackContext.releaseAfterNativeStopsCalling()
            if let callbackError = runtime.takeCallbackError() { throw callbackError }
            if result == 9 && !callbackFailureWasSurfaced {
                throw CNAError.nativeFailure(
                    operation: "cna_game_destroy callback",
                    result: result,
                    message: "native shutdown callback failed without a stored Swift Error"
                )
            }
            callbackFailureWasSurfaced = false
        }

        public var GraphicsDevice: Graphics.GraphicsDevice {
            get throws { try Graphics.GraphicsDevice.borrow(from: runtime) }
        }

        /// `protected virtual void Initialize()`.
        ///
        /// The IL is
        ///
        /// ```text
        /// HookDeviceEvents()
        /// while (notYetInitialized.Count != 0) {
        ///     notYetInitialized[0].Initialize()
        ///     notYetInitialized.RemoveAt(0)
        /// }
        /// if (graphicsDeviceService != null && GraphicsDevice != null)
        ///     LoadContent()
        /// ```
        ///
        /// Two things about the transcription:
        ///
        /// - the drain takes index **0** each time and removes it, so a
        ///   component whose own `Initialize` adds another component sees that
        ///   one initialized too, in the same pass. Iterating a snapshot would
        ///   not;
        /// - `LoadContent()` is **not** called here. The CNA host issues that
        ///   call as its own `load_content` callback, immediately after this
        ///   one -- measured, not assumed, by
        ///   `testNativeCallbackOrderIsMeasuredNotAssumed`. The two are the
        ///   same XNA lifecycle occurrence; calling it here as well would give
        ///   a consumer two invocations for one, and assigning it to the one
        ///   callback path is what keeps the invariant.
        ///
        /// `HookDeviceEvents` is absent because the device events it hooks are
        /// not projected; nothing is invented in its place. Two consequences
        /// of that absence are recorded rather than half-reproduced, because
        /// closing either needs `IGraphicsDeviceService`:
        ///
        /// - XNA calls `LoadContent` only `if (graphicsDeviceService != null
        ///   && GraphicsDevice != null)`. Here the host decides, so a game
        ///   with no `GraphicsDeviceManager` still receives `LoadContent`;
        /// - XNA's `LoadContent` fires from **inside** this base body, so an
        ///   override that does not call `super.Initialize()` never receives
        ///   it. Here it arrives on its own callback and so always does.
        ///
        /// Gating the callback on this body having run would fix the second
        /// and would also suppress the device-reset reload XNA issues through
        /// the very handlers `HookDeviceEvents` installs -- behaviour this
        /// host has not been measured for. A guard that trades a known
        /// divergence for an unmeasured one is not an improvement.
        open func Initialize() throws {
            while !notYetInitialized.isEmpty {
                let component = notYetInitialized[0]
                try component.Initialize()
                // Guard against a handler having already drained it.
                if !notYetInitialized.isEmpty {
                    notYetInitialized.remove(at: 0)
                }
            }
        }

        open func LoadContent() throws {}
        open func UnloadContent() throws {}

        /// `protected virtual void Update(GameTime gameTime)`.
        ///
        /// ```text
        /// for (i = 0; i < updateableComponents.Count; i++)
        ///     currentlyUpdatingComponents.Add(updateableComponents[i])
        /// for (j = 0; j < currentlyUpdatingComponents.Count; j++) {
        ///     var u = currentlyUpdatingComponents[j]
        ///     if (u.Enabled) u.Update(gameTime)
        /// }
        /// currentlyUpdatingComponents.Clear()
        /// ```
        ///
        /// The copy is what makes mutation during traversal safe: a component
        /// that adds or removes another during its own `Update` changes
        /// `updateableComponents`, not the list being walked, so the current
        /// pass runs over exactly the components that were present when it
        /// began. `Enabled` is read per component at the moment it is reached,
        /// so a component disabled by an earlier one in the same pass is
        /// skipped.
        open func Update(_ gameTime: GameTime) throws {
            for component in updateableComponents {
                currentlyUpdatingComponents.append(component)
            }
            var index = 0
            while index < currentlyUpdatingComponents.count {
                let component = currentlyUpdatingComponents[index]
                if component.Enabled { try component.Update(gameTime) }
                index += 1
            }
            currentlyUpdatingComponents.removeAll(keepingCapacity: true)
        }

        /// `protected virtual void Draw(GameTime gameTime)`.
        ///
        /// The same shape as `Update`, over `drawableComponents` and guarded
        /// by `Visible`.
        open func Draw(_ gameTime: GameTime) throws {
            for component in drawableComponents {
                currentlyDrawingComponents.append(component)
            }
            var index = 0
            while index < currentlyDrawingComponents.count {
                let component = currentlyDrawingComponents[index]
                if component.Visible { try component.Draw(gameTime) }
                index += 1
            }
            currentlyDrawingComponents.removeAll(keepingCapacity: true)
        }

        /// `protected virtual void BeginRun()`.
        ///
        /// XNA's own body is empty. `inRun` is set by `RunGame` immediately
        /// **before** this call and cleared immediately after `EndRun`, and
        /// the CNA host issues both hooks at the same points -- measured, not
        /// assumed. Setting the flag here rather than in an invented place is
        /// what makes `GameComponentAdded`'s `inRun` branch real.
        open func BeginRun() throws {
            inRun = true
        }

        /// `protected virtual void EndRun()`. XNA's own body is empty.
        open func EndRun() throws {
            inRun = false
        }
        open func BeginDraw() throws -> Bool { true }
        open func EndDraw() throws {}
        open func OnExiting(_ sender: Any?, args: CNAEventArgs) throws {}

        // ------------------------------------------------------------------
        // `Game::GameComponentAdded` and `Game::GameComponentRemoved`.
        // ------------------------------------------------------------------

        /// ```text
        /// if (inRun) e.GameComponent.Initialize()
        /// else       notYetInitialized.Add(e.GameComponent)
        /// if (e.GameComponent is IUpdateable u) insert sorted, subscribe
        /// if (e.GameComponent is IDrawable d)   insert sorted, subscribe
        /// ```
        private func gameComponentAdded(
            _ component: any IGameComponent
        ) throws {
            if inRun {
                try component.Initialize()
            } else {
                notYetInitialized.append(component)
            }
            if let updateable = component as? any IUpdateable {
                insertUpdateable(updateable)
            }
            if let drawable = component as? any IDrawable {
                insertDrawable(drawable)
            }
        }

        /// ```text
        /// if (!inRun) notYetInitialized.Remove(e.GameComponent)
        /// if (u != null) { updateableComponents.Remove(u); u.UpdateOrderChanged -= h }
        /// if (d != null) { drawableComponents.Remove(d);   d.DrawOrderChanged  -= h }
        /// ```
        ///
        /// The `notYetInitialized` removal happens only when the game is not
        /// running, which is the same condition that put it there.
        private func gameComponentRemoved(_ component: any IGameComponent) {
            if !inRun {
                if let index = notYetInitialized.firstIndex(where: {
                    cnaDefaultEquals($0, component)
                }) {
                    notYetInitialized.remove(at: index)
                }
            }
            if let updateable = component as? any IUpdateable {
                removeUpdateable(updateable)
            }
            if let drawable = component as? any IDrawable {
                removeDrawable(drawable)
            }
        }

        /// The sorted insertion `GameComponentAdded` and
        /// `UpdateableUpdateOrderChanged` share.
        ///
        /// ```text
        /// i = updateableComponents.BinarySearch(u, UpdateOrderComparer.Default)
        /// if (i >= 0) return                       // already present
        /// i = ~i
        /// while (i < Count && list[i].UpdateOrder == u.UpdateOrder) i++
        /// updateableComponents.Insert(i, u)
        /// u.UpdateOrderChanged += UpdateableUpdateOrderChanged
        /// ```
        ///
        /// `UpdateOrderComparer.Compare` never returns 0 for two DISTINCT
        /// objects -- it returns 0 only when `x.Equals(y)` -- so the binary
        /// search finds a non-negative index only for a component that is
        /// already in the list, and the tie scan then places a new
        /// equal-ordered component **after** every existing one. That is what
        /// makes the ordering stable, and it is why a comparer that merely
        /// compared `UpdateOrder` would have been wrong.
        private func insertUpdateable(_ component: any IUpdateable) {
            guard !updateableComponents.contains(where: {
                cnaDefaultEquals($0, component)
            }) else { return }
            var index = updateableComponents.firstIndex {
                $0.UpdateOrder > component.UpdateOrder
            } ?? updateableComponents.count
            while index < updateableComponents.count,
                  updateableComponents[index].UpdateOrder == component.UpdateOrder {
                index += 1
            }
            updateableComponents.insert(component, at: index)
            let token = component.UpdateOrderChanged.Add { [weak self] sender, _ in
                guard let self, let changed = sender as? any IUpdateable else { return }
                self.removeUpdateable(changed, keepingSubscription: true)
                self.reinsertUpdateable(changed)
            }
            updateOrderSubscriptions.append((component, token))
        }

        private func insertDrawable(_ component: any IDrawable) {
            guard !drawableComponents.contains(where: {
                cnaDefaultEquals($0, component)
            }) else { return }
            var index = drawableComponents.firstIndex {
                $0.DrawOrder > component.DrawOrder
            } ?? drawableComponents.count
            while index < drawableComponents.count,
                  drawableComponents[index].DrawOrder == component.DrawOrder {
                index += 1
            }
            drawableComponents.insert(component, at: index)
            let token = component.DrawOrderChanged.Add { [weak self] sender, _ in
                guard let self, let changed = sender as? any IDrawable else { return }
                self.removeDrawable(changed, keepingSubscription: true)
                self.reinsertDrawable(changed)
            }
            drawOrderSubscriptions.append((component, token))
        }

        /// `Game::UpdateableUpdateOrderChanged` -- remove, then re-insert at
        /// the position the new order gives, WITHOUT resubscribing: the CLR
        /// handler does not touch the delegate.
        private func reinsertUpdateable(_ component: any IUpdateable) {
            var index = updateableComponents.firstIndex {
                $0.UpdateOrder > component.UpdateOrder
            } ?? updateableComponents.count
            while index < updateableComponents.count,
                  updateableComponents[index].UpdateOrder == component.UpdateOrder {
                index += 1
            }
            updateableComponents.insert(component, at: index)
        }

        private func reinsertDrawable(_ component: any IDrawable) {
            var index = drawableComponents.firstIndex {
                $0.DrawOrder > component.DrawOrder
            } ?? drawableComponents.count
            while index < drawableComponents.count,
                  drawableComponents[index].DrawOrder == component.DrawOrder {
                index += 1
            }
            drawableComponents.insert(component, at: index)
        }

        private func removeUpdateable(
            _ component: any IUpdateable, keepingSubscription: Bool = false
        ) {
            if let index = updateableComponents.firstIndex(where: {
                cnaDefaultEquals($0, component)
            }) {
                updateableComponents.remove(at: index)
            }
            guard !keepingSubscription else { return }
            if let index = updateOrderSubscriptions.firstIndex(where: {
                cnaDefaultEquals($0.component, component)
            }) {
                component.UpdateOrderChanged.Remove(
                    updateOrderSubscriptions[index].token)
                updateOrderSubscriptions.remove(at: index)
            }
        }

        private func removeDrawable(
            _ component: any IDrawable, keepingSubscription: Bool = false
        ) {
            if let index = drawableComponents.firstIndex(where: {
                cnaDefaultEquals($0, component)
            }) {
                drawableComponents.remove(at: index)
            }
            guard !keepingSubscription else { return }
            if let index = drawOrderSubscriptions.firstIndex(where: {
                cnaDefaultEquals($0.component, component)
            }) {
                component.DrawOrderChanged.Remove(
                    drawOrderSubscriptions[index].token)
                drawOrderSubscriptions.remove(at: index)
            }
        }

        private func validatedHandle(_ operation: String) throws -> UInt64 {
            guard !disposed, runtime.gameHandle != 0 else { throw CNAError.disposedObject("Game") }
            try runtime.validateGeneration(runtime.generation)
            try runtime.owner.validate(operation)
            return runtime.gameHandle
        }
    }
}
