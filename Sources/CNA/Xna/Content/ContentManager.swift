// SPDX-License-Identifier: MIT

import CNAShim
import Foundation

extension Microsoft.Xna.Framework.Content {

    /// `Microsoft.Xna.Framework.Content.ContentManager`.
    ///
    /// Ten members, and the interesting half is managed: the disposal test, the
    /// empty-name test, the path normalisation, and the cache — including what
    /// happens when a cached asset is the wrong type.
    ///
    /// **`Load` reuses `TitleContainer.GetCleanPath`.** XNA's does, in the
    /// instruction right after its argument checks, so an asset named
    /// `"a/../b"` and one named `"b"` are the same cache entry. Foundation 73
    /// built that routine from the same IL, and this calls it rather than
    /// reimplementing the agreement.
    public class ContentManager: RuntimeOwnedChild {

        private let runtime: RuntimeState
        private var handle: UInt64
        private let serviceProvider: (any CNAServiceProvider)?
        private var storedRootDirectory: String?

        /// XNA's `loadedAssets`, and **null is what "disposed" means here**:
        /// `Load` tests it before anything else and raises
        /// `ObjectDisposedException` when it is gone. Optional for the same
        /// reason.
        private var loadedAssets: [String: Any]?

        /// `ContentManager(IServiceProvider serviceProvider)`.
        public convenience init(
            serviceProvider: any CNAServiceProvider
        ) throws {
            try self.init(serviceProvider: serviceProvider, rootDirectory: "")
        }

        /// `ContentManager(IServiceProvider serviceProvider, String rootDirectory)`.
        ///
        /// The two-argument constructor sets `RootDirectory` **through the
        /// property**, so its null check runs — which is why a null root
        /// directory is refused at construction and not merely at assignment.
        public init(
            serviceProvider: any CNAServiceProvider,
            rootDirectory: String
        ) throws {
            let rt = try RuntimeRegistry.current()
            self.runtime = rt
            self.serviceProvider = serviceProvider
            self.storedRootDirectory = rootDirectory
            self.loadedAssets = [:]

            var device: UInt64 = 0
            try rt.functions.check(
                rt.functions.gameGetGraphicsDevice(rt.gameHandle, &device),
                operation: "cna_game_get_graphics_device")

            var utf8 = Array(rootDirectory.utf8)
            var created: UInt64 = 0
            try rt.functions.check(
                ContentManager.withStringView(&utf8) { view in
                    var info = CNASwift_ContentManagerCreateInfo()
                    info.struct_size =
                        UInt32(MemoryLayout<CNASwift_ContentManagerCreateInfo>.size)
                    info.struct_version = 1
                    info.root_directory = view
                    return rt.functions.contentManagerCreate(
                        device, &info, &created)
                },
                operation: "cna_content_manager_create")
            handle = created

            // CNA requires a content manager to be destroyed BEFORE its parent
            // game, so the manager joins the runtime's child registry and is
            // torn down by `Game.Dispose` if the caller never disposes it.
            rt.register(self)
        }

        /// `ContentManager.ServiceProvider`.
        ///
        /// Infallible and a bare field read, so it is a stored value here too.
        public var ServiceProvider: (any CNAServiceProvider)? {
            serviceProvider
        }

        /// `ContentManager.RootDirectory`.
        ///
        /// The getter is infallible; **the setter raises
        /// `ArgumentNullException("value")`**, so it is a writer method taking
        /// an Optional — without which that branch could not be reached from
        /// Swift at all.
        public var RootDirectory: String? { storedRootDirectory }

        public func SetRootDirectory(_ value: String?) throws {
            guard let value else {
                throw CNAArgumentNullException(paramName: "value")
            }
            storedRootDirectory = value
        }

        /// `ContentManager.Load<T>(String assetName)`.
        ///
        /// XNA's 199 bytes, in order:
        ///
        /// ```text
        /// if (loadedAssets == null) throw ObjectDisposedException(ToString());
        /// if (String.IsNullOrEmpty(assetName)) throw ArgumentNullException("assetName");
        /// assetName = TitleContainer.GetCleanPath(assetName);
        /// if (loadedAssets.TryGetValue(assetName, out cached)) {
        ///     if (!(cached is T)) throw ContentLoadException(BadXnbWrongType, …);
        ///     return (T)cached;
        /// }
        /// … ReadAsset<T> and store
        /// ```
        ///
        /// **The disposal test comes first**, before the name is even looked
        /// at, so `Load(null)` on a disposed manager reports the disposal.
        ///
        /// **A cache hit of the wrong type throws rather than reloading.** The
        /// message names the asset, the type found and the type asked for, in
        /// that order.
        public func Load<T>(_ assetName: String?) throws -> T {
            guard var assets = loadedAssets else {
                throw CNAObjectDisposedException(objectName: "\(type(of: self))")
            }
            guard let assetName, !assetName.isEmpty else {
                throw CNAArgumentNullException(paramName: "assetName")
            }
            let key = Microsoft.Xna.Framework.TitleContainer.GetCleanPath(assetName)

            // One cast site, reached by both paths. A freshly loaded asset
            // always matches, because `readAsset` picks its route from `T`;
            // a cached one need not, and that is the case `BadXnbWrongType`
            // was written for -- the same name loaded twice as two types.
            let asset: Any
            if let cached = assets[key] {
                asset = cached
            } else {
                asset = try readAsset(key, as: T.self)
                assets[key] = asset
                loadedAssets = assets
            }
            guard let typed = asset as? T else {
                throw Microsoft.Xna.Framework.Content.ContentLoadException(
                    message: ContentManager.badXnbWrongTypeMessage(
                        key, String(describing: type(of: asset)),
                        String(describing: T.self)))
            }
            return typed
        }

