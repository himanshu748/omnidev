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
            let frontend = candidate.appendingPathComponent("frontend")
            if fileManager.fileExists(atPath: backend.path) && fileManager.fileExists(atPath: frontend.path) {
                return candidate.standardizedFileURL
            }
        }

        return cwd.standardizedFileURL
    }
}
