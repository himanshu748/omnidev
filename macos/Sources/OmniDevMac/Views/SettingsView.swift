import SwiftUI

struct SettingsView: View {
    @ObservedObject var manager: LocalStackManager
    @AppStorage(AppSettings.aiProviderKey) private var aiProvider = AppSettings.defaultAIProvider
    @AppStorage(AppSettings.devopsReadOnlyKey) private var devopsReadOnly = false
    @AppStorage(AppSettings.backendPortKey) private var backendPort = AppSettings.defaultBackendPort
    @AppStorage(AppSettings.frontendPortKey) private var frontendPort = AppSettings.defaultFrontendPort

    var body: some View {
        Form {
            Section {
                Picker("AI provider", selection: $aiProvider) {
                    Text("Auto (Gemini if key set, else Ollama)").tag("auto")
                    Text("Ollama — fully local").tag("ollama")
                    Text("Gemini — cloud").tag("gemini")
                }

                Toggle("Read-only DevOps mode", isOn: $devopsReadOnly)
                Text("Refuses every destructive AWS action, even when confirmed.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } header: {
                Text("Engine")
            }

            Section {
                TextField("Backend port", text: $backendPort)
                TextField("Frontend port", text: $frontendPort)
            } header: {
                Text("Ports")
            }

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
        .formStyle(.grouped)
        .frame(width: 440)
        .fixedSize(horizontal: false, vertical: true)
    }
}
