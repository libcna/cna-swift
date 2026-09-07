// SPDX-License-Identifier: MIT

import XCTest
@testable import CNA

/// Storage, projected at Foundation 102.
///
/// **These tests need no `Game`.** Every other runtime-backed suite here drives
/// a probe game, because every other owned type reaches its routes through
/// `RuntimeRegistry.current()`. `cna_storage_device_show_selector` takes no
/// game handle, so `StorageDevice` does not either, and the tests say so by
/// simply calling it.
///
/// **They write to a real directory and clean up after themselves.** CNA's
/// storage root is `~/.local/share/game`, which on this machine holds forty
/// directories belonging to other agents' runs. The container name below is
/// this suite's own, nothing else is touched, and `DeleteContainer` removes it
/// at the end. Foundation 102 learned that the hard way by deleting a
/// neighbour's empty directory it had mistaken for its own.
final class Foundation102StorageTests: XCTestCase {

    private static let container = "cna-swift-f102-tests"

    private func device() throws -> Microsoft.Xna.Framework.Storage.StorageDevice {
        var delivered: (any CNAAsyncResult)?
        let result = try Microsoft.Xna.Framework.Storage.StorageDevice
            .BeginShowSelector({ delivered = $0 }, state: nil)
        XCTAssertNotNil(
            delivered,
            "the callback must have run before BeginShowSelector returned: CNA's "
            + "header says the completion callback fires before the call does")
        return try Microsoft.Xna.Framework.Storage.StorageDevice
            .EndShowSelector(result)
    }

    // MARK: - Selection

    func testBeginShowSelectorCompletesSynchronously() throws {
        let result = try Microsoft.Xna.Framework.Storage.StorageDevice
            .BeginShowSelector({ _ in }, state: nil)
        XCTAssertTrue(result.IsCompleted)
        XCTAssertTrue(
            result.CompletedSynchronously,
            "CNA's storage routes finish on the calling thread, and the CLR "
            + "contract has a property for saying exactly that")
    }

    func testTheStateIsHandedBackUnchanged() throws {
        let token = NSObject()
        let result = try Microsoft.Xna.Framework.Storage.StorageDevice
            .BeginShowSelector({ _ in }, state: token)
        XCTAssertTrue(result.AsyncState as? NSObject === token)
    }

    func testANilStateIsAllowedAndReportedAsNil() throws {
        let result = try Microsoft.Xna.Framework.Storage.StorageDevice
            .BeginShowSelector({ _ in }, state: nil)
        XCTAssertNil(result.AsyncState)
    }

    func testEndShowSelectorRefusesAContainerResult() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        XCTAssertThrowsError(
            try Microsoft.Xna.Framework.Storage.StorageDevice
                .EndShowSelector(opened),
            "a result from BeginOpenContainer is not a device result"
        ) { error in
            XCTAssertTrue(error is CNAArgumentException)
        }
        try selector.EndOpenContainer(opened).Dispose()
    }

    // MARK: - Device state

    func testTheDeviceAnswersItsSpaceAndConnection() throws {
        let selector = try device()
        XCTAssertTrue(selector.IsConnected)
        let total = try selector.TotalSpace
        let free = try selector.FreeSpace
        XCTAssertGreaterThan(total, 0)
        XCTAssertGreaterThan(free, 0)
        // STRICTLY less, not `<=`. The weaker form let
        // `storage-free-space-answers-the-total` survive: a FreeSpace that
        // reads the total-space route answers free == total, which satisfies
        // `<=` and reports a nearly full device as empty.
        //
        // This does lean on the host having something on its storage volume.
        // A completely empty one would make free == total honestly and fail
        // here -- loudly, which is the right way round for an assertion that
        // has stopped being able to tell two routes apart.
        XCTAssertLessThan(
            free, total,
            "FreeSpace and TotalSpace must be different routes, and on any "
            + "host with a byte written they answer differently")
    }

    // MARK: - Containers

    func testAContainerReportsTheNameItWasOpenedWith() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        let container = try selector.EndOpenContainer(opened)
        XCTAssertEqual(try container.DisplayName, Self.container)
        XCTAssertFalse(container.IsDisposed)
        try container.Dispose()
        XCTAssertTrue(container.IsDisposed)
    }

    func testTheContainerRefusesEveryCallAfterDisposal() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        let container = try selector.EndOpenContainer(opened)
        try container.Dispose()
        XCTAssertThrowsError(try container.FileExists("anything")) { error in
            XCTAssertTrue(error is CNAObjectDisposedException)
        }
        XCTAssertThrowsError(try container.DisplayName) { error in
            XCTAssertTrue(error is CNAObjectDisposedException)
        }
    }

    func testDisposingTwiceIsSilent() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        let container = try selector.EndOpenContainer(opened)
        try container.Dispose()
        XCTAssertNoThrow(try container.Dispose())
    }

    func testTheContainerCarriesTheDeviceItCameFrom() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        let container = try selector.EndOpenContainer(opened)
        XCTAssertTrue(try container.StorageDevice === selector)
        try container.Dispose()
    }

    // MARK: - Files and directories

    func testAFileRoundTripsThroughExistenceAndNames() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        let container = try selector.EndOpenContainer(opened)
        defer { try? container.Dispose() }

        XCTAssertFalse(try container.DirectoryExists("f102"))
        try container.CreateDirectory("f102")
        XCTAssertTrue(try container.DirectoryExists("f102"))
        XCTAssertTrue(try container.GetDirectoryNames().contains("f102"))
        XCTAssertTrue(try container.GetDirectoryNames("f10*").contains("f102"))
        XCTAssertFalse(try container.GetDirectoryNames("zzz*").contains("f102"))

        try container.DeleteDirectory("f102")
        XCTAssertFalse(try container.DirectoryExists("f102"))
    }

    func testAnAbsentFileIsReportedAbsent() throws {
        let selector = try device()
        let opened = try selector.BeginOpenContainer(
            Self.container, callback: { _ in }, state: nil)
        let container = try selector.EndOpenContainer(opened)
        defer { try? container.Dispose() }
        XCTAssertFalse(try container.FileExists("no-such-file"))
        XCTAssertEqual(try container.GetFileNames("no-such-*"), [])
    }

    // MARK: - Cleanup

    /// Removes what this suite created, and only that.
    override class func tearDown() {
        let selector = try? Microsoft.Xna.Framework.Storage.StorageDevice
            .BeginShowSelector({ _ in }, state: nil)
        if let selector,
           let opened = try? Microsoft.Xna.Framework.Storage.StorageDevice
            .EndShowSelector(selector) {
            try? opened.DeleteContainer(container)
        }
        super.tearDown()
    }
}