        /// The typed half of `ReadAsset<T>`.
        ///
        /// XNA reads an `.xnb` header and picks a type reader from it. CNA
        /// publishes **one route per asset kind** instead —
        /// `load_texture2d`, `load_texture_cube`, `load_sprite_font`,
        /// `load_effect`, `load_sound_effect`, `load_model` — so the type
        /// argument selects the route rather than validating a header this
        /// binding never sees.
        ///
        /// **Only `Texture2D` is wired here.** CNA publishes five more
        /// loaders -- cube, sprite font, effect, sound effect, model -- and
        /// none is bound, because adopting what they produce needs machinery
        /// those types own and this milestone does not build. A route with no
        /// consuming member is not bound, so they wait for the milestones that
        /// can receive them.
        ///
        /// A type with no loader is refused by name. That is narrower than
        /// XNA, which loads whatever the `.xnb` declares, and the refusal says
        /// so rather than reporting the asset as missing.
        private func readAsset<T>(_ key: String, as: T.Type) throws -> Any {
            var utf8 = Array(key.utf8)
            var produced: UInt64 = 0
            let functions = runtime.functions

            func load(
                _ route: (UInt64, CNASwift_StringView, UnsafeMutablePointer<UInt64>?) -> UInt32,
                _ operation: String
            ) throws {
                try functions.check(
                    ContentManager.withStringView(&utf8) { view in
                        route(handle, view, &produced)
                    },
                    operation: operation)
            }

            switch T.self {
            case is Microsoft.Xna.Framework.Graphics.Texture2D.Type:
                try load(functions.contentManagerLoadTexture2d,
                         "cna_content_manager_load_texture2d")
                return try Microsoft.Xna.Framework.Graphics.Texture2D
                    .adoptLoaded(handle: produced, runtime: runtime)
            default:
                throw Microsoft.Xna.Framework.Content.ContentLoadException(
                    message: ContentManager.noLoaderMessage(
                        String(describing: T.self)))
            }
        }

        /// `ContentManager.Unload()`.
        ///
        /// Releases every asset the manager loaded and empties the cache. The
        /// manager stays usable afterwards, which is what separates `Unload`
        /// from `Dispose`.
        public func Unload() throws {
            try runtime.functions.check(
                runtime.functions.contentManagerUnload(handle),
                operation: "cna_content_manager_unload")
            loadedAssets = [:]
        }

        /// `ContentManager.Dispose()` and `Dispose(Boolean)`.
        ///
        /// **Nulling the cache is what makes the manager disposed**, because
        /// that is the field `Load` tests. Disposing twice is a no-op, as
        /// XNA's is.
        public func Dispose() throws {
            try Dispose(true)
        }

        open func Dispose(_ disposing: Bool) throws {
            guard loadedAssets != nil else { return }
            loadedAssets = nil
            try runtime.functions.check(
                runtime.functions.contentManagerDestroy(handle),
                operation: "cna_content_manager_destroy")
            handle = 0
        }

        /// `FrameworkResources.BadXnbWrongType`, a three-argument format.
        internal static let badXnbWrongType =
            "Error loading \"{0}\". File contains {1} but trying to load as {2}."

        internal static func badXnbWrongTypeMessage(
            _ asset: String, _ found: String, _ wanted: String
        ) -> String {
            badXnbWrongType
                .replacingOccurrences(of: "{0}", with: asset)
                .replacingOccurrences(of: "{1}", with: found)
                .replacingOccurrences(of: "{2}", with: wanted)
        }

        /// Not a Microsoft string: XNA has no such case, because it reads the
        /// type out of the `.xnb` rather than being told one.
        internal static func noLoaderMessage(_ wanted: String) -> String {
            "This runtime loads content through one route per asset kind, and "
            + "has none for \(wanted). It reads no .xnb header, so it cannot "
            + "discover the type from the file."
        }

        /// The size this binding declares to CNA, exposed so a test can
        /// assert the value the *binding* sees rather than the one a test
        /// module computes from its own copy of the header.
        internal static let createInfoSize =
            MemoryLayout<CNASwift_ContentManagerCreateInfo>.size

        internal var runtimeObjectIsDisposed: Bool { loadedAssets == nil }
        internal func disposeFromParent() throws { try Dispose() }

        private static func withStringView(
            _ utf8: inout [UInt8], _ body: (CNASwift_StringView) -> UInt32
        ) -> UInt32 {
            utf8.withUnsafeMutableBufferPointer { buffer -> UInt32 in
                var view = CNASwift_StringView()
                view.byte_length = UInt64(buffer.count)
                guard let base = buffer.baseAddress else { return body(view) }
                return base.withMemoryRebound(to: CChar.self, capacity: buffer.count) {
                    view.data = UnsafePointer($0)
                    return body(view)
                }
            }
        }
    }
}
