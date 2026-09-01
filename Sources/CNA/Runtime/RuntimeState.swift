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

    // ------------------------------------------------------------------
    // Device-owned managed state.
    //
    // XNA's `GraphicsDevice` is one long-lived object per device, and its
    // `cachedBlendState`, its two `SamplerStateCollection`s and the values it
    // copies out of a state on assignment all live as long as the device does.
    // `set_BlendState`'s early-out is REFERENCE equality against that field.
    //
    // CNA's device handle cannot carry that: measured with
    // `build-probe/f42b_identity.c`, `cna_game_get_graphics_device` answers a
    // handle that is stable within one lifecycle callback and DIFFERENT in
    // every callback, so it is a per-callback capability token rather than the
    // device's identity. The Swift `GraphicsDevice` facade is built fresh on
    // every access to match, and anything cached on it would be lost.
    //
    // The object that does have the device's lifetime is the game, and this is
    // its runtime state. So the cache lives here and the facade reads and
    // writes through it. That is a divergence in where the storage physically
    // sits, which is not observable, decided by a measurement rather than by
    // convenience.
    var cachedBlendState: Microsoft.Xna.Framework.Graphics.BlendState?
    var cachedDepthStencilState: Microsoft.Xna.Framework.Graphics.DepthStencilState?
    var cachedRasterizerState: Microsoft.Xna.Framework.Graphics.RasterizerState?

    // `set_BlendState` copies these two out of the state it accepts, and
    // `set_DepthStencilState` copies the third. They are separate fields on
    // XNA's device, not reads through the cached state, so a later mutation of
    // a state object would not move them -- which is moot for a bound state
    // but is the shape being reproduced.
    var cachedBlendFactor = Microsoft.Xna.Framework.Color.White
    var cachedMultiSampleMask: Int32 = -1
    var cachedReferenceStencil: Int32 = 0

    // XNA re-applies when the flag is set even if the same instance is
    // assigned again. `set_RasterizerState` has NO such flag: an identical
    // instance is always a no-op there, with no escape hatch.
    //
    // **Both flags are permanently false today**, because the two things that
    // set them in XNA -- a device reset and an effect pass ending -- are not
    // projected yet. They are transcribed rather than omitted so that the
    // setters are the algorithm XNA runs and not a simplification of it, but
    // nothing in this binding can currently observe the difference between
    // having a flag and not having one. That is why the mutation aimed at the
    // rasterizer's *absence* of a flag was withdrawn as unfalsifiable rather
    // than left in the harness claiming coverage it does not have: see
    // `docs/foundation-45-device-state-evidence.md`.
    var blendStateDirty = false
    var depthStencilStateDirty = false

    /// `currentRenderTargets[0]`, as `get_DefaultClearOptions` reads it.
    ///
    /// XNA keeps an array and a count; this binding binds only the single
    /// `SetRenderTarget(RenderTarget2D)` route, so one slot is the whole of
    /// what it can honestly track. Nil means the backbuffer, which is XNA's
    /// `currentRenderTargetCount == 0` branch. It lives here rather than on
    /// the facade for the same reason the state cache does: the facade is a
    /// per-callback token, not an identity.
    ///
    /// Weak, where XNA's array is a strong reference. A strong one here would
    /// close a retain cycle -- runtime to target to device facade and back to
    /// runtime -- that nothing would ever break, and the difference between
    /// the two is confined to a target whose last reference the caller has
    /// already dropped while it is still bound. CNA refuses to leave that
    /// state cleanly: `cna_render_target_destroy` on a bound target answers
    /// `CNA_RESULT_INVALID_STATE`, measured in `build-probe/f48b_params.c`,
    /// so a caller who drops a bound target has already stranded the native
    /// object whatever this reference does. Reporting the backbuffer's depth
    /// format for a target that is no longer projected is the honest answer
    /// of the two.
    weak var currentRenderTarget: Microsoft.Xna.Framework.Graphics.RenderTarget2D?

    // XNA builds both collections in the GraphicsDevice constructor, with
    // `ProfileCapabilities.MaxSamplers` (16 in both profiles) and
    // `MaxVertexSamplers` (0 under Reach, 4 under HiDef) slots and offsets 0
    // and 0x101. They are created lazily here because `RuntimeState` exists
    // before any device does, and creating them eagerly would claim a lifetime
    // this binding cannot justify.
    private var pixelSamplerStates: Microsoft.Xna.Framework.Graphics.SamplerStateCollection?
    private var vertexSamplerStates: Microsoft.Xna.Framework.Graphics.SamplerStateCollection?

    /// `CNA_MAX_SAMPLERS`, measured with `build-probe/f42_states.c`: CNA
    /// accepts slots 0 through 15 on **both** stages and answers
    /// `CNA_RESULT_INVALID_ARGUMENT` for 16 and above.
    ///
    /// A recorded divergence. XNA's vertex collection is 0 long under Reach
    /// and 4 under HiDef, and this binding has no profile selection, so both
    /// collections are the length CNA actually accepts. The bounds check is
    /// observable, so this is a behaviour decision and is recorded in
    /// `docs/runtime-capabilities.json` rather than left implicit.
    static let maxSamplers = 16

    func samplerStates(
        for device: Microsoft.Xna.Framework.Graphics.GraphicsDevice, vertex: Bool
    ) -> Microsoft.Xna.Framework.Graphics.SamplerStateCollection {
        if vertex {
            if let existing = vertexSamplerStates {
                existing.rebind(to: device)
                return existing
            }
            let created = Microsoft.Xna.Framework.Graphics.SamplerStateCollection(
                device: device, samplerOffset: 0x101, stage: 1,
                count: RuntimeState.maxSamplers)
            vertexSamplerStates = created
            return created
        }
        if let existing = pixelSamplerStates {
            existing.rebind(to: device)
            return existing
        }
        let created = Microsoft.Xna.Framework.Graphics.SamplerStateCollection(
            device: device, samplerOffset: 0, stage: 0,
            count: RuntimeState.maxSamplers)
        pixelSamplerStates = created
        return created
    }

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
