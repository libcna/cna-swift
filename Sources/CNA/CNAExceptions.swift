// SPDX-License-Identifier: MIT

import Foundation

// BCL exception support projection.
//
// Eight XNA types are exception classes, and every one of them declares
// nothing but constructors: their entire observable behaviour — the message
// they report, the inner exception they carry, the HResult they expose — is
// inherited from `System.Exception` and, for three of them, from
// `System.Runtime.InteropServices.ExternalException`. Dropping those bases
// would leave the subclasses empty, exactly as dropping `Collection<T>` would
// have left `GameComponentCollection` empty, so the Foundation 27 rule applies
// unchanged:
//
//     a CLR BCL base class with a registered projection becomes a REAL Swift
//     superclass.
//
//     System.Exception                                 -> CNAException
//     System.SystemException                           -> CNASystemException
//     System.Runtime.InteropServices.ExternalException -> CNAExternalException
//
// The middle link is not decoration. `ExternalException`'s exact direct base
// in the admitted `mscorlib` is `SystemException`, whose constructors
// substitute their own default message and set HResult to `0x80131501` before
// `ExternalException` overwrites it with `0x80004005`. Collapsing the chain to
// two links would change both, so it is projected at full length and the
// verifier measures each link.
//
// `CNAException` conforms to Swift `Error`. That is the whole point: a CLR
// `Exception` object is a thing you throw, so its Swift projection must be a
// thing you can `throw`, and `catch is DeviceLostException` must work. A
// struct or an enum could not carry the inheritance chain, and an alias to
// `CNAError` would confuse two different channels — see below.
//
// These three classes live outside `Microsoft.Xna.Framework`. They are
// language/BCL-support API, not XNA types and not XNA identities, are counted
// in no XNA scoreboard, and no `::System` namespace is fabricated for them.
// Their shape is measured against the pinned selected-BCL manifest in
// `tools/api_compat/reference/bcl40-selected-shape.json`, reconstructed from
// the hash-registered Microsoft .NET Framework 4.0 `mscorlib` — see
// `docs/foundation-30-bcl-exception-projection-evidence.md`.
//
// Unlike every other support type here, these three DO carry a `Sendable`
// conformance, and it is worth being exact about why: the Swift standard
// library declares `Error` as refining `Sendable`, so conforming to `Error`
// conforms to `Sendable` and this file can neither add nor decline it. It is
// not a promise the projection makes. `HResult` and `HelpLink` are mutable
// here exactly as `mscorlib` declares them, and all three classes are `open`,
// so a subclass anywhere may add more mutable state; nothing about the
// cross-actor safety of a `CNAException` is being asserted by this file, and
// the conformance the Symbol Graph reports is the language's, not a claim.
//
// ## `CNAError` stays a separate channel
//
// `CNAError` is **not** in this hierarchy and must not be. It reports
// CNA-Swift runtime and language-support failures — a native library that will
// not load, an owner-thread violation, a stale runtime generation, an
// unsupported platform, callback lifecycle misuse — none of which corresponds
// to a selected XNA exception identity. `CNAError` is not a `CNAException`,
// `CNAException` does not wrap `CNAError`, and a test asserts both.
//
// ## What is deliberately absent
//
// `mscorlib` declares more on `System.Exception` than is projected here:
// `StackTrace`, `Source`, `TargetSite`, `Data`, `GetObjectData`, `GetType`,
// `ToString` and the protected `SerializeObjectState` event. Each of them
// needs a CLR runtime service this projection does not have — the runtime's
// captured managed stack, `System.Reflection.MethodBase`, `System.Type`,
// `System.Collections.IDictionary`, or the serialization runtime — and each is
// therefore **forbidden** by the verifier rather than merely missing. A
// `StackTrace` that answered with an empty string, or a `Data` that answered
// with a dictionary XNA never populated, would be a fabrication; an absence
// that the gate enforces is not.

/// The `System.Exception` projection.
///
/// Conforms to Swift `Error`, so every projected XNA exception subclass is a
/// real throwable Swift error.
open class CNAException: Error {
    // ------------------------------------------------------------------
    // Resource strings.
    //
    // `Exception.get_Message`, `SystemException..ctor()` and
    // `ExternalException..ctor()` do NOT carry their default messages as IL
    // literals: each loads a resource KEY and calls
    // `Environment.GetResourceString`. These values were read out of the
    // admitted assembly's own embedded `mscorlib.resources` string table by
    // `tools/api_compat/bcl_authority_audit.py`, are pinned in
    // `reference/bcl40-selected-shape.json` under `resourceStrings`, and the
    // verifier reads these literals back out of this source and compares them.
    // None of them is transcribed from documentation or memory.
    // ------------------------------------------------------------------

    /// `Exception_WasThrown`, formatted with the CLR class name.
    internal static let exceptionWasThrownFormat =
        "Exception of type '{0}' was thrown."

    /// `Arg_SystemException`.
    internal static let argSystemExceptionMessage = "System error."

    /// `Arg_ExternalException`.
    internal static let argExternalExceptionMessage =
        "External component has thrown an exception."

