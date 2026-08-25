// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework.Media {
    // Pinned in Microsoft.Xna.Framework.Video.dll as a public **sealed** class
    // extending System.Object whose only constructor is `assembly`:
    // `.ctor(GraphicsDevice device, string file, int32 duration, int32 width,
    // int32 height, float32 framesPerSecond, VideoSoundtrackType)`. A CLR class
    // with no accessible constructor cannot be constructed or derived outside
    // its own assembly, so this maps to a `final class` -- metadata sealed --
    // with no public initializer. The internal initializer below is
    // construction infrastructure, not an XNA public member. This is the
    // `DisplayModeCollection` precedent.
    //
    // The public contract is exactly five get-only properties, each returning a
    // stored field verbatim. The IL also declares `assembly` `GraphicsDevice`
    // and `Filename` accessors; both are internal to XNA, are not public
    // contract, and their only consumer is `VideoPlayer`, which is not
    // implemented. Nothing here is carried, because nothing could read it.
    //
    // Completing this type claims **no** video capability. It has no public
    // constructor, so no consumer can obtain an instance; XNA's only producer
    // is `ContentManager`, which is not implemented. Nothing here opens a file,
    // decodes a frame, or invents a duration.
    public final class Video {
        private let duration: Duration
        private let width: Int32
        private let height: Int32
        private let framesPerSecond: Float
        private let soundtrackType: Microsoft.Xna.Framework.Media.VideoSoundtrackType

        // The pinned constructor takes the duration as an `int32` and builds
        // the stored TimeSpan with `TimeSpan(0, 0, 0, 0, duration)` -- the
        // five-argument days/hours/minutes/seconds/**milliseconds** overload.
        // The argument is therefore whole milliseconds, and that conversion is
        // preserved here rather than the caller being asked for a Duration.
        internal init(
            durationMilliseconds: Int32,
            width: Int32,
            height: Int32,
            framesPerSecond: Float,
            soundtrackType: Microsoft.Xna.Framework.Media.VideoSoundtrackType
        ) {
            duration = .milliseconds(durationMilliseconds)
            self.width = width
            self.height = height
            self.framesPerSecond = framesPerSecond
            self.soundtrackType = soundtrackType
        }

        public var Duration: Swift.Duration { duration }

        public var Width: Int32 { width }

        public var Height: Int32 { height }

        public var FramesPerSecond: Float { framesPerSecond }

        public var VideoSoundtrackType:
            Microsoft.Xna.Framework.Media.VideoSoundtrackType
        {
            soundtrackType
        }
    }
}
