import SwiftUI

/// Native streaming chat against the local model. Tokens render live from
/// `POST /api/chat/stream`. Conversations persist via SQLite sessions, and
/// the model can call MCP tools when the Tools toggle is on.
///
/// With the Agent toggle on the prompt runs through `POST /api/agent/stream`
/// instead: a plan/act loop that reads and edits files in your workspaces and
/// asks permission for anything outside them.
/// Conversation state lives here rather than in the view, because SwiftUI
/// destroys a detail view's @State the moment you navigate to another page.
/// Losing a transcript (and cancelling a running generation) just because the
/// user pressed Cmd-1 to glance at the Command Center is unacceptable when a
/// local model can take a minute to answer.
@MainActor
final class ChatStore: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var draft = ""
    @Published var isStreaming = false
    @Published var pendingApproval: BackendClient.AgentApproval?
    @Published var toolsEnabled = false
    @Published var knowledgeEnabled = false
    @Published var agentEnabled = false

    var sessionId: String?
    var activeStream: Task<Void, Never>?

    func reset() {
        activeStream?.cancel()
        activeStream = nil
        isStreaming = false
        messages = []
        sessionId = nil
        pendingApproval = nil
    }

    /// Index of the trailing (in-progress) assistant message.
    func answerIndex() -> Int? {
        messages.lastIndex { $0.role == .assistant }
    }

    func appendToAnswer(_ delta: String) {
        if let index = answerIndex() {
            messages[index].text += delta
        }
    }

    func insertBeforeAnswer(_ message: ChatMessage) {
        if let index = answerIndex() {
            messages.insert(message, at: index)
        } else {
            messages.append(message)
        }
    }

    func failAnswer(_ description: String) {
        if let index = answerIndex(), messages[index].text.isEmpty {
            messages[index].text = "⚠︎ \(description)"
            messages[index].isError = true
        }
    }
}

