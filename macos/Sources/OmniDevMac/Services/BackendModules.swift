import Foundation

/// Module APIs (DevOps, Code Gen, Scraper, Vision, Storage) for the native
/// SwiftUI surfaces — same thin URLSession bridge as the core BackendClient.
extension BackendClient {

    // MARK: - DevOps

    struct DevOpsPlan: Decodable {
        let service: String
        let operation: String
        let params: [String: JSONValue]?
        let destructive: Bool
        let readOnly: Bool?
        let impact: String?
    }

    struct DevOpsResult: Decodable {
        let action: String
        let summary: String
        let needsConfirmation: Bool
        let plan: DevOpsPlan?
    }

    func devopsCommand(_ message: String, confirmDestructive: Bool) async throws -> DevOpsResult {
        try await post(
            "api/devops/command",
            body: ["message": message, "confirm_destructive": confirmDestructive]
        )
    }

    // MARK: - Code Gen

    struct GeneratedFile: Decodable, Identifiable, Hashable {
        let path: String
        var content: String

        var id: String { path }
    }

    struct CodeGenResult: Decodable {
        let files: [GeneratedFile]
        let instructions: String
        let summary: String
        let entry: String
    }

    func generateProject(prompt: String, framework: String) async throws -> CodeGenResult {
        try await post(
            "api/codegen/generate",
            body: ["prompt": prompt, "framework": framework],
            timeout: 600
        )
    }

    func refineProject(
        files: [GeneratedFile],
        instruction: String,
        framework: String
    ) async throws -> CodeGenResult {
        try await post(
            "api/codegen/refine",
            body: [
                "files": files.map { ["path": $0.path, "content": $0.content] },
                "instruction": instruction,
                "framework": framework,
            ],
            timeout: 600
        )
    }

    // MARK: - Scraper

    struct ScrapedLink: Decodable, Identifiable {
        let href: String
        let text: String
        let isExternal: Bool?

        var id: String { href + text }
    }

    struct ScrapedArticle: Decodable {
        let title: String
        let byline: String
        let text: String
        let wordCount: Int
    }

    struct ScrapedMetadata: Decodable {
        let title: String
        let description: String
        let canonical: String
        let language: String
        let wordCount: Int
        let h1Tags: [String]
    }

    struct ScrapeResult: Decodable {
        let url: String
        let title: String
        let statusCode: Int?
        let content: String
        let screenshotB64: String?
        let pdfB64: String?
        let links: [ScrapedLink]?
        let markdown: String?
        let article: ScrapedArticle?
        let metadata: ScrapedMetadata?
        let elapsedMs: Int?
    }

    func scrape(url: String, extract: String, waitSeconds: Double = 0) async throws -> ScrapeResult {
        try await post(
            "api/scraper/scrape",
            body: ["url": url, "extract": extract, "wait_seconds": waitSeconds],
            timeout: 180
        )
    }

    struct CrawlPage: Decodable, Identifiable {
        let url: String
        let title: String
        let excerpt: String
        let depth: Int
        let statusCode: Int?

        var id: String { url }
    }

    struct CrawlResult: Decodable {
        let startUrl: String
        let domain: String
        let pages: [CrawlPage]
        let pagesCrawled: Int
    }

    func crawl(url: String, maxPages: Int, maxDepth: Int) async throws -> CrawlResult {
        try await post(
            "api/scraper/crawl",
            body: ["url": url, "max_pages": maxPages, "max_depth": maxDepth],
            timeout: 300
        )
    }

    // MARK: - Vision

    struct VisionResult: Decodable {
        let mode: String
        let result: String
        let model: String
    }

    func analyzeImage(
        data: Data,
        filename: String,
        contentType: String,
        mode: String,
        prompt: String
    ) async throws -> VisionResult {
        try await postMultipart(
            "api/vision/analyze",
            fields: ["mode": mode, "prompt": prompt],
            fileField: "image",
            filename: filename,
            contentType: contentType,
            fileData: data,
            timeout: 600
        )
    }

    // MARK: - Storage

    struct Bucket: Decodable, Identifiable {
        let name: String
        let creationDate: String?

        var id: String { name }
    }

    private struct BucketList: Decodable {
        let buckets: [Bucket]
    }

    struct S3Object: Decodable, Identifiable {
        let key: String
        let size: Int
        let lastModified: String?
        let storageClass: String

        var id: String { key }
    }

    private struct S3ObjectList: Decodable {
        let files: [S3Object]
    }

    private struct PresignedDownload: Decodable {
        let presignedUrl: String
    }

    func listBuckets() async throws -> [Bucket] {
        let list: BucketList = try await get("api/storage/buckets")
        return list.buckets
    }

    func listObjects(bucket: String, prefix: String) async throws -> [S3Object] {
        let list: S3ObjectList = try await get(
            "api/storage/files",
            query: ["bucket": bucket, "prefix": prefix]
        )
        return list.files
    }

    func uploadObject(
        data: Data,
        filename: String,
        contentType: String,
        bucket: String
    ) async throws {
        struct UploadAck: Decodable { let key: String }
        let _: UploadAck = try await postMultipart(
            "api/storage/upload",
            fields: ["bucket": bucket, "key": ""],
            fileField: "file",
            filename: filename,
            contentType: contentType,
            fileData: data,
            timeout: 600
        )
    }

    func downloadURL(bucket: String, key: String) async throws -> URL {
        let response: PresignedDownload = try await get(
            "api/storage/download",
            query: ["bucket": bucket, "key": key]
        )
        guard let url = URL(string: response.presignedUrl) else {
            throw BackendError.stream("Backend returned an invalid presigned URL.")
        }
        return url
    }

    func deleteObject(bucket: String, key: String) async throws {
        struct DeleteAck: Decodable { let key: String }
        let _: DeleteAck = try await send("DELETE", "api/storage/files", query: ["bucket": bucket, "key": key])
    }
}

/// Loosely-typed JSON for plan params and similar heterogeneous payloads.
enum JSONValue: Decodable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else if let value = try? container.decode([JSONValue].self) {
            self = .array(value)
        } else {
            self = .null
        }
    }

    var display: String {
        switch self {
        case .string(let value):
            return value
        case .number(let value):
            return value == value.rounded() ? String(Int(value)) : String(value)
        case .bool(let value):
            return value ? "true" : "false"
        case .object(let value):
            let body = value.map { "\($0.key): \($0.value.display)" }.sorted().joined(separator: ", ")
            return "{\(body)}"
        case .array(let value):
            return "[\(value.map(\.display).joined(separator: ", "))]"
        case .null:
            return "—"
        }
    }
}
