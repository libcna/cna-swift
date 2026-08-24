// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework {
    /// XNA's packed little-endian RGBA value. Named colors not needed by the
    /// Foundation-1 canary remain structurally absent and reported.
    public struct Color {
        private var packedValue: UInt32

        public var R: UInt8 {
            get { UInt8(truncatingIfNeeded: packedValue) }
            set { packedValue = (packedValue & 0xFFFF_FF00) | UInt32(newValue) }
        }

        public var G: UInt8 {
            get { UInt8(truncatingIfNeeded: packedValue >> 8) }
            set { packedValue = (packedValue & 0xFFFF_00FF) | (UInt32(newValue) << 8) }
        }

        public var B: UInt8 {
            get { UInt8(truncatingIfNeeded: packedValue >> 16) }
            set { packedValue = (packedValue & 0xFF00_FFFF) | (UInt32(newValue) << 16) }
        }

        public var A: UInt8 {
            get { UInt8(truncatingIfNeeded: packedValue >> 24) }
            set { packedValue = (packedValue & 0x00FF_FFFF) | (UInt32(newValue) << 24) }
        }

        public var PackedValue: UInt32 {
            get { packedValue }
            set { packedValue = newValue }
        }

        public init(_ r: Int32, _ g: Int32, _ b: Int32) {
            self.init(r, g, b, 255)
        }

        public init(_ r: Int32, _ g: Int32, _ b: Int32, _ a: Int32) {
            packedValue = Self.packIntegers(r, g, b, a)
        }

        public init(_ r: Float, _ g: Float, _ b: Float) {
            self.init(r, g, b, 1)
        }

        public init(_ r: Float, _ g: Float, _ b: Float, _ a: Float) {
            packedValue = Self.packFloats(r, g, b, a)
        }

        internal init(packedValue: UInt32) { self.packedValue = packedValue }

        public static var Transparent: Color { Color(packedValue: 0x0000_0000) }
        public static var Black: Color { Color(packedValue: 0xFF00_0000) }
        public static var White: Color { Color(packedValue: 0xFFFF_FFFF) }
        public static var CornflowerBlue: Color { Color(packedValue: 0xFFED_9564) }

        public static func Multiply(_ value: Color, scale: Float) -> Color {
            let scaled = scale * 65_536
            let factor: UInt32
            if scaled.isNaN || scaled < 0 {
                factor = 0
            } else if scaled > 16_777_215 {
                factor = 16_777_215
            } else {
                factor = UInt32(scaled)
            }
            func channel(_ value: UInt8) -> UInt32 {
                Swift.min((UInt32(value) * factor) >> 16, 255)
            }
            return Color(packedValue: channel(value.R) | (channel(value.G) << 8) |
                (channel(value.B) << 16) | (channel(value.A) << 24))
        }

        public func Equals(_ other: Color) -> Bool { self == other }

        public func Equals(_ obj: Any?) -> Bool {
            guard let other = obj as? Color else { return false }
            return self == other
        }

        public func GetHashCode() -> Int32 { Int32(bitPattern: packedValue) }
        public func ToString() -> String { "{R:\(R) G:\(G) B:\(B) A:\(A)}" }

        public static func * (lhs: Color, rhs: Float) -> Color { Multiply(lhs, scale: rhs) }
        public static func == (lhs: Color, rhs: Color) -> Bool { lhs.packedValue == rhs.packedValue }
        public static func != (lhs: Color, rhs: Color) -> Bool { !(lhs == rhs) }

        internal var native: CNASwift_Color { CNASwift_Color(r: R, g: G, b: B, a: A) }

        private static func packIntegers(_ r: Int32, _ g: Int32, _ b: Int32, _ a: Int32) -> UInt32 {
            func clamp(_ value: Int32) -> UInt32 { UInt32(Swift.max(0, Swift.min(255, value))) }
            return clamp(r) | (clamp(g) << 8) | (clamp(b) << 16) | (clamp(a) << 24)
        }

        private static func packFloats(_ r: Float, _ g: Float, _ b: Float, _ a: Float) -> UInt32 {
            func pack(_ value: Float) -> UInt32 {
                let scaled = value * 255
                if scaled.isNaN || scaled <= 0 { return 0 }
                if scaled >= 255 { return 255 }
                return UInt32(scaled.rounded(.toNearestOrEven))
            }
            return pack(r) | (pack(g) << 8) | (pack(b) << 16) | (pack(a) << 24)
        }
    }
}
