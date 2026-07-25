import Foundation

/// UserDefaults-backed app settings, shared by the Settings window and
/// LocalStackManager. Environment variables still win so scripted launches
/// keep working; changes apply when local services restart.
enum AppSettings {
    static let backendPortKey = "backendPort"
    static let aiProviderKey = "aiProvider"
    static let devopsReadOnlyKey = "devopsReadOnly"
    static let onboardingCompletedKey = "onboardingCompleted"
    static let awsAccessKeyIdKey = "awsAccessKeyId"
    static let awsRegionKey = "awsRegion"
    static let ollamaModelKey = "ollamaModel"
    static let knowledgeExclusionsKey = "knowledgeExclusions"

    static let defaultBackendPort = "8010"
    static let defaultAIProvider = "auto"
    static let defaultAWSRegion = "us-east-1"
    static let defaultOllamaModel = "gemma4:12b"

    static var backendPort: String {
        resolve(env: "OMNIDEV_BACKEND_PORT", key: backendPortKey, fallback: defaultBackendPort)
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

    static var awsAccessKeyId: String {
        resolve(env: "AWS_ACCESS_KEY_ID", key: awsAccessKeyIdKey, fallback: "")
    }

    static var awsRegion: String {
        resolve(env: "AWS_DEFAULT_REGION", key: awsRegionKey, fallback: defaultAWSRegion)
    }

    /// The local model both the engine default and vision default follow.
    /// Empty means "use the backend's built-in default". Settings is the
    /// single source of truth — inherited env vars are stripped before the
    /// sidecar launches, so the picker always wins.
    static var ollamaModel: String {
        UserDefaults.standard.string(forKey: ollamaModelKey) ?? ""
    }

    /// Gemini API key lives in the login keychain, like the AWS secret.
    /// Keychain-only on purpose: clearing the field must actually turn
    /// cloud mode off, even if the app inherited GEMINI_API_KEY.
    static var geminiApiKey: String {
        KeychainStore.read(account: "gemini-api-key") ?? ""
    }

    static func setGeminiApiKey(_ key: String) {
        if key.isEmpty {
            KeychainStore.delete(account: "gemini-api-key")
        } else {
            KeychainStore.write(account: "gemini-api-key", value: key)
        }
    }

    /// The AWS secret key never touches UserDefaults — it lives in the login
    /// keychain, keyed by the access key id it belongs to.
    static var awsSecretAccessKey: String {
        if let env = ProcessInfo.processInfo.environment["AWS_SECRET_ACCESS_KEY"], !env.isEmpty {
            return env
        }
        return KeychainStore.read(account: "aws-secret-access-key") ?? ""
    }

    static func setAWSSecretAccessKey(_ secret: String) {
        if secret.isEmpty {
            KeychainStore.delete(account: "aws-secret-access-key")
        } else {
            KeychainStore.write(account: "aws-secret-access-key", value: secret)
        }
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
    static let version = "0.7.0"
    static let repository = "himanshu748/omnidev"
    static let releasesURL = URL(string: "https://github.com/himanshu748/omnidev/releases")!
}
