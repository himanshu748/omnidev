import SwiftUI

/// Native tabbed Settings — General (engine + port), Model, and AWS — so no
/// section ever scrolls off screen.
struct SettingsView: View {
    @ObservedObject var manager: LocalStackManager
    @AppStorage(AppSettings.aiProviderKey) private var aiProvider = AppSettings.defaultAIProvider
    @AppStorage(AppSettings.devopsReadOnlyKey) private var devopsReadOnly = false
    @AppStorage(AppSettings.backendPortKey) private var backendPort = AppSettings.defaultBackendPort
    @AppStorage(AppSettings.ollamaModelKey) private var ollamaModel = ""
    @AppStorage(AppSettings.awsAccessKeyIdKey) private var awsAccessKeyId = ""
    @AppStorage(AppSettings.awsRegionKey) private var awsRegion = AppSettings.defaultAWSRegion
    @AppStorage(AppSettings.knowledgeExclusionsKey) private var knowledgeExclusions = ""

    /// Secrets load from the keychain when the window appears — not at App
    /// body evaluation — and persist on change.
    @State private var awsSecretAccessKey = ""
    @State private var geminiApiKey = ""
    @State private var secretsLoaded = false

    /// Explicit picker state: "" (engine default), a catalog name, or
    /// "custom". Kept in sync with `ollamaModel` in onAppear/onChange so the
    /// Custom row is actually reachable and sticky.
    @State private var modelChoice = ""
    @State private var customModel = ""

    var body: some View {
        TabView {
            generalTab
                .tabItem { Label("General", systemImage: "gearshape") }
            modelTab
                .tabItem { Label("Model", systemImage: "cpu") }
            WorkspacesTab(manager: manager)
                .tabItem { Label("Agent", systemImage: "wand.and.rays") }
            awsTab
                .tabItem { Label("AWS", systemImage: "cloud") }
        }
        .frame(width: 500, height: 460)
        .onAppear {
            if !secretsLoaded {
                awsSecretAccessKey = AppSettings.awsSecretAccessKey
                geminiApiKey = AppSettings.geminiApiKey
                secretsLoaded = true
            }
            if !ollamaModel.isEmpty && LocalModelCatalog.entry(for: ollamaModel) == nil {
                modelChoice = "custom"
                customModel = ollamaModel
            } else {
                modelChoice = ollamaModel
            }
        }
    }

    // MARK: - General

    private var generalTab: some View {
        Form {
            Section {
                Picker("AI provider", selection: $aiProvider) {
                    Text("Auto (Gemini if key set, else Ollama)").tag("auto")
                    Text("Ollama — fully local").tag("ollama")
                    Text("Gemini — cloud").tag("gemini")
                }

                SecureField("Gemini API key", text: $geminiApiKey)
                    .onChange(of: geminiApiKey) { newValue in
                        guard secretsLoaded else { return }
                        AppSettings.setGeminiApiKey(newValue)
                    }
                Text("Only needed for cloud mode. Stored in your login keychain.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Toggle("Read-only DevOps mode", isOn: $devopsReadOnly)
                Text("Refuses every destructive AWS action, even when confirmed.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } header: {
                Text("Engine")
            }

            Section {
                TextField(
                    "Never index",
                    text: $knowledgeExclusions,
                    prompt: Text("~/Private, *.draft.md")
                )
                .autocorrectionDisabled()
                Text("Comma-separated folders or patterns, applied on top of the built-in protections. Keys, keychains, browser profiles, .env files, shell histories and ~/Library are always excluded and cannot be indexed.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } header: {
                Text("Knowledge Privacy")
            }

            Section {
                TextField("Backend port", text: $backendPort)
            } header: {
                Text("Engine Port")
            }

            applySection
        }
        .formStyle(.grouped)
    }

    // MARK: - Model

    private var modelTab: some View {
        Form {
            Section {
                LabeledContent("Best for this Mac") {
                    HStack(spacing: 8) {
                        Text("\(LocalModelCatalog.recommendedForThisMac.label) · \(LocalModelCatalog.machineMemoryGB) GB RAM")
                            .foregroundStyle(.secondary)
                        Button("Use") {
                            ollamaModel = LocalModelCatalog.recommendedForThisMac.name
                            modelChoice = ollamaModel
                        }
                        .controlSize(.small)
                        .disabled(ollamaModel == LocalModelCatalog.recommendedForThisMac.name)
                    }
                }

                Picker("Local model", selection: $modelChoice) {
                    Text("Engine default (\(AppSettings.defaultOllamaModel))").tag("")
                    ForEach(LocalModelCatalog.entries) { entry in
                        Text("\(entry.label) — \(entry.sizeGB, specifier: "%.1f") GB\(entry.audio ? " · audio" : "")")
                            .tag(entry.name)
                    }
                    Text("Custom…").tag("custom")
                }
                .onChange(of: modelChoice) { newValue in
                    if newValue == "custom" {
                        customModel = ollamaModel
                    } else {
                        ollamaModel = newValue
                    }
                }

                if modelChoice == "custom" {
                    TextField("Model reference", text: $customModel, prompt: Text("e.g. llama3.2:3b"))
                        .autocorrectionDisabled()
                        .onChange(of: customModel) { newValue in
                            let trimmed = newValue.trimmingCharacters(in: .whitespaces)
                            // Never wipe the stored ref from a half-typed field.
                            if !trimmed.isEmpty {
                                ollamaModel = trimmed
                            }
                        }
                    Text("Any Ollama model with structured-output support works.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if let entry = LocalModelCatalog.entry(for: ollamaModel) {
                    Text(entry.note)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Text("Download and remove models in Command Center → Local Models.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } header: {
                Text("Local Model")
            }

            applySection
        }
        .formStyle(.grouped)
    }

    // MARK: - AWS

    private var awsTab: some View {
        Form {
            Section {
                TextField("Access key ID", text: $awsAccessKeyId)
                    .autocorrectionDisabled()
                SecureField("Secret access key", text: $awsSecretAccessKey)
                    .onChange(of: awsSecretAccessKey) { newValue in
                        guard secretsLoaded else { return }
                        AppSettings.setAWSSecretAccessKey(newValue)
                    }
                TextField("Region", text: $awsRegion, prompt: Text(AppSettings.defaultAWSRegion))
                    .autocorrectionDisabled()
                Text("Used by the DevOps Agent and Cloud Storage. Leave the keys empty to use the standard AWS credential chain (~/.aws, SSO, instance role). The secret is stored in your login keychain.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } header: {
                Text("AWS Credentials")
            }

            applySection
        }
        .formStyle(.grouped)
    }

    // MARK: - Shared apply/status footer

    private var applySection: some View {
        Section {
            LabeledContent("Status") {
                Text(manager.state.title)
            }
            if !manager.aiModel.isEmpty {
                LabeledContent("Active model") {
                    Text(manager.aiModel)
                        .font(.body.monospaced())
                }
            }
            Button("Apply & Restart Services") {
                manager.restartServices()
            }
            Text("Changes take effect when the local services restart.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

/// Agent workspaces: folders the agent may edit without asking. Anything
/// outside these prompts for approval on every action.
private struct WorkspacesTab: View {
    @ObservedObject var manager: LocalStackManager
    @State private var workspaces: [BackendClient.AgentWorkspace] = []
    @State private var errorText = ""
    @State private var loading = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Agent workspaces")
                .font(.headline)
            Text("The agent reads and edits freely inside these folders. Anywhere else it asks you first, every time.")
                .font(.caption)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            List {
                ForEach(workspaces) { workspace in
                    HStack(spacing: 8) {
                        Image(systemName: workspace.implicit ? "shippingbox" : "folder")
                            .foregroundStyle(Color.omniAccent)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(workspace.name).font(.body)
                            Text((workspace.path as NSString).abbreviatingWithTildeInPath)
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        if workspace.implicit {
                            Text("built in")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        } else {
                            Button {
                                remove(workspace)
                            } label: {
                                Image(systemName: "minus.circle")
                            }
                            .buttonStyle(.plain)
                            .help("Stop trusting this folder")
                        }
                    }
                    .padding(.vertical, 2)
                }
                if workspaces.isEmpty && !loading {
                    Text("No workspaces yet.")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(minHeight: 200)

            if !errorText.isEmpty {
                Text(errorText)
                    .font(.caption)
                    .foregroundStyle(.orange)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack {
                Button("Add Folder…", action: pickFolder)
                Spacer()
                Button("Refresh", action: load)
            }
        }
        .padding(20)
        .onAppear(perform: load)
    }

    private func load() {
        loading = true
        let client = manager.backendClient
        Task {
            defer { loading = false }
            do {
                workspaces = try await client.agentWorkspaces()
                errorText = ""
            } catch {
                errorText = error.localizedDescription
            }
        }
    }

    private func pickFolder() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.prompt = "Trust Folder"
        panel.message = "Pick a folder the agent may edit without asking."
        guard panel.runModal() == .OK, let url = panel.url else { return }

        let client = manager.backendClient
        Task {
            do {
                try await client.addAgentWorkspace(path: url.path)
                errorText = ""
                load()
            } catch {
                errorText = error.localizedDescription
            }
        }
    }

    private func remove(_ workspace: BackendClient.AgentWorkspace) {
        let client = manager.backendClient
        Task {
            do {
                try await client.removeAgentWorkspace(path: workspace.path)
                load()
            } catch {
                errorText = error.localizedDescription
            }
        }
    }
}
