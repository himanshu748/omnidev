import Foundation

enum OmniDevRoute: String, CaseIterable, Identifiable {
    case cockpit
    case chat
    case knowledge
    case devops
    case codegen
    case scraper
    case vision
    case storage
    case mcp

    var id: String { rawValue }

    /// The feature modules, excluding the cockpit and chat surfaces.
    static let modules: [OmniDevRoute] = [
        .knowledge, .devops, .codegen, .scraper, .vision, .storage, .mcp,
    ]

    var title: String {
        switch self {
        case .cockpit:
            return "Command Center"
        case .chat:
            return "Chat"
        case .knowledge:
            return "Knowledge"
        case .devops:
            return "DevOps Agent"
        case .codegen:
            return "Code Gen"
        case .scraper:
            return "Web Scraper"
        case .vision:
            return "Vision Lab"
        case .storage:
            return "Cloud Storage"
        case .mcp:
            return "MCP Marketplace"
        }
    }

    var subtitle: String {
        switch self {
        case .cockpit:
            return "Status, models, and modules"
        case .chat:
            return "Stream the local model"
        case .knowledge:
            return "Ask your files, offline"
        case .devops:
            return "AWS plans and boto3 actions"
        case .codegen:
            return "Generate and refine projects"
        case .scraper:
            return "Guarded browser extraction"
        case .vision:
            return "Image analysis and OCR"
        case .storage:
            return "S3 buckets and objects"
        case .mcp:
            return "Tools for the local model"
        }
    }

    var systemImage: String {
        switch self {
        case .cockpit:
            return "rectangle.grid.2x2"
        case .chat:
            return "bubble.left.and.text.bubble.right"
        case .knowledge:
            return "books.vertical"
        case .devops:
            return "flowchart"
        case .codegen:
            return "curlybraces"
        case .scraper:
            return "globe"
        case .vision:
            return "eye"
        case .storage:
            return "externaldrive"
        case .mcp:
            return "puzzlepiece.extension"
        }
    }
}
