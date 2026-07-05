import AppKit
import Foundation

@MainActor
final class LocalStackManager: ObservableObject {
    @Published private(set) var state: LocalStackState = .idle
    @Published private(set) var backendHealthy = false
    @Published private(set) var frontendReady = false
    @Published private(set) var message = "Preparing local services."
    @Published private(set) var aiProvider = ""
    @Published private(set) var aiModel = ""

    let rootURL: URL
    private(set) var backendPort: String
    private(set) var frontendPort: String
    private(set) var backendURL: URL
    private(set) var frontendURL: URL

    var backendClient: BackendClient {
        BackendClient(baseURL: backendURL)
    }

    var launcherLogURL: URL {
        rootURL.appendingPathComponent(".omnidev-macos/launcher.log")
    }

    init(rootURL: URL = ProjectPaths.detectProjectRoot()) {
        self.rootURL = rootURL
        backendPort = AppSettings.backendPort
        frontendPort = AppSettings.frontendPort
        backendURL = URL(string: "http://127.0.0.1:\(backendPort)")!
        frontendURL = URL(string: "http://127.0.0.1:\(frontendPort)")!
    }

    /// Re-read Settings-window values; called before (re)starting services so
    /// port changes take effect without relaunching the app.
    private func reloadConfiguration() {
        backendPort = AppSettings.backendPort
        frontendPort = AppSettings.frontendPort
        backendURL = URL(string: "http://127.0.0.1:\(backendPort)")!
        frontendURL = URL(string: "http://127.0.0.1:\(frontendPort)")!
    }

    func pageURL(for route: OmniDevRoute) -> URL {
        URL(string: route.path, relativeTo: frontendURL)!.absoluteURL
    }

    func startServicesIfNeeded() {
        guard state != .starting && state != .ready else { return }
        reloadConfiguration()
        state = .starting
        message = "Starting FastAPI sidecar and Next.js cockpit."

        Task {
            await runLaunchScript()
            await pollServices()
        }
    }

    func restartServices() {
        guard state != .stopping else { return }
        state = .stopping
        message = "Restarting local services."

        Task {
            try? await runProcess(rootURL.appendingPathComponent("scripts/macos/stop-omnidev.sh"))
            backendHealthy = false
            frontendReady = false
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

    func openInBrowser(path: String) {
        let url = URL(string: path, relativeTo: frontendURL)!.absoluteURL
        NSWorkspace.shared.open(url)
    }

    func openLogs() {
        NSWorkspace.shared.activateFileViewerSelecting([launcherLogURL])
    }

    private func runLaunchScript() async {
        do {
            try await runProcess(
                rootURL.appendingPathComponent("scripts/macos/launch-omnidev.sh"),
                environment: [
                    "OMNIDEV_OPEN_BROWSER": "0",
                    "OMNIDEV_BACKEND_PORT": backendPort,
                    "OMNIDEV_FRONTEND_PORT": frontendPort,
                    // Settings-window values; inherited by the uvicorn sidecar,
                    // where they take precedence over backend/.env.
                    "AI_PROVIDER": AppSettings.aiProvider,
                    "DEVOPS_READ_ONLY": AppSettings.devopsReadOnly ? "1" : "0",
                ]
            )
        } catch {
            state = .failed(error.localizedDescription)
            message = "The launcher failed. Open logs for details."
        }
    }

    private func pollServices() async {
        guard case .failed = state else {
            breakPoll: for _ in 0..<120 {
                let backend = await checkHTTP(backendURL.appendingPathComponent("health"))
                let frontend = await checkHTTP(frontendURL)
                backendHealthy = backend
                frontendReady = frontend

                if backend && frontend {
                    state = .ready
                    message = "Local services are running on loopback."
                    await refreshHealthInfo()
                    break breakPoll
                }

                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }

            if state != .ready {
                state = backendHealthy || frontendReady ? .degraded : .failed("Services did not become reachable.")
                message = backendHealthy || frontendReady
                    ? "Only part of the local stack is reachable."
                    : "Local services did not become reachable."
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
