// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework.Content {
    /// `Microsoft.Xna.Framework.Content.ContentLoadException`.
    ///
    /// Pinned in `Microsoft.Xna.Framework.dll` as a public **unsealed** class whose direct base
    /// is `System.Exception`, and it declares **nothing but constructors**: every
    /// usable member — `Message`, `InnerException`, `HResult` — is
    /// inherited, which is why the base is a real Swift superclass rather than
    /// a dropped one.
    ///
    /// One of the two XNA exception types the CLR leaves **unsealed**, so
    /// it is `open` rather than `final` and a consumer may derive from it.
    ///
    /// It also declares a fourth, `protected`, constructor taking
    /// `(SerializationInfo, StreamingContext)`. That one is deliberately
    /// **not** implemented: reconstructing it means reading named values
    /// back out of a `SerializationInfo`, which needs `System.Type`,
    /// `System.Collections.IDictionary` and a deserialization runtime this
    /// projection does not have. Swift has no `protected`, so a projected
    /// version would be publicly callable and would silently produce an
    /// exception carrying none of the serialized state. It is therefore
    /// counted as a MISSING_MEMBER with a named blocker rather than faked.
    ///
    /// Every constructor body in the IL is a bare forward to the base:
    /// `ldarg.0`, the arguments, `call base..ctor`, `ret`. No message is
    /// synthesized here, so whatever `CNAException` produces for a null message
    /// is what this type reports.
    ///
    /// CLR non-sealed maps to Swift `open`.
    open class ContentLoadException: CNAException {
        /// `.ctor()`.
        public override init() {
            super.init()
        }

        /// `.ctor(String message)`.
        ///
        /// The CLR stores the argument without validating it, so `nil` is a
        /// normal state and selects the base's default message.
        public override init(message: String?) {
            super.init(message: message)
        }

        /// `.ctor(String message, Exception innerException)`.
        public override init(message: String?, innerException: CNAException?) {
            super.init(message: message, innerException: innerException)
        }
    }
}
