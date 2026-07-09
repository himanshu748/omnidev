import Foundation

/// Installs the engine bundled in the .app (backend source + launch
/// scripts) into Application Support, so the packaged app runs on machines
/// that never cloned the repo. Dev checkouts are preferred when present.
enum EngineInstaller {
    static var applicationSupportRoot: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("OmniDev/engine", isDirectory: true)
    }

    /// The engine copied into the .app by build-app.sh; nil under bare
    /// `swift run` dev builds, which use the repo checkout instead.
    private static var bundledEngineURL: URL? {
        let url = Bundle.main.resourceURL?.appendingPathComponent("engine", isDirectory: true)
        guard let url, FileManager.default.fileExists(atPath: url.path) else { return nil }
        return url
    }

    /// Returns the installed engine root, re-syncing the bundled copy when
    /// the app version changes. The user's virtualenv and runtime state
    /// survive upgrades.
    static func ensureInstalled() -> URL? {
        guard let bundled = bundledEngineURL else { return nil }
        let fm = FileManager.default
        let root = applicationSupportRoot
        let marker = root.appendingPathComponent(".engine-version")

        if let installed = try? String(contentsOf: marker, encoding: .utf8),
           installed == AppInfo.version,
           fm.fileExists(atPath: root.appendingPathComponent("backend").path) {
            return root
        }

        try? fm.createDirectory(at: root, withIntermediateDirectories: true)

        let rsync = Process()
        rsync.executableURL = URL(fileURLWithPath: "/usr/bin/rsync")
        rsync.arguments = [
            "-a", "--delete",
            // Keep the bootstrapped venv and runtime state across upgrades.
            "--exclude", ".venv",
            "--exclude", ".omnidev-macos",
            "--exclude", ".env",
            bundled.path + "/", root.path + "/",
        ]
        do {
            try rsync.run()
            rsync.waitUntilExit()
        } catch {
            return nil
        }
        guard rsync.terminationStatus == 0 else { return nil }

        try? AppInfo.version.write(to: marker, atomically: true, encoding: .utf8)
        return root
    }
}
