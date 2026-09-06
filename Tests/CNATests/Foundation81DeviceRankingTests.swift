import XCTest
@testable import CNA

/// `GraphicsDeviceInformationComparer` and `GraphicsDeviceManager.RankDevices`.
///
/// The 638-byte comparison chain, asserted one link at a time. Every link
/// returns immediately, so a test that exercised two at once would not tell
/// which one answered.
final class Foundation81DeviceRankingTests: XCTestCase {
    private typealias Info = Microsoft.Xna.Framework.GraphicsDeviceInformation

    private func candidate(
        profile: Microsoft.Xna.Framework.Graphics.GraphicsProfile = .Reach,
        fullScreen: Bool = true,
        format: Microsoft.Xna.Framework.Graphics.SurfaceFormat = .Color,
        samples: Int32 = 0,
        width: Int32 = 800, height: Int32 = 480
    ) -> Info {
        let info = Info()
        info.GraphicsProfile = profile
        info.PresentationParameters.IsFullScreen = fullScreen
        info.PresentationParameters.BackBufferFormat = format
        info.PresentationParameters.MultiSampleCount = samples
        info.PresentationParameters.BackBufferWidth = width
        info.PresentationParameters.BackBufferHeight = height
        return info
    }

    private func comparer(_ game: RankingProbeGame) throws
        -> Microsoft.Xna.Framework.GraphicsDeviceInformationComparer {
        Microsoft.Xna.Framework.GraphicsDeviceInformationComparer(
            try XCTUnwrap(game.manager))
    }

    func testTheChainInOrder() throws {
        let game = try RankingProbeGame()
        let c = try comparer(game)

        // 1. Higher profile first.
        XCTAssertEqual(c.Compare(candidate(profile: .HiDef),
                                 candidate(profile: .Reach)), -1)
        XCTAssertEqual(c.Compare(candidate(profile: .Reach),
                                 candidate(profile: .HiDef)), 1)

        // 2. The candidate agreeing with the MANAGER's IsFullScreen first.
        let managerWantsFullScreen = try XCTUnwrap(game.manager).IsFullScreen
        XCTAssertEqual(
            c.Compare(candidate(fullScreen: managerWantsFullScreen),
                      candidate(fullScreen: !managerWantsFullScreen)), -1,
            "the manager's own flag decides, not either candidate's")

        // 4. Higher multi-sample count first.
        XCTAssertEqual(c.Compare(candidate(samples: 4), candidate(samples: 0)), -1)
        XCTAssertEqual(c.Compare(candidate(samples: 0), candidate(samples: 4)), 1)
    }

    /// Three answers, and the third is `Int32.max` — which is why the rank
    /// sorts ascending: an unrelated format goes to the very end.
    func testRankFormatHasThreeAnswers() throws {
        let game = try RankingProbeGame()
        let c = try comparer(game)
        let preferred = try XCTUnwrap(game.manager).PreferredBackBufferFormat

        XCTAssertEqual(c.RankFormat(preferred), 0, "the preferred format ranks 0")

        typealias Comparer = Microsoft.Xna.Framework.GraphicsDeviceInformationComparer
        let sameDepth = Comparer.surfaceFormatBitDepth(preferred) == 32
            ? Microsoft.Xna.Framework.Graphics.SurfaceFormat.Rgba1010102
            : Microsoft.Xna.Framework.Graphics.SurfaceFormat.Bgr565
        if sameDepth != preferred {
            XCTAssertEqual(c.RankFormat(sameDepth), 1, "same bit depth ranks 1")
        }
        XCTAssertEqual(c.RankFormat(.Vector4), Int32.max,
                       "an unrelated depth ranks Int32.max, not a middling score")

        // And the rank must sort ASCENDING through Compare, which testing
        // RankFormat alone does not show: a mutation reversing that link
        // survived until this pair existed.
        XCTAssertEqual(c.Compare(candidate(format: preferred),
                                 candidate(format: .Vector4)), -1,
                       "the preferred format outranks an unrelated one")
        XCTAssertEqual(c.Compare(candidate(format: .Vector4),
                                 candidate(format: preferred)), 1)
    }

