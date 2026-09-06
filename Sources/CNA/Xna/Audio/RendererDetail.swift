// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework.Audio {

    /// `Microsoft.Xna.Framework.Audio.RendererDetail`.
    ///
    /// One audio renderer's identity: a name to show and an id to pass back.
    /// Entirely managed -- two strings, value equality over them, and the
    /// `ToString` that renders the friendly name.
    ///
    /// **Nothing populates one yet, and that is stated rather than hidden.**
    /// XNA produces these from `AudioEngine.RendererDetails`, and the XACT
    /// family is blocked on a `.xgs` settings file this repository does not
    /// have. The type is projected anyway because it is part of the pinned
    /// contract and its whole behaviour is managed: a consumer can hold one,
    /// compare it and print it, which is all XNA lets them do with one either.
    ///
    /// Both getters are `IL_NO_FAILURE_PATH` and neither return is *proven*
    /// nullable, so both are non-Optional -- the same rule
    /// `GraphicsAdapter.DefaultAdapter` was decided by. A default-constructed
    /// value therefore reads two empty strings rather than two nils.
    public struct RendererDetail {

        private let friendlyName: String
        private let rendererId: String

        /// **Internal, and the reference metadata is why.** C# gives every
        /// struct an implicit parameterless constructor, but the pinned
        /// contract declares none -- so a public Swift `init()` is a member
        /// XNA does not have, and the strict comparison says so by name. The
        /// engine that will fill these does not exist here yet either.
        internal init() {
            self.init(friendlyName: "", rendererId: "")
        }

        internal init(friendlyName: String, rendererId: String) {
            self.friendlyName = friendlyName
            self.rendererId = rendererId
        }

        /// `RendererDetail.FriendlyName`.
        public var FriendlyName: String { friendlyName }

        /// `RendererDetail.RendererId`.
        public var RendererId: String { rendererId }

        public func Equals(_ obj: Any?) -> Bool {
            guard let other = obj as? RendererDetail else { return false }
            return self == other
        }

        /// `rendererId.GetHashCode()` -- the **id** alone, not the pair: two
        /// details naming the same renderer are the same renderer whatever
        /// they are called.
        public func GetHashCode() -> Int32 {
            Microsoft.Xna.Framework.Audio.RendererDetail.stringHash(rendererId)
        }

        /// `friendlyName`, which is what XNA's `ToString` returns -- not a
        /// braced field list like the geometry types.
        public func ToString() -> String { friendlyName }

        public static func == (lhs: RendererDetail, rhs: RendererDetail) -> Bool {
            lhs.rendererId == rhs.rendererId
        }

        public static func != (lhs: RendererDetail, rhs: RendererDetail) -> Bool {
            !(lhs == rhs)
        }

        /// The CLR's `String.GetHashCode` is not specified across runtimes, so
        /// this reproduces a stable hash rather than claiming to be Microsoft's
        /// -- what the contract requires is that equal values hash equally.
        private static func stringHash(_ value: String) -> Int32 {
            var hash: Int32 = 0
            for unit in value.utf16 {
                hash = hash &* 31 &+ Int32(unit)
            }
            return hash
        }
    }
}