struct ChatView: View {
    @ObservedObject var manager: LocalStackManager
    @ObservedObject var store: ChatStore
    @FocusState private var inputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            if store.messages.isEmpty {
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
                .disabled(store.messages.isEmpty)
            }
        }
        .onAppear {
            inputFocused = true
        }
        .sheet(item: $store.pendingApproval) { approval in
            ApprovalSheet(approval: approval) { decision in
                let client = manager.backendClient
                store.pendingApproval = nil
                Task { try? await client.resolveApproval(id: approval.id, decision: decision) }
            }
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
            Text(store.agentEnabled
                 ? "Agent mode: it reads and edits files in your workspaces, and asks before anything else."
                 : "Conversations are remembered, so follow-ups like “now add auth” work.")
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
                    ForEach(store.messages) { message in
                        ChatBubble(message: message)
                            .id(message.id)
                    }
                }
                .padding(20)
            }
            .onChange(of: store.messages.last?.text) { _ in
                if let last = store.messages.last {
                    proxy.scrollTo(last.id, anchor: .bottom)
                }
            }
        }
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            Toggle(isOn: $store.toolsEnabled) {
                Image(systemName: "wrench.and.screwdriver")
            }
            .toggleStyle(.button)
            .help("Let the model call tools from enabled MCP servers")

            Toggle(isOn: $store.knowledgeEnabled) {
                Image(systemName: "books.vertical")
            }
            .toggleStyle(.button)
            .help("Ground answers in your local knowledge index (cites files)")

            Toggle(isOn: $store.agentEnabled) {
                Image(systemName: "wand.and.rays")
            }
            .toggleStyle(.button)
            .disabled(store.isStreaming)
            .help("Agent mode: let the model read, edit and verify files step by step")

            TextField(store.agentEnabled ? "Give the agent a task…" : "Message the local model…",
                      text: $store.draft, axis: .vertical)
                .textFieldStyle(.plain)
                .lineLimit(1...5)
                .focused($inputFocused)
                .onSubmit(send)

            Button(action: send) {
                Image(systemName: store.isStreaming ? "stop.circle.fill" : "arrow.up.circle.fill")
                    .font(.system(size: 24))
                    .foregroundStyle(canSend || store.isStreaming ? Color.omniAccent : Color.secondary)
            }
            .buttonStyle(.plain)
            .disabled(!canSend && !store.isStreaming)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(.regularMaterial)
        .overlay(alignment: .top) {
            Divider()
        }
    }

    private var canSend: Bool {
        !store.draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !store.isStreaming
    }

    private func newChat() {
        store.reset()
    }

    private func send() {
        if store.isStreaming {
            store.activeStream?.cancel()
            store.isStreaming = false
            return
        }
        let prompt = store.draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !prompt.isEmpty else { return }
        store.draft = ""
        store.messages.append(ChatMessage(role: .user, text: prompt))
        store.messages.append(ChatMessage(role: .assistant, text: ""))
        store.isStreaming = true

        if store.agentEnabled {
            runAgent(task: prompt)
            return
        }

        let client = manager.backendClient
        let currentSession = store.sessionId
        let useTools = store.toolsEnabled
        let useKnowledge = store.knowledgeEnabled
        store.activeStream = Task {
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
                        store.sessionId = id
                    case .delta(let delta):
                        store.appendToAnswer(delta)
                    case .knowledge(let citedFiles):
                        guard !citedFiles.isEmpty else { break }
                        let names = citedFiles
                            .map { ($0 as NSString).abbreviatingWithTildeInPath }
                            .joined(separator: "  ·  ")
                        store.insertBeforeAnswer(ChatMessage(role: .tool, text: "📚 \(names)"))
                    case .toolCall(let tool, let arguments):
                        store.insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: arguments.isEmpty || arguments == "{}"
                                ? "⚙ \(tool)" : "⚙ \(tool) \(arguments)"
                        ))
                    case .toolResult(let tool, let result):
                        store.insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: "→ \(tool): \(result.prefix(400))"
                        ))
                    }
                }
            } catch is CancellationError {
                // Stopped by the user; keep the partial answer.
            } catch {
                store.failAnswer(error.localizedDescription)
            }
            store.isStreaming = false
        }
    }

    /// Run the prompt as an agent task: steps and tool activity stream in as
    /// they happen, and approvals interrupt with a sheet.
    private func runAgent(task: String) {
        let client = manager.backendClient
        let useMCP = store.toolsEnabled
        store.activeStream = Task {
            do {
                for try await event in client.agentStream(task: task, useMCP: useMCP) {
                    switch event {
                    case .started(let model, let workspaces, let tools):
                        let where_ = workspaces.isEmpty
                            ? "no workspaces yet"
                            : "\(workspaces.count) workspace\(workspaces.count == 1 ? "" : "s")"
                        store.insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: "🤖 agent on \(model.isEmpty ? "local model" : model) · "
                                + "\(where_) · \(tools.count) tools"
                        ))
                    case .step(let number, let thought):
                        let trimmed = thought.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !trimmed.isEmpty else { break }
                        store.insertBeforeAnswer(ChatMessage(role: .tool, text: "① step \(number): \(trimmed)"))
                    case .checkpoint(let repo, let head, let dirty):
                        store.insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: "⎇ \((repo as NSString).lastPathComponent) at \(head)"
                                + (dirty ? " (uncommitted changes present)" : "")
                        ))
                    case .toolCall(let tool, let arguments):
                        store.insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: arguments.isEmpty || arguments == "{}"
                                ? "⚙ \(tool)" : "⚙ \(tool) \(arguments.prefix(300))"
                        ))
                    case .toolResult(let tool, let result, let ok):
                        var message = ChatMessage(
                            role: .tool,
                            text: "\(ok ? "→" : "✗") \(tool): \(result.prefix(400))"
                        )
                        message.isError = !ok
                        store.insertBeforeAnswer(message)
                    case .approvalRequired(let approval):
                        store.pendingApproval = approval
                    case .approvalResolved(let id, let decision):
                        if store.pendingApproval?.id == id { store.pendingApproval = nil }
                        store.insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: decision == "deny" ? "🚫 denied" : "✓ approved (\(decision))"
                        ))
                    case .delta(let delta):
                        store.appendToAnswer(delta)
                    }
                }
            } catch is CancellationError {
                store.pendingApproval = nil
            } catch {
                store.pendingApproval = nil
                store.failAnswer(error.localizedDescription)
            }
            store.isStreaming = false
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

/// Native permission prompt for an agent action outside a workspace, or for
/// any shell command. Deny is the default: closing the sheet without a choice
/// leaves the run waiting, and the backend denies on timeout.
private struct ApprovalSheet: View {
    let approval: BackendClient.AgentApproval
    let onDecision: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 10) {
                Image(systemName: "hand.raised.fill")
                    .font(.title2)
                    .foregroundStyle(Color.omniAccent)
                VStack(alignment: .leading, spacing: 2) {
                    Text("The agent wants permission")
                        .font(.headline)
                    Text(approval.tool)
                        .font(.caption.monospaced())
                        .foregroundStyle(.secondary)
                }
            }

            Text(approval.summary)
                .font(.body.weight(.medium))
                .textSelection(.enabled)
                .fixedSize(horizontal: false, vertical: true)

            if !approval.detail.isEmpty {
                ScrollView {
                    Text(approval.detail)
                        .font(.caption.monospaced())
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                }
                .frame(maxHeight: 220)
                .background(.quaternary.opacity(0.4),
                            in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            }

            HStack {
                Button("Deny") { onDecision("deny") }
                    .keyboardShortcut(.cancelAction)
                Spacer()
                Button("Always Allow") { onDecision("allow_always") }
                    .help("Allow this kind of action for the rest of this task")
                Button("Allow Once") { onDecision("allow_once") }
                    .keyboardShortcut(.defaultAction)
            }
        }
        .padding(20)
        .frame(width: 520)
    }
}
