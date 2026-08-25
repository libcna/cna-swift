// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework.Graphics {
    // The pinned metadata declares a public abstract interface with no base
    // interface and exactly four read/write properties, all abstract. It
    // declares no method and no conformer is required to exist.
    public protocol IEffectFog {
        var FogEnabled: Bool { get set }

        var FogStart: Float { get set }

        var FogEnd: Float { get set }

        var FogColor: Microsoft.Xna.Framework.Vector3 { get set }
    }
}
