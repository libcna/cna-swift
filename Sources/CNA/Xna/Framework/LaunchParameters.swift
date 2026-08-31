// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework {
    /// `Microsoft.Xna.Framework.LaunchParameters`.
    ///
    /// Pinned in `Microsoft.Xna.Framework.Game.dll` as a public **unsealed**
    /// class whose direct base is
    /// `System.Collections.Generic.Dictionary<System.String, System.String>`,
    /// declaring **one parameterless constructor and nothing else**. Every
    /// usable member — `Count`, the indexer, `Add`, `Remove`, `Clear`,
    /// `ContainsKey`, `ContainsValue`, `TryGetValue`, `Keys`, `Values`,
    /// `Comparer`, `GetEnumerator` — is inherited.
    ///
    /// That is why the base is a real Swift superclass. `CNADictionary` is the
    /// measured projection of the `Dictionary<TKey,TValue>` shape pinned in
    /// `tools/api_compat/reference/bcl40-selected-shape.json`, and the CLR
    /// generic arguments are preserved in the specialization: the base is
    /// `Dictionary<string, string>`, so the Swift superclass is
    /// `CNADictionary<String, String>` and never `CNADictionary<Any, Any>` or
    /// a flattened Swift `[String: String]`.
    ///
    /// A Swift dictionary would have been the obvious shortcut and is wrong in
    /// three ways at once: it is a value, so a caller would get a copy of the
    /// launch data rather than the object the `Game` owns; it has no `Add` that
    /// refuses a duplicate key; and it has no defined enumeration order, where
    /// the CLR's is insertion order.
    ///
    /// The IL body of the constructor is exactly `base..ctor()`, so a fresh
    /// `LaunchParameters` is empty and its comparer is
    /// `EqualityComparer<string>.Default`. **Nothing is populated here.**
    /// XNA fills this collection from the process command line, and this
    /// binding has no producer for that yet: `Game.LaunchParameters` is still
    /// absent, and fabricating launch data would be worse than not having it.
    /// A consumer can construct one and use every inherited member; what is
    /// missing is the `Game` property that would hand out the one the runtime
    /// built.
    ///
    /// CLR non-sealed maps to Swift `open`.
    open class LaunchParameters: CNADictionary<String, String> {
        /// `.ctor()`.
        ///
        /// The IL body is `ldarg.0; call Dictionary`2::.ctor(); ret` — the
        /// parameterless base constructor, which allocates no table until the
        /// first insertion.
        public override init() {
            super.init()
        }
    }
}
