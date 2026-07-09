import Foundation

enum ProjectPaths {
    static func detectProjectRoot() -> URL {
        let fileManager = FileManager.default
        var candidates: [URL] = []

        if let envRoot = ProcessInfo.processInfo.environment["OMNIDEV_PROJECT_ROOT"], !envRoot.isEmpty {
            candidates.append(URL(fileURLWithPath: envRoot))
        }

        let bundleURL = Bundle.main.bundleURL
        candidates.append(bundleURL.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent())

        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        candidates.append(cwd)
        candidates.append(cwd.deletingLastPathComponent())

        for candidate in candidates {
            let backend = candidate.appendingPathComponent("backend")
            let launcher = candidate.appendingPathComponent("scripts/macos/launch-omnidev.sh")
            if fileManager.fileExists(atPath: backend.path) && fileManager.fileExists(atPath: launcher.path) {
                return candidate.standardizedFileURL
            }
        }

        // No dev checkout — install the engine bundled inside the .app.
        if let engineRoot = EngineInstaller.ensureInstalled() {
            return engineRoot.standardizedFileURL
        }

        return cwd.standardizedFileURL
    }
}
