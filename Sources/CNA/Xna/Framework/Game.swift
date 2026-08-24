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

        open func Initialize() throws {}
        open func LoadContent() throws {}
        open func UnloadContent() throws {}
        open func Update(_ gameTime: GameTime) throws {}
        open func Draw(_ gameTime: GameTime) throws {}
        open func BeginRun() throws {}
        open func EndRun() throws {}
        open func BeginDraw() throws -> Bool { true }
        open func EndDraw() throws {}
        open func OnExiting(_ sender: Any?, args: CNAEventArgs) throws {}

        private func validatedHandle(_ operation: String) throws -> UInt64 {
            guard !disposed, runtime.gameHandle != 0 else { throw CNAError.disposedObject("Game") }
            try runtime.validateGeneration(runtime.generation)
            try runtime.owner.validate(operation)
            return runtime.gameHandle
        }
    }
}
