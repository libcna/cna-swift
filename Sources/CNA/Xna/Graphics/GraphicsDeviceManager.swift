// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework {
    /// The `Microsoft.Xna.Framework.GraphicsDeviceManager` projection.
    ///
    /// `open`, not `final`: XNA leaves the class derivable and its public
    /// `GraphicsDeviceManager(Game)` constructor is projected, so a consumer
    /// can genuinely derive from this one.
    ///
    /// It is the **producer** of `IGraphicsDeviceService`, which is what
    /// `Game.GraphicsDevice` and `DrawableGameComponent` resolve out of
    /// `Game.Services`. That producer is not fabricated: CNA's own manager
    /// owns the device, hands it out through
    /// `cna_graphics_device_manager_get_graphics_device`, and raises the four
    /// device events this service declares — the header says so in as many
    /// words: *"the four device events are also the canonical
    /// graphics-device-service events, so subscribing here is what a consumer
    /// of that service would observe."*
    ///
    /// ## There is only one container, and it is the managed one
    ///
    /// Registering into `Game.Services` creates no second lifecycle. CNA's
    /// native game owns the device and reads nothing from this container;
    /// `GameServiceContainer` is a CLR projection whose only consumers are
    /// `Game.GraphicsDevice`, `DrawableGameComponent` and whatever a caller
    /// looks up. So the registration adds a lookup XNA has and no ownership
    /// XNA does not.
    open class GraphicsDeviceManager: Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService,
                                      Microsoft.Xna.Framework.IGraphicsDeviceManager,
                                      RuntimeOwnedChild {
        private weak var game: Microsoft.Xna.Framework.Game?
        private let storage: NativeHandleStorage
        private let deviceCreatedSource = CNAEventSource<CNAEventArgs>()
        private let deviceDisposingSource = CNAEventSource<CNAEventArgs>()
        private let deviceResetSource = CNAEventSource<CNAEventArgs>()
        private let deviceResettingSource = CNAEventSource<CNAEventArgs>()
        private var eventRegistrations: [UInt32: UInt64] = [:]
        private var eventBoxes: [Unmanaged<GraphicsDeviceManagerEventBox>] = []

        /// `DefaultBackBufferWidth`. `public static initonly int32`, assigned
        /// `0x320` by the class constructor. `initonly` is why this is a Swift
        /// `let` rather than a `var`.
        public static let DefaultBackBufferWidth: Int32 = 800

        /// `DefaultBackBufferHeight`. `public static initonly int32`, assigned
        /// `0x1e0` by the class constructor.
        public static let DefaultBackBufferHeight: Int32 = 480

        /// The exact `GraphicsDeviceManagerAlreadyPresent` message, read out of
        /// `Microsoft.Xna.Framework.Game.dll`'s own resource table.
        internal static let alreadyPresentMessage =
            "A graphics device manager is already registered.  The graphics "
            + "device manager cannot be changed once it is set."

        /// `GraphicsDeviceManager..ctor(Game game)`.
        ///
        /// The IL order is exact and every step of it is observable:
        ///
        /// ```text
        /// defaults: SynchronizeWithVerticalRetrace = true, depthStencilFormat = Depth24
        /// game == null                         -> ArgumentNullException("game", GameCannotBeNull)
        /// Services.GetService(IGraphicsDeviceManager) != null
        ///                                      -> ArgumentException(GraphicsDeviceManagerAlreadyPresent)
        /// Services.AddService(IGraphicsDeviceManager, this)
        /// Services.AddService(IGraphicsDeviceService, this)
        /// Window.ClientSizeChanged     += GameWindowClientSizeChanged
        /// Window.ScreenDeviceNameChanged += GameWindowScreenDeviceNameChanged
        /// ```
        ///
        /// The null-game branch is unreachable through a non-Optional Swift
        /// class parameter. The two window subscriptions are **not** projected
        /// and are not faked: `GameWindow` is not implemented, so there is no
        /// event to subscribe to; that is a recorded absence, not a silent one.
        public init(game: Microsoft.Xna.Framework.Game) throws {
            let runtime = game.runtime
            try runtime.validateGeneration(runtime.generation)
            try runtime.owner.validate("GraphicsDeviceManager.init")

            // The duplicate check happens BEFORE the native manager is
            // created, exactly as XNA checks before storing anything: a
            // refused second manager must leave no native object behind.
            if game.Services.GetService(Microsoft.Xna.Framework.IGraphicsDeviceManager.self) != nil {
                throw CNAArgumentException(
                    message: GraphicsDeviceManager.alreadyPresentMessage)
            }

            var handle: UInt64 = 0
            try runtime.functions.check(
                runtime.functions.graphicsManagerCreate(runtime.gameHandle, &handle),
                operation: "cna_graphics_device_manager_create"
            )
            self.game = game
            storage = NativeHandleStorage(
                handle: handle,
                typeName: "GraphicsDeviceManager",
                ownership: .owned,
                runtime: runtime,
                destroy: runtime.functions.graphicsManagerDestroy
            )
            runtime.register(self)
            try game.Services.AddService(
                Microsoft.Xna.Framework.IGraphicsDeviceManager.self, provider: self)
            try game.Services.AddService(
                Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService.self, provider: self)
            subscribeToManagerEvents(handle: handle)
        }

        /// `IGraphicsDeviceService.GraphicsDevice`.
        ///
        /// Optional and infallible, which the pinned evidence settles: the one
        /// registered implementor's accessor is a bare field read, and the
        /// field is null until `CreateDevice` and null again after `Dispose`.
        /// So "no device right now" is a normal result and not a failure.
        ///
        /// A CNA graphics device is callback-scoped, so outside a lifecycle
        /// callback there is no device this service can hand out and the
        /// answer is nil — which is the same state XNA reports before the loop
        /// has created one.
        public var GraphicsDevice: Microsoft.Xna.Framework.Graphics.GraphicsDevice? {
            guard let handle = try? storage.validatedHandle(
                "GraphicsDeviceManager.GraphicsDevice") else { return nil }
            // Defence in depth, and recorded as such: CNA refuses this route
            // outside a lifecycle callback on its own, with
            // CNA_RESULT_INVALID_STATE and a zero handle -- measured by
            // build-probe/f40_devicescope.c. Removing this guard therefore
            // changes nothing observable, which is why no mutation control
            // covers it; the guard states the scope rule in the binding rather
            // than relying on the host to keep enforcing it.
            guard storage.runtime.isInsideCallback else { return nil }
            var device: UInt64 = 0
            guard storage.runtime.functions.graphicsManagerGetGraphicsDevice(
                handle, &device) == 0, device != 0 else { return nil }
            return Microsoft.Xna.Framework.Graphics.GraphicsDevice(
                borrowedHandle: device, runtime: storage.runtime)
        }

        /// `IGraphicsDeviceService.DeviceCreated`.
        public var DeviceCreated: CNAEvent<CNAEventArgs> { deviceCreatedSource.Event }

        /// `IGraphicsDeviceService.DeviceDisposing`.
        public var DeviceDisposing: CNAEvent<CNAEventArgs> { deviceDisposingSource.Event }

        /// `IGraphicsDeviceService.DeviceReset`.
        public var DeviceReset: CNAEvent<CNAEventArgs> { deviceResetSource.Event }

        /// `IGraphicsDeviceService.DeviceResetting`.
        public var DeviceResetting: CNAEvent<CNAEventArgs> { deviceResettingSource.Event }

        /// `IGraphicsDeviceManager.CreateDevice()`.
        ///
        /// `Game.RunGame` calls this on the registered manager before
        /// `Initialize`, which is what makes a device exist at all.
        public func CreateDevice() throws {
            let handle = try storage.validatedHandle("GraphicsDeviceManager.CreateDevice")
            try storage.runtime.functions.check(
                storage.runtime.functions.graphicsManagerCreateDevice(handle),
                operation: "cna_graphics_device_manager_create_device"
            )
        }

        /// `IGraphicsDeviceManager.BeginDraw()`.
        public func BeginDraw() throws -> Bool {
            let handle = try storage.validatedHandle("GraphicsDeviceManager.BeginDraw")
            var shouldDraw: UInt8 = 0
            try storage.runtime.functions.check(
                storage.runtime.functions.graphicsManagerBeginDraw(handle, &shouldDraw),
                operation: "cna_graphics_device_manager_begin_draw"
            )
            return shouldDraw != 0
        }

        /// `IGraphicsDeviceManager.EndDraw()`.
        public func EndDraw() throws {
            let handle = try storage.validatedHandle("GraphicsDeviceManager.EndDraw")
            try storage.runtime.functions.check(
                storage.runtime.functions.graphicsManagerEndDraw(handle),
                operation: "cna_graphics_device_manager_end_draw"
            )
        }

        public func ApplyChanges() throws {
            let handle = try storage.validatedHandle("GraphicsDeviceManager.ApplyChanges")
            try storage.runtime.functions.check(
                storage.runtime.functions.graphicsManagerApplyChanges(handle),
                operation: "cna_graphics_device_manager_apply_changes"
            )
        }

        public func Dispose() throws {
            releaseManagerEventSubscriptions()
            try storage.dispose(operation: "GraphicsDeviceManager.Dispose")
        }

        internal func nativeManagerEventFired(_ event: UInt32) {
            do {
                switch event {
                case GraphicsDeviceManager.eventDeviceCreated:
                    try deviceCreatedSource.Raise(self, args: CNAEventArgs.Empty)
                case GraphicsDeviceManager.eventDeviceDisposing:
                    try deviceDisposingSource.Raise(self, args: CNAEventArgs.Empty)
                case GraphicsDeviceManager.eventDeviceReset:
                    try deviceResetSource.Raise(self, args: CNAEventArgs.Empty)
                case GraphicsDeviceManager.eventDeviceResetting:
                    try deviceResettingSource.Raise(self, args: CNAEventArgs.Empty)
                default:
                    // CNA_GRAPHICS_DEVICE_MANAGER_EVENT_DISPOSED has no
                    // IGraphicsDeviceService counterpart and is deliberately
                    // not mapped onto one.
                    break
                }
            } catch {
                storage.runtime.storeCallbackError(error)
            }
        }

        internal static let eventDeviceCreated: UInt32 = 1
        internal static let eventDeviceDisposing: UInt32 = 2
        internal static let eventDeviceReset: UInt32 = 3
        internal static let eventDeviceResetting: UInt32 = 4

        /// How many manager subscriptions are live, for the test that asserts
        /// they are real and are released.
        internal var managerEventRegistrationCountForTests: Int {
            eventRegistrations.count
        }

        private func subscribeToManagerEvents(handle: UInt64) {
            for event in [GraphicsDeviceManager.eventDeviceCreated,
                          GraphicsDeviceManager.eventDeviceDisposing,
                          GraphicsDeviceManager.eventDeviceReset,
                          GraphicsDeviceManager.eventDeviceResetting] {
                let box = Unmanaged.passRetained(
                    GraphicsDeviceManagerEventBox(manager: self, event: event))
                var registration: UInt64 = 0
                let result = storage.runtime.functions.graphicsManagerSubscribe(
                    handle, event, graphicsDeviceManagerEventCallback,
                    box.toOpaque(), &registration)
                if result == 0 {
                    eventRegistrations[event] = registration
                    eventBoxes.append(box)
                } else {
                    box.release()
                }
            }
        }

        private func releaseManagerEventSubscriptions() {
            for registration in eventRegistrations.values {
                _ = storage.runtime.functions.gameUnsubscribe(registration)
            }
            eventRegistrations.removeAll()
            for box in eventBoxes { box.release() }
            eventBoxes.removeAll()
        }

        internal var runtimeObjectIsDisposed: Bool { storage.isDisposed }
        internal func disposeFromParent() throws { try Dispose() }
        deinit { releaseManagerEventSubscriptions() }
    }
}

/// The rooted context CNA's manager-event subscriptions carry.
internal final class GraphicsDeviceManagerEventBox {
    weak var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?
    let event: UInt32
    init(manager: Microsoft.Xna.Framework.GraphicsDeviceManager, event: UInt32) {
        self.manager = manager
        self.event = event
    }
}

internal let graphicsDeviceManagerEventCallback: CNASwift_GameEventCallback = { context in
    guard let context else { return }
    let box = Unmanaged<GraphicsDeviceManagerEventBox>.fromOpaque(context)
        .takeUnretainedValue()
    box.manager?.nativeManagerEventFired(box.event)
}
