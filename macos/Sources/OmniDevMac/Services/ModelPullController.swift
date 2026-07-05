import Foundation

/// Drives a one-click model pull with live progress, shared by the
/// onboarding flow and the native cockpit's model manager.
@MainActor
final class ModelPullController: ObservableObject {
    enum Phase: Equatable {
        case idle
        case pulling(status: String, fraction: Double?)
        case done
        case failed(String)
    }

    @Published private(set) var phase: Phase = .idle

    var isPulling: Bool {
        if case .pulling = phase { return true }
        return false
    }

    func pull(model: String, client: BackendClient, onFinished: @escaping () -> Void = {}) {
        guard !isPulling else { return }
        phase = .pulling(status: "starting", fraction: nil)

        Task {
            do {
                for try await progress in client.pullModel(model) {
                    phase = .pulling(
                        status: progress.status.isEmpty ? "downloading" : progress.status,
                        fraction: progress.fraction
                    )
                }
                phase = .done
                onFinished()
            } catch {
                phase = .failed(error.localizedDescription)
            }
        }
    }
}
