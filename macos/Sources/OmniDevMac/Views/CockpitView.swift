import SwiftUI

/// Native command center: engine status, local model manager, and module
/// shortcuts — replaces the webview cockpit page inside the app.
struct CockpitView: View {
    @ObservedObject var manager: LocalStackManager
    @Binding var selectedRoute: OmniDevRoute
    @State private var overview: BackendClient.ModelsOverview?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                header
                engineCard
                ModelManagerCard(manager: manager, pull: manager.modelPull, overview: $overview)
                modulesCard
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("Command Center")
        .navigationSubtitle("Status, models, and modules")
        .task {
            await refresh()
        }
        .onChange(of: manager.backendHealthy) { healthy in
            if healthy {
                Task { await refresh() }
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .omniDevModelsChanged)) { _ in
            Task { await refresh() }
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

/// Full local-model manager: what's installed (with delete), the curated
/// catalog (with one-click download + progress), and the active default.
struct ModelManagerCard: View {
    @ObservedObject var manager: LocalStackManager
    @ObservedObject var pull: ModelPullController
    @Binding var overview: BackendClient.ModelsOverview?
    @State private var deleteCandidate: BackendClient.InstalledModel?
    @State private var actionError: String?

    var body: some View {
        CockpitCard(title: "Local Models", systemImage: "cpu") {
            VStack(alignment: .leading, spacing: 12) {
                if let overview {
                    if overview.status.provider != "ollama" {
                        Text("Cloud provider (\(overview.status.provider)) is active — local models are managed by Ollama and optional here.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        if let actionError {
                            Text(actionError)
                                .font(.caption)
                                .foregroundStyle(.orange)
                        }

                        readinessWarning(overview)
                        installedSection(overview)
                        Divider()
                        catalogSection(overview)
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
        .confirmationDialog(
            "Remove \(deleteCandidate?.name ?? "model")?",
            isPresented: Binding(
                get: { deleteCandidate != nil },
                set: { if !$0 { deleteCandidate = nil } }
            ),
            titleVisibility: .visible
        ) {
            Button("Remove — frees \(String(format: "%.1f GB", deleteCandidate?.sizeGb ?? 0))", role: .destructive) {
                if let model = deleteCandidate {
                    delete(model)
                }
            }
        } message: {
            Text("The model can be downloaded again at any time.")
        }
    }

    /// The engine default must exist or every AI module 503s — surface that
    /// above everything, with a one-click fix even for non-catalog refs.
    @ViewBuilder
    private func readinessWarning(_ overview: BackendClient.ModelsOverview) -> some View {
        let model = overview.status.textModel
        if overview.status.textModelReady != true {
            HStack(spacing: 8) {
                Label("Default model \(model) is not installed.", systemImage: "exclamationmark.triangle.fill")
                    .font(.caption)
                    .foregroundStyle(.orange)
                Spacer()
                if LocalModelCatalog.entry(for: model) == nil, pull.model != model || !pull.isPulling {
                    Button("Download") {
                        download(model)
                    }
                    .controlSize(.small)
                    .disabled(pull.isPulling)
                }
            }
            if pull.model == model, case .pulling(let status, let fraction) = pull.phase {
                VStack(alignment: .leading, spacing: 3) {
                    ProgressView(value: fraction)
                        .progressViewStyle(.linear)
                    Text(fraction.map { "\(status) — \(Int($0 * 100))%" } ?? status)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    @ViewBuilder
    private func installedSection(_ overview: BackendClient.ModelsOverview) -> some View {
        let local = overview.installed.filter { $0.sizeGb > 0 }
        if local.isEmpty {
            Text("No local models installed yet — download one below.")
                .font(.caption)
                .foregroundStyle(.secondary)
        } else {
            ForEach(local) { model in
                HStack(spacing: 8) {
                    Text(model.name)
                        .font(.callout.monospaced())
                    if isActive(model.name, overview) {
                        Text("ACTIVE")
                            .font(.caption2.weight(.bold))
                            .foregroundStyle(Color.omniAccent)
                            .padding(.horizontal, 5)
                            .padding(.vertical, 1)
                            .background(Color.omniAccent.opacity(0.14), in: Capsule())
                    }
                    Spacer()
                    Text(String(format: "%.1f GB", model.sizeGb))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Button {
                        deleteCandidate = model
                    } label: {
                        Image(systemName: "trash")
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.secondary)
                    .help(isActive(model.name, overview)
                          ? "This is the active model — switch models in Settings before removing it."
                          : "Remove this model to free disk space")
                    .disabled(isActive(model.name, overview))
                }
            }
        }
    }

    @ViewBuilder
    private func catalogSection(_ overview: BackendClient.ModelsOverview) -> some View {
        let installedNames = Set(overview.installed.map(\.name))
        Text("Recommended")
            .font(.caption.weight(.semibold))
            .foregroundStyle(.secondary)
            .textCase(.uppercase)

        ForEach(LocalModelCatalog.entries) { entry in
            let installed = installedNames.contains(entry.name)
                || installedNames.contains("\(entry.name):latest")
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    VStack(alignment: .leading, spacing: 1) {
                        HStack(spacing: 6) {
                            Text(entry.label)
                                .font(.subheadline.weight(.medium))
                            if entry.audio {
                                Image(systemName: "waveform")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                    .help("Native audio input")
                            }
                        }
                        Text(entry.note)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if installed {
                        Label("Installed", systemImage: "checkmark.circle.fill")
                            .font(.caption)
                            .foregroundStyle(.green)
                    } else if pull.model == entry.name, pull.isPulling {
                        EmptyView()
                    } else {
                        Button("Get — \(String(format: "%.1f GB", entry.sizeGB))") {
                            download(entry.name)
                        }
                        .controlSize(.small)
                        .disabled(pull.isPulling)
                    }
                }

                if pull.model == entry.name, case .pulling(let status, let fraction) = pull.phase {
                    VStack(alignment: .leading, spacing: 3) {
                        ProgressView(value: fraction)
                            .progressViewStyle(.linear)
                        Text(fraction.map { "\(status) — \(Int($0 * 100))%" } ?? status)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                if pull.model == entry.name, case .failed(let message) = pull.phase {
                    Text("Download failed: \(message)")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
            }
        }
    }

    private func isActive(_ name: String, _ overview: BackendClient.ModelsOverview) -> Bool {
        var actives = [overview.status.textModel]
        if let vision = overview.status.visionModel {
            actives.append(vision)
        }
        return actives.contains { name == $0 || name == "\($0):latest" }
    }

    private func download(_ name: String) {
        actionError = nil
        pull.pull(model: name, client: manager.backendClient) {
            Task { await refreshOverview() }
        }
    }

    private func delete(_ model: BackendClient.InstalledModel) {
        actionError = nil
        Task {
            do {
                try await manager.backendClient.deleteModel(model.name)
                NotificationCenter.default.post(name: .omniDevModelsChanged, object: model.name)
                await refreshOverview()
            } catch {
                actionError = "Could not remove \(model.name): \(error.localizedDescription)"
            }
        }
    }

    private func refreshOverview() async {
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
