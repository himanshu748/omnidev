import SwiftUI

/// Native Cloud Storage: browse S3 buckets and objects, upload, presigned
/// download, and confirmed delete — via the local backend's boto3 layer.
struct StorageView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var buckets: [BackendClient.Bucket] = []
    @State private var selectedBucket: String?
    @State private var objects: [BackendClient.S3Object] = []
    @State private var prefix = ""
    @State private var error: String?
    @State private var busy = false
    @State private var showImporter = false
    @State private var pendingDelete: BackendClient.S3Object?
    @State private var notice: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ModuleHeader(
                    title: "Cloud Storage",
                    subtitle: "S3 buckets and objects through the boto3 credential chain."
                )

                if let error {
                    ErrorBanner(message: error)
                }
                if let notice {
                    Text(notice)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                HStack(alignment: .top, spacing: 16) {
                    bucketsCard
                    objectsCard
                }
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("Cloud Storage")
        .task {
            await loadBuckets()
        }
        .fileImporter(isPresented: $showImporter, allowedContentTypes: [.item]) { result in
            if case .success(let url) = result {
                upload(url)
            }
        }
        .confirmationDialog(
            "Delete \(pendingDelete?.key ?? "")?",
            isPresented: Binding(get: { pendingDelete != nil }, set: { if !$0 { pendingDelete = nil } })
        ) {
            Button("Delete Object", role: .destructive) {
                if let object = pendingDelete {
                    deleteObject(object)
                }
            }
        } message: {
            Text("This permanently removes the object from S3.")
        }
    }

    private var bucketsCard: some View {
        ModuleCard(title: "Buckets") {
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Button {
                        Task { await loadBuckets() }
                    } label: {
                        Label("Refresh", systemImage: "arrow.clockwise")
                            .font(.caption)
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                    if busy {
                        ProgressView().controlSize(.small)
                    }
                }
                .padding(.bottom, 6)

                if buckets.isEmpty && !busy {
                    Text("No buckets (or AWS credentials not configured).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                ForEach(buckets) { bucket in
                    Button {
                        selectedBucket = bucket.name
                        Task { await loadObjects() }
                    } label: {
                        HStack {
                            Image(systemName: "externaldrive")
                                .font(.caption)
                            Text(bucket.name)
                                .font(.callout.monospaced())
                                .lineLimit(1)
                            Spacer()
                        }
                        .padding(.vertical, 5)
                        .padding(.horizontal, 6)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .background(
                        selectedBucket == bucket.name
                            ? AnyShapeStyle(Color.omniAccent.opacity(0.18))
                            : AnyShapeStyle(.clear),
                        in: RoundedRectangle(cornerRadius: 6, style: .continuous)
                    )
                }
            }
        }
        .frame(width: 280)
    }

    private var objectsCard: some View {
        ModuleCard(title: selectedBucket.map { "Objects — \($0)" } ?? "Objects") {
            if selectedBucket == nil {
                Text("Select a bucket to list its objects.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 10) {
                        TextField("Prefix filter", text: $prefix)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 220)
                            .onSubmit { Task { await loadObjects() } }
                        Button("Filter") {
                            Task { await loadObjects() }
                        }
                        Spacer()
                        Button {
                            showImporter = true
                        } label: {
                            Label("Upload…", systemImage: "arrow.up.doc")
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.omniAccent)
                    }

                    if objects.isEmpty && !busy {
                        Text("No objects.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    ForEach(objects) { object in
                        HStack(spacing: 10) {
                            Text(object.key)
                                .font(.caption.monospaced())
                                .lineLimit(1)
                                .textSelection(.enabled)
                            Spacer()
                            Text(Self.formatSize(object.size))
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Button("Open") {
                                openPresigned(object)
                            }
                            .controlSize(.small)
                            Button(role: .destructive) {
                                pendingDelete = object
                            } label: {
                                Image(systemName: "trash")
                            }
                            .controlSize(.small)
                        }
                        .padding(.vertical, 2)
                    }
                }
            }
        }
    }

    private static func formatSize(_ bytes: Int) -> String {
        ByteCountFormatter.string(fromByteCount: Int64(bytes), countStyle: .file)
    }

    private func loadBuckets() async {
        busy = true
        error = nil
        do {
            buckets = try await manager.backendClient.listBuckets()
        } catch {
            self.error = error.localizedDescription
        }
        busy = false
    }

    private func loadObjects() async {
        guard let bucket = selectedBucket else { return }
        busy = true
        error = nil
        do {
            objects = try await manager.backendClient.listObjects(bucket: bucket, prefix: prefix)
        } catch {
            self.error = error.localizedDescription
        }
        busy = false
    }

    private func upload(_ url: URL) {
        guard let bucket = selectedBucket else { return }
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        guard let data = try? Data(contentsOf: url) else {
            error = "Could not read the selected file."
            return
        }
        let client = manager.backendClient
        let filename = url.lastPathComponent
        busy = true
        Task {
            do {
                try await client.uploadObject(
                    data: data,
                    filename: filename,
                    contentType: "application/octet-stream",
                    bucket: bucket
                )
                notice = "Uploaded \(filename)."
                await loadObjects()
            } catch {
                self.error = error.localizedDescription
            }
            busy = false
        }
    }

    private func openPresigned(_ object: BackendClient.S3Object) {
        guard let bucket = selectedBucket else { return }
        let client = manager.backendClient
        Task {
            do {
                let url = try await client.downloadURL(bucket: bucket, key: object.key)
                NSWorkspace.shared.open(url)
            } catch {
                self.error = error.localizedDescription
            }
        }
    }

    private func deleteObject(_ object: BackendClient.S3Object) {
        guard let bucket = selectedBucket else { return }
        let client = manager.backendClient
        busy = true
        Task {
            do {
                try await client.deleteObject(bucket: bucket, key: object.key)
                notice = "Deleted \(object.key)."
                await loadObjects()
            } catch {
                self.error = error.localizedDescription
            }
            busy = false
        }
    }
}
