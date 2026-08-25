#!/usr/bin/env python3
"""Audit an exact source archive and qualify a fresh independent consumer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

PACKAGE = '''// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CNAArchiveConsumer",
    dependencies: [.package(path: "{dependency}")],
    targets: [.executableTarget(
        name: "ArchiveCanary",
        dependencies: [.product(name: "CNA", package: "{identity}")]
    )]
)
'''

SOURCE = r'''import CNA
import Foundation

func qualifyManagedCurve() throws {
    typealias F = Microsoft.Xna.Framework
    let curve = F.Curve()
    let first = F.CurveKey(position: 2, value: 10, tangentIn: 3, tangentOut: 0)
    let last = F.CurveKey(position: 5, value: 22, tangentIn: 0, tangentOut: -4)
    curve.Keys.Add(last)
    curve.Keys.Add(first)
    guard curve.Keys.Count == 2, try curve.Keys.Item(0) === first else {
        throw CNAError.argument("isolated Curve collection qualification failed")
    }
    curve.ComputeTangents(.Smooth)
    curve.PreLoop = .CycleOffset
    curve.PostLoop = .Oscillate
    guard curve.Evaluate(1) == curve.Evaluate(4) - 12,
          curve.Evaluate(6).bitPattern == curve.Evaluate(4).bitPattern else {
        throw CNAError.argument("isolated Curve loop qualification failed")
    }
    let nan = F.CurveKey(position: .nan, value: 0)
    guard try nan.CompareTo(first) == 1, try first.CompareTo(nan) == 1 else {
        throw CNAError.argument("isolated Curve CompareTo qualification failed")
    }
    let enumerator = curve.Keys.GetEnumerator()
    curve.Keys.Add(F.CurveKey(position: 8, value: 30))
    do {
        _ = try enumerator.Next()
        throw CNAError.argument("isolated Curve enumerator did not invalidate")
    } catch CNAError.collectionModified {
        // Exact expected mutation failure.
    }
}

// DisplayMode is a managed descriptor with no public constructor, so an
// external consumer can name the type and consume its read-only surface but can
// never construct one and never needs a native library to do either. This
// closure compiles only if all six pinned identities are public with exactly
// these names, kinds and types, and it is deliberately never called with a
// value, because no external construction route exists.
func qualifyPublicDisplayModeSurface() throws {
    typealias Mode = Microsoft.Xna.Framework.Graphics.DisplayMode
    let read: (Mode) -> (Int32, Int32, Microsoft.Xna.Framework.Graphics.SurfaceFormat,
                         Float, Microsoft.Xna.Framework.Rectangle, String) = { mode in
        (mode.Width, mode.Height, mode.Format, mode.AspectRatio,
         mode.TitleSafeArea, mode.ToString())
    }
    _ = read
    guard String(describing: Mode.self) == "DisplayMode" else {
        throw CNAError.argument("isolated DisplayMode type qualification failed")
    }
}

final class ArchiveGame: Microsoft.Xna.Framework.Game {
    let requested: Int
    var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?
    var texture: Microsoft.Xna.Framework.Graphics.Texture2D?
    var batch: Microsoft.Xna.Framework.Graphics.SpriteBatch?
    var updates = 0
    var draws = 0

    init(_ requested: Int) throws {
        self.requested = requested
        try super.init()
        manager = try Microsoft.Xna.Framework.GraphicsDeviceManager(game: self)
    }

    override func LoadContent() throws {
        let bytes = Data(base64Encoded: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+Xw2kWQAAAABJRU5ErkJggg==")!
        let device = try GraphicsDevice
        texture = try Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(
            device, stream: InputStream(data: bytes))
        batch = try Microsoft.Xna.Framework.Graphics.SpriteBatch(graphicsDevice: device)
    }

    override func Update(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        updates += 1
        _ = try Microsoft.Xna.Framework.Input.Keyboard.GetState()
    }

    override func Draw(_ gameTime: Microsoft.Xna.Framework.GameTime) throws {
        guard let texture, let batch else { return }
        try GraphicsDevice.Clear(.CornflowerBlue)
        try batch.Begin()
        try batch.Draw(texture, position: .Zero, color: .White)
        try batch.End()
        draws += 1
        if draws == requested { try Exit() }
    }
}

// RenderTargetUsage is a pure managed non-flags Int32 enum. An external
// consumer must be able to name it in the exact Graphics namespace, read every
// pinned raw value, round-trip each one through the raw initializer, and get
// nil for an undefined pattern, all without a native library, a render target,
// or any device. Naming the type is not evidence that discard, preserve, or
// platform-defined content behavior exists anywhere in the runtime.
func qualifyPublicRenderTargetUsageSurface() throws {
    typealias Usage = Microsoft.Xna.Framework.Graphics.RenderTargetUsage
    let table: [(Int32, Usage)] = [
        (0, .DiscardContents), (1, .PreserveContents), (2, .PlatformContents),
    ]
    for (rawValue, value) in table {
        let observed: Int32 = value.rawValue
        guard observed == rawValue, Usage(rawValue: rawValue) == value else {
            throw CNAError.argument("isolated RenderTargetUsage table qualification failed")
        }
    }
    guard Usage(rawValue: 3) == nil, Usage(rawValue: -1) == nil,
          String(describing: Usage.self) == "RenderTargetUsage" else {
        throw CNAError.argument("isolated RenderTargetUsage projection qualification failed")
    }
}


// Foundation 14 pure managed batch. An external consumer must be able to name
// all 25 types in their exact namespaces, read every pinned raw value, and use
// the value struct and the two protocols, with no native library, no device,
// no buffer, no effect and no audio backend. Naming these types is a
// public-surface check only and carries no runtime behavior claim.
private final class ExternalGameComponent: Microsoft.Xna.Framework.IGameComponent {
    private(set) var initialized = false
    func Initialize() throws { initialized = true }
}

private final class ExternalDeviceManager:
    Microsoft.Xna.Framework.IGraphicsDeviceManager
{
    func CreateDevice() throws {}
    func BeginDraw() throws -> Bool { true }
    func EndDraw() throws {}
}

private struct ExternalFogWitness: Microsoft.Xna.Framework.Graphics.IEffectFog {
    var FogEnabled: Bool = false
    var FogStart: Float = 0
    var FogEnd: Float = 0
    var FogColor: Microsoft.Xna.Framework.Vector3 = .Zero
}

private struct ExternalMatricesWitness: Microsoft.Xna.Framework.Graphics.IEffectMatrices {
    var World: Microsoft.Xna.Framework.Matrix = .Identity
    var View: Microsoft.Xna.Framework.Matrix = .Identity
    var Projection: Microsoft.Xna.Framework.Matrix = .Identity
}

func qualifyFoundation14ManagedSurface() throws {
    typealias G = Microsoft.Xna.Framework.Graphics
    typealias A = Microsoft.Xna.Framework.Audio

    func check(_ condition: Bool, _ what: String) throws {
        guard condition else {
            throw CNAError.argument("isolated Foundation-14 \(what) qualification failed")
        }
    }

    // Ordinary Int32 raw enums: exact raw values, and no representation for an
    // undefined pattern.
    try check(G.GraphicsProfile.Reach.rawValue == 0 && G.GraphicsProfile.HiDef.rawValue == 1, "GraphicsProfile")
    try check(G.GraphicsProfile(rawValue: 2) == nil, "GraphicsProfile undefined")
    try check(G.PresentInterval.Default.rawValue == 0 && G.PresentInterval.Immediate.rawValue == 3, "PresentInterval")
    try check(G.VertexElementFormat.Single.rawValue == 0 && G.VertexElementFormat.HalfVector4.rawValue == 11, "VertexElementFormat")
    try check(G.VertexElementUsage.Position.rawValue == 0 && G.VertexElementUsage.TessellateFactor.rawValue == 12, "VertexElementUsage")
    try check(G.CompareFunction.Always.rawValue == 0 && G.CompareFunction.NotEqual.rawValue == 7, "CompareFunction")
    try check(G.CubeMapFace.PositiveX.rawValue == 0 && G.CubeMapFace.NegativeZ.rawValue == 5, "CubeMapFace")
    try check(G.IndexElementSize.SixteenBits.rawValue == 0 && G.IndexElementSize.ThirtyTwoBits.rawValue == 1, "IndexElementSize")
    try check(G.Blend.One.rawValue == 0 && G.Blend.SourceAlphaSaturation.rawValue == 12, "Blend")
    try check(G.BlendFunction.Add.rawValue == 0 && G.BlendFunction.Max.rawValue == 4, "BlendFunction")
    try check(G.CullMode.None.rawValue == 0 && G.CullMode.CullCounterClockwiseFace.rawValue == 2, "CullMode")
    try check(G.StencilOperation.Keep.rawValue == 0 && G.StencilOperation.Invert.rawValue == 7, "StencilOperation")
    try check(G.TextureAddressMode.Wrap.rawValue == 0 && G.TextureAddressMode.Mirror.rawValue == 2, "TextureAddressMode")
    try check(G.TextureFilter.Linear.rawValue == 0 && G.TextureFilter.MinPointMagLinearMipPoint.rawValue == 8, "TextureFilter")
    try check(G.GraphicsDeviceStatus.Normal.rawValue == 0 && G.GraphicsDeviceStatus.NotReset.rawValue == 2, "GraphicsDeviceStatus")
    try check(G.PrimitiveType.TriangleList.rawValue == 0 && G.PrimitiveType.LineStrip.rawValue == 3, "PrimitiveType")
    try check(G.EffectParameterClass.Scalar.rawValue == 0 && G.EffectParameterClass.Struct.rawValue == 4, "EffectParameterClass")
    try check(G.EffectParameterType.Void.rawValue == 0 && G.EffectParameterType.TextureCube.rawValue == 9, "EffectParameterType")
    try check(A.SoundState.Playing.rawValue == 0 && A.SoundState.Stopped.rawValue == 2, "SoundState")
    try check(A.AudioChannels.Mono.rawValue == 1 && A.AudioChannels.Stereo.rawValue == 2, "AudioChannels")
    try check(A.AudioChannels(rawValue: 0) == nil, "AudioChannels undefined zero")

    // The three pinned [Flags] enums are Int32 OptionSets.
    func requireInt32OptionSet<T: OptionSet>(_ value: T) -> Int32 where T.RawValue == Int32 {
        value.rawValue
    }
    try check(requireInt32OptionSet(G.ColorWriteChannels.All) == 15, "ColorWriteChannels")
    try check(G.ColorWriteChannels.All.rawValue ==
              G.ColorWriteChannels.Red.rawValue | G.ColorWriteChannels.Green.rawValue |
              G.ColorWriteChannels.Blue.rawValue | G.ColorWriteChannels.Alpha.rawValue,
              "ColorWriteChannels composite")
    try check(requireInt32OptionSet(G.ClearOptions.Target.union(.DepthBuffer).union(.Stencil)) == 7, "ClearOptions")
    try check(requireInt32OptionSet(G.SetDataOptions.None) == 0 &&
              G.SetDataOptions.NoOverwrite.rawValue == 2, "SetDataOptions")

    // The value struct: verbatim construction, four-field equality, the
    // reference word-XOR hash with its zero substitution, and the exact string.
    var element = G.VertexElement(12, .Vector3, .Normal, 3)
    try check(element.Offset == 12 && element.VertexElementFormat == .Vector3 &&
              element.VertexElementUsage == .Normal && element.UsageIndex == 3, "VertexElement storage")
    element.Offset = -4
    try check(element.Offset == -4, "VertexElement mutation")
    try check(G.VertexElement(0, .Vector3, .Position, 0) == G.VertexElement(0, .Vector3, .Position, 0), "VertexElement equality")
    try check(G.VertexElement(0, .Vector3, .Position, 0) != G.VertexElement(1, .Vector3, .Position, 0), "VertexElement inequality")
    try check(G.VertexElement(0, .Single, .Position, 0).GetHashCode() == Int32.max, "VertexElement zero hash")
    try check(G.VertexElement(8, .Vector2, .Color, 4).GetHashCode() == 8 ^ 1 ^ 1 ^ 4, "VertexElement hash")
    try check(G.VertexElement(0, .Vector3, .Position, 0).ToString() ==
              "{Offset:0 Format:Vector3 Usage:Position UsageIndex:0}", "VertexElement string")
    try check(!G.VertexElement(0, .Vector3, .Position, 0).Equals(nil), "VertexElement Equals null")

    // The two protocols are externally conformable with exactly their pinned
    // requirement sets.
    var fog = ExternalFogWitness()
    fog.FogEnabled = true
    fog.FogEnd = 40
    // Spelled in full rather than through the `G` typealias: Swift 6.0.3
    // asserts while mangling debug info for an existential named through a
    // nested typealias ("While mangling type for debugger type 'any
    // G.IEffectFog'"). The protocol itself is fine either way.
    let readFog: Microsoft.Xna.Framework.Graphics.IEffectFog = fog
    try check(readFog.FogEnabled && readFog.FogEnd == 40, "IEffectFog")
    let readMatrices: Microsoft.Xna.Framework.Graphics.IEffectMatrices =
        ExternalMatricesWitness()
    try check(readMatrices.World == Microsoft.Xna.Framework.Matrix.Identity, "IEffectMatrices")
}


// Foundation 15-18: the managed surface added after the Foundation 14 batch,
// exercised from an *external* module. The in-module tests use
// `@testable import`, so only this canary can prove what the genuinely public
// surface allows and forbids.
// Foundation 19: real *external* conformers to the XNA event-bearing
// protocols. This is the canary that matters most for the event architecture:
// only a package outside CNA can prove that a user type can own private
// CNAEventSource instances, publish CNAEvent views, satisfy every protocol
// requirement, and raise its own events — with no `@testable import` and no
// access to anything internal.
private final class ExternalUpdateable: Microsoft.Xna.Framework.IUpdateable {
    private let enabledChangedSource = CNAEventSource<CNAEventArgs>()
    private let updateOrderChangedSource = CNAEventSource<CNAEventArgs>()
    private var enabled = true
    private var updateOrder: Int32 = 0
    private(set) var updates = 0

    var Enabled: Bool { enabled }

    var UpdateOrder: Int32 { updateOrder }

    var EnabledChanged: CNAEvent<CNAEventArgs> { enabledChangedSource.Event }

    var UpdateOrderChanged: CNAEvent<CNAEventArgs> { updateOrderChangedSource.Event }

    func Update(_ gameTime: Microsoft.Xna.Framework.GameTime) throws { updates += 1 }

    func setEnabled(_ value: Bool) throws {
        guard enabled != value else { return }
        enabled = value
        try enabledChangedSource.Raise(self, args: CNAEventArgs.Empty)
    }

    func setUpdateOrder(_ value: Int32) throws {
        guard updateOrder != value else { return }
        updateOrder = value
        try updateOrderChangedSource.Raise(self, args: CNAEventArgs.Empty)
    }
}

private final class ExternalDrawable: Microsoft.Xna.Framework.IDrawable {
    private let visibleChangedSource = CNAEventSource<CNAEventArgs>()
    private let drawOrderChangedSource = CNAEventSource<CNAEventArgs>()
    private var visible = true
    private var drawOrder: Int32 = 0
    private(set) var draws = 0

    var Visible: Bool { visible }

    var DrawOrder: Int32 { drawOrder }

    var VisibleChanged: CNAEvent<CNAEventArgs> { visibleChangedSource.Event }

    var DrawOrderChanged: CNAEvent<CNAEventArgs> { drawOrderChangedSource.Event }

    func Draw(_ gameTime: Microsoft.Xna.Framework.GameTime) throws { draws += 1 }

    func setVisible(_ value: Bool) throws {
        guard visible != value else { return }
        visible = value
        try visibleChangedSource.Raise(self, args: CNAEventArgs.Empty)
    }

    func setDrawOrder(_ value: Int32) throws {
        guard drawOrder != value else { return }
        drawOrder = value
        try drawOrderChangedSource.Raise(self, args: CNAEventArgs.Empty)
    }
}

private final class ExternalComponent: Microsoft.Xna.Framework.IGameComponent {
    func Initialize() throws {}
}

// A user subclass of the support base, proving the migrated CNAEventArgs really
// is open across module boundaries.
private final class ExternalArgs: CNAEventArgs {
    let marker: Int32
    init(marker: Int32) {
        self.marker = marker
        super.init()
    }
}

func qualifyFoundation19EventSurface() throws {
    typealias F = Microsoft.Xna.Framework
    typealias G = Microsoft.Xna.Framework.Graphics

    func check(_ condition: Bool, _ what: String) throws {
        guard condition else {
            throw CNAError.argument("isolated Foundation-19 \(what) qualification failed")
        }
    }

    // 1. Both protocols are externally conformable, and the conformers raise
    //    their own events.
    let updateable = ExternalUpdateable()
    // Spelled in full rather than through the `F` alias: Swift 6.0.3 asserts in
    // IRGen while mangling the debugger type for `any F.IUpdateable`, so the
    // alias is avoided for existential annotations only.
    let asUpdateable: Microsoft.Xna.Framework.IUpdateable = updateable
    try asUpdateable.Update(F.GameTime())
    try check(updateable.updates == 1, "IUpdateable Update")

    var enabledSenderMatched = false
    var enabledArgsWereEmpty = false
    var enabledRaises = 0
    let enabledToken = asUpdateable.EnabledChanged.Add { sender, args in
        enabledRaises += 1
        enabledSenderMatched = (sender as? ExternalUpdateable) === updateable
        enabledArgsWereEmpty = args === CNAEventArgs.Empty
    }
    try updateable.setEnabled(false)
    try check(!asUpdateable.Enabled, "IUpdateable Enabled mutation")
    try check(enabledRaises == 1, "IUpdateable EnabledChanged raise")
    try check(enabledSenderMatched, "IUpdateable EnabledChanged sender identity")
    try check(enabledArgsWereEmpty, "IUpdateable EnabledChanged EventArgs.Empty identity")

    // 2. Unsubscribe really unsubscribes.
    asUpdateable.EnabledChanged.Remove(enabledToken)
    try updateable.setEnabled(true)
    try check(enabledRaises == 1, "IUpdateable EnabledChanged unsubscribe")

    // 3. Duplicate registrations of one closure are independent, each with its
    //    own token, and removal is exact.
    var duplicateCalls = 0
    let handler: (Any?, CNAEventArgs) throws -> Void = { _, _ in duplicateCalls += 1 }
    let firstToken = asUpdateable.UpdateOrderChanged.Add(handler)
    let secondToken = asUpdateable.UpdateOrderChanged.Add(handler)
    try check(!(firstToken === secondToken), "distinct subscription identities")
    try updateable.setUpdateOrder(4)
    try check(duplicateCalls == 2, "duplicate registrations both fire")
    asUpdateable.UpdateOrderChanged.Remove(firstToken)
    try updateable.setUpdateOrder(5)
    try check(duplicateCalls == 3, "exact duplicate removal")
    // Removing an already-removed token, and a token from another event, are
    // both harmless.
    asUpdateable.UpdateOrderChanged.Remove(firstToken)
    asUpdateable.UpdateOrderChanged.Remove(enabledToken)
    try updateable.setUpdateOrder(6)
    try check(duplicateCalls == 4, "repeated and foreign token removal are harmless")
    asUpdateable.UpdateOrderChanged.Remove(secondToken)

    // 4. A no-change assignment raises nothing, as GameComponent's setters do.
    try updateable.setUpdateOrder(6)
    try check(updateable.UpdateOrder == 6, "IUpdateable UpdateOrder mutation")

    // 5. IDrawable is independently conformable and does not imply IUpdateable.
    let drawable = ExternalDrawable()
    let asDrawable: Microsoft.Xna.Framework.IDrawable = drawable
    try asDrawable.Draw(F.GameTime())
    try check(drawable.draws == 1, "IDrawable Draw")
    var visibleRaises = 0
    var drawOrderRaises = 0
    asDrawable.VisibleChanged.Add { _, _ in visibleRaises += 1 }
    asDrawable.DrawOrderChanged.Add { _, _ in drawOrderRaises += 1 }
    try drawable.setVisible(false)
    try drawable.setDrawOrder(-3)
    try check(!asDrawable.Visible && asDrawable.DrawOrder == -3, "IDrawable mutation")
    try check(visibleRaises == 1 && drawOrderRaises == 1, "IDrawable raises")
    try check(!((asDrawable as Any) is Microsoft.Xna.Framework.IUpdateable),
              "IDrawable does not extend IUpdateable")

    // 6. A handler error propagates to the raiser, stops the dispatch, and
    //    leaves the registration list intact.
    let source = CNAEventSource<CNAEventArgs>()
    var visited: [Int32] = []
    source.Event.Add { _, _ in visited.append(1) }
    source.Event.Add { _, _ in
        visited.append(2)
        throw CNAError.argument("external handler failed")
    }
    source.Event.Add { _, _ in visited.append(3) }
    do {
        try source.Raise(nil, args: CNAEventArgs.Empty)
        throw CNAError.argument("isolated Foundation-19 handler error was swallowed")
    } catch CNAError.argument(let message) where message == "external handler failed" {
        // Exactly the handler's own error, unwrapped.
    }
    try check(visited == [1, 2], "throwing handler stops later handlers")

    // 7. Dispatch walks a snapshot: a subscription added by a handler affects
    //    only later raises.
    let snapshotSource = CNAEventSource<CNAEventArgs>()
    var snapshotCalls: Int32 = 0
    snapshotSource.Event.Add { _, _ in
        snapshotCalls += 1
        snapshotSource.Event.Add { _, _ in snapshotCalls += 10 }
    }
    try snapshotSource.Raise(nil, args: CNAEventArgs.Empty)
    try check(snapshotCalls == 1, "dispatch snapshot excludes handlers added mid-raise")

    // 8. CNAEventArgs is open across the module boundary, and a derived
    //    argument survives dispatch with its dynamic type and object identity.
    let derivedSource = CNAEventSource<CNAEventArgs>()
    var observedMarker: Int32 = 0
    var observedIdentity = false
    let derived = ExternalArgs(marker: 21)
    derivedSource.Event.Add { _, args in
        observedIdentity = args === derived
        observedMarker = (args as? ExternalArgs)?.marker ?? 0
    }
    try derivedSource.Raise(nil, args: derived)
    try check(observedIdentity, "derived EventArgs object identity")
    try check(observedMarker == 21, "derived EventArgs dynamic type")

    // 9. The event-argument types are externally usable with exactly their
    //    pinned construction rules: GameComponentCollectionEventArgs is
    //    publicly constructible, and the two Graphics ones are not. The closure
    //    below compiles only if their read-only surface is public with these
    //    exact names and types; it is never called with a value, because no
    //    external construction route exists.
    let componentArgs = F.GameComponentCollectionEventArgs(
        gameComponent: ExternalComponent())
    try check(componentArgs.GameComponent is ExternalComponent,
              "GameComponentCollectionEventArgs storage")
    try check((componentArgs as Any) is CNAEventArgs,
              "GameComponentCollectionEventArgs base")
    let readCreated: (G.ResourceCreatedEventArgs) -> Any? = { $0.Resource }
    let readDestroyed: (G.ResourceDestroyedEventArgs) -> (String, Any?) = {
        ($0.Name, $0.Tag)
    }
    _ = readCreated
    _ = readDestroyed
    try check(String(describing: G.ResourceCreatedEventArgs.self)
                  == "ResourceCreatedEventArgs",
              "ResourceCreatedEventArgs type identity")
    try check(String(describing: G.ResourceDestroyedEventArgs.self)
                  == "ResourceDestroyedEventArgs",
              "ResourceDestroyedEventArgs type identity")

    // 10. A typed event carries its own argument type end to end.
    let typedSource = CNAEventSource<F.GameComponentCollectionEventArgs>()
    var typedSeen = false
    typedSource.Event.Add { _, args in typedSeen = args.GameComponent is ExternalComponent }
    try typedSource.Raise(nil, args: componentArgs)
    try check(typedSeen, "typed event argument")
}

func qualifyFoundation15To18ManagedSurface() throws {
    typealias F = Microsoft.Xna.Framework
    typealias G = Microsoft.Xna.Framework.Graphics
    typealias I = Microsoft.Xna.Framework.Input
    typealias T = Microsoft.Xna.Framework.Input.Touch

    func check(_ condition: Bool, _ what: String) throws {
        guard condition else {
            throw CNAError.argument("isolated Foundation-15..18 \(what) qualification failed")
        }
    }

    // Foundation 15: PresentationParameters is publicly constructible and
    // derivable, IsFullScreen defaults to true, Bounds tracks the back buffer
    // live, and DeviceWindowHandle is a plain Swift Int.
    let parameters = G.PresentationParameters()
    try check(parameters.IsFullScreen, "PresentationParameters IsFullScreen default")
    try check(parameters.BackBufferWidth == 0 && parameters.BackBufferFormat == .Color,
              "PresentationParameters defaults")
    try check(parameters.DeviceWindowHandle == 0, "DeviceWindowHandle default")
    parameters.BackBufferWidth = 800
    parameters.BackBufferHeight = 480
    parameters.DeviceWindowHandle = -1
    parameters.IsFullScreen = false
    try check(parameters.Bounds.Width == 800 && parameters.Bounds.Height == 480 &&
              parameters.Bounds.X == 0, "PresentationParameters Bounds")
    try check(parameters.DeviceWindowHandle == -1, "DeviceWindowHandle signed round trip")
    let clone = parameters.Clone()
    try check(clone.BackBufferWidth == 800 && !clone.IsFullScreen && clone.DeviceWindowHandle == -1,
              "PresentationParameters Clone")
    clone.BackBufferWidth = 1
    try check(parameters.BackBufferWidth == 800, "PresentationParameters Clone independence")

    // The IntPtr projection is exactly Int, never a pointer.
    let handle: Int = parameters.DeviceWindowHandle
    try check(MemoryLayout.size(ofValue: handle) == MemoryLayout<UnsafeRawPointer>.size,
              "DeviceWindowHandle is pointer width")

    // Foundation 16: MouseState is publicly constructible with unlabelled
    // arguments in the pinned order, and its hash is not zero-substituted.
    let mouse = I.MouseState(10, 20, 30, .Pressed, .Released, .Pressed, .Released, .Pressed)
    try check(mouse.X == 10 && mouse.Y == 20 && mouse.ScrollWheelValue == 30,
              "MouseState storage")
    try check(mouse.MiddleButton == .Released && mouse.RightButton == .Pressed,
              "MouseState middle/right order")
    try check(mouse.GetHashCode() == 1, "MouseState hash")
    try check(I.MouseState(0, 0, 0, .Released, .Released, .Released, .Released, .Released)
                  .GetHashCode() == 0, "MouseState zero hash is not substituted")
    try check(mouse.ToString() == "{X:10 Y:20 Buttons:Left Right XButton2 Wheel:30}",
              "MouseState string")
    try check(F.Media.MediaState.Paused.rawValue == 2 &&
              F.Media.MediaSourceType.WindowsMediaConnect.rawValue == 4 &&
              F.Audio.MicrophoneState.Started.rawValue == 0, "Foundation 16 enums")

    // Foundation 17: the flags/non-flags split, and both protocols are
    // externally conformable with exactly their pinned requirement sets.
    let drag: T.GestureType = [.HorizontalDrag, .VerticalDrag]
    try check(drag.rawValue == 24 && drag.contains(.VerticalDrag), "GestureType flags")
    try check(T.TouchLocationState.Invalid.rawValue == 0 &&
              F.Audio.AudioStopOptions.Immediate.rawValue == 1 &&
              F.Media.VideoSoundtrackType.MusicAndDialog.rawValue == 2,
              "Foundation 17 enums")
    let component: Microsoft.Xna.Framework.IGameComponent = ExternalGameComponent()
    try component.Initialize()
    let manager: Microsoft.Xna.Framework.IGraphicsDeviceManager = ExternalDeviceManager()
    try manager.CreateDevice()
    try check(try manager.BeginDraw(), "IGraphicsDeviceManager BeginDraw")
    try manager.EndDraw()

    // Foundation 18: TouchLocation's equality asymmetry and out parameter, and
    // GestureSample's verbatim storage.
    let location = T.TouchLocation(1, .Moved, F.Vector2(2, 3), .Pressed, F.Vector2(4, 5))
    let differentStates =
        T.TouchLocation(1, .Released, F.Vector2(2, 3), .Released, F.Vector2(4, 5))
    try check(location.Equals(differentStates), "TouchLocation typed Equals ignores state")
    try check(!(location == differentStates), "TouchLocation op_Equality compares state")
    try check(location.ToString() == "{Position:{X:2 Y:3}}", "TouchLocation string")
    try check(T.TouchLocation(7, .Moved, F.Vector2(1, 2)).GetHashCode() == 2139095047,
              "TouchLocation hash")
    var previous = T.TouchLocation(0, .Invalid, F.Vector2(0, 0))
    try check(location.TryGetPreviousLocation(&previous), "TouchLocation previous present")
    try check(previous.Id == 1 && previous.State == .Pressed && previous.Position.X == 4,
              "TouchLocation previous promotion")
    try check(!T.TouchLocation(9, .Moved, F.Vector2(0, 0)).TryGetPreviousLocation(&previous),
              "TouchLocation previous absent")
    try check(previous.Id == -1, "TouchLocation absent previous is written")
    let sample = T.GestureSample(
        .Tap, .seconds(2), F.Vector2(1, 2), F.Vector2(3, 4), F.Vector2(5, 6), F.Vector2(7, 8))
    try check(sample.GestureType == .Tap && sample.Timestamp == .seconds(2) &&
              sample.Delta2.Y == 8, "GestureSample storage")
}

do {
    try qualifyManagedCurve()
    try qualifyPublicDisplayModeSurface()
    try qualifyPublicRenderTargetUsageSurface()
    try qualifyFoundation14ManagedSurface()
    try qualifyFoundation15To18ManagedSurface()
    try qualifyFoundation19EventSurface()
    let index = CommandLine.arguments.firstIndex(of: "--frames")!
    let requested = Int(CommandLine.arguments[index + 1])!
    let game = try ArchiveGame(requested)
    try game.Run()
    print("ARCHIVE_CANARY requested=\(requested) updates=\(game.updates) draws=\(game.draws) texture=\(game.texture?.Width ?? 0)x\(game.texture?.Height ?? 0) curve=PASS displayMode=PASS renderTargetUsage=PASS foundation14=PASS foundation15to18=PASS foundation19=PASS")
    try game.Dispose()
} catch {
    FileHandle.standardError.write(Data("archive canary failed: \(error)\n".utf8))
    Foundation.exit(1)
}
'''


def run(command: list[str], cwd: Path, environment: dict[str, str]) -> str:
    completed = subprocess.run(
        command, cwd=cwd, env=environment, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout


def validate_canary(output: str, requested: int) -> bool:
    match = re.search(
        r"ARCHIVE_CANARY requested=(\d+) updates=(\d+) draws=(\d+) "
        r"texture=(\d+)x(\d+) curve=(PASS) displayMode=(PASS) "
        r"renderTargetUsage=(PASS) foundation14=(PASS) foundation15to18=(PASS) "
        r"foundation19=(PASS)",
        output,
    )
    if not match:
        return False
    observed_request, updates, draws, width, height = map(int, match.groups()[:5])
    return (
        observed_request == requested and
        updates >= requested and
        draws == requested and
        width == 1 and
        height == 1 and
        match.group(6) == "PASS" and
        match.group(7) == "PASS" and
        match.group(8) == "PASS" and
        match.group(9) == "PASS"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--swift-build", default="swift-build")
    parser.add_argument("--swift-run", default="swift-run")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.archive.is_absolute() or not args.archive.is_file():
        parser.error("--archive must be an absolute existing file")
    if not args.library.is_absolute() or not args.library.is_file():
        parser.error("--library must be an absolute existing file")

    forbidden: list[str] = []
    native_libraries: list[str] = []
    microsoft_reference_binaries: list[str] = []
    path_leaks: list[str] = []
    path_patterns = {
        str(Path.home()).encode(),
        str(Path.cwd().resolve()).encode(),
    }
    with zipfile.ZipFile(args.archive) as archive:
        entries = archive.namelist()
        for name in entries:
            parts = Path(name).parts
            if any(part in {".git", ".build"} for part in parts):
                forbidden.append(name)
            if name.endswith((".so", ".dylib", ".dll", ".a")):
                native_libraries.append(name)
            if (
                Path(name).name.lower().startswith("microsoft.xna.framework") and
                name.lower().endswith((".dll", ".exe"))
            ):
                microsoft_reference_binaries.append(name)
            if not name.endswith("/"):
                data = archive.read(name)
                if any(pattern and pattern in data for pattern in path_patterns):
                    path_leaks.append(name)

        with tempfile.TemporaryDirectory(prefix="cna-swift-archive-consumer-") as temporary:
            root = Path(temporary)
            extracted = root / "extracted"
            consumer = root / "consumer"
            archive.extractall(extracted)
            package_roots = [item for item in extracted.iterdir() if item.is_dir()]
            if len(package_roots) != 1:
                raise RuntimeError(f"archive has {len(package_roots)} package roots")
            dependency = package_roots[0]
            for path in sorted(dependency.rglob("*"), reverse=True):
                path.chmod(path.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
            dependency.chmod(dependency.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)

            sources = consumer / "Sources/ArchiveCanary"
            sources.mkdir(parents=True)
            identity = dependency.name.lower()
            (consumer / "Package.swift").write_text(
                PACKAGE.format(dependency=dependency.as_posix(), identity=identity), encoding="utf-8")
            (sources / "main.swift").write_text(SOURCE, encoding="utf-8")

            environment = os.environ.copy()
            environment["CNA_NATIVE_LIBRARY"] = str(args.library)
            scratch = root / "scratch"
            run([args.swift_build, "--scratch-path", str(scratch)], consumer, environment)
            debug_output = run([
                args.swift_run, "--scratch-path", str(scratch), "ArchiveCanary", "--frames", "60"
            ], consumer, environment)
            run([args.swift_build, "--scratch-path", str(scratch), "-c", "release"], consumer, environment)
            release_output = run([
                args.swift_run, "--scratch-path", str(scratch), "-c", "release",
                "ArchiveCanary", "--frames", "600"
            ], consumer, environment)
            if not validate_canary(debug_output, 60):
                raise RuntimeError(
                    "debug archive consumer callback/dimension evidence did not match:\n" +
                    debug_output
                )
            if not validate_canary(release_output, 600):
                raise RuntimeError(
                    "release archive consumer callback/dimension evidence did not match:\n" +
                    release_output
                )

    report = {
        "schemaVersion": 1,
        "SOURCE_ARCHIVE_FILENAME": args.archive.name,
        "SOURCE_ARCHIVE_SHA256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        "SOURCE_ARCHIVE_ENTRIES": len(entries),
        "FORBIDDEN_ENTRIES": forbidden,
        "NATIVE_LIBRARIES": native_libraries,
        "MICROSOFT_REFERENCE_BINARIES": microsoft_reference_binaries,
        "DEVELOPER_PATH_LEAKS": path_leaks,
        "DEBUG_BUILD": "PASS",
        "RELEASE_BUILD": "PASS",
        "RUN_60": "PASS",
        "RUN_600": "PASS",
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    print(" ".join(f"{key}={report[key]}" for key in (
        "SOURCE_ARCHIVE_FILENAME", "SOURCE_ARCHIVE_SHA256", "SOURCE_ARCHIVE_ENTRIES",
        "DEBUG_BUILD", "RELEASE_BUILD", "RUN_60", "RUN_600"
    )))
    return 1 if forbidden or native_libraries or path_leaks or microsoft_reference_binaries else 0


if __name__ == "__main__":
    raise SystemExit(main())
