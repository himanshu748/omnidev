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

    static let defaultBackendPort = "8010"
    static let defaultAIProvider = "auto"
    static let defaultAWSRegion = "us-east-1"

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
    static let version = "0.3.0"
    static let repository = "himanshu748/omnidev"
    static let releasesURL = URL(string: "https://github.com/himanshu748/omnidev/releases")!
}
