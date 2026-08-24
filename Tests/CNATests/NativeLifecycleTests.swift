// SPDX-License-Identifier: MIT

import Foundation
import XCTest
@testable import CNA

private enum CallbackProbeError: Error, Equatable {
    case initialize
    case loadContent
    case update
    case draw
    case unloadContent
}

private enum StressProbeError: Error {
    case invalidPNGWasAccepted
}

private let nativeTestPNG = Data(base64Encoded:
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+Xw2kWQAAAABJRU5ErkJggg=="
)!

private final class LockedErrorBox: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Error?

    func store(_ error: Error) {
        lock.lock()
        value = error
        lock.unlock()
    }

    func take() -> Error? {
        lock.lock()
        defer { lock.unlock() }
        return value
    }
}

private final class LifecycleProbeGame: Microsoft.Xna.Framework.Game {
    let frameLimit: Int
    var events: [String] = []
    var Updates = 0
    var Draws = 0
    var viewport: Microsoft.Xna.Framework.Graphics.Viewport?
    var observedPressedKeys: [Microsoft.Xna.Framework.Input.Keys] = []
    var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?
    var texture: Microsoft.Xna.Framework.Graphics.Texture2D?
    var spriteBatch: Microsoft.Xna.Framework.Graphics.SpriteBatch?

    init(frameLimit: Int, exerciseGraphics: Bool = false) throws {
        self.frameLimit = frameLimit
        try super.init()
        if exerciseGraphics {
            manager = try Microsoft.Xna.Framework.GraphicsDeviceManager(game: self)
        }
    }

    override func Initialize() throws { events.append("Initialize") }

    override func LoadContent() throws {
        events.append("LoadContent")
        guard manager != nil else { return }
        let device = try GraphicsDevice
        viewport = try device.Viewport
        try device.Clear(.CornflowerBlue)
        observedPressedKeys = try Microsoft.Xna.Framework.Input.Keyboard.GetState().GetPressedKeys()

        // A test-owned, valid 1x1 RGBA PNG. Its native-reported dimensions are
        // asserted below; Texture2D never synthesizes those dimensions.
        texture = try Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(
            device,
            stream: InputStream(data: nativeTestPNG)
        )
        spriteBatch = try Microsoft.Xna.Framework.Graphics.SpriteBatch(graphicsDevice: device)
    }

    override func BeginRun() throws { events.append("BeginRun") }

    override func Update(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        XCTAssertGreaterThanOrEqual(gameTime.TotalGameTime, .zero)
        XCTAssertGreaterThan(gameTime.ElapsedGameTime, .zero)
        Updates += 1
        if Updates == frameLimit { try Exit() }
    }

    override func Draw(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        Draws += 1
        guard let texture, let spriteBatch else { return }
        try GraphicsDevice.Clear(.CornflowerBlue)
        try spriteBatch.Begin()
        try spriteBatch.Draw(
            texture,
            position: Microsoft.Xna.Framework.Vector2(Float(Draws), 2),
            sourceRectangle: nil,
            color: .White,
            rotation: Float(Draws) * 0.01,
            origin: .Zero,
            scale: 1,
            effects: .None,
            layerDepth: 0
        )
        try spriteBatch.End()
    }

    override func EndRun() throws { events.append("EndRun") }
    override func UnloadContent() throws { events.append("UnloadContent") }
    override func OnExiting(_ sender: Any?, args: CNAEventArgs) throws { events.append("Exiting") }
}

private final class ResourceStressGame: Microsoft.Xna.Framework.Game {
    var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?
    var retainedTexture: Microsoft.Xna.Framework.Graphics.Texture2D?
    var retainedBatch: Microsoft.Xna.Framework.Graphics.SpriteBatch?
    var retainedBorrow: Microsoft.Xna.Framework.Graphics.GraphicsDevice?
    var TextureCycles = 0
    var SpriteBatchCycles = 0

    override init() throws {
        try super.init()
        manager = try Microsoft.Xna.Framework.GraphicsDeviceManager(game: self)
    }

    override func LoadContent() throws {
        let device = try GraphicsDevice
        retainedBorrow = device
        for index in 0..<20 {
            let texture = try Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(
                device,
                stream: InputStream(data: nativeTestPNG)
            )
            TextureCycles += 1
            let batch = try Microsoft.Xna.Framework.Graphics.SpriteBatch(graphicsDevice: device)
            SpriteBatchCycles += 1
            try batch.Begin()
            try batch.Draw(
                texture,
                position: Microsoft.Xna.Framework.Vector2(Float(index), Float(index)),
                color: .White
            )
            try batch.End()
            try batch.Dispose()
            try batch.Dispose()
            try texture.Dispose()
            try texture.Dispose()
        }

        do {
            _ = try Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(
                device,
                stream: InputStream(data: Data([0x00, 0x01, 0x02, 0x03]))
            )
            throw StressProbeError.invalidPNGWasAccepted
        } catch StressProbeError.invalidPNGWasAccepted {
            throw StressProbeError.invalidPNGWasAccepted
        } catch {
            // A structured native decode failure is the required result.
        }

        retainedTexture = try Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(
            device,
            stream: InputStream(data: nativeTestPNG)
        )
        retainedBatch = try Microsoft.Xna.Framework.Graphics.SpriteBatch(graphicsDevice: device)
    }

    override func Update(_ gameTime: Microsoft.Xna.Framework.GameTime) throws { try Exit() }
}

private final class FailingProbeGame: Microsoft.Xna.Framework.Game {
    let failure: CallbackProbeError

