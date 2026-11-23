import XCTest
@testable import OmniDevMac

final class LocalModelCatalogTests: XCTestCase {
    func testRecommendationAtMemoryBoundary() {
        for memoryGB in [8, 15] {
            XCTAssertEqual(LocalModelCatalog.recommended(memoryGB: memoryGB).name, "gemma4:e2b")
        }
        for memoryGB in [16, 32, 64] {
            XCTAssertEqual(LocalModelCatalog.recommended(memoryGB: memoryGB).name, "gemma4:12b")
        }
    }

    func testCatalogEntriesHaveStableUniqueIdentity() {
        let entries = LocalModelCatalog.entries
        XCTAssertEqual(Set(entries.map(\.id)).count, entries.count)
        for entry in entries {
            XCTAssertEqual(LocalModelCatalog.entry(for: entry.name), entry)
            XCTAssertGreaterThan(entry.sizeGB, 0)
            XCTAssertFalse(entry.label.isEmpty)
        }
        XCTAssertNil(LocalModelCatalog.entry(for: "unknown:custom"))
    }

    func testVisionCapabilityForKnownAndCustomModels() {
        XCTAssertTrue(LocalModelCatalog.isVisionCapable("gemma4:e4b"))
        XCTAssertFalse(LocalModelCatalog.isVisionCapable("qwen2.5-coder:7b"))
        XCTAssertTrue(LocalModelCatalog.isVisionCapable("gemma-custom:latest"))
        XCTAssertFalse(LocalModelCatalog.isVisionCapable("custom:latest"))
    }
}
