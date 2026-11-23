import Foundation
import XCTest
@testable import OmniDevMac

final class BackendModulesDecodingTests: XCTestCase {
    private func fixture(_ name: String) throws -> Data {
        let url = try XCTUnwrap(Bundle.module.url(forResource: name, withExtension: "json",
                                                  subdirectory: "Fixtures"))
        return try Data(contentsOf: url)
    }

    func testDevOpsConfirmationAndPlanDecodeFromBackendKeys() throws {
        let result = try BackendClient.decoder.decode(BackendClient.DevOpsResult.self,
                                                      from: fixture("devops"))
        XCTAssertTrue(result.needsConfirmation)
        let plan = try XCTUnwrap(result.plan)
        XCTAssertTrue(plan.destructive)
        XCTAssertEqual(plan.readOnly, false)
        XCTAssertEqual(plan.operation, "stop_instances")
        XCTAssertEqual(plan.impact, "Stops the selected fixture instance")
    }

    func testCodeGenFilePayload() throws {
        let result = try BackendClient.decoder.decode(BackendClient.CodeGenResult.self,
                                                      from: fixture("codegen"))
        XCTAssertEqual(result.entry, "index.html")
        XCTAssertEqual(result.files.map(\.path), ["index.html"])
        XCTAssertEqual(result.files.first?.content, "<main>Fixture</main>")
        XCTAssertEqual(result.instructions, "Preview locally")
    }

    func testScraperSnakeCaseAndOptionalFields() throws {
        let result = try BackendClient.decoder.decode(BackendClient.ScrapeResult.self,
                                                      from: fixture("scraper"))
        XCTAssertEqual(result.statusCode, 200)
        XCTAssertEqual(result.elapsedMs, 12)
        XCTAssertEqual(result.links?.first?.isExternal, true)
        XCTAssertNil(result.screenshotB64)
        XCTAssertNil(result.article)
    }

    func testMissingConfirmationIsRejected() throws {
        var payload = try XCTUnwrap(JSONSerialization.jsonObject(with: fixture("devops")) as? [String: Any])
        payload.removeValue(forKey: "needs_confirmation")
        XCTAssertThrowsError(try BackendClient.decoder.decode(BackendClient.DevOpsResult.self,
                                                               from: JSONSerialization.data(withJSONObject: payload)))
    }

    func testStringConfirmationIsRejected() throws {
        var payload = try XCTUnwrap(JSONSerialization.jsonObject(with: fixture("devops")) as? [String: Any])
        payload["needs_confirmation"] = "true"
        XCTAssertThrowsError(try BackendClient.decoder.decode(BackendClient.DevOpsResult.self,
                                                               from: JSONSerialization.data(withJSONObject: payload)))
    }
}
