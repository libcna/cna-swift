// SPDX-License-Identifier: MIT

import CNAShim
import Foundation

internal enum RuntimeRegistry {
    private static let lock = NSLock()
    private static weak var callbackRuntime: RuntimeState?

    static func enter(_ runtime: RuntimeState) {
        lock.lock()
        callbackRuntime = runtime
        lock.unlock()
    }

    static func leave(_ runtime: RuntimeState) {
        lock.lock()
        if callbackRuntime === runtime { callbackRuntime = nil }
        lock.unlock()
    }

    static func current() throws -> RuntimeState {
        lock.lock()
        defer { lock.unlock() }
        guard let callbackRuntime else { throw CNAError.callbackOutsideGameLifecycle }
        return callbackRuntime
    }
}

internal final class RuntimeState {
    let functions: NativeFunctions
    let generation: UInt64
    let owner: OwnerThread
    weak var game: Microsoft.Xna.Framework.Game?

    private(set) var gameHandle: UInt64 = 0
    private(set) var isActive = true
    private(set) var callbackEpoch: UInt64 = 0
    private(set) var isInsideCallback = false
    private var callbackError: Error?
    private var children: [WeakRuntimeChild] = []

    init(functions: NativeFunctions) {
        self.functions = functions
        generation = GenerationSequence.next()
        owner = OwnerThread()
    }

    func installGameHandle(_ handle: UInt64) { gameHandle = handle }

    func validateGeneration(_ expected: UInt64) throws {
        guard isActive, expected == generation else {
            throw CNAError.staleRuntimeGeneration(expected: expected, actual: isActive ? generation : nil)
        }
    }

    func enterCallback(nativeGame: UInt64) throws {
        try owner.validate("Game callback")
        try validateGeneration(generation)
        guard nativeGame == gameHandle else {
            throw CNAError.nativeFailure(operation: "Game callback handle validation", result: 2, message: "native callback supplied another Game handle")
        }
        callbackEpoch &+= 1
        if callbackEpoch == 0 { callbackEpoch = 1 }
        isInsideCallback = true
        RuntimeRegistry.enter(self)
    }

    func leaveCallback() {
        isInsideCallback = false
        RuntimeRegistry.leave(self)
    }

    func validateBorrowed(epoch: UInt64, operation: String) throws {
        try validateGeneration(generation)
        try owner.validate(operation)
        guard isInsideCallback, callbackEpoch == epoch else {
            throw CNAError.callbackOutsideGameLifecycle
        }
    }

    func gameTime(from pointer: UnsafePointer<CNASwift_GameTime>?) throws -> Microsoft.Xna.Framework.GameTime {
        guard let value = pointer?.pointee else {
            throw CNAError.nativeFailure(operation: "GameTime callback", result: 12, message: "native update/draw omitted GameTime")
        }
        return Microsoft.Xna.Framework.GameTime(
            totalTicks: value.total_game_time_ticks,
            elapsedTicks: value.elapsed_game_time_ticks,
            runningSlowly: value.is_running_slowly != 0
        )
    }

    func storeCallbackError(_ error: Error) {
        if callbackError == nil { callbackError = error }
    }

    func clearCallbackError() { callbackError = nil }

    func takeCallbackError() -> Error? {
        defer { callbackError = nil }
        return callbackError
    }

    func register(_ child: RuntimeOwnedChild) {
        children.removeAll { $0.value == nil }
        children.append(WeakRuntimeChild(child))
    }

    func disposeChildren() throws {
        var firstError: Error?
        for weakChild in children.reversed() {
            guard let child = weakChild.value, !child.runtimeObjectIsDisposed else { continue }
            do { try child.disposeFromParent() } catch { if firstError == nil { firstError = error } }
        }
        children.removeAll { $0.value == nil || $0.value?.runtimeObjectIsDisposed == true }
        if let firstError { throw firstError }
    }

    func invalidateAfterNativeShutdown() {
        isActive = false
        gameHandle = 0
        isInsideCallback = false
        RuntimeRegistry.leave(self)
    }
}
