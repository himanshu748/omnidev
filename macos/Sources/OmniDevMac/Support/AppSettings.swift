import Foundation

/// UserDefaults-backed app settings, shared by the Settings window and
/// LocalStackManager. Environment variables still win so scripted launches
/// keep working; changes apply when local services restart.
enum AppSettings {
    static let backendPortKey = "backendPort"
    static let frontendPortKey = "frontendPort"
    static let aiProviderKey = "aiProvider"
    static let devopsReadOnlyKey = "devopsReadOnly"
    static let onboardingCompletedKey = "onboardingCompleted"

    static let defaultBackendPort = "8010"
    static let defaultFrontendPort = "3010"
    static let defaultAIProvider = "auto"

    static var backendPort: String {
        resolve(env: "OMNIDEV_BACKEND_PORT", key: backendPortKey, fallback: defaultBackendPort)
    }

    static var frontendPort: String {
        resolve(env: "OMNIDEV_FRONTEND_PORT", key: frontendPortKey, fallback: defaultFrontendPort)
    }

    static var aiProvider: String {
        resolve(env: "AI_PROVIDER", key: aiProviderKey, fallback: defaultAIProvider)
    }

    static var devopsReadOnly: Bool {
        if let env = ProcessInfo.processInfo.environment["DEVOPS_READ_ONLY"], !env.isEmpty {
            return env == "1" || env.lowercased() == "true"
        }
        return UserDefaults.standard.bool(forKey: devopsReadOnlyKey)
    }

    private static func resolve(env: String, key: String, fallback: String) -> String {
        if let value = ProcessInfo.processInfo.environment[env], !value.isEmpty {
            return value
        }
        if let stored = UserDefaults.standard.string(forKey: key), !stored.isEmpty {
            return stored
        }
        return fallback
    }
}

enum AppInfo {
    static let version = "0.3.0"
    static let repository = "himanshu748/omnidev"
    static let releasesURL = URL(string: "https://github.com/himanshu748/omnidev/releases")!
}
