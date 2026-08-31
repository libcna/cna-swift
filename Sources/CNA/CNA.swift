// SPDX-License-Identifier: MIT

import Foundation

/// The formal `System.EventArgs` projection.
///
/// This is a CLR *class*, and the whole XNA event-argument hierarchy derives
/// from it: `GameComponentCollectionEventArgs`, `ResourceCreatedEventArgs`,
/// `ResourceDestroyedEventArgs` and `PreparingDeviceSettingsEventArgs` all have
/// `System.EventArgs` as their direct base. Projecting it as a Swift `struct`
/// would make that hierarchy inexpressible, so it is an `open class`: base
/// fidelity is worth more than the accidental value semantics the earlier
/// support struct happened to have. The base is a measured mapping, not a
/// dropped one — see `BASE_MAPPING_MISMATCH` in the strict verifier.
///
/// It deliberately does **not** conform to `Sendable`. It is open, so a
/// subclass anywhere may add mutable stored state, and neither this type nor
/// the compiler can make a cross-actor safety promise on that subclass's
/// behalf. `@unchecked Sendable` would assert exactly the guarantee that
/// cannot be earned here.
///
/// It is deliberately outside the strict XNA namespace and is not counted as
/// an XNA type.
open class CNAEventArgs {
    /// `System.EventArgs.Empty`.
    ///
    /// The pinned XNA IL never constructs an event-argument object for an
    /// `EventHandler<EventArgs>` raise: all 46 raise sites across the
    /// registered `Microsoft.Xna.Framework.Game.dll` and
    /// `Microsoft.Xna.Framework.Graphics.dll` load the static
    /// `System.EventArgs::Empty` field, and none executes `newobj`. One shared
    /// instance therefore preserves the object identity a handler observes.
    public static let Empty = CNAEventArgs()

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
    case argument(String)
    case argumentNull(String)
    case argumentOutOfRange(String)
    case indexOutOfRange(String)
    case nullReference(String)
    case collectionModified
    case keyNotFound(String)
    case notSupported(String)

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
        case .argument(let message):
            return message
        case .argumentNull(let parameter):
            // The CLR raises ArgumentNullException, whose Message composes
            // two resource strings around Environment.NewLine. Only the
            // parameter name is reported here: composing that message would
            // mean asserting the reference platform's newline, and the
            // exception CLASS is what the payload milestone will project.
            return "Argument must not be null or empty: \(parameter)"
        case .argumentOutOfRange(let parameter):
            return "Argument is outside the XNA range: \(parameter)"
        case .indexOutOfRange(let parameter):
            return "Index is outside the XNA array range: \(parameter)"
        case .nullReference(let operation):
            return "XNA null reference in \(operation)"
        case .collectionModified:
            return "Collection was modified after the enumerator was created"
        case .keyNotFound(let message):
            return message
        case .notSupported(let operation):
            return "XNA does not support \(operation)"
        }
    }
}

/// Throwing support projection for CLR `IEnumerator<T>` return values.
///
/// This type deliberately does not conform to Swift `IteratorProtocol`: XNA
/// collection enumeration can fail when the source mutates, while
/// `IteratorProtocol.next()` cannot throw.
public final class CNAEnumerator<Element> {
    private let nextElement: (Int, UInt64) throws -> Element?
    private let expectedVersion: UInt64
    private var index = 0

    internal init(
        expectedVersion: UInt64,
        nextElement: @escaping (Int, UInt64) throws -> Element?
    ) {
        self.expectedVersion = expectedVersion
        self.nextElement = nextElement
    }

    public func Next() throws -> Element? {
        let value = try nextElement(index, expectedVersion)
        if value != nil { index += 1 }
        return value
    }
}
