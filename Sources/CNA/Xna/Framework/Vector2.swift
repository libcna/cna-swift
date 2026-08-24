// SPDX-License-Identifier: MIT

import Foundation

extension Microsoft.Xna.Framework {
    /// A real binary32 Vector2 implementation. The structural report records
    /// the still-absent Matrix/Quaternion/array overload closure.
    public struct Vector2 {
        public var X: Float
        public var Y: Float

        public init(_ x: Float, _ y: Float) {
            X = x
            Y = y
        }

        public init(_ value: Float) {
            X = value
            Y = value
        }

        public static var Zero: Vector2 { Vector2(0, 0) }
        public static var One: Vector2 { Vector2(1, 1) }
        public static var UnitX: Vector2 { Vector2(1, 0) }
        public static var UnitY: Vector2 { Vector2(0, 1) }

        public func Length() -> Float { sqrtf((X * X) + (Y * Y)) }
        public func LengthSquared() -> Float { (X * X) + (Y * Y) }

        public mutating func Normalize() {
            let inverse = 1 / Length()
            X *= inverse
            Y *= inverse
        }

        public static func Normalize(_ value: Vector2) -> Vector2 {
            let inverse = 1 / value.Length()
            return Vector2(value.X * inverse, value.Y * inverse)
        }

        public static func Normalize(_ value: inout Vector2, result: inout Vector2) {
            result = Normalize(value)
        }

        public static func Distance(_ value1: Vector2, value2: Vector2) -> Float {
            sqrtf(DistanceSquared(value1, value2: value2))
        }

        public static func Distance(_ value1: inout Vector2, value2: inout Vector2, result: inout Float) {
            result = Distance(value1, value2: value2)
        }

        public static func DistanceSquared(_ value1: Vector2, value2: Vector2) -> Float {
            let x = value1.X - value2.X
            let y = value1.Y - value2.Y
            return x * x + y * y
        }

        public static func DistanceSquared(
            _ value1: inout Vector2,
            value2: inout Vector2,
            result: inout Float
        ) {
            result = DistanceSquared(value1, value2: value2)
        }

        public static func Dot(_ value1: Vector2, value2: Vector2) -> Float {
            value1.X * value2.X + value1.Y * value2.Y
        }

        public static func Dot(_ value1: inout Vector2, value2: inout Vector2, result: inout Float) {
            result = Dot(value1, value2: value2)
        }

        public static func Min(_ value1: Vector2, value2: Vector2) -> Vector2 {
            Vector2(Swift.min(value1.X, value2.X), Swift.min(value1.Y, value2.Y))
        }

        public static func Min(_ value1: inout Vector2, value2: inout Vector2, result: inout Vector2) {
            result = Min(value1, value2: value2)
        }

        public static func Max(_ value1: Vector2, value2: Vector2) -> Vector2 {
            Vector2(Swift.max(value1.X, value2.X), Swift.max(value1.Y, value2.Y))
        }

        public static func Max(_ value1: inout Vector2, value2: inout Vector2, result: inout Vector2) {
            result = Max(value1, value2: value2)
        }

        public static func Clamp(_ value1: Vector2, min: Vector2, max: Vector2) -> Vector2 {
            Vector2(
                MathHelper.Clamp(value1.X, min: min.X, max: max.X),
                MathHelper.Clamp(value1.Y, min: min.Y, max: max.Y)
            )
        }

        public static func Clamp(
            _ value1: inout Vector2,
            min: inout Vector2,
            max: inout Vector2,
            result: inout Vector2
        ) {
            result = Clamp(value1, min: min, max: max)
        }

        public static func Lerp(_ value1: Vector2, value2: Vector2, amount: Float) -> Vector2 {
            Vector2(
                MathHelper.Lerp(value1.X, value2: value2.X, amount: amount),
                MathHelper.Lerp(value1.Y, value2: value2.Y, amount: amount)
            )
        }

        public static func Lerp(
            _ value1: inout Vector2,
            value2: inout Vector2,
            amount: Float,
            result: inout Vector2
        ) {
            result = Lerp(value1, value2: value2, amount: amount)
        }

        public static func Add(_ value1: Vector2, value2: Vector2) -> Vector2 { value1 + value2 }
        public static func Subtract(_ value1: Vector2, value2: Vector2) -> Vector2 { value1 - value2 }
        public static func Multiply(_ value1: Vector2, value2: Vector2) -> Vector2 { value1 * value2 }
        public static func Multiply(_ value1: Vector2, scaleFactor: Float) -> Vector2 { value1 * scaleFactor }
        public static func Divide(_ value1: Vector2, value2: Vector2) -> Vector2 { value1 / value2 }
        public static func Divide(_ value1: Vector2, divider: Float) -> Vector2 { value1 / divider }
        public static func Negate(_ value: Vector2) -> Vector2 { -value }

        public func Equals(_ other: Vector2) -> Bool { self == other }

        public func Equals(_ obj: Any?) -> Bool {
            guard let other = obj as? Vector2 else { return false }
            return self == other
        }

        public func GetHashCode() -> Int32 {
            Int32(bitPattern: X.bitPattern) &+ Int32(bitPattern: Y.bitPattern)
        }

        public func ToString() -> String { "{X:\(X) Y:\(Y)}" }

        public static prefix func - (value: Vector2) -> Vector2 { Vector2(-value.X, -value.Y) }
        public static func + (lhs: Vector2, rhs: Vector2) -> Vector2 { Vector2(lhs.X + rhs.X, lhs.Y + rhs.Y) }
        public static func - (lhs: Vector2, rhs: Vector2) -> Vector2 { Vector2(lhs.X - rhs.X, lhs.Y - rhs.Y) }
        public static func * (lhs: Vector2, rhs: Vector2) -> Vector2 { Vector2(lhs.X * rhs.X, lhs.Y * rhs.Y) }
        public static func * (lhs: Vector2, rhs: Float) -> Vector2 { Vector2(lhs.X * rhs, lhs.Y * rhs) }
        public static func * (lhs: Float, rhs: Vector2) -> Vector2 { rhs * lhs }
        public static func / (lhs: Vector2, rhs: Vector2) -> Vector2 { Vector2(lhs.X / rhs.X, lhs.Y / rhs.Y) }
        public static func / (lhs: Vector2, rhs: Float) -> Vector2 { Vector2(lhs.X / rhs, lhs.Y / rhs) }
        public static func == (lhs: Vector2, rhs: Vector2) -> Bool { lhs.X == rhs.X && lhs.Y == rhs.Y }
        public static func != (lhs: Vector2, rhs: Vector2) -> Bool { !(lhs == rhs) }
    }
}
