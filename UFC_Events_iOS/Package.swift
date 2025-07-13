// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "UFC_Events_iOS",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(
            name: "UFC_Events_iOS",
            targets: ["UFC_Events_iOS"]),
    ],
    targets: [
        .target(
            name: "UFC_Events_iOS",
            path: "UFC_Events_iOS",
            resources: [
                .process("Resources")
            ]
        ),
    ]
)