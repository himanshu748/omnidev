import AppKit
import SwiftUI

/// Opens the app's Settings scene from anywhere (onboarding, menus). The
/// selector name changed in macOS 13, so try both.
enum SettingsOpener {
    static func open() {
        NSApp.activate(ignoringOtherApps: true)
        if NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil) {
            return
        }
        NSApp.sendAction(Selector(("showPreferencesWindow:")), to: nil, from: nil)
    }
}

/// First-run setup: verifies the local engine, Ollama, and the default
/// model — and pulls the model with live progress, so a new user reaches a
/// working offline setup without touching a terminal.
struct OnboardingView: View {
    @ObservedObject var manager: LocalStackManager
    @ObservedObject private var pull: ModelPullController
    @State private var status: BackendClient.ProviderStatus?
    @State private var refreshing = false
    @Environment(\.dismiss) private var dismiss

    init(manager: LocalStackManager) {
        self.manager = manager
        _pull = ObservedObject(wrappedValue: manager.modelPull)
    }

    private var ollamaReachable: Bool { status?.reachable ?? false }
    private var usesOllama: Bool { status == nil || status?.provider == "ollama" }
    private var modelReady: Bool {
        if pull.phase == .done { return true }
        return status?.textModelReady ?? false
    }
    private var defaultModel: String {
        let model = status?.textModel ?? ""
        return model.isEmpty ? "gemma4:12b" : model
    }
    private var allReady: Bool {
        manager.backendHealthy && (!usesOllama || (ollamaReachable && modelReady))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            HStack(spacing: 12) {
                LogoMarkView(size: 34)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Welcome to OmniDev")
                        .font(.title2.weight(.semibold))
                    Text("Nothing leaves your Mac. Let's get the local engine ready.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            }

            VStack(spacing: 10) {
                OnboardingStep(
                    title: "Local engine",
                    detail: manager.backendHealthy
                        ? "FastAPI backend is running on 127.0.0.1:\(manager.backendPort)."
                        : "Starting the FastAPI backend sidecar…",
                    state: manager.backendHealthy ? .done : .waiting
                )

                if usesOllama {
                    OnboardingStep(
                        title: "Ollama",
                        detail: ollamaReachable
                            ? "Local Ollama server is reachable."
                            : "Install and start Ollama from ollama.com, then refresh.",
                        state: ollamaReachable ? .done : (manager.backendHealthy ? .action : .waiting)
                    )

                    OnboardingStep(
                        title: "Local model — \(defaultModel)",
                        detail: modelStepDetail,
                        state: modelReady ? .done : (ollamaReachable ? .action : .waiting)
                    ) {
                        if !modelReady && ollamaReachable {
                            if case .pulling(_, let fraction) = pull.phase {
                                ProgressView(value: fraction)
                                    .progressViewStyle(.linear)
                                    .frame(maxWidth: .infinity)
                            } else {
                                Button("Download (~7.6 GB)") {
                                    pull.pull(model: defaultModel, client: manager.backendClient) {
                                        Task { await refresh() }
                                    }
                                }
                                .buttonStyle(.borderedProminent)
                                .tint(.omniAccent)
                            }
                        }
                    }
                } else {
                    OnboardingStep(
                        title: "Cloud provider",
                        detail: "Using \(status?.provider ?? "gemini") — no local model needed.",
                        state: .done
                    )
                }

                OnboardingStep(
                    title: "Knowledge (optional)",
                    detail: "Add a folder of notes, docs or code and OmniDev can answer questions about it, fully offline with citations.",
                    state: .optional
                ) {
                    Button("Open Knowledge…") {
                        NotificationCenter.default.post(name: .omniDevNavigate, object: OmniDevRoute.knowledge)
                        dismiss()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }

                OnboardingStep(
                    title: "AWS (optional)",
                    detail: "The DevOps Agent and Cloud Storage use your AWS credentials. Keys from ~/.aws work automatically; you can also set a key pair in Settings.",
                    state: .optional
                ) {
                    Button("Configure AWS…") {
                        SettingsOpener.open()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
            }

            HStack {
                Button("Refresh") {
                    Task { await refresh() }
                }
                .disabled(refreshing || pull.isPulling)

                Spacer()

                Button("Skip for Now") {
                    dismiss()
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)

                Button("Start Using OmniDev") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
                .tint(.omniAccent)
                .disabled(!allReady)
            }
        }
        .padding(28)
        .frame(width: 520)
        .task {
            await refresh()
        }
        .onReceive(NotificationCenter.default.publisher(for: .omniDevModelsChanged)) { _ in
            Task { await refresh() }
        }
    }

    private var modelStepDetail: String {
        switch pull.phase {
        case .pulling(let status, let fraction):
            if let fraction {
                return "\(status) — \(Int(fraction * 100))%"
            }
            return status
        case .failed(let message):
            return "Download failed: \(message)"
        case .done:
            return "Installed. Text, structured output, and vision — fully offline."
        case .idle:
            return modelReady
                ? "Installed. Text, structured output, and vision — fully offline."
                : "One download covers chat, DevOps intent parsing, codegen, and vision."
        }
    }

    private func refresh() async {
        refreshing = true
        defer { refreshing = false }
        await manager.refreshHealthInfo()
        status = try? await manager.backendClient.models().status
    }
}

private struct OnboardingStep<Accessory: View>: View {
    enum StepState {
        case waiting
        case action
        case done
        case optional
    }

    let title: String
    let detail: String
    let state: StepState
    @ViewBuilder var accessory: Accessory

    init(
        title: String,
        detail: String,
        state: StepState,
        @ViewBuilder accessory: () -> Accessory = { EmptyView() }
    ) {
        self.title = title
        self.detail = detail
        self.state = state
        self.accessory = accessory()
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: symbol)
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(state == .done ? AnyShapeStyle(.green) : AnyShapeStyle(Color.omniAccent))
                .frame(width: 24)
                .padding(.top, 1)

            VStack(alignment: .leading, spacing: 5) {
                Text(title)
                    .font(.subheadline.weight(.semibold))
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                accessory
            }
            Spacer(minLength: 0)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private var symbol: String {
        switch state {
        case .waiting: return "clock"
        case .action: return "arrow.down.circle"
        case .done: return "checkmark.circle.fill"
        case .optional: return "gearshape"
        }
    }
}
