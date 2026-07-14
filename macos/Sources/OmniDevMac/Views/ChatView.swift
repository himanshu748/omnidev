import SwiftUI

/// Native streaming chat against the local model — tokens render live from
/// `POST /api/chat/stream`. Conversations persist via SQLite sessions, and
/// the model can call MCP tools when the Tools toggle is on.
struct ChatView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var messages: [ChatMessage] = []
    @State private var draft = ""
    @State private var isStreaming = false
    @State private var sessionId: String?
    @State private var toolsEnabled = false
    @State private var knowledgeEnabled = false
    @State private var activeStream: Task<Void, Never>?
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
        .navigationSubtitle(manager.aiModel.isEmpty ? "Local model" : manager.aiModel)
        .toolbar {
            ToolbarItem {
                Button {
                    newChat()
                } label: {
                    Label("New Chat", systemImage: "square.and.pencil")
                }
                .disabled(messages.isEmpty)
            }
        }
        .onAppear {
            inputFocused = true
        }
    }

    private var emptyState: some View {
        VStack(spacing: 14) {
            Spacer()
            LogoMarkView(size: 44)
            Text("Ask OmniDev anything")
                .font(.title3.weight(.semibold))
            Text(manager.aiModel.isEmpty
                 ? "Streams from the local engine — nothing leaves your Mac."
                 : "Streams from \(manager.aiModel) — nothing leaves your Mac.")
                .font(.callout)
                .foregroundStyle(.secondary)
            Text("Conversations are remembered, so follow-ups like “now add auth” work.")
                .font(.caption)
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
            Toggle(isOn: $toolsEnabled) {
                Image(systemName: "wrench.and.screwdriver")
            }
            .toggleStyle(.button)
            .help("Let the model call tools from enabled MCP servers")

            Toggle(isOn: $knowledgeEnabled) {
                Image(systemName: "books.vertical")
            }
            .toggleStyle(.button)
            .help("Ground answers in your local knowledge index (cites files)")

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

    private func newChat() {
        activeStream?.cancel()
        isStreaming = false
        messages = []
        sessionId = nil
    }

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
        let currentSession = sessionId
        let useTools = toolsEnabled
        let useKnowledge = knowledgeEnabled
        activeStream = Task {
            do {
                let stream = client.chatStream(
                    message: prompt,
                    sessionId: currentSession,
                    useTools: useTools,
                    useKnowledge: useKnowledge
                )
                for try await event in stream {
                    switch event {
                    case .sessionId(let id):
                        sessionId = id
                    case .delta(let delta):
                        appendToAnswer(delta)
                    case .knowledge(let citedFiles):
                        guard !citedFiles.isEmpty else { break }
                        let names = citedFiles
                            .map { ($0 as NSString).abbreviatingWithTildeInPath }
                            .joined(separator: "  ·  ")
                        insertBeforeAnswer(ChatMessage(role: .tool, text: "📚 \(names)"))
                    case .toolCall(let tool, let arguments):
                        insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: arguments.isEmpty || arguments == "{}"
                                ? "⚙ \(tool)" : "⚙ \(tool) \(arguments)"
                        ))
                    case .toolResult(let tool, let result):
                        insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: "→ \(tool): \(result.prefix(400))"
                        ))
                    }
                }
            } catch is CancellationError {
                // Stopped by the user; keep the partial answer.
            } catch {
                if let index = answerIndex(), messages[index].text.isEmpty {
                    messages[index].text = "⚠︎ \(error.localizedDescription)"
                    messages[index].isError = true
                }
            }
            isStreaming = false
        }
    }

    /// Index of the trailing (in-progress) assistant message.
    private func answerIndex() -> Int? {
        messages.lastIndex { $0.role == .assistant }
    }

    private func appendToAnswer(_ delta: String) {
        if let index = answerIndex() {
            messages[index].text += delta
        }
    }

    private func insertBeforeAnswer(_ message: ChatMessage) {
        if let index = answerIndex() {
            messages.insert(message, at: index)
        } else {
            messages.append(message)
        }
    }
}

struct ChatMessage: Identifiable {
    enum Role {
        case user
        case assistant
        case tool
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
                        .font(message.role == .tool ? .caption.monospaced() : .body)
                        .foregroundStyle(bubbleForeground)
                        .textSelection(.enabled)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(.horizontal, message.role == .tool ? 10 : 14)
            .padding(.vertical, message.role == .tool ? 6 : 10)
            .background(bubbleBackground, in: RoundedRectangle(cornerRadius: 12, style: .continuous))

            if message.role != .user { Spacer(minLength: 60) }
        }
    }

    private var bubbleForeground: AnyShapeStyle {
        if message.isError { return AnyShapeStyle(.orange) }
        if message.role == .tool { return AnyShapeStyle(.secondary) }
        return AnyShapeStyle(.primary)
    }

    private var bubbleBackground: AnyShapeStyle {
        switch message.role {
        case .user:
            return AnyShapeStyle(Color.omniAccent.opacity(0.22))
        case .assistant:
            return AnyShapeStyle(.regularMaterial)
        case .tool:
            return AnyShapeStyle(.quaternary.opacity(0.5))
        }
    }
}
