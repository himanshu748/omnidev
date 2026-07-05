import SwiftUI

/// Native command center: engine status, local model manager, and module
/// shortcuts — replaces the webview cockpit page inside the app.
struct CockpitView: View {
    @ObservedObject var manager: LocalStackManager
    @Binding var selectedRoute: OmniDevRoute
    @StateObject private var pull = ModelPullController()
    @State private var overview: BackendClient.ModelsOverview?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                header
                HStack(alignment: .top, spacing: 16) {
                    engineCard
                    modelsCard
                }
                modulesCard
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("Command Center")
        .task {
            await refresh()
        }
        .onChange(of: manager.backendHealthy) { healthy in
            if healthy {
                Task { await refresh() }
            }
        }
    }

    private var header: some View {
        HStack(spacing: 12) {
            LogoMarkView(size: 36)
            VStack(alignment: .leading, spacing: 2) {
                Text("OmniDev")
                    .font(.title2.weight(.semibold))
                Text("Local-first AI dev cockpit — nothing leaves your Mac.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Button {
                selectedRoute = .chat
            } label: {
                Label("Ask OmniDev", systemImage: "bubble.left.and.text.bubble.right")
            }
            .buttonStyle(.borderedProminent)
            .tint(.omniAccent)
        }
    }

    private var engineCard: some View {
        CockpitCard(title: "Engine", systemImage: "bolt.horizontal") {
            VStack(alignment: .leading, spacing: 10) {
                StatusRow(label: "Backend API", ready: manager.backendHealthy,
                          detail: "127.0.0.1:\(manager.backendPort)")
                if !manager.aiProvider.isEmpty {
                    StatusRow(label: "AI provider", ready: true,
                              detail: manager.aiProvider == "ollama"
                                  ? "\(manager.aiModel) · fully local"
                                  : "\(manager.aiProvider) · \(manager.aiModel)")
                }

                HStack {
                    Button("Restart") {
                        manager.restartServices()
                    }
                    Button("Logs") {
                        manager.openLogs()
                    }
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
        }
    }

    private var modelsCard: some View {
        CockpitCard(title: "Local Models", systemImage: "cpu") {
            VStack(alignment: .leading, spacing: 10) {
                if let overview {
                    if overview.status.provider != "ollama" {
                        Text("Cloud provider (\(overview.status.provider)) is active — local models are optional.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else if overview.status.textModelReady != true {
                        Text("Default model \(overview.status.textModel) is not installed.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        pullControls(model: overview.status.textModel)
                    }

                    let local = overview.installed.filter { $0.sizeGb > 0 }
                    if local.isEmpty && overview.status.provider == "ollama" && overview.status.textModelReady == true {
                        Text("Models are served by Ollama.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    ForEach(local.prefix(4)) { model in
                        HStack {
                            Text(model.name)
                                .font(.callout.monospaced())
                            Spacer()
                            Text(String(format: "%.1f GB", model.sizeGb))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                } else if manager.backendHealthy {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Text("Waiting for the backend…")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    @ViewBuilder
    private func pullControls(model: String) -> some View {
        switch pull.phase {
        case .pulling(let status, let fraction):
            VStack(alignment: .leading, spacing: 4) {
                ProgressView(value: fraction)
                    .progressViewStyle(.linear)
                Text(fraction.map { "\(status) — \(Int($0 * 100))%" } ?? status)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        case .failed(let message):
            Text("Pull failed: \(message)")
                .font(.caption)
                .foregroundStyle(.orange)
            pullButton(model: model)
        default:
            pullButton(model: model)
        }
    }

    private func pullButton(model: String) -> some View {
        Button("Download \(model)") {
            pull.pull(model: model, client: manager.backendClient) {
                Task { await refresh() }
            }
        }
        .buttonStyle(.borderedProminent)
        .tint(.omniAccent)
        .controlSize(.small)
    }

    private var modulesCard: some View {
        CockpitCard(title: "Modules", systemImage: "square.grid.2x2") {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 190), spacing: 10)], spacing: 10) {
                ForEach(OmniDevRoute.modules) { route in
                    Button {
                        selectedRoute = route
                    } label: {
                        HStack(spacing: 10) {
                            Image(systemName: route.systemImage)
                                .foregroundStyle(Color.omniAccent)
                                .frame(width: 22)
                            VStack(alignment: .leading, spacing: 1) {
                                Text(route.title)
                                    .font(.subheadline.weight(.medium))
                                Text(route.subtitle)
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            Spacer(minLength: 0)
                        }
                        .padding(10)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 9, style: .continuous))
                }
            }
        }
    }

    private func refresh() async {
        await manager.refreshHealthInfo()
        overview = try? await manager.backendClient.models()
    }
}

private struct CockpitCard<Content: View>: View {
    let title: String
    let systemImage: String
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label(title, systemImage: systemImage)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
            content
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

private struct StatusRow: View {
    let label: String
    let ready: Bool
    let detail: String

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(ready ? .green : .orange)
                .frame(width: 7, height: 7)
            Text(label)
                .font(.callout)
            Spacer()
            Text(detail)
                .font(.caption.monospaced())
                .foregroundStyle(.secondary)
        }
    }
}
