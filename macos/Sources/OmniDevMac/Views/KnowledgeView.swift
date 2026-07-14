import SwiftUI

/// Local knowledge index: register folders (or the chat history), watch
/// indexing progress, and search the index. Everything is embedded and
/// stored on this Mac; nothing leaves the machine.
struct KnowledgeView: View {
    @ObservedObject var manager: LocalStackManager

    static let embedModel = "mxbai-embed-large"

    @State private var sources: [BackendClient.KnowledgeSource] = []
    @State private var status: BackendClient.KnowledgeIndexStatus?
    @State private var errorMessage: String?
    @State private var searchQuery = ""
    @State private var searchHits: [BackendClient.KnowledgeHit] = []
    @State private var isSearching = false
    @State private var isPullingEmbedder = false
    @State private var pullFraction: Double?

    private let statusTimer = Timer.publish(every: 1.0, on: .main, in: .common).autoconnect()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if let errorMessage {
                    ErrorBanner(message: errorMessage)
                    if needsEmbedder {
                        embedderCard
                    }
                }
                sourcesCard
                if !sources.isEmpty {
                    searchCard
                }
            }
            .padding(20)
        }
        .navigationTitle("Knowledge")
        .navigationSubtitle("Ask your files, offline")
        .toolbar {
            ToolbarItem {
                Button(action: addFolder) {
                    Label("Add Folder", systemImage: "folder.badge.plus")
                }
            }
        }
        .task { await refresh() }
        .onReceive(statusTimer) { _ in
            guard status?.running == true || isPullingEmbedder else { return }
            Task { await refresh() }
        }
    }

    private var needsEmbedder: Bool {
        errorMessage?.contains(Self.embedModel) == true
    }

    // MARK: - Cards

    private var sourcesCard: some View {
        ModuleCard(title: "Sources") {
            if sources.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Add a folder and OmniDev can answer questions about it.")
                        .font(.callout)
                    Text("Notes, docs and code are chunked, embedded with \(Self.embedModel) and stored in ~/.omnidev. Works with wifi off.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    HStack {
                        Button("Add Folder…", action: addFolder)
                            .buttonStyle(.borderedProminent)
                        Button("Index Chat History", action: addChatHistory)
                    }
                }
            } else {
                VStack(spacing: 0) {
                    ForEach(sources) { source in
                        sourceRow(source)
                        if source.id != sources.last?.id {
                            Divider().padding(.vertical, 8)
                        }
                    }
                }
                if !hasChatSource {
                    Divider().padding(.vertical, 8)
                    Button("Index Chat History", action: addChatHistory)
                        .controlSize(.small)
                }
            }
        }
    }

    private func sourceRow(_ source: BackendClient.KnowledgeSource) -> some View {
        HStack(alignment: .center, spacing: 12) {
            Image(systemName: iconName(for: source.kind))
                .foregroundStyle(Color.omniAccent)
                .frame(width: 20)
            VStack(alignment: .leading, spacing: 3) {
                Text(displayPath(source))
                    .font(.callout.weight(.medium))
                    .lineLimit(1)
                    .truncationMode(.middle)
                HStack(spacing: 6) {
                    if isIndexing(source), let status {
                        ProgressView(value: status.fraction ?? 0)
                            .frame(width: 120)
                        Text("\(status.filesDone)/\(status.filesTotal) files")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        Text(summaryLine(source))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            Spacer()
            Button {
                reindex(source)
            } label: {
                Image(systemName: "arrow.clockwise")
            }
            .help("Re-index changed files")
            .disabled(status?.running == true)
            Button(role: .destructive) {
                remove(source)
            } label: {
                Image(systemName: "trash")
            }
            .help("Remove from the index")
        }
        .buttonStyle(.borderless)
    }

    private var searchCard: some View {
        ModuleCard(title: "Search the index") {
            HStack {
                TextField("What do these files say about…", text: $searchQuery)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit(search)
                Button("Search", action: search)
                    .disabled(searchQuery.trimmingCharacters(in: .whitespaces).isEmpty || isSearching)
            }
            if isSearching {
                ProgressView().controlSize(.small)
            }
            ForEach(searchHits) { hit in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(shortPath(hit.filePath))
                            .font(.caption.weight(.semibold).monospaced())
                            .foregroundStyle(Color.omniAccent)
                        Spacer()
                        Text(String(format: "%.2f", hit.score))
                            .font(.caption2.monospaced())
                            .foregroundStyle(.secondary)
                    }
                    Text(hit.snippet)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(4)
                        .textSelection(.enabled)
                }
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            }
        }
    }

    private var embedderCard: some View {
        ModuleCard(title: "Embedding model") {
            Text("Knowledge needs the \(Self.embedModel) embedding model (about 670 MB, one download, runs locally).")
                .font(.callout)
            if isPullingEmbedder {
                ProgressView(value: pullFraction ?? 0)
                Text("Downloading…")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                Button("Download \(Self.embedModel)") {
                    pullEmbedder()
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    // MARK: - Actions

    private func refresh() async {
        let client = manager.backendClient
        do {
            sources = try await client.knowledgeSources()
            let latest = try await client.knowledgeStatus()
            status = latest
            if let indexError = latest.error, !latest.running {
                errorMessage = indexError
            } else if latest.running {
                errorMessage = nil
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func addFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.message = "Choose a folder OmniDev can answer questions about"
        panel.prompt = "Add to Knowledge"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let kind = looksLikeCode(url) ? "code" : "docs"
        Task {
            do {
                errorMessage = nil
                try await manager.backendClient.addKnowledgeSource(path: url.path, kind: kind)
                await refresh()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func addChatHistory() {
        Task {
            do {
                errorMessage = nil
                try await manager.backendClient.addKnowledgeSource(path: "", kind: "chat")
                await refresh()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func reindex(_ source: BackendClient.KnowledgeSource) {
        Task {
            do {
                errorMessage = nil
                try await manager.backendClient.reindexKnowledgeSource(id: source.id)
                await refresh()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func remove(_ source: BackendClient.KnowledgeSource) {
        Task {
            do {
                try await manager.backendClient.deleteKnowledgeSource(id: source.id)
                await refresh()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func search() {
        let query = searchQuery.trimmingCharacters(in: .whitespaces)
        guard !query.isEmpty else { return }
        isSearching = true
        Task {
            do {
                errorMessage = nil
                searchHits = try await manager.backendClient.knowledgeSearch(query: query)
            } catch {
                errorMessage = error.localizedDescription
            }
            isSearching = false
        }
    }

    private func pullEmbedder() {
        isPullingEmbedder = true
        pullFraction = nil
        let client = manager.backendClient
        let pending = sources
        Task {
            do {
                for try await progress in client.pullModel(Self.embedModel) {
                    pullFraction = progress.fraction
                }
                errorMessage = nil
                // Re-run indexing for everything that failed without the model.
                for source in pending where source.chunkCount == 0 {
                    _ = try? await client.reindexKnowledgeSource(id: source.id)
                }
                await refresh()
            } catch {
                errorMessage = error.localizedDescription
            }
            isPullingEmbedder = false
        }
    }

    // MARK: - Helpers

    private var hasChatSource: Bool {
        sources.contains { $0.kind == "chat" }
    }

    private func isIndexing(_ source: BackendClient.KnowledgeSource) -> Bool {
        status?.running == true && status?.sourceId == source.id
    }

    private func iconName(for kind: String) -> String {
        switch kind {
        case "code": return "curlybraces"
        case "chat": return "bubble.left.and.text.bubble.right"
        default: return "doc.text"
        }
    }

    private func displayPath(_ source: BackendClient.KnowledgeSource) -> String {
        if source.kind == "chat" { return "Chat history" }
        return (source.path as NSString).abbreviatingWithTildeInPath
    }

    private func shortPath(_ path: String) -> String {
        (path as NSString).abbreviatingWithTildeInPath
    }

    private func summaryLine(_ source: BackendClient.KnowledgeSource) -> String {
        var parts = ["\(source.fileCount) files", "\(source.chunkCount) chunks"]
        if source.lastIndexedAt == nil {
            parts.append("not indexed yet")
        }
        return parts.joined(separator: " · ")
    }

    private func looksLikeCode(_ url: URL) -> Bool {
        let markers = [".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Package.swift"]
        return markers.contains { FileManager.default.fileExists(atPath: url.appendingPathComponent($0).path) }
    }
}
