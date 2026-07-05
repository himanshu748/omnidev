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

    /// Stream chat completion deltas for a prompt.
    func chatStream(message: String) -> AsyncThrowingStream<String, Error> {
        streamNDJSON(
            path: "api/chat/stream",
            body: ["message": message]
        ) { object in
            if let message = object["error"] as? String {
                throw BackendError.stream(message)
            }
            return object["delta"] as? String
        }
    }

    // MARK: - Internals

    private func get<T: Decodable>(_ path: String) async throws -> T {
        let (data, response) = try await URLSession.shared.data(from: baseURL.appendingPathComponent(path))
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
        guard let http = response as? HTTPURLResponse, http.statusCode != 200 else { return }
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
