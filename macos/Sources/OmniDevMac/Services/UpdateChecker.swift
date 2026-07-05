import AppKit
import Foundation

/// Lightweight update check against GitHub Releases — no framework, no
/// background daemon. Invoked from the OmniDev menu and the menu-bar extra.
@MainActor
enum UpdateChecker {
    private struct Release: Decodable {
        let tagName: String
        let htmlUrl: String

        enum CodingKeys: String, CodingKey {
            case tagName = "tag_name"
            case htmlUrl = "html_url"
        }
    }

    static func checkForUpdates() async {
        let url = URL(string: "https://api.github.com/repos/\(AppInfo.repository)/releases/latest")!
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                presentUpToDate(note: "No published releases yet — you are on the source build.")
                return
            }
            let release = try JSONDecoder().decode(Release.self, from: data)
            let latest = release.tagName.hasPrefix("v") ? String(release.tagName.dropFirst()) : release.tagName
            if isNewer(latest, than: AppInfo.version) {
                presentUpdateAvailable(version: latest, url: URL(string: release.htmlUrl) ?? AppInfo.releasesURL)
            } else {
                presentUpToDate(note: "OmniDev \(AppInfo.version) is the latest version.")
            }
        } catch {
            presentUpToDate(note: "Could not reach GitHub to check for updates.")
        }
    }

    static func isNewer(_ candidate: String, than current: String) -> Bool {
        let lhs = candidate.split(separator: ".").compactMap { Int($0.prefix(while: \.isNumber)) }
        let rhs = current.split(separator: ".").compactMap { Int($0.prefix(while: \.isNumber)) }
        for index in 0..<max(lhs.count, rhs.count) {
            let a = index < lhs.count ? lhs[index] : 0
            let b = index < rhs.count ? rhs[index] : 0
            if a != b { return a > b }
        }
        return false
    }

    private static func presentUpdateAvailable(version: String, url: URL) {
        let alert = NSAlert()
        alert.messageText = "OmniDev \(version) is available"
        alert.informativeText = "You are running \(AppInfo.version). Open the release page to download the update."
        alert.addButton(withTitle: "View Release")
        alert.addButton(withTitle: "Later")
        if alert.runModal() == .alertFirstButtonReturn {
            NSWorkspace.shared.open(url)
        }
    }

    private static func presentUpToDate(note: String) {
        let alert = NSAlert()
        alert.messageText = "You're up to date"
        alert.informativeText = note
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
}
