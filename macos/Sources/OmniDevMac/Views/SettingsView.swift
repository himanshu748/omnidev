import SwiftUI

struct SettingsView: View {
    @ObservedObject var manager: LocalStackManager
    @AppStorage(AppSettings.aiProviderKey) private var aiProvider = AppSettings.defaultAIProvider
    @AppStorage(AppSettings.devopsReadOnlyKey) private var devopsReadOnly = false
    @AppStorage(AppSettings.backendPortKey) private var backendPort = AppSettings.defaultBackendPort
    @AppStorage(AppSettings.ollamaModelKey) private var ollamaModel = ""
    @AppStorage(AppSettings.awsAccessKeyIdKey) private var awsAccessKeyId = ""
    @AppStorage(AppSettings.awsRegionKey) private var awsRegion = AppSettings.defaultAWSRegion

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
        Form {
            engineSection
            modelSection
            awsSection
            portSection
            statusSection
        }
        .formStyle(.grouped)
        .frame(width: 460)
        .fixedSize(horizontal: false, vertical: true)
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

    private var engineSection: some View {
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
    }

    private var modelSection: some View {
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
    }

    private var awsSection: some View {
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
            Text("AWS")
        }
    }

    private var portSection: some View {
        Section {
            TextField("Backend port", text: $backendPort)
        } header: {
            Text("Engine Port")
        }
    }

    private var statusSection: some View {
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