    /// `COR_E_EXCEPTION`, the HResult `Exception::Init` assigns.
    internal static let corExceptionHResult = Int32(bitPattern: 0x8013_1500)

    /// `COR_E_SYSTEM`, the HResult every `SystemException` constructor assigns.
    internal static let corSystemHResult = Int32(bitPattern: 0x8013_1501)

    /// `E_FAIL`, the HResult every `ExternalException` constructor assigns
    /// except the one that takes an explicit error code.
    internal static let externalExceptionHResult = Int32(bitPattern: 0x8000_4005)

    // `Exception._message`. Held as written: the CLR stores the argument
    // without validating it, and `get_Message` branches on it being null, so
    // nil is a real state and not an empty string.
    private let storedMessage: String?

    // `Exception._innerException`, stored by the constructor and never
    // rewritten.
    private let storedInnerException: CNAException?

    /// `Exception.HResult`.
    ///
    /// `mscorlib` declares this `protected` with both accessors and no virtual
    /// flag. Swift has no `protected`, so it is public here — the same single
    /// widening `CNACollection.Items` already makes — and `final`, because the
    /// CLR does not make it an override point. Its value is what
    /// `ExternalException.ErrorCode` reads.
    public final var HResult: Int32

    /// `Exception.HelpLink`.
    ///
    /// `get_HelpLink` returns the `_helpURL` field and `set_HelpLink` stores
    /// it; both are `virtual` and neither is `final`, so this is an `open`
    /// read/write property. `Init` leaves the field null, so the projection is
    /// Optional and never an empty string.
    open var HelpLink: String?

    /// `Exception..ctor()`.
    ///
    /// The IL is `Object..ctor(); Init()`, and `Init` nulls `_message` and
    /// sets HResult to `0x80131500`. `Message` therefore reports the
    /// synthesized default.
    public init() {
        self.storedMessage = nil
        self.storedInnerException = nil
        self.HelpLink = nil
        self.HResult = CNAException.corExceptionHResult
    }

    /// `Exception..ctor(String message)`.
    ///
    /// The IL is `Object..ctor(); Init(); _message = message`. The argument is
    /// stored unvalidated, so a nil message is a normal observable state that
    /// selects the synthesized default from `Message` — which is why the
    /// parameter is Optional rather than an empty-string stand-in.
    public init(message: String?) {
        self.storedMessage = message
        self.storedInnerException = nil
        self.HelpLink = nil
        self.HResult = CNAException.corExceptionHResult
    }

    /// `Exception..ctor(String message, Exception innerException)`.
    ///
    /// The IL stores both arguments and validates neither.
    public init(message: String?, innerException: CNAException?) {
        self.storedMessage = message
        self.storedInnerException = innerException
        self.HelpLink = nil
        self.HResult = CNAException.corExceptionHResult
    }

    /// `Exception.Message`.
    ///
    /// `get_Message` returns `_message` when it is not null, and otherwise
    /// formats the `Exception_WasThrown` resource string with the exception's
    /// own CLR class name. Both halves are reproduced, so
    /// `DeviceLostException().Message` is the sentence XNA reports and not an
    /// empty string. `virtual` and not `final` in the metadata, so `open`.
    open var Message: String {
        if let storedMessage { return storedMessage }
        return CNAException.exceptionWasThrownFormat.replacingOccurrences(
            of: "{0}", with: cnaClassName)
    }

    /// `Exception.InnerException`.
    ///
    /// `get_InnerException` is `virtual final` in the metadata — a sealed
    /// interface implementation, not an override point — so this is `final`
    /// rather than `open`. It returns the field, which is null unless a
    /// two-argument constructor supplied one.
    public final var InnerException: CNAException? { storedInnerException }

    /// `Exception.GetBaseException()`.
    ///
    /// The IL walks the `InnerException` chain to its end and returns the last
    /// non-null exception, which is `self` when there is no inner exception.
    /// `virtual` and not `final`, so `open`.
    open func GetBaseException() -> CNAException {
        var deepest: CNAException = self
        var next = InnerException
        while let current = next {
            deepest = current
            next = current.InnerException
        }
        return deepest
    }

