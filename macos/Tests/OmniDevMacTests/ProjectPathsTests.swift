import Foundation
import XCTest
@testable import OmniDevMac

final class ProjectPathsTests: XCTestCase {
    private func temporaryDirectory() throws -> URL {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent("omnidev-path-tests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        addTeardownBlock { try FileManager.default.removeItem(at: directory) }
        return directory
    }

    private func addCheckoutMarkers(at root: URL) throws {
        let launcher = root.appendingPathComponent("scripts/macos/launch-omnidev.sh")
        try FileManager.default.createDirectory(at: root.appendingPathComponent("backend"),
                                                withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: launcher.deletingLastPathComponent(),
                                                withIntermediateDirectories: true)
        try Data("#!/bin/sh\n".utf8).write(to: launcher)
    }

    func testBothCheckoutMarkersAreRequired() throws {
        let backendOnly = try temporaryDirectory()
        try FileManager.default.createDirectory(at: backendOnly.appendingPathComponent("backend"),
                                                withIntermediateDirectories: true)
        let launcherOnly = try temporaryDirectory()
        let launcher = launcherOnly.appendingPathComponent("scripts/macos/launch-omnidev.sh")
        try FileManager.default.createDirectory(at: launcher.deletingLastPathComponent(),
                                                withIntermediateDirectories: true)
        try Data().write(to: launcher)
        XCTAssertNil(ProjectPaths.checkoutRoot(candidates: [backendOnly, launcherOnly]))
    }

    func testFirstCompleteCheckoutWins() throws {
        let invalid = try temporaryDirectory()
        let first = try temporaryDirectory()
        let second = try temporaryDirectory()
        try addCheckoutMarkers(at: first)
        try addCheckoutMarkers(at: second)
        XCTAssertEqual(ProjectPaths.checkoutRoot(candidates: [invalid, first, second]),
                       first.standardizedFileURL)
        XCTAssertEqual(ProjectPaths.checkoutRoot(candidates: [second, first]),
                       second.standardizedFileURL)
    }

    func testNoCandidatesDoesNotInstallAnEngine() {
        XCTAssertNil(ProjectPaths.checkoutRoot(candidates: []))
    }
}
