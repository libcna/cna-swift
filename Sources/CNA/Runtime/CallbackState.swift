// SPDX-License-Identifier: MIT

import CNAShim

internal final class CallbackContext {
    private(set) var pointer: UnsafeMutableRawPointer?

    init(runtime: RuntimeState) {
        pointer = Unmanaged.passRetained(runtime).toOpaque()
    }

    func releaseAfterNativeStopsCalling() {
        guard let pointer else { return }
        Unmanaged<RuntimeState>.fromOpaque(pointer).release()
        self.pointer = nil
    }
}

private enum LifecyclePhase {
    case initialize
    case loadContent
    case update
    case draw
    case unloadContent
    case exiting
    case beginRun
    case endRun
    case endDraw
}

private func dispatchLifecycle(
    context: UnsafeMutableRawPointer?,
    nativeGame: UInt64,
    nativeTime: UnsafePointer<CNASwift_GameTime>?,
    phase: LifecyclePhase
) -> UInt32 {
    guard let context else { return 9 }
    let runtime = Unmanaged<RuntimeState>.fromOpaque(context).takeUnretainedValue()
    do {
        try runtime.enterCallback(nativeGame: nativeGame)
        defer { runtime.leaveCallback() }
        guard let game = runtime.game else { throw CNAError.disposedObject("Game") }
        switch phase {
        case .initialize: try game.Initialize()
        case .loadContent: try game.LoadContent()
        case .update: try game.Update(runtime.gameTime(from: nativeTime))
        case .draw: try game.Draw(runtime.gameTime(from: nativeTime))
        case .unloadContent: try game.UnloadContent()
        case .exiting: try game.OnExiting(game, args: CNAEventArgs.Empty)
        case .beginRun: try game.BeginRun()
        case .endRun: try game.EndRun()
        case .endDraw: try game.EndDraw()
        }
        return 0
    } catch {
        runtime.storeCallbackError(error)
        return 9
    }
}

internal let gameInitializeCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .initialize)
}

internal let gameLoadContentCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .loadContent)
}

internal let gameUpdateCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .update)
}

internal let gameDrawCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .draw)
}

internal let gameUnloadContentCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .unloadContent)
}

internal let gameExitingCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .exiting)
}

internal let gameBeginRunCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .beginRun)
}

internal let gameEndRunCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .endRun)
}

internal let gameEndDrawCallback: CNASwift_GameLifecycleCallback = { game, time, context, _ in
    dispatchLifecycle(context: context, nativeGame: game, nativeTime: time, phase: .endDraw)
}

internal let gameBeginDrawCallback: CNASwift_GameBeginDrawCallback = { game, _, context, shouldDraw, _ in
    guard let context else { return 9 }
    let runtime = Unmanaged<RuntimeState>.fromOpaque(context).takeUnretainedValue()
    do {
        try runtime.enterCallback(nativeGame: game)
        defer { runtime.leaveCallback() }
        guard let swiftGame = runtime.game else { throw CNAError.disposedObject("Game") }
        shouldDraw?.pointee = try swiftGame.BeginDraw() ? 1 : 0
        return 0
    } catch {
        runtime.storeCallbackError(error)
        return 9
    }
}
