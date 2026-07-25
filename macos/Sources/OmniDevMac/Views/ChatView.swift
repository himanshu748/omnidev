import SwiftUI

/// Native streaming chat against the local model. Tokens render live from
/// `POST /api/chat/stream`. Conversations persist via SQLite sessions, and
/// the model can call MCP tools when the Tools toggle is on.
///
/// With the Agent toggle on the prompt runs through `POST /api/agent/stream`
/// instead: a plan/act loop that reads and edits files in your workspaces and
/// asks permission for anything outside them.
struct ChatView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var messages: [ChatMessage] = []
    @State private var draft = ""
    @State private var isStreaming = false
    @State private var sessionId: String?
    @State private var toolsEnabled = false
    @State private var knowledgeEnabled = false
    @State private var agentEnabled = false
    @State private var pendingApproval: BackendClient.AgentApproval?
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
        .sheet(item: $pendingApproval) { approval in
            ApprovalSheet(approval: approval) { decision in
                let client = manager.backendClient
                pendingApproval = nil
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
            Text(agentEnabled
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

            Toggle(isOn: $agentEnabled) {
                Image(systemName: "wand.and.rays")
            }
            .toggleStyle(.button)
            .disabled(isStreaming)
            .help("Agent mode: let the model read, edit and verify files step by step")

            TextField(agentEnabled ? "Give the agent a task…" : "Message the local model…",
                      text: $draft, axis: .vertical)
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

        if agentEnabled {
            runAgent(task: prompt)
            return
        }

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

    /// Run the prompt as an agent task: steps and tool activity stream in as
    /// they happen, and approvals interrupt with a sheet.
    private func runAgent(task: String) {
        let client = manager.backendClient
        let useMCP = toolsEnabled
        activeStream = Task {
            do {
                for try await event in client.agentStream(task: task, useMCP: useMCP) {
                    switch event {
                    case .started(let model, let workspaces, let tools):
                        let where_ = workspaces.isEmpty
                            ? "no workspaces yet"
                            : "\(workspaces.count) workspace\(workspaces.count == 1 ? "" : "s")"
                        insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: "🤖 agent on \(model.isEmpty ? "local model" : model) · "
                                + "\(where_) · \(tools.count) tools"
                        ))
                    case .step(let number, let thought):
                        let trimmed = thought.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !trimmed.isEmpty else { break }
                        insertBeforeAnswer(ChatMessage(role: .tool, text: "① step \(number): \(trimmed)"))
                    case .checkpoint(let repo, let head, let dirty):
                        insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: "⎇ \((repo as NSString).lastPathComponent) at \(head)"
                                + (dirty ? " (uncommitted changes present)" : "")
                        ))
                    case .toolCall(let tool, let arguments):
                        insertBeforeAnswer(ChatMessage(
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
                        insertBeforeAnswer(message)
                    case .approvalRequired(let approval):
                        pendingApproval = approval
                    case .approvalResolved(let id, let decision):
                        if pendingApproval?.id == id { pendingApproval = nil }
                        insertBeforeAnswer(ChatMessage(
                            role: .tool,
                            text: decision == "deny" ? "🚫 denied" : "✓ approved (\(decision))"
                        ))
                    case .delta(let delta):
                        appendToAnswer(delta)
                    }
                }
            } catch is CancellationError {
                pendingApproval = nil
            } catch {
                pendingApproval = nil
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
