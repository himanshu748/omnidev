import SwiftUI

struct SettingsView: View {
    @ObservedObject var manager: LocalStackManager
    @AppStorage(AppSettings.aiProviderKey) private var aiProvider = AppSettings.defaultAIProvider
    @AppStorage(AppSettings.devopsReadOnlyKey) private var devopsReadOnly = false
    @AppStorage(AppSettings.backendPortKey) private var backendPort = AppSettings.defaultBackendPort
    @AppStorage(AppSettings.awsAccessKeyIdKey) private var awsAccessKeyId = ""
    @AppStorage(AppSettings.awsRegionKey) private var awsRegion = AppSettings.defaultAWSRegion
    @State private var awsSecretAccessKey = AppSettings.awsSecretAccessKey

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
            } header: {
                Text("Engine Port")
            }

            Section {
                TextField("Access key ID", text: $awsAccessKeyId)
                    .autocorrectionDisabled()
                SecureField("Secret access key", text: $awsSecretAccessKey)
                    .onChange(of: awsSecretAccessKey) { newValue in
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
