import SwiftUI

/// Native DevOps agent: natural-language AWS commands with the enriched
/// plan preview and explicit confirmation for destructive actions.
struct DevOpsView: View {
    @ObservedObject var manager: LocalStackManager
    @StateObject private var run = ModuleRun<BackendClient.DevOpsResult>()
    @State private var command = ""

    private static let examples = [
        "List my EC2 instances",
        "Show my S3 buckets",
        "List Lambda functions",
        "Show CloudWatch alarms in ALARM state",
        "Who am I? (STS caller identity)",
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ModuleHeader(
                    title: "DevOps Agent",
                    subtitle: "Natural language → boto3 plan → human-approved execution."
                )

                ModuleCard {
                    HStack(spacing: 10) {
                        TextField("e.g. List my EC2 instances", text: $command)
                            .textFieldStyle(.roundedBorder)
                            .onSubmit { execute(confirm: false) }

                        Menu("Examples") {
                            ForEach(Self.examples, id: \.self) { example in
                                Button(example) { command = example }
                            }
                        }
                        .frame(width: 110)

                        Button {
                            execute(confirm: false)
                        } label: {
                            if run.isRunning {
                                ProgressView().controlSize(.small)
                            } else {
                                Text("Run")
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.omniAccent)
                        .disabled(command.trimmingCharacters(in: .whitespaces).isEmpty || run.isRunning)
                    }
                }

                if let error = run.error {
                    ErrorBanner(message: error)
                }

                if let result = run.output {
                    if let plan = result.plan {
                        planCard(plan, needsConfirmation: result.needsConfirmation)
                    }
                    ModuleCard(title: "Summary") {
                        Text(result.summary)
                            .font(.callout)
                            .textSelection(.enabled)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("DevOps Agent")
    }

    private func planCard(_ plan: BackendClient.DevOpsPlan, needsConfirmation: Bool) -> some View {
        ModuleCard(title: "Plan Preview") {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    TagView(text: plan.service.uppercased(), color: .omniAccent)
                    TagView(text: plan.operation, color: .secondary)
                    TagView(
                        text: plan.destructive ? "DESTRUCTIVE" : "READ-ONLY",
                        color: plan.destructive ? .orange : .green
                    )
                }

                if let impact = plan.impact {
                    Text(impact)
                        .font(.callout)
                        .foregroundStyle(plan.destructive ? .orange : .secondary)
                }

                if let params = plan.params, !params.isEmpty {
                    ForEach(params.keys.sorted(), id: \.self) { key in
                        HStack(alignment: .top) {
                            Text(key)
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                            Text(params[key]?.display ?? "—")
                                .font(.caption.monospaced())
                                .textSelection(.enabled)
                        }
                    }
                }

                if needsConfirmation {
                    Divider()
                    HStack {
                        Label("This action changes AWS resources.", systemImage: "hand.raised.fill")
                            .font(.callout)
                            .foregroundStyle(.orange)
                        Spacer()
                        Button("Confirm & Execute") {
                            execute(confirm: true)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.orange)
                        .disabled(run.isRunning)
                    }
                }
            }
        }
    }

    private func execute(confirm: Bool) {
        let message = command.trimmingCharacters(in: .whitespaces)
        guard !message.isEmpty else { return }
        let client = manager.backendClient
        run.run {
            try await client.devopsCommand(message, confirmDestructive: confirm)
        }
    }
}

struct TagView: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold).monospaced())
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.16), in: Capsule())
            .foregroundStyle(color)
    }
}
