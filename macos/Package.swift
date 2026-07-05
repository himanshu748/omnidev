// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "OmniDevMac",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "OmniDev", targets: ["OmniDevMac"])
    ],
    targets: [
        .executableTarget(
            name: "OmniDevMac",
            resources: [
                .copy("Resources/AppIcon.png")
            ]
        )
    ]
)
