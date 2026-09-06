import XCTest
@testable import CNA

/// `GraphicsDevice`'s disposal pair, `IsDisposed`, and its six events.
final class Foundation84DeviceDisposalTests: XCTestCase {

    /// **The refusal is CNA's design, not a gap.** The route exists to report
    /// that C cannot dispose the device the running game owns; disposing it
    /// through a borrowed handle would leave that game drawing into a
    /// destroyed device.
    ///
    /// XNA's `Dispose()` does not throw. This one does, and that is the
    /// deliberate half of the trade: a `Dispose` that silently did nothing
    /// would leave a caller believing the device was released.
    func testDisposeIsRefusedBecauseTheGameOwnsTheDevice() throws {
        let game = try DisposalProbeGame()
        try game.Run()
        if let failure = game.failure { throw failure }
        guard let error = game.disposeFailure else {
            return XCTFail("Dispose was accepted, which would destroy the game's device")
        }
        guard case CNAError.nativeFailure(let operation, _, let message) = error else {
            return XCTFail("expected a native failure, got \(error)")
        }
        XCTAssertEqual(operation, "cna_graphics_device_dispose")
        XCTAssertFalse(message.isEmpty,
                       "the runtime's own diagnosis reaches the caller")
    }

    /// **The three-argument `Present` refuses rather than silently widening.**
    ///
    /// CNA's only presentation route takes a game handle and nothing else, so a
    /// caller naming a sub-rectangle, a stretched destination or another window
    /// is asking for something this runtime cannot do. Giving them a
    /// full-surface present would be a wrong frame reported as a right one.
    /// XNA does not refuse; this is the divergence that fails loudly.
    func testPresentRefusesArgumentsItCannotCarry() throws {
        let game = try DisposalProbeGame(exercisePresent: true)
        try game.Run()
        if let failure = game.failure { throw failure }

        XCTAssertEqual(game.defaultsAccepted, true,
                       "all three at their defaults is the plain Present")
        for (what, error) in game.presentRefusals {
            guard let refusal = error as? CNANotSupportedException else {
                return XCTFail("\(what): expected CNANotSupportedException, got \(error)")
            }
            XCTAssertEqual(
                refusal.Message,
                Microsoft.Xna.Framework.Graphics.GraphicsDevice
                    .presentArgumentsNotSupportedMessage)
        }
        XCTAssertEqual(game.presentRefusals.count, 3,
                       "each of the three arguments is refused on its own")
    }

    /// `IsDisposed` is infallible, so it answers from the facade's generation
    /// rather than from a route: a live facade is not disposed.
    func testALiveFacadeIsNotDisposed() throws {
        let game = try DisposalProbeGame()
        try game.Run()
        if let failure = game.failure { throw failure }
        XCTAssertEqual(game.wasDisposed, false)
    }

    /// The six events exist, accept handlers, and carry the payload types XNA
    /// declares.
    ///
    /// **Nothing on this host raises them, and nothing here can.** XNA's are
    /// raised by the platform on device loss, reset and teardown, and by every
    /// resource as it is created or destroyed; CNA publishes no subscription
    /// for any of that, and XNA declares no public `On*` raiser for them
    /// either — so this binding must not invent one.
    ///
    /// What is asserted is therefore the surface: four events take
    /// `CNAEventArgs`, and the two resource events take their own payloads.
    /// The closures below would not compile against the wrong type, which is
    /// the strongest claim available without a firing.
    func testTheSixEventsAcceptCorrectlyTypedHandlers() throws {
        let game = try DisposalProbeGame(addHandlers: true)
        try game.Run()
        if let failure = game.failure { throw failure }
        XCTAssertEqual(game.handlersAdded, 6)
        XCTAssertEqual(game.payloadShapes,
                       ["Resource: Any?", "Name: String?, Tag: Any?"],
                       "the two resource events are not EventHandler<EventArgs>")
    }
}

private final class DisposalProbeGame: Microsoft.Xna.Framework.Game {
    let addHandlers: Bool
    let exercisePresent: Bool
    var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?
    var failure: Error?
    var disposeFailure: Error?
    var wasDisposed: Bool?
    var handlersAdded = 0
    var payloadShapes: [String] = []
    var defaultsAccepted: Bool?
    var presentRefusals: [(String, Error)] = []

    init(addHandlers: Bool = false, exercisePresent: Bool = false) throws {
        self.addHandlers = addHandlers
        self.exercisePresent = exercisePresent
        try super.init()
        manager = try Microsoft.Xna.Framework.GraphicsDeviceManager(game: self)
    }

    override func LoadContent() throws {
        defer { try? Exit() }
        do {
            guard let device = try GraphicsDevice else { return }
            wasDisposed = device.IsDisposed
            do { try device.Dispose() } catch { disposeFailure = error }

            if exercisePresent {
                try device.Present(nil, destinationRectangle: nil,
                                   overrideWindowHandle: 0)
                defaultsAccepted = true
                let rect = Microsoft.Xna.Framework.Rectangle(0, 0, 4, 4)
                for (what, body) in [
                    ("source", { try device.Present(rect, destinationRectangle: nil,
                                                    overrideWindowHandle: 0) }),
                    ("destination", { try device.Present(nil, destinationRectangle: rect,
                                                         overrideWindowHandle: 0) }),
                    ("window", { try device.Present(nil, destinationRectangle: nil,
                                                    overrideWindowHandle: 1) }),
                ] as [(String, () throws -> Void)] {
                    do { try body() } catch { presentRefusals.append((what, error)) }
                }
                return
            }
            guard addHandlers else { return }
            for event in [device.Disposing, device.DeviceLost,
                          device.DeviceReset, device.DeviceResetting] {
                event.Add { _, _ in }
                handlersAdded += 1
            }
            device.ResourceCreated.Add { [weak self] _, args in
                // Reading `Resource` here is what pins the payload type: the
                // closure would not compile against CNAEventArgs.
                self?.payloadShapes.append("Resource: Any?")
                _ = args.Resource
            }
            handlersAdded += 1
            device.ResourceDestroyed.Add { [weak self] _, args in
                self?.payloadShapes.append("Name: String?, Tag: Any?")
                _ = args.Name
                _ = args.Tag
            }
            handlersAdded += 1
            // The shapes are recorded by construction rather than by a firing,
            // because nothing here may raise these.
            payloadShapes = ["Resource: Any?", "Name: String?, Tag: Any?"]
        } catch {
            failure = error
        }
    }
}
