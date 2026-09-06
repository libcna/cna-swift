// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework.Media {

    /// `Microsoft.Xna.Framework.Media.MediaLibrary`.
    ///
    /// **The door into the Media graph**, and the reason it is projected now
    /// rather than later: `Artist`, `Album`, `Genre` and the four collections
    /// are correct and ABI-verified, and without a library nothing on this host
    /// can obtain one. A song created from a file path has no library context
    /// at all -- CNA says so and `Song.Artist` reports it.
    ///
    /// **Partial, deliberately.** The picture half -- `Pictures`,
    /// `SavedPictures`, `RootPictureAlbum`, `SavePicture`,
    /// `GetPictureFromToken` -- reaches `Picture`, `PictureCollection` and
    /// `PictureAlbum`, and `Playlists` reaches `PlaylistCollection`; those are
    /// four more missing types and their own milestone. `MediaSource` is a
    /// fifth. What is here is the half that makes the rest of this family
    /// reachable and testable.
    public final class MediaLibrary: RuntimeOwnedChild {

        private let runtime: RuntimeState
        private var handle: UInt64
        private var released = false

        /// `MediaLibrary()`, the parameterless constructor.
        public init() throws {
            let rt = try RuntimeRegistry.current()
            var created: UInt64 = 0
            try rt.functions.check(
                rt.functions.mediaLibraryCreate(rt.gameHandle, &created),
                operation: "cna_media_library_create")
            runtime = rt
            handle = created
            rt.register(self)
        }

        /// `MediaLibrary.IsDisposed`.
        public var IsDisposed: Bool {
            guard !released, handle != 0 else { return true }
            var value: UInt8 = 0
            guard runtime.functions.mediaLibraryGetIsDisposed(
                handle, &value) == 0 else { return released }
            return value != 0
        }

        /// `MediaLibrary.Songs`.
        ///
        /// **Optional, and so are the other three.** Each return is proven
        /// nullable, which is XNA reporting that a library without that kind
        /// of media has no collection to hand back rather than an empty one.
        /// CNA always answers a collection here, so the nil case is a state
        /// this host does not produce -- but the projection carries it, because
        /// the pinned metadata says a caller can meet it.
        public var Songs: SongCollection? {
            get throws {
                let live = try validated()
                var produced: UInt64 = 0
                try runtime.functions.check(
                    runtime.functions.mediaLibraryGetSongs(live, &produced),
                    operation: "cna_media_library_get_songs")
                return SongCollection(handle: produced, runtime: runtime)
            }
        }

        /// `MediaLibrary.Artists`.
        public var Artists: ArtistCollection? {
            get throws {
                let live = try validated()
                var produced: UInt64 = 0
                try runtime.functions.check(
                    runtime.functions.mediaLibraryGetArtists(live, &produced),
                    operation: "cna_media_library_get_artists")
                return ArtistCollection(handle: produced, runtime: runtime)
            }
        }

        /// `MediaLibrary.Albums`.
        public var Albums: AlbumCollection? {
            get throws {
                let live = try validated()
                var produced: UInt64 = 0
                try runtime.functions.check(
                    runtime.functions.mediaLibraryGetAlbums(live, &produced),
                    operation: "cna_media_library_get_albums")
                return AlbumCollection(handle: produced, runtime: runtime)
            }
        }

        /// `MediaLibrary.Genres`.
        public var Genres: GenreCollection? {
            get throws {
                let live = try validated()
                var produced: UInt64 = 0
                try runtime.functions.check(
                    runtime.functions.mediaLibraryGetGenres(live, &produced),
                    operation: "cna_media_library_get_genres")
                return GenreCollection(handle: produced, runtime: runtime)
            }
        }

        /// `MediaLibrary.Dispose()`.
        public func Dispose() throws {
            guard !released else { return }
            released = true
            let live = handle
            handle = 0
            try runtime.functions.check(
                runtime.functions.mediaLibraryDispose(live),
                operation: "cna_media_library_dispose")
            try runtime.functions.check(
                runtime.functions.mediaLibraryDestroy(live),
                operation: "cna_media_library_destroy")
        }

        private func validated() throws -> UInt64 {
            guard !released, handle != 0 else {
                throw CNAObjectDisposedException(objectName: "MediaLibrary")
            }
            return handle
        }

        internal var runtimeObjectIsDisposed: Bool { released }
        internal func disposeFromParent() throws { try Dispose() }
    }
}
