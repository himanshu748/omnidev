import SwiftUI
import WebKit

/// Native Code Gen: generate a validated multi-file project, browse and
/// copy files, refine with follow-up instructions, preview HTML output in
/// an isolated web view, and save the files to a folder you choose.
struct CodeGenView: View {
    @ObservedObject var manager: LocalStackManager
    @StateObject private var run = ModuleRun<BackendClient.CodeGenResult>()
    @State private var prompt = ""
    @State private var framework = "react"
    @State private var refineInstruction = ""
    @State private var selectedPath: String?
    @State private var showPreview = false
    @State private var saveMessage: String?
    @State private var landName = ""

    private static let frameworks = [
        "react", "next", "streamlit", "node", "express", "python", "fastapi",
        "vue", "svelte", "astro", "remix", "solid", "sveltekit", "django",
        "flask", "go", "html",
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ModuleCard {
                    VStack(alignment: .leading, spacing: 10) {
                        TextField("What to build — e.g. A todo app with dark mode", text: $prompt)
                            .textFieldStyle(.roundedBorder)
                            .onSubmit(generate)

                        HStack {
                            Picker("Framework", selection: $framework) {
                                ForEach(Self.frameworks, id: \.self) { Text($0).tag($0) }
                            }
                            .frame(width: 220)

                            Spacer()

                            Button {
                                generate()
                            } label: {
                                if run.isRunning {
                                    ProgressView().controlSize(.small)
                                } else {
                                    Text("Generate")
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.omniAccent)
                            .disabled(prompt.trimmingCharacters(in: .whitespaces).isEmpty || run.isRunning)
                        }
                    }
                }

                if let error = run.error {
                    ErrorBanner(message: error)
                }

                if let result = run.output {
                    resultSection(result)
                }
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("Code Gen")
        .navigationSubtitle("Validated project files from the local model — never executed by the backend.")
        .sheet(isPresented: $showPreview) {
            if let result = run.output {
                HTMLPreviewSheet(result: result)
            }
        }
    }

    @ViewBuilder
    private func resultSection(_ result: BackendClient.CodeGenResult) -> some View {
        if !result.summary.isEmpty {
            ModuleCard(title: "Summary") {
                Text(result.summary)
                    .font(.callout)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }

        ModuleCard(title: "Files (\(result.files.count))") {
            HStack(alignment: .top, spacing: 14) {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(result.files) { file in
                        Button {
                            selectedPath = file.path
                        } label: {
                            Text(file.path)
                                .font(.caption.monospaced())
                                .lineLimit(1)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.vertical, 4)
                                .padding(.horizontal, 6)
                                .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .background(
                            selectedPath == file.path
                                ? AnyShapeStyle(Color.omniAccent.opacity(0.18))
                                : AnyShapeStyle(.clear),
                            in: RoundedRectangle(cornerRadius: 5, style: .continuous)
                        )
                    }
                }
                .frame(width: 230)

                Divider()

                if let file = result.files.first(where: { $0.path == (selectedPath ?? result.files.first?.path) })
                    ?? result.files.first {
                    MonoResult(text: file.content, maxHeight: 420)
                }
            }

            HStack {
                Button("Save to Folder…") {
                    saveToFolder(result)
                }
                if htmlEntry(result) != nil {
                    Button("Preview") {
                        showPreview = true
                    }
                }

                Divider().frame(height: 18)

                TextField("repo name (e.g. todo-app)", text: $landName)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 190)
                Button("Land in Repo") {
                    land(result)
                }
                .buttonStyle(.borderedProminent)
                .tint(.omniAccent)
                .disabled(landName.trimmingCharacters(in: .whitespaces).isEmpty)
                .help("Writes validated files under ~/OmniDev/projects/<name> and commits them")

                if let saveMessage {
                    Text(saveMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }
        }

        ModuleCard(title: "Refine") {
            HStack(spacing: 10) {
                TextField("e.g. add auth, convert to TypeScript", text: $refineInstruction)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { refine(result) }

                Button("Refine") {
                    refine(result)
                }
                .disabled(refineInstruction.trimmingCharacters(in: .whitespaces).isEmpty || run.isRunning)
            }
        }
    }

    private func generate() {
        let text = prompt.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        let client = manager.backendClient
        let framework = framework
        saveMessage = nil
        selectedPath = nil
        run.run {
            try await client.generateProject(prompt: text, framework: framework)
        }
    }

    private func refine(_ current: BackendClient.CodeGenResult) {
        let instruction = refineInstruction.trimmingCharacters(in: .whitespaces)
        guard !instruction.isEmpty else { return }
        let client = manager.backendClient
        let framework = framework
        refineInstruction = ""
        run.run {
            try await client.refineProject(files: current.files, instruction: instruction, framework: framework)
        }
    }

    private func htmlEntry(_ result: BackendClient.CodeGenResult) -> BackendClient.GeneratedFile? {
        if !result.entry.isEmpty, result.entry.hasSuffix(".html") {
            return result.files.first { $0.path == result.entry }
        }
        return result.files.first { $0.path.hasSuffix(".html") }
    }

    private func land(_ result: BackendClient.CodeGenResult) {
        let name = landName.trimmingCharacters(in: .whitespaces).lowercased()
        let client = manager.backendClient
        saveMessage = "Landing…"
        Task {
            do {
                let landed = try await client.landProject(
                    name: name, files: result.files, message: "Land \(name) from OmniDev Code Gen"
                )
                saveMessage = "\(landed.message) → \(landed.path) @ \(landed.commit)"
                NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: landed.path)])
            } catch {
                saveMessage = "Landing failed: \(error.localizedDescription)"
            }
        }
    }

    private func saveToFolder(_ result: BackendClient.CodeGenResult) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.prompt = "Save Files Here"
        guard panel.runModal() == .OK, let root = panel.url else { return }

        do {
            for file in result.files {
                // Paths are backend-validated as safe relative paths; keep a
                // client-side guard anyway.
                let destination = root.appendingPathComponent(file.path).standardizedFileURL
                guard destination.path.hasPrefix(root.standardizedFileURL.path) else { continue }
                try FileManager.default.createDirectory(
                    at: destination.deletingLastPathComponent(),
                    withIntermediateDirectories: true
                )
                try file.content.write(to: destination, atomically: true, encoding: .utf8)
            }
            saveMessage = "Saved \(result.files.count) files to \(root.lastPathComponent)/"
        } catch {
            saveMessage = "Save failed: \(error.localizedDescription)"
        }
    }
}

/// Isolated preview of a generated HTML entry file: loaded from a string
/// with no base URL, so it has no origin and no access to local files —
/// the native equivalent of the web cockpit's sandboxed iframe.
private struct HTMLPreviewSheet: View {
    let result: BackendClient.CodeGenResult
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Label("Sandboxed preview — generated code runs isolated, not against your backend.",
                      systemImage: "lock.shield")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Button("Done") { dismiss() }
            }
            .padding(12)

            if let html = result.files.first(where: { $0.path.hasSuffix(".html") })?.content {
                IsolatedWebView(html: html)
            }
        }
        .frame(width: 900, height: 640)
    }
}

private struct IsolatedWebView: NSViewRepresentable {
    let html: String

    func makeNSView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.loadHTMLString(html, baseURL: nil)
        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {}
}
