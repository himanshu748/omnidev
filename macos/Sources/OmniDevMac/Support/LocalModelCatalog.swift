import Foundation

/// The curated local models OmniDev offers in Settings and the Command
/// Center — mirrors the backend's RECOMMENDED_MODELS so both surfaces and
/// the sidecar agree on names and capabilities.
enum LocalModelCatalog {
    struct Entry: Identifiable, Hashable {
        let name: String
        let label: String
        let sizeGB: Double
        let note: String
        let vision: Bool
        let audio: Bool

        var id: String { name }
    }

    static let entries: [Entry] = [
        Entry(name: "gemma4:12b", label: "Gemma 4 12B", sizeGB: 7.6,
              note: "Default — 256K context, best coding of the laptop tiers.",
              vision: true, audio: false),
        Entry(name: "gemma4:e4b", label: "Gemma 4 E4B", sizeGB: 9.6,
              note: "Edge model with native audio input.",
              vision: true, audio: true),
        Entry(name: "gemma4:e2b", label: "Gemma 4 E2B", sizeGB: 5.5,
              note: "Lightest Gemma 4 — best for 8GB Macs.",
              vision: true, audio: false),
        Entry(name: "qwen2.5-coder:7b", label: "Qwen2.5 Coder 7B", sizeGB: 4.7,
              note: "Code-focused; Vision Lab keeps the Gemma default.",
              vision: false, audio: false),
    ]

    static func entry(for name: String) -> Entry? {
        entries.first { $0.name == name }
    }

    static func isVisionCapable(_ name: String) -> Bool {
        // Unknown (custom) models: assume vision-capable only for Gemma refs.
        entry(for: name)?.vision ?? name.hasPrefix("gemma")
    }

    /// Physical memory in GB, rounded to the marketing size.
    static var machineMemoryGB: Int {
        Int((Double(ProcessInfo.processInfo.physicalMemory) / 1_073_741_824).rounded())
    }

    /// The best default for this machine: 12B needs headroom for its 7.6GB
    /// weights plus context; below 16GB the E2B keeps everything responsive.
    static var recommendedForThisMac: Entry {
        machineMemoryGB >= 16 ? entries[0] : entries[2]
    }
}
