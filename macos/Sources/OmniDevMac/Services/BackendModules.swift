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

    // MARK: - Git landing

    struct LandResult: Decodable {
        let path: String
        let commit: String
        let filesWritten: Int
        let message: String
    }

    func landProject(
        name: String,
        files: [GeneratedFile],
        message: String
    ) async throws -> LandResult {
        try await post(
            "api/git/land",
            body: [
                "name": name,
                "files": files.map { ["path": $0.path, "content": $0.content] },
                "message": message,
            ]
        )
    }

    // MARK: - MCP marketplace

    struct MCPCatalogParam: Decodable, Identifiable {
        let name: String
        let type: String
        let description: String

        var id: String { name }
    }

    struct MCPCatalogEntry: Decodable, Identifiable {
        let id: String
        let name: String
        let description: String
        let capabilities: String
        let runtime: String
        let runtimeAvailable: Bool
        let params: [MCPCatalogParam]
    }

    private struct MCPCatalog: Decodable {
        let entries: [MCPCatalogEntry]
    }

    struct MCPServer: Decodable, Identifiable {
        let name: String
        let catalogId: String
        let params: [String: String]
        let enabled: Bool

        var id: String { name }
    }

    private struct MCPServerList: Decodable {
        let servers: [MCPServer]
    }

    struct MCPTool: Decodable, Identifiable {
        let name: String
        let description: String

        var id: String { name }
    }

    private struct MCPToolList: Decodable {
        let tools: [MCPTool]
    }

    func mcpCatalog() async throws -> [MCPCatalogEntry] {
        let catalog: MCPCatalog = try await get("api/mcp/catalog")
        return catalog.entries
    }

    func mcpServers() async throws -> [MCPServer] {
        let list: MCPServerList = try await get("api/mcp/servers")
        return list.servers
    }

    func mcpAddServer(catalogId: String, params: [String: String]) async throws -> MCPServer {
        try await post("api/mcp/servers", body: ["catalog_id": catalogId, "params": params])
    }

    func mcpRemoveServer(_ name: String) async throws {
        struct Ack: Decodable { let deleted: String }
        let _: Ack = try await send("DELETE", "api/mcp/servers/\(name)")
    }

    func mcpSetEnabled(_ name: String, enabled: Bool) async throws {
        var request = URLRequest(url: baseURL.appendingPathComponent("api/mcp/servers/\(name)"))
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["enabled": enabled])
        let (data, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, http.statusCode != 200 {
            throw BackendError.http(http.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
    }

    func mcpTools(server: String) async throws -> [MCPTool] {
        let list: MCPToolList = try await get("api/mcp/servers/\(server)/tools")
        return list.tools
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

    // MARK: - Knowledge

    struct KnowledgeSource: Decodable, Identifiable {
        let id: Int
        let path: String
        let kind: String
        let lastIndexedAt: String?
        let fileCount: Int
        let chunkCount: Int
    }

    struct KnowledgeSourceList: Decodable {
        let sources: [KnowledgeSource]
    }

    struct KnowledgeIndexStatus: Decodable {
        let running: Bool
        let sourceId: Int?
        let filesTotal: Int
        let filesDone: Int
        let error: String?

        var fraction: Double? {
            guard running, filesTotal > 0 else { return nil }
            return Double(filesDone) / Double(filesTotal)
        }
    }

    struct KnowledgeHit: Decodable, Identifiable {
        let sourceId: Int
        let kind: String
        let filePath: String
        let snippet: String
        let score: Double

        var id: String { "\(sourceId):\(filePath):\(score)" }
    }

    struct KnowledgeSearchResult: Decodable {
        let results: [KnowledgeHit]
    }

    func knowledgeSources() async throws -> [KnowledgeSource] {
        let list: KnowledgeSourceList = try await get("api/knowledge/sources")
        return list.sources
    }

    @discardableResult
    func addKnowledgeSource(path: String, kind: String) async throws -> KnowledgeSource {
        try await post("api/knowledge/sources", body: ["path": path, "kind": kind])
    }

    func deleteKnowledgeSource(id: Int) async throws {
        struct DeleteAck: Decodable { let deleted: Int }
        let _: DeleteAck = try await send("DELETE", "api/knowledge/sources/\(id)")
    }

    @discardableResult
    func reindexKnowledgeSource(id: Int, full: Bool = false) async throws -> KnowledgeIndexStatus {
        try await send(
            "POST",
            "api/knowledge/sources/\(id)/reindex",
            query: full ? ["full": "true"] : [:]
        )
    }

    func knowledgeStatus() async throws -> KnowledgeIndexStatus {
        try await get("api/knowledge/status")
    }

    func knowledgeSearch(query: String, topK: Int = 8) async throws -> [KnowledgeHit] {
        let result: KnowledgeSearchResult = try await post(
            "api/knowledge/search",
            body: ["query": query, "top_k": topK]
        )
        return result.results
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
