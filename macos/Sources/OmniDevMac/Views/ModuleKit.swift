import SwiftUI

/// Shared chrome for the native module pages — one error banner and one
/// result surface, so every module reads the same. Page identity lives in
/// the window toolbar via navigationTitle/navigationSubtitle.
struct ErrorBanner: View {
    let message: String

    var body: some View {
        Label(message, systemImage: "exclamationmark.triangle.fill")
            .font(.callout)
            .foregroundStyle(.orange)
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.orange.opacity(0.12), in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

struct ModuleCard<Content: View>: View {
    var title: String? = nil
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let title {
                Text(title)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)
            }
            content
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

/// Selectable monospaced output with a copy button — the standard result
/// surface for text-shaped module output.
struct MonoResult: View {
    let text: String
    var maxHeight: CGFloat = .infinity

    var body: some View {
        VStack(alignment: .trailing, spacing: 6) {
            CopyButton(text: text)
            ScrollView {
                Text(text)
                    .font(.callout.monospaced())
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxHeight: maxHeight)
        }
    }
}

struct CopyButton: View {
    let text: String
    @State private var copied = false

    var body: some View {
        Button {
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(text, forType: .string)
            copied = true
            Task {
                try? await Task.sleep(nanoseconds: 1_400_000_000)
                copied = false
            }
        } label: {
            Label(copied ? "Copied" : "Copy", systemImage: copied ? "checkmark" : "doc.on.doc")
                .font(.caption)
        }
        .buttonStyle(.bordered)
        .controlSize(.small)
    }
}

/// One state machine per module run: idle → running → output or error.
@MainActor
final class ModuleRun<Output>: ObservableObject {
    @Published private(set) var output: Output?
    @Published private(set) var error: String?
    @Published private(set) var isRunning = false

    func run(_ work: @escaping () async throws -> Output) {
        guard !isRunning else { return }
        isRunning = true
        error = nil
        Task {
            do {
                output = try await work()
            } catch {
                self.error = error.localizedDescription
            }
            isRunning = false
        }
    }

    func reset() {
        output = nil
        error = nil
    }
}
