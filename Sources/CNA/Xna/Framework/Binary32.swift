// SPDX-License-Identifier: MIT

import Foundation

// XNA's scalar transcendental operations accept a binary32 input, execute the
// corresponding System.Math operation, and round the result back to Single.
// Keeping that boundary explicit avoids accidental whole-algorithm promotion.
@inline(__always) internal func xnaSqrt(_ value: Float) -> Float {
    Float(Foundation.sqrt(Double(value)))
}

@inline(__always) internal func xnaSin(_ value: Float) -> Float {
    Float(Foundation.sin(Double(value)))
}

@inline(__always) internal func xnaCos(_ value: Float) -> Float {
    Float(Foundation.cos(Double(value)))
}

@inline(__always) internal func xnaTan(_ value: Float) -> Float {
    Float(Foundation.tan(Double(value)))
}

@inline(__always) internal func xnaAcos(_ value: Float) -> Float {
    Float(Foundation.acos(Double(value)))
}

@inline(__always) internal func xnaSinReciprocal(_ value: Float) -> Float {
    Float(1.0 / Foundation.sin(Double(value)))
}

@inline(__always) internal func xnaFloatHash(_ value: Float) -> Int32 {
    if value == 0 { return 0 }
    return Int32(bitPattern: value.bitPattern)
}

internal func xnaFloatString(_ value: Float) -> String {
    if value.isNaN { return "NaN" }
    if value == .infinity { return "Infinity" }
    if value == -.infinity { return "-Infinity" }
    if value == 0 { return "0" }
    return String(format: "%.7g", locale: Locale(identifier: "en_US_POSIX"), Double(value))
}

internal func xnaValidateTransformArrayRanges(
    sourceCount: Int,
    sourceIndex: Int32,
    destinationCount: Int,
    destinationIndex: Int32,
    length: Int32
) throws {
    let sourceEnd = Int64(sourceIndex) + Int64(length)
    let destinationEnd = Int64(destinationIndex) + Int64(length)
    if Int64(sourceCount) < sourceEnd {
        throw CNAError.argument("The source array is too small.")
    }
    if Int64(destinationCount) < destinationEnd {
        throw CNAError.argument("The destination array is too small.")
    }
    if length > 0 && sourceIndex < 0 {
        throw CNAError.indexOutOfRange("sourceIndex")
    }
    if length > 0 && destinationIndex < 0 {
        throw CNAError.indexOutOfRange("destinationIndex")
    }
}
