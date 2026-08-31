// SPDX-License-Identifier: MIT

import XCTest
@testable import CNA

// Pure XNA-derived behaviour for `Microsoft.Xna.Framework.LaunchParameters`,
// transcribed from the CIL of the hash-registered
// `Microsoft.Xna.Framework.Game.dll` (SHA-256 b5dffdd8…a1f0).
//
// The type declares one parameterless constructor whose body is exactly
// `base..ctor()`, so everything asserted here about its usable surface is the
// inherited `Dictionary<string, string>` behaviour arriving through an XNA
// type — which is precisely the claim the base projection makes.
extension PureValueTests {

    func testLaunchParametersDerivesFromTheDictionarySpecialization() {
        let parameters = Microsoft.Xna.Framework.LaunchParameters()
        XCTAssertTrue(parameters is CNADictionary<String, String>)
        // The element types are preserved, not erased: a `CNADictionary<Any,
        // Any>` would have made every inherited signature wrong.
        let asBase: CNADictionary<String, String> = parameters
        XCTAssertEqual(asBase.Count, 0)
    }

    // `base..ctor()` and nothing else: a fresh instance is empty, and this
    // binding has no producer that fills it. Fabricating launch data would be
    // worse than not having it.
    func testLaunchParametersStartsEmpty() throws {
        let parameters = Microsoft.Xna.Framework.LaunchParameters()
        XCTAssertEqual(parameters.Count, 0)
        XCTAssertFalse(parameters.ContainsKey("/windowed"))
        XCTAssertNil(try parameters.GetEnumerator().Next())
    }

    // Reference identity, which is the whole reason the base is a class: two
    // instances are distinct, and a second binding of the same instance is the
    // same object rather than a copy.
    func testLaunchParametersHasReferenceIdentity() throws {
        let first = Microsoft.Xna.Framework.LaunchParameters()
        let second = Microsoft.Xna.Framework.LaunchParameters()
        XCTAssertFalse(first === second)

        let alias = first
        try alias.Add("/windowed", value: "")
        XCTAssertEqual(
            first.Count, 1,
            "a Swift dictionary would have given the alias a copy here")
        XCTAssertTrue(alias === first)
    }

    // The inherited surface is usable through the XNA type, including the two
    // behaviours a Swift `[String: String]` could not have provided.
    func testTheInheritedDictionarySurfaceWorksThroughTheXnaType() throws {
        let parameters = Microsoft.Xna.Framework.LaunchParameters()
        try parameters.Add("/windowed", value: "true")
        try parameters.Add("/level", value: "3")

        XCTAssertEqual(parameters.Count, 2)
        XCTAssertEqual(try parameters.Item("/level"), "3")
        XCTAssertTrue(parameters.ContainsKey("/windowed"))
        XCTAssertTrue(parameters.ContainsValue("3"))

        var value: String?
        XCTAssertTrue(parameters.TryGetValue("/level", value: &value))
        XCTAssertEqual(value, "3")

        // Add refuses a duplicate; the indexer overwrites one.
        XCTAssertThrowsError(try parameters.Add("/level", value: "4"))
        try parameters.SetItem("/level", "4")
        XCTAssertEqual(try parameters.Item("/level"), "4")

        // Enumeration is in insertion order.
        var collected: [String] = []
        let enumerator = parameters.GetEnumerator()
        while let pair = try enumerator.Next() { collected.append(pair.Key) }
        XCTAssertEqual(collected, ["/windowed", "/level"])

        XCTAssertTrue(parameters.Remove("/windowed"))
        XCTAssertEqual(parameters.Count, 1)
        parameters.Clear()
        XCTAssertEqual(parameters.Count, 0)
    }

    // CLR non-sealed maps to Swift `open`, so a consumer can derive from it
    // exactly as XNA allows.
    func testLaunchParametersIsDerivable() throws {
        let derived = DerivedLaunchParameters()
        try derived.Add("/mode", value: "test")
        XCTAssertEqual(derived.Count, 1)
        XCTAssertTrue(derived is Microsoft.Xna.Framework.LaunchParameters)
        XCTAssertTrue(derived is CNADictionary<String, String>)
    }
}

final class DerivedLaunchParameters: Microsoft.Xna.Framework.LaunchParameters {}
