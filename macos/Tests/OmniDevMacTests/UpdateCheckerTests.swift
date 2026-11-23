import XCTest
@testable import OmniDevMac

final class UpdateCheckerTests: XCTestCase {
    func testNumericComponentOrdering() async {
        await MainActor.run {
            for (candidate, current, expected) in [
                ("0.7.10", "0.7.9", true),
                ("0.7.9", "0.7.10", false),
                ("1.0.0", "0.99.99", true),
                ("0.8.0", "0.7.99", true),
                ("0.7.1", "0.7.1", false),
            ] {
                XCTAssertEqual(UpdateChecker.isNewer(candidate, than: current), expected,
                               "\(candidate) compared with \(current)")
            }
        }
    }

    func testMissingComponentsAreZero() async {
        await MainActor.run {
            XCTAssertFalse(UpdateChecker.isNewer("1.2", than: "1.2.0"))
            XCTAssertFalse(UpdateChecker.isNewer("1.2.0", than: "1.2"))
            XCTAssertTrue(UpdateChecker.isNewer("1.2.1", than: "1.2"))
        }
    }
}