    /// `Color` and `Rgba1010102` are 32; `Bgr565`, `Bgra5551` and `Bgra4444`
    /// are 16; **everything else is zero**, so all the floating-point and
    /// compressed formats share a depth.
    func testTheBitDepthTableIsExactlyXnasFive() {
        typealias Comparer = Microsoft.Xna.Framework.GraphicsDeviceInformationComparer
        XCTAssertEqual(Comparer.surfaceFormatBitDepth(.Color), 32)
        XCTAssertEqual(Comparer.surfaceFormatBitDepth(.Rgba1010102), 32)
        XCTAssertEqual(Comparer.surfaceFormatBitDepth(.Bgr565), 16)
        XCTAssertEqual(Comparer.surfaceFormatBitDepth(.Bgra5551), 16)
        XCTAssertEqual(Comparer.surfaceFormatBitDepth(.Bgra4444), 16)
        for other: Microsoft.Xna.Framework.Graphics.SurfaceFormat in
            [.Dxt1, .Dxt5, .Alpha8, .Single, .Vector4, .HalfSingle, .HdrBlendable] {
            XCTAssertEqual(Comparer.surfaceFormatBitDepth(other), 0,
                           "\(other) is not in XNA's table")
        }
    }

    /// The aspect-ratio link only decides when the two distances differ by
    /// **more than 0.2** — otherwise the pixel count does.
    func testAspectRatioOnlyDecidesBeyondTheTolerance() throws {
        let game = try RankingProbeGame()
        let c = try comparer(game)

        // 800x480 is 1.667; 640x480 is 1.333; 1600x480 is 3.333. Against a
        // 1.667 target the first two differ by 0.333 -- beyond the tolerance --
        // while 800x480 and 816x480 differ by far less.
        let near = candidate(width: 800, height: 480)
        let wide = candidate(width: 1600, height: 480)
        XCTAssertEqual(c.Compare(near, wide), -1, "0.333 apart: shape decides")

        // Within the tolerance the pixel count decides -- and the two must
        // be made to DISAGREE, or removing the tolerance changes nothing and
        // the mutation survives, which is what happened first.
        //
        //   A 1600x960 -> aspect 1.667, exactly the target: shape says A.
        //   B 1500x960 -> aspect 1.563, 0.104 away: inside the 0.2 tolerance.
        //   Areas 1,536,000 and 1,440,000: B is nearer any target below both,
        //   so pixel count says B.
        //
        // With the tolerance the answer is B. Without it, shape would answer A.
        let exactShape = candidate(width: 1600, height: 960)
        let nearerArea = candidate(width: 1500, height: 960)
        XCTAssertEqual(c.Compare(exactShape, nearerArea), 1,
                       "inside the tolerance, area decides against shape")
    }

    /// `RankDevices` reorders the caller's list in place.
    func testRankDevicesSortsTheCallersListInPlace() throws {
        let game = try RankingProbeGame()
        let manager = try XCTUnwrap(game.manager)
        let worst = candidate(profile: .Reach, samples: 0)
        let best = candidate(profile: .HiDef, samples: 4)
        let list = CNAList<Info>()
        try list.Add(worst)
        try list.Add(best)

        try manager.RankDevices(list)

        XCTAssertTrue(try list.Item(0) === best, "the list is reordered")
        XCTAssertTrue(try list.Item(1) === worst)
        XCTAssertEqual(list.Count, 2, "and not replaced or resized")
    }
}

private final class RankingProbeGame: Microsoft.Xna.Framework.Game {
    var manager: Microsoft.Xna.Framework.GraphicsDeviceManager?

    override init() throws {
        try super.init()
        manager = try Microsoft.Xna.Framework.GraphicsDeviceManager(game: self)
    }
}
