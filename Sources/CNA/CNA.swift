// SPDX-License-Identifier: MIT

import Foundation

/// Empty support value used by the formal `System.EventArgs` language mapping.
/// It is deliberately outside the strict XNA namespace and is not counted as
/// an XNA type.
public struct CNAEventArgs: Sendable {
    public init() {}
}

/// Errors raised by CNA-Swift support code. This type is intentionally outside
/// the strict `Microsoft.Xna.Framework` projection.
public enum CNAError: Error, Equatable, CustomStringConvertible {
    case nativeLibraryNotFound(candidates: [String])
    case nativeLibraryLoadFailed(path: String, message: String)
    case missingNativeSymbol(String)
    case unsupportedABIVersion(expected: UInt32, actual: UInt32)
    case nativeFailure(operation: String, result: UInt32, message: String)
    case unsupportedPlatform(String)
    case disposedObject(String)
    case ownerThreadViolation(String)
    case staleRuntimeGeneration(expected: UInt64, actual: UInt64?)
    case callbackOutsideGameLifecycle
    case streamFailure(String)

    public var description: String {
        switch self {
        case .nativeLibraryNotFound(let candidates):
            return "CNA native library was not found; tried: \(candidates.joined(separator: ", "))"
        case .nativeLibraryLoadFailed(let path, let message):
            return "Could not load CNA native library at \(path): \(message)"
        case .missingNativeSymbol(let symbol):
            return "CNA native library is missing required symbol \(symbol)"
        case .unsupportedABIVersion(let expected, let actual):
            return String(format: "Unsupported CNA C ABI 0x%08X; expected exactly 0x%08X", actual, expected)
        case .nativeFailure(let operation, let result, let message):
            return "CNA operation \(operation) failed with result \(result): \(message)"
        case .unsupportedPlatform(let platform):
            return "CNA-Swift runtime is not qualified on \(platform)"
        case .disposedObject(let type):
            return "\(type) is disposed"
        case .ownerThreadViolation(let operation):
            return "\(operation) must run on the native Game owner thread"
        case .staleRuntimeGeneration(let expected, let actual):
            return "Native object belongs to stale Game generation \(expected); active generation is \(actual.map(String.init) ?? "none")"
        case .callbackOutsideGameLifecycle:
            return "The native operation requires an active Game lifecycle callback"
        case .streamFailure(let message):
            return "InputStream failed: \(message)"
        }
    }
}
