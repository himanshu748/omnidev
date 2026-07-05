import SwiftUI

/// The MCP marketplace: install curated tool servers, toggle them, and see
/// the tools the local model can call from chat. Catalog-only by design —
/// arbitrary commands cannot be added from the UI or the API.
struct MCPMarketplaceView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var catalog: [BackendClient.MCPCatalogEntry] = []
    @State private var servers: [BackendClient.MCPServer] = []
    @State private var toolsByServer: [String: [BackendClient.MCPTool]] = [:]
    @State private var paramDrafts: [String: [String: String]] = [:]
    @State private var error: String?
    @State private var busyServer: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ModuleHeader(
                    title: "MCP Marketplace",
                    subtitle: "Give the local model tools. Gemma 4 calls them from chat when the Tools toggle is on."
                )

                if let error {
                    ErrorBanner(message: error)
                }

                if !servers.isEmpty {
                    installedCard
                }
                catalogCard

                Text("Safety: only this curated catalog can be installed; folder access is scoped to directories you pick inside your home folder; servers run with a minimal environment (no backend credentials); every tool call is shown in the chat transcript.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("MCP Marketplace")
        .task {
            await refresh()
        }
    }

    private var installedCard: some View {
        ModuleCard(title: "Installed (\(servers.count))") {
            VStack(alignment: .leading, spacing: 12) {
                ForEach(servers) { server in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack(spacing: 10) {
                            Toggle("", isOn: Binding(
                                get: { server.enabled },
                                set: { setEnabled(server, $0) }
                            ))
                            .labelsHidden()
                            .toggleStyle(.switch)
                            .controlSize(.small)

                            Text(server.name)
                                .font(.callout.weight(.semibold).monospaced())
                            if let dir = server.params.values.first {
                                Text(dir)
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            Spacer()

                            if busyServer == server.name {
                                ProgressView().controlSize(.small)
                            }
                            Button("Tools") {
                                loadTools(server)
                            }
                            .controlSize(.small)
                            Button(role: .destructive) {
                                remove(server)
                            } label: {
                                Image(systemName: "trash")
                            }
                            .controlSize(.small)
                        }

                        if let tools = toolsByServer[server.name] {
                            VStack(alignment: .leading, spacing: 3) {
                                ForEach(tools) { tool in
                                    HStack(alignment: .top, spacing: 8) {
                                        Text(tool.name)
                                            .font(.caption.monospaced())
                                            .foregroundStyle(Color.omniAccent)
                                        Text(tool.description)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                            .lineLimit(1)
                                    }
                                }
                            }
                            .padding(.leading, 42)
                        }
                    }
                }
            }
        }
    }

    private var catalogCard: some View {
        ModuleCard(title: "Catalog") {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 300), spacing: 12)], spacing: 12) {
                ForEach(catalog) { entry in
                    catalogTile(entry)
                }
            }
        }
    }

    private func catalogTile(_ entry: BackendClient.MCPCatalogEntry) -> some View {
        let installed = servers.contains { $0.catalogId == entry.id }
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(entry.name)
                    .font(.subheadline.weight(.semibold))
                Spacer()
                TagView(text: entry.capabilities, color: entry.capabilities.contains("write") ? .orange : .green)
            }
            Text(entry.description)
                .font(.caption)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            ForEach(entry.params) { param in
                TextField(
                    param.type == "path" ? "\(param.name) — e.g. ~/Projects/demo" : param.name,
                    text: Binding(
                        get: { paramDrafts[entry.id]?[param.name] ?? "" },
                        set: { paramDrafts[entry.id, default: [:]][param.name] = $0 }
                    )
                )
                .textFieldStyle(.roundedBorder)
                .font(.caption)
            }

            HStack {
                if !entry.runtimeAvailable {
                    Text("Requires \(entry.runtime) — not installed")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
                Spacer()
                Button(installed ? "Installed" : "Add") {
                    add(entry)
                }
                .buttonStyle(.borderedProminent)
                .tint(.omniAccent)
                .controlSize(.small)
                .disabled(installed || !entry.runtimeAvailable)
            }
        }
        .padding(12)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private func refresh() async {
        error = nil
        do {
            async let catalogTask = manager.backendClient.mcpCatalog()
            async let serversTask = manager.backendClient.mcpServers()
            catalog = try await catalogTask
            servers = try await serversTask
        } catch {
            self.error = error.localizedDescription
        }
    }

    private func add(_ entry: BackendClient.MCPCatalogEntry) {
        let params = paramDrafts[entry.id] ?? [:]
        let client = manager.backendClient
        Task {
            do {
                _ = try await client.mcpAddServer(catalogId: entry.id, params: params)
                await refresh()
            } catch {
                self.error = error.localizedDescription
            }
        }
    }

    private func remove(_ server: BackendClient.MCPServer) {
        let client = manager.backendClient
        Task {
            do {
                try await client.mcpRemoveServer(server.name)
                toolsByServer[server.name] = nil
                await refresh()
            } catch {
                self.error = error.localizedDescription
            }
        }
    }

    private func setEnabled(_ server: BackendClient.MCPServer, _ enabled: Bool) {
        let client = manager.backendClient
        Task {
            do {
                try await client.mcpSetEnabled(server.name, enabled: enabled)
                await refresh()
            } catch {
                self.error = error.localizedDescription
            }
        }
    }

    private func loadTools(_ server: BackendClient.MCPServer) {
        busyServer = server.name
        let client = manager.backendClient
        Task {
            do {
                toolsByServer[server.name] = try await client.mcpTools(server: server.name)
            } catch {
                self.error = error.localizedDescription
            }
            busyServer = nil
        }
    }
}
