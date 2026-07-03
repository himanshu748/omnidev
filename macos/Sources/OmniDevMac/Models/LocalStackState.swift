import Foundation

enum LocalStackState: Equatable {
    case idle
    case starting
    case ready
    case degraded
    case failed(String)
    case stopping

    var title: String {
        switch self {
        case .idle:
            return "Idle"
        case .starting:
            return "Starting"
        case .ready:
            return "Ready"
        case .degraded:
            return "Partial"
        case .failed:
            return "Failed"
        case .stopping:
            return "Stopping"
        }
    }

    var systemImage: String {
        switch self {
        case .idle:
            return "circle"
        case .starting:
            return "arrow.triangle.2.circlepath"
        case .ready:
            return "checkmark.circle.fill"
        case .degraded:
            return "exclamationmark.triangle.fill"
        case .failed:
            return "xmark.octagon.fill"
        case .stopping:
            return "stop.circle"
        }
    }
}
