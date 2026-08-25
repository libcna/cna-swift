// SPDX-License-Identifier: MIT

import XCTest
@testable import CNA

// Swift-language qualification of the `IGraphicsDeviceService` projection. None
// of this is XNA runtime behaviour and none of it is counted as such: it
// measures the shape the Swift compiler actually emitted.
final class Foundation24ProjectionTests: XCTestCase {
    typealias Service = Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService

    private final class Stub: Service {
        let device: Microsoft.Xna.Framework.Graphics.GraphicsDevice?
        private let created = CNAEventSource<CNAEventArgs>()
        private let disposing = CNAEventSource<CNAEventArgs>()
        private let reset = CNAEventSource<CNAEventArgs>()
        private let resetting = CNAEventSource<CNAEventArgs>()

        init(device: Microsoft.Xna.Framework.Graphics.GraphicsDevice? = nil) {
            self.device = device
        }

        var GraphicsDevice: Microsoft.Xna.Framework.Graphics.GraphicsDevice? { device }
        var DeviceCreated: CNAEvent<CNAEventArgs> { created.Event }
        var DeviceDisposing: CNAEvent<CNAEventArgs> { disposing.Event }
        var DeviceReset: CNAEvent<CNAEventArgs> { reset.Event }
        var DeviceResetting: CNAEvent<CNAEventArgs> { resetting.Event }
    }

    // The requirement's declared type is exactly the Optional class, and the
    // reader is non-throwing: a key path can only be written when the type
    // matches, and Swift refuses one to a throwing property outright. Both
    // facts are the compiler's, not this test's.
    func testRequirementIsOptionalAndNonThrowing() {
        let path: KeyPath<Stub, Microsoft.Xna.Framework.Graphics.GraphicsDevice?> =
            \Stub.GraphicsDevice
        XCTAssertNil(Stub()[keyPath: path])
        XCTAssertNil(path as? ReferenceWritableKeyPath<
            Stub, Microsoft.Xna.Framework.Graphics.GraphicsDevice?>)
    }

    // A conformer is reachable through the existential, and reading the device
    // needs no `try`: the interface carries no failure path at all.
    func testExistentialReadNeedsNoTry() {
        let service: any Service = Stub()
        XCTAssertNil(service.GraphicsDevice)

        // The nil branch is an ordinary optional test, not error handling.
        let described = service.GraphicsDevice == nil ? "absent" : "present"
        XCTAssertEqual(described, "absent")
    }

    // The four events are get-only consumer views with stable identity, and no
    // `add_`/`remove_`/`raise_` accessor leaks into the protocol.
    func testEventsAreGetOnlyViewsWithStableIdentity() {
        let service = Stub()
        XCTAssertTrue(service.DeviceCreated === service.DeviceCreated)
        XCTAssertTrue(service.DeviceDisposing === service.DeviceDisposing)
        XCTAssertTrue(service.DeviceReset === service.DeviceReset)
        XCTAssertTrue(service.DeviceResetting === service.DeviceResetting)
        XCTAssertFalse(service.DeviceCreated === service.DeviceReset)

        let event: KeyPath<Stub, CNAEvent<CNAEventArgs>> = \Stub.DeviceCreated
        XCTAssertNil(event as? ReferenceWritableKeyPath<Stub, CNAEvent<CNAEventArgs>>)
    }

    // GraphicsDeviceManager is deliberately not a conformer: its own reader is
    // still `get throws` and non-Optional, which no `IGraphicsDeviceService`
    // requirement can witness.
    func testGraphicsDeviceManagerDoesNotConform() {
        XCTAssertFalse(
            (Microsoft.Xna.Framework.GraphicsDeviceManager.self as Any) is Service.Type)
    }
}
