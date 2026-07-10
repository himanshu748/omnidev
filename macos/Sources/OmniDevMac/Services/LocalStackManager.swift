import AppKit
import Foundation

@MainActor
final class LocalStackManager: ObservableObject {
    @Published private(set) var state: LocalStackState = .idle
    @Published private(set) var backendHealthy = false
    @Published private(set) var message = "Preparing the local engine."
    @Published private(set) var aiProvider = ""
    @Published private(set) var aiModel = ""

    /// One pull at a time, visible from every surface (onboarding, cockpit).
    let modelPull = ModelPullController()

    let rootURL: URL
    private(set) var backendPort: String
    private(set) var backendURL: URL

    var backendClient: BackendClient {
        BackendClient(baseURL: backendURL)
    }

    var launcherLogURL: URL {
        rootURL.appendingPathComponent(".omnidev-macos/launcher.log")
    }

    init(rootURL: URL = ProjectPaths.detectProjectRoot()) {
        self.rootURL = rootURL
        backendPort = AppSettings.backendPort
        backendURL = URL(string: "http://127.0.0.1:\(backendPort)")!
    }

    /// Re-read Settings-window values; called before (re)starting services so
    /// port changes take effect without relaunching the app.
    private func reloadConfiguration() {
        backendPort = AppSettings.backendPort
        backendURL = URL(string: "http://127.0.0.1:\(backendPort)")!
    }

    func startServicesIfNeeded() {
        guard state != .starting && state != .ready else { return }
        reloadConfiguration()
        state = .starting
        message = "Starting the local engine — the first run installs it and can take a few minutes."

        Task {
            await runLaunchScript()
            await pollServices()
        }
    }

    func restartServices() {
        guard state != .stopping else { return }
        state = .stopping
        message = "Restarting the local engine."

        Task {
            try? await runProcess(rootURL.appendingPathComponent("scripts/macos/stop-omnidev.sh"))
            backendHealthy = false
            state = .idle
            startServicesIfNeeded()
        }
    }

    func stopServicesSync() {
        let scriptURL = rootURL.appendingPathComponent("scripts/macos/stop-omnidev.sh")
        guard FileManager.default.fileExists(atPath: scriptURL.path) else { return }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [scriptURL.path, rootURL.path]
        process.currentDirectoryURL = rootURL
        try? process.run()
        process.waitUntilExit()
    }

    func openAPIDocs() {
        NSWorkspace.shared.open(backendURL.appendingPathComponent("docs"))
    }

    func openLogs() {
        NSWorkspace.shared.activateFileViewerSelecting([launcherLogURL])
    }

    private func runLaunchScript() async {
        var environment = [
            "OMNIDEV_BACKEND_PORT": backendPort,
            // Settings-window values; inherited by the uvicorn sidecar,
            // where they take precedence over backend/.env.
            "AI_PROVIDER": AppSettings.aiProvider,
            "DEVOPS_READ_ONLY": AppSettings.devopsReadOnly ? "1" : "0",
        ]
        let model = AppSettings.ollamaModel
        if !model.isEmpty {
            environment["OLLAMA_MODEL"] = model
            // Vision-capable picks drive Vision Lab too; text-only picks
            // leave the vision default alone.
            if LocalModelCatalog.isVisionCapable(model) {
                environment["OLLAMA_VISION_MODEL"] = model
            }
        }
        let geminiKey = AppSettings.geminiApiKey
        if !geminiKey.isEmpty {
            environment["GEMINI_API_KEY"] = geminiKey
        }

        // Only override AWS when Settings holds a full key pair, so an empty
        // form still falls through to the boto3 credential chain (~/.aws).
        let awsKey = AppSettings.awsAccessKeyId
        let awsSecret = AppSettings.awsSecretAccessKey
        if !awsKey.isEmpty && !awsSecret.isEmpty {
            environment["AWS_ACCESS_KEY_ID"] = awsKey
            environment["AWS_SECRET_ACCESS_KEY"] = awsSecret
        }
        if !AppSettings.awsRegion.isEmpty {
            environment["AWS_DEFAULT_REGION"] = AppSettings.awsRegion
        }

        do {
            try await runProcess(
                rootURL.appendingPathComponent("scripts/macos/launch-omnidev.sh"),
                environment: environment
            )
        } catch {
            state = .failed(error.localizedDescription)
            message = "The launcher failed. Open logs for details."
        }
    }

    private func pollServices() async {
        guard case .failed = state else {
            for _ in 0..<120 {
                let backend = await checkHTTP(backendURL.appendingPathComponent("health"))
                backendHealthy = backend

                if backend {
                    state = .ready
                    message = "Local engine is running on loopback."
                    await refreshHealthInfo()
                    break
                }

                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }

            if state != .ready {
                state = .failed("The engine did not become reachable.")
                message = "The local engine did not become reachable."
            }
            return
        }
    }

    func refreshHealthInfo() async {
        guard let health = try? await backendClient.health() else { return }
        aiProvider = health.aiProvider
        aiModel = health.aiModel
    }

    private func checkHTTP(_ url: URL) async -> Bool {
        var request = URLRequest(url: url)
        request.timeoutInterval = 1.5

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else { return false }
            return (200..<500).contains(http.statusCode)
        } catch {
            return false
        }
    }

    private func runProcess(
        _ scriptURL: URL,
        environment extraEnvironment: [String: String] = [:]
    ) async throws {
        guard FileManager.default.fileExists(atPath: scriptURL.path) else {
            throw CocoaError(.fileNoSuchFile)
        }

        try await withCheckedThrowingContinuation { continuation in
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/bin/bash")
            process.arguments = [scriptURL.path, rootURL.path]
            process.currentDirectoryURL = rootURL

            var environment = ProcessInfo.processInfo.environment
            // Settings own these; a value inherited from the launching shell
            // must not shadow what the user configured (or cleared) in-app.
            for key in ["OLLAMA_MODEL", "OLLAMA_VISION_MODEL", "GEMINI_API_KEY"] {
                environment.removeValue(forKey: key)
            }
            environment["OMNIDEV_PROJECT_ROOT"] = rootURL.path
            environment["PATH"] = "\(NSHomeDirectory())/.local/bin:/opt/homebrew/bin:/usr/local/bin:/opt/anaconda3/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            for (key, value) in extraEnvironment {
                environment[key] = value
            }
            process.environment = environment

            process.terminationHandler = { completed in
                if completed.terminationStatus == 0 {
                    continuation.resume()
                } else {
                    continuation.resume(
                        throwing: CocoaError(.executableLoad, userInfo: [
                            NSLocalizedDescriptionKey: "Process exited with status \(completed.terminationStatus)"
                        ])
                    )
                }
            }

            do {
                try process.run()
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
}
