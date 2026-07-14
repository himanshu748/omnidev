import Foundation

/// Thin async client for the local FastAPI engine. All calls stay on
/// 127.0.0.1; streaming endpoints yield NDJSON lines as typed events.
struct BackendClient {
    let baseURL: URL

    struct Health: Decodable {
        let aiProvider: String
        let aiModel: String
    }

    struct ProviderStatus: Decodable {
        let provider: String
        let textModel: String
        let visionModel: String?
        let reachable: Bool
        let textModelReady: Bool?
        let visionModelReady: Bool?
    }

    struct InstalledModel: Decodable, Identifiable {
        let name: String
        let sizeGb: Double
        let parameterSize: String
        let quantization: String

        var id: String { name }
    }

    struct ModelsOverview: Decodable {
        let status: ProviderStatus
        let installed: [InstalledModel]
    }

    struct DeleteResult: Decodable {
        let deleted: String
    }

    struct PullProgress {
        let status: String
        let completed: Int64?
        let total: Int64?

        var fraction: Double? {
            guard let completed, let total, total > 0 else { return nil }
            return Double(completed) / Double(total)
        }
    }

    enum BackendError: LocalizedError {
        case http(Int, String)
        case stream(String)

        var errorDescription: String? {
            switch self {
            case .http(let code, let detail):
                return detail.isEmpty ? "Backend returned HTTP \(code)." : detail
            case .stream(let message):
                return message
            }
        }
    }

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    func health() async throws -> Health {
        try await get("health")
    }

    func models() async throws -> ModelsOverview {
        try await get("api/models")
    }

    @discardableResult
    func deleteModel(_ name: String) async throws -> DeleteResult {
        try await send("DELETE", "api/models", query: ["name": name])
    }

    /// Stream `ollama pull` progress events for a model.
    func pullModel(_ name: String) -> AsyncThrowingStream<PullProgress, Error> {
        streamNDJSON(
            path: "api/models/pull",
            body: ["name": name]
        ) { object in
            if let message = object["error"] as? String {
                throw BackendError.stream(message)
            }
            return PullProgress(
                status: object["status"] as? String ?? "",
                completed: (object["completed"] as? NSNumber)?.int64Value,
                total: (object["total"] as? NSNumber)?.int64Value
            )
        }
    }

    enum ChatEvent {
        case sessionId(String)
        case delta(String)
        case toolCall(tool: String, arguments: String)
        case toolResult(tool: String, result: String)
        case knowledge(citedFiles: [String])
    }

    /// Stream chat events for a prompt: session id first, then deltas and
    /// (with `useTools`) MCP tool activity. With `useKnowledge` the answer is
    /// grounded in the local index and cited files arrive as a knowledge event.
    func chatStream(
        message: String,
        sessionId: String?,
        useTools: Bool,
        useKnowledge: Bool = false
    ) -> AsyncThrowingStream<ChatEvent, Error> {
        var body: [String: Any] = [
            "message": message,
            "use_tools": useTools,
            "use_knowledge": useKnowledge,
        ]
        if let sessionId {
            body["session_id"] = sessionId
        }
        return streamNDJSON(path: "api/chat/stream", body: body) { object in
            if let message = object["error"] as? String {
                throw BackendError.stream(message)
            }
            if let id = object["session_id"] as? String {
                return .sessionId(id)
            }
            if let knowledge = object["knowledge"] as? [String: Any] {
                return .knowledge(citedFiles: knowledge["cited_files"] as? [String] ?? [])
            }
            if let delta = object["delta"] as? String {
                return .delta(delta)
            }
            if let call = object["tool_call"] as? [String: Any] {
                let arguments = (call["arguments"] as? [String: Any])
                    .flatMap { try? JSONSerialization.data(withJSONObject: $0) }
                    .flatMap { String(data: $0, encoding: .utf8) } ?? ""
                return .toolCall(tool: call["tool"] as? String ?? "?", arguments: arguments)
            }
            if let result = object["tool_result"] as? [String: Any] {
                return .toolResult(
                    tool: result["tool"] as? String ?? "?",
                    result: result["result"] as? String ?? ""
                )
            }
            return nil
        }
    }

    // MARK: - Request helpers (shared with BackendModules)

    func get<T: Decodable>(_ path: String, query: [String: String] = [:]) async throws -> T {
        try await send("GET", path, query: query)
    }

    func send<T: Decodable>(_ method: String, _ path: String, query: [String: String] = [:]) async throws -> T {
        var components = URLComponents(
            url: baseURL.appendingPathComponent(path),
            resolvingAgainstBaseURL: false
        )!
        if !query.isEmpty {
            components.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        var request = URLRequest(url: components.url!)
        request.httpMethod = method
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.ensureOK(response, data: data)
        return try Self.decoder.decode(T.self, from: data)
    }

    func post<T: Decodable>(
        _ path: String,
        body: [String: Any],
        timeout: TimeInterval = 300
    ) async throws -> T {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        request.timeoutInterval = timeout
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.ensureOK(response, data: data)
        return try Self.decoder.decode(T.self, from: data)
    }

    func postMultipart<T: Decodable>(
        _ path: String,
        fields: [String: String],
        fileField: String,
        filename: String,
        contentType: String,
        fileData: Data,
        timeout: TimeInterval = 300
    ) async throws -> T {
        let boundary = "omnidev-\(UUID().uuidString)"
        var body = Data()
        for (name, value) in fields {
            body.append(Data("--\(boundary)\r\n".utf8))
            body.append(Data("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n\(value)\r\n".utf8))
        }
        body.append(Data("--\(boundary)\r\n".utf8))
        let fileHeader = "Content-Disposition: form-data; name=\"\(fileField)\"; filename=\"\(filename)\"\r\n"
            + "Content-Type: \(contentType)\r\n\r\n"
        body.append(Data(fileHeader.utf8))
        body.append(fileData)
        body.append(Data("\r\n--\(boundary)--\r\n".utf8))

        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        request.timeoutInterval = timeout
        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.ensureOK(response, data: data)
        return try Self.decoder.decode(T.self, from: data)
    }

    /// POST `body` to `path` and yield one transformed event per NDJSON line.
    /// The transform may return nil to skip a line (e.g. `{"done": true}`).
    private func streamNDJSON<Event>(
        path: String,
        body: [String: Any],
        transform: @escaping ([String: Any]) throws -> Event?
    ) -> AsyncThrowingStream<Event, Error> {
        AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    var request = URLRequest(url: baseURL.appendingPathComponent(path))
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    request.httpBody = try JSONSerialization.data(withJSONObject: body)
                    request.timeoutInterval = 3600

                    let (bytes, response) = try await URLSession.shared.bytes(for: request)
                    if let http = response as? HTTPURLResponse, http.statusCode != 200 {
                        var detail = ""
                        for try await line in bytes.lines {
                            detail += line
                        }
                        throw BackendError.http(http.statusCode, Self.extractDetail(detail))
                    }
                    for try await line in bytes.lines {
                        guard
                            let data = line.data(using: .utf8),
                            let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
                        else { continue }
                        if let event = try transform(object) {
                            continuation.yield(event)
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in
                task.cancel()
            }
        }
    }

    private static func ensureOK(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) else { return }
        throw BackendError.http(http.statusCode, extractDetail(String(data: data, encoding: .utf8) ?? ""))
    }

    private static func extractDetail(_ body: String) -> String {
        guard
            let data = body.data(using: .utf8),
            let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let detail = object["detail"] as? String
        else { return body }
        return detail
    }
}
