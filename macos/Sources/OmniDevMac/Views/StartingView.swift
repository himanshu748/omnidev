import SwiftUI

struct StartingView: View {
    @ObservedObject var manager: LocalStackManager

    var body: some View {
        VStack(spacing: 18) {
            LogoMarkView(size: 52)

            VStack(spacing: 6) {
                Text("Starting OmniDev")
                    .font(.title2.weight(.semibold))
                Text(manager.message)
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }

            ServiceReadinessLabel(title: "FastAPI engine", isReady: manager.backendHealthy)

            HStack {
                Button("Restart Services") {
                    manager.restartServices()
                }
                Button("Open Logs") {
                    manager.openLogs()
                }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(34)
        .frame(maxWidth: 460)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

private struct ServiceReadinessLabel: View {
    let title: String
    let isReady: Bool

    var body: some View {
        Label(title, systemImage: isReady ? "checkmark.circle.fill" : "clock")
            .font(.caption.weight(.semibold))
            .foregroundStyle(isReady ? .green : .secondary)
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(.thinMaterial, in: Capsule())
    }
}
