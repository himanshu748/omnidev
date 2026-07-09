import SwiftUI
import UniformTypeIdentifiers

/// Native Vision Lab: analyze, OCR, or custom-prompt a local image with
/// the on-device vision model.
struct VisionView: View {
    @ObservedObject var manager: LocalStackManager
    @StateObject private var run = ModuleRun<BackendClient.VisionResult>()
    @State private var imageURL: URL?
    @State private var image: NSImage?
    @State private var mode = "analyze"
    @State private var prompt = ""
    @State private var showImporter = false
    @State private var loadError: String?

    private static let maxBytes = 10 * 1024 * 1024
    private static let contentTypes: [String: String] = [
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif",
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ModuleCard {
                    VStack(alignment: .leading, spacing: 12) {
                        HStack(spacing: 12) {
                            Button("Choose Image…") {
                                showImporter = true
                            }

                            if let imageURL {
                                Text(imageURL.lastPathComponent)
                                    .font(.callout.monospaced())
                                    .foregroundStyle(.secondary)
                            }

                            Spacer()

                            Picker("Mode", selection: $mode) {
                                Text("Analyze").tag("analyze")
                                Text("OCR").tag("ocr")
                                Text("Custom").tag("custom")
                            }
                            .frame(width: 220)

                            Button {
                                analyze()
                            } label: {
                                if run.isRunning {
                                    ProgressView().controlSize(.small)
                                } else {
                                    Text("Analyze")
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.omniAccent)
                            .disabled(imageURL == nil || run.isRunning)
                        }

                        if mode == "custom" {
                            TextField("Ask about the image…", text: $prompt)
                                .textFieldStyle(.roundedBorder)
                                .onSubmit(analyze)
                        }

                        if let image {
                            Image(nsImage: image)
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(maxHeight: 260)
                                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                        }
                    }
                }

                if let message = loadError ?? run.error {
                    ErrorBanner(message: message)
                }

                if let result = run.output {
                    ModuleCard(title: "Result — \(result.model)") {
                        MonoResult(text: result.result, maxHeight: 420)
                    }
                }
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("Vision Lab")
        .navigationSubtitle("Image analysis and OCR — the image never leaves your Mac.")
        .fileImporter(
            isPresented: $showImporter,
            allowedContentTypes: [.png, .jpeg, .webP, .gif]
        ) { result in
            loadError = nil
            run.reset()
            if case .success(let url) = result {
                let scoped = url.startAccessingSecurityScopedResource()
                defer { if scoped { url.stopAccessingSecurityScopedResource() } }
                guard let data = try? Data(contentsOf: url), data.count <= Self.maxBytes else {
                    loadError = "Could not read the image, or it exceeds the 10 MB limit."
                    return
                }
                imageURL = url
                image = NSImage(data: data)
            }
        }
    }

    private func analyze() {
        guard let imageURL else { return }
        let scoped = imageURL.startAccessingSecurityScopedResource()
        defer { if scoped { imageURL.stopAccessingSecurityScopedResource() } }
        guard let data = try? Data(contentsOf: imageURL) else {
            loadError = "Could not re-read the image file."
            return
        }
        let contentType = Self.contentTypes[imageURL.pathExtension.lowercased()] ?? "image/png"
        let filename = imageURL.lastPathComponent
        let mode = mode
        let prompt = mode == "custom" ? prompt : ""
        let client = manager.backendClient
        run.run {
            try await client.analyzeImage(
                data: data,
                filename: filename,
                contentType: contentType,
                mode: mode,
                prompt: prompt
            )
        }
    }
}
