import Foundation

enum OmniDevRoute: String, CaseIterable, Identifiable {
    case cockpit
    case devops
    case codegen
    case scraper
    case vision
    case storage

    var id: String { rawValue }

    var title: String {
        switch self {
        case .cockpit:
            return "Command Center"
        case .devops:
            return "DevOps Agent"
        case .codegen:
            return "Code Gen Agent"
        case .scraper:
            return "Browser Agent"
        case .vision:
            return "Vision Agent"
        case .storage:
            return "Storage Agent"
        }
    }

    var subtitle: String {
        switch self {
        case .cockpit:
            return "Setup, approvals, and overview"
        case .devops:
            return "AWS plans and boto3 actions"
        case .codegen:
            return "Generate and inspect projects"
        case .scraper:
            return "Authorized browser extraction"
        case .vision:
            return "Image analysis and OCR"
        case .storage:
            return "S3 buckets and objects"
        }
    }

    var path: String {
        switch self {
        case .cockpit:
            return "/app"
        case .devops:
            return "/devops"
        case .codegen:
            return "/codegen"
        case .scraper:
            return "/scraper"
        case .vision:
            return "/vision"
        case .storage:
            return "/storage"
        }
    }

    var systemImage: String {
        switch self {
        case .cockpit:
            return "rectangle.grid.2x2"
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
        }
    }
}
