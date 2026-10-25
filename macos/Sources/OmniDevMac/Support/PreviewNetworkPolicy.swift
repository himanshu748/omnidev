import Foundation

/// Network policy for the Code Gen HTML preview, kept free of app
/// dependencies so CI can compile it into a real WKWebView check
/// (scripts/macos/check-preview-isolation.sh).
///
/// Content-blocker rules see URL text, not resolved addresses, so a denylist
/// of local spellings cannot stop a hostname that resolves to loopback (DNS
/// rebinding). Instead every network load is blocked, and only HTTPS to a
/// few public CDNs is let back in: their DNS is not attacker-controlled.
enum PreviewNetworkPolicy {
    static let identifier = "omnidev-preview-network-v2"

    static let allowedHosts = [
        "cdn.jsdelivr.net",
        "unpkg.com",
        "cdnjs.cloudflare.com",
        "cdn.tailwindcss.com",
        "esm.sh",
        "fonts.googleapis.com",
        "fonts.gstatic.com",
    ]

    /// WebKit evaluates rules in order and `ignore-previous-rules` cancels
    /// the block. The trailing "/" in each allow rule means look-alike hosts
    /// (`unpkg.com.evil.test`, `unpkg.com@evil.test`, `unpkg.com:8010`) stay blocked.
    static var contentRuleList: String {
        var rules: [[String: Any]] = [
            block("^https?://"),
            block("^wss?://"),
            block("^ftp://"),
            block("^file:"),
        ]
        for host in allowedHosts {
            let escaped = host.replacingOccurrences(of: ".", with: "\\.")
            rules.append([
                "trigger": ["url-filter": "^https://\(escaped)/"],
                "action": ["type": "ignore-previous-rules"],
            ])
        }
        let data = try? JSONSerialization.data(withJSONObject: rules, options: [.sortedKeys])
        return data.flatMap { String(data: $0, encoding: .utf8) } ?? "[]"
    }

    private static func block(_ filter: String) -> [String: Any] {
        ["trigger": ["url-filter": filter], "action": ["type": "block"]]
    }
}
