import SwiftUI

/// Native streaming chat against the local model — tokens render live from
/// `POST /api/chat/stream`, no webview involved.
struct ChatView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var messages: [ChatMessage] = []
    @State private var draft = ""
    @State private var isStreaming = false
    @FocusState private var inputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            if messages.isEmpty {
                emptyState
            } else {
                transcript
            }
            inputBar
        }
        .background(.background)
        .navigationTitle("Chat")
        .onAppear {
            inputFocused = true
        }
    }

    private var emptyState: some View {
        VStack(spacing: 14) {
            Spacer()
            LogoMarkView(size: 44, color: .omniAccent.opacity(0.9))
            Text("Ask OmniDev anything")
                .font(.title3.weight(.semibold))
            Text(manager.aiModel.isEmpty
                 ? "Streams from the local engine — nothing leaves your Mac."
                 : "Streams from \(manager.aiModel) — nothing leaves your Mac.")
                .font(.callout)
                .foregroundStyle(.secondary)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var transcript: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 14) {
                    ForEach(messages) { message in
                        ChatBubble(message: message)
                            .id(message.id)
                    }
                }
                .padding(20)
            }
            .onChange(of: messages.last?.text) { _ in
                if let last = messages.last {
                    proxy.scrollTo(last.id, anchor: .bottom)
                }
            }
        }
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("Message the local model…", text: $draft, axis: .vertical)
                .textFieldStyle(.plain)
                .lineLimit(1...5)
                .focused($inputFocused)
                .onSubmit(send)

            Button(action: send) {
                Image(systemName: isStreaming ? "stop.circle.fill" : "arrow.up.circle.fill")
                    .font(.system(size: 24))
                    .foregroundStyle(canSend || isStreaming ? Color.omniAccent : Color.secondary)
            }
            .buttonStyle(.plain)
            .disabled(!canSend && !isStreaming)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(.regularMaterial)
        .overlay(alignment: .top) {
            Divider()
        }
    }

    private var canSend: Bool {
        !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isStreaming
    }

    @State private var activeStream: Task<Void, Never>?

    private func send() {
        if isStreaming {
            activeStream?.cancel()
            isStreaming = false
            return
        }
        let prompt = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else { return }
        draft = ""
        messages.append(ChatMessage(role: .user, text: prompt))
        messages.append(ChatMessage(role: .assistant, text: ""))
        isStreaming = true

        let client = manager.backendClient
        activeStream = Task {
            do {
                for try await delta in client.chatStream(message: prompt) {
                    messages[messages.count - 1].text += delta
                }
            } catch is CancellationError {
                // Stopped by the user; keep the partial answer.
            } catch {
                if messages[messages.count - 1].text.isEmpty {
                    messages[messages.count - 1].text = "⚠︎ \(error.localizedDescription)"
                    messages[messages.count - 1].isError = true
                }
            }
            isStreaming = false
        }
    }
}

struct ChatMessage: Identifiable {
    enum Role {
        case user
        case assistant
    }

    let id = UUID()
    let role: Role
    var text: String
    var isError = false
}

private struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 60) }

            VStack(alignment: .leading, spacing: 0) {
                if message.text.isEmpty && message.role == .assistant {
                    ProgressView()
                        .controlSize(.small)
                        .padding(4)
                } else {
                    Text(message.text)
                        .font(.body)
                        .foregroundStyle(message.isError ? AnyShapeStyle(.orange) : AnyShapeStyle(.primary))
                        .textSelection(.enabled)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(
                message.role == .user
                    ? AnyShapeStyle(Color.omniAccent.opacity(0.22))
                    : AnyShapeStyle(.regularMaterial),
                in: RoundedRectangle(cornerRadius: 12, style: .continuous)
            )

            if message.role == .assistant { Spacer(minLength: 60) }
        }
    }
}