    /// `Exception.GetClassName()` — the CLR full type name.
    ///
    /// `GetClassName` reads `_className`, which the runtime fills from
    /// `RuntimeTypeHandle::ConstructName`: the namespace-qualified CLR name of
    /// the object's own type. The Swift namespace enums mirror the CLR
    /// namespaces exactly, so the reflected Swift name of a projected XNA
    /// exception is that CLR name with the module component in front, and
    /// dropping the module recovers it. The three support classes are the only
    /// types whose CLR name is not recoverable that way — nothing named
    /// `CNAException` exists in `mscorlib` — so they are the only entries in
    /// the table below.
    ///
    /// This is internal: it is the CLR machinery `Message` needs, not a
    /// projected member, and inventing a public `ClassName` would add a member
    /// `mscorlib` does not declare. It is deliberately a single
    /// implementation rather than a per-class override, because an override on
    /// `CNAExternalException` would be inherited by the three XNA subclasses
    /// that derive from it and would report the base's name for all of them. A
    /// test asserts the result for every projected XNA exception and for each
    /// support class.
    internal var cnaClassName: String {
        let reflected = String(reflecting: type(of: self))
        // Only THIS module's qualifier is removed, and only when it is
        // actually there. Stripping whichever component happens to come first
        // would also strip a consumer's module from their own subclass of one
        // of the two unsealed XNA exceptions, leaving a bare name where the
        // CLR reports a qualified one -- so the prefix is matched, not
        // counted. The qualifier is read back from a type known to live here
        // rather than written down, so renaming the module cannot desynchronize
        // it.
        let unqualified: String
        if reflected.hasPrefix(CNAException.moduleQualifier) {
            unqualified = String(
                reflected.dropFirst(CNAException.moduleQualifier.count))
        } else {
            unqualified = reflected
        }
        return CNAException.supportClassNames[unqualified] ?? unqualified
    }

    /// `"CNA."` — this module's own reflection qualifier, derived from a type
    /// that is certainly in it.
    private static let moduleQualifier: String = {
        let reflected = String(reflecting: CNAException.self)
        guard let separator = reflected.firstIndex(of: ".") else { return "" }
        return String(reflected[...separator])
    }()

    /// The CLR names of the support classes themselves.
    private static let supportClassNames: [String: String] = [
        "CNAException": "System.Exception",
        "CNASystemException": "System.SystemException",
        "CNAExternalException": "System.Runtime.InteropServices.ExternalException",
    ]
}

/// The `System.SystemException` projection.
///
/// Declares no member of its own — `mscorlib` gives it four constructors and
/// nothing else — but it is not a marker. Each constructor sets HResult to
/// `COR_E_SYSTEM`, and the parameterless one substitutes the
/// `Arg_SystemException` resource message, so a projection that skipped this
/// link would report a different message and a different HResult for
/// `ExternalException`'s own parameterless path.
open class CNASystemException: CNAException {
    /// `SystemException..ctor()`.
    ///
    /// The IL is
    /// `base..ctor(GetResourceString("Arg_SystemException")); SetErrorCode(0x80131501)`.
    /// The message is substituted, so `Message` is `"System error."` and never
    /// the `Exception_WasThrown` default.
    public override init() {
        super.init(message: CNAException.argSystemExceptionMessage)
        HResult = CNAException.corSystemHResult
    }

    /// `SystemException..ctor(String message)`.
    public override init(message: String?) {
        super.init(message: message)
        HResult = CNAException.corSystemHResult
    }

    /// `SystemException..ctor(String message, Exception innerException)`.
    public override init(message: String?, innerException: CNAException?) {
        super.init(message: message, innerException: innerException)
        HResult = CNAException.corSystemHResult
    }
}

/// The `System.Runtime.InteropServices.ExternalException` projection.
///
/// The direct base of `InstancePlayLimitException`, `NoAudioHardwareException`
/// and `StorageDeviceNotConnectedException`. It substitutes its own default
/// message, overwrites the HResult its base has just set, and adds the one
/// public member the family has: `ErrorCode`.
open class CNAExternalException: CNASystemException {
    /// `ExternalException..ctor()`.
    ///
    /// `base..ctor(GetResourceString("Arg_ExternalException"))` then
    /// `SetErrorCode(0x80004005)`. Both the message and the HResult replace
    /// what `SystemException..ctor(String)` produced, in that order.
    public override init() {
        super.init(message: CNAException.argExternalExceptionMessage)
        HResult = CNAException.externalExceptionHResult
    }

    /// `ExternalException..ctor(String message)`.
    public override init(message: String?) {
        super.init(message: message)
        HResult = CNAException.externalExceptionHResult
    }

    /// `ExternalException..ctor(String message, Exception inner)`.
    ///
    /// The CLR parameter is named `inner` here and `innerException` on
    /// `System.Exception`. The Swift label follows the base whose initializer
    /// this overrides, because Swift requires an override to keep the
    /// inherited signature; the CLR name difference is recorded rather than
    /// projected, and it is invisible to a caller of any XNA subclass, whose
    /// own labels come from its own metadata.
    public override init(message: String?, innerException: CNAException?) {
        super.init(message: message, innerException: innerException)
        HResult = CNAException.externalExceptionHResult
    }

    /// `ExternalException..ctor(String message, Int32 errorCode)`.
    ///
    /// The one constructor of this family that does not use the fixed HResult:
    /// it calls `SetErrorCode(errorCode)` with the caller's value, which is
    /// exactly what `ErrorCode` then reports.
    public init(message: String?, errorCode: Int32) {
        super.init(message: message)
        HResult = errorCode
    }

    /// `ExternalException.ErrorCode`.
    ///
    /// `get_ErrorCode` is `ldarg.0; call get_HResult; ret` — the same value,
    /// exposed publicly and get-only. `virtual` and not `final`, so `open`.
    open var ErrorCode: Int32 { HResult }
}
