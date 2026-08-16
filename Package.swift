// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CNA",
    platforms: [
        .macOS(.v10_15), .iOS(.v13), .tvOS(.v13), .visionOS(.v1)
    ],
    products: [
        .library(name: "CNA", targets: ["CNA"]),
    ],
    dependencies: [
        // .package(url: "../cnabinding", from: "1.0.0"), // In a real scenario, we'd link to the C binding
    ],
    targets: [
        .target(
            name: "CNA",
            dependencies: [],
            path: "Sources/CNA"
        ),
        .testTarget(
            name: "CNATests",
            dependencies: ["CNA"],
            path: "Tests/CNATests"
        ),
    ]
)