    init(_ failure: CallbackProbeError) throws {
        self.failure = failure
        try super.init()
    }

    override func Initialize() throws {
        if failure == .initialize { throw CallbackProbeError.initialize }
    }

    override func LoadContent() throws {
        if failure == .loadContent { throw CallbackProbeError.loadContent }
    }

    override func Update(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        if failure == .update { throw CallbackProbeError.update }
        if failure == .unloadContent { try Exit() }
    }

    override func Draw(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        if failure == .draw { throw CallbackProbeError.draw }
    }

    override func UnloadContent() throws {
        if failure == .unloadContent { throw CallbackProbeError.unloadContent }
    }
}

final class NativeLifecycleTests: XCTestCase {
    private var nativeConfigured: Bool {
        guard let value = ProcessInfo.processInfo.environment["CNA_NATIVE_LIBRARY"] else { return false }
        return value.hasPrefix("/") && FileManager.default.fileExists(atPath: value)
    }

    private func requireNative() throws {
        if !nativeConfigured { throw XCTSkip("set CNA_NATIVE_LIBRARY to an exact ABI-0.7 library") }
    }

    func testNativeGameSixtyFramesAndGraphicsCanary() throws {
        try requireNative()
        let game = try LifecycleProbeGame(frameLimit: 60, exerciseGraphics: true)
        try game.Run()
        XCTAssertEqual(game.Updates, 60)
        XCTAssertGreaterThanOrEqual(game.Draws, 59)
        XCTAssertEqual(game.viewport?.Width, 800)
        XCTAssertEqual(game.viewport?.Height, 480)
        XCTAssertEqual(game.texture?.Width, 1)
        XCTAssertEqual(game.texture?.Height, 1)
        XCTAssertTrue(game.observedPressedKeys.isEmpty)
        XCTAssertEqual(Array(game.events.prefix(3)), ["Initialize", "LoadContent", "BeginRun"])
        XCTAssertTrue(game.events.contains("EndRun"))
        try game.Dispose()
        XCTAssertTrue(game.events.contains("UnloadContent"))
        XCTAssertTrue(game.events.contains("Exiting"))
    }

    func testNativeGameSixHundredFrames() throws {
        try requireNative()
        let game = try LifecycleProbeGame(frameLimit: 600)
        try game.Run()
        XCTAssertEqual(game.Updates, 600)
        XCTAssertGreaterThanOrEqual(game.Draws, 599)
        try game.Dispose()
    }

    func testCallbackErrorsReturnToRunBoundary() throws {
        try requireNative()
        for failure in [CallbackProbeError.initialize, .loadContent, .update, .draw] {
            let game = try FailingProbeGame(failure)
            XCTAssertThrowsError(try game.Run()) { error in
                XCTAssertEqual(error as? CallbackProbeError, failure)
            }
            try game.Dispose()
        }

        let unloadGame = try FailingProbeGame(.unloadContent)
        try unloadGame.Run()
        XCTAssertThrowsError(try unloadGame.Dispose()) { error in
            XCTAssertEqual(error as? CallbackProbeError, .unloadContent)
        }
    }

    func testTwentyGameRecreations() throws {
        try requireNative()
        for _ in 0..<20 {
            let game = try LifecycleProbeGame(frameLimit: 1)
            try game.Run()
            try game.Dispose()
            XCTAssertThrowsError(try game.Run())
        }
    }

    func testTwentyTextureAndSpriteBatchCycles() throws {
        try requireNative()
        let game = try ResourceStressGame()
        try game.Run()
        XCTAssertEqual(game.TextureCycles, 20)
        XCTAssertEqual(game.SpriteBatchCycles, 20)
        XCTAssertThrowsError(try game.retainedBorrow?.Clear(.Black))

        let captured = LockedErrorBox()
        let finished = expectation(description: "wrong-thread Texture2D.Dispose returned")
        Thread.detachNewThread {
            do { try game.retainedTexture?.Dispose() } catch { captured.store(error) }
            finished.fulfill()
        }
        wait(for: [finished], timeout: 10)
        guard case .ownerThreadViolation? = captured.take() as? CNAError else {
            return XCTFail("wrong-thread resource disposal did not report owner-thread failure")
        }
        try game.retainedTexture?.Dispose()

        let retainedTexture = game.retainedTexture
        let retainedBatch = game.retainedBatch
        try game.Dispose()
        try retainedTexture?.Dispose()
        try retainedBatch?.Dispose()
        XCTAssertThrowsError(try game.retainedBorrow?.Clear(.Black))
    }

    func testTwentyCallbackErrorCycles() throws {
        try requireNative()
        for index in 0..<20 {
            let failure: CallbackProbeError = index.isMultiple(of: 2) ? .update : .draw
            let game = try FailingProbeGame(failure)
            XCTAssertThrowsError(try game.Run()) { error in
                XCTAssertEqual(error as? CallbackProbeError, failure)
            }
            try game.Dispose()
        }
    }

    func testWrongThreadDisposeKeepsHandleForOwnerRetry() throws {
        try requireNative()
        let game = try LifecycleProbeGame(frameLimit: 1)
        try game.Run()
        let finished = expectation(description: "wrong-thread Dispose returned")
        let captured = LockedErrorBox()
        Thread.detachNewThread {
            do { try game.Dispose() } catch { captured.store(error) }
            finished.fulfill()
        }
        wait(for: [finished], timeout: 10)
        let error = captured.take()
        guard case .ownerThreadViolation? = error as? CNAError else {
            return XCTFail("expected owner-thread error, got \(String(describing: error))")
        }
        try game.Dispose()
    }
}
