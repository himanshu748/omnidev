import SwiftUI

struct SidebarView: View {
    @Binding var selectedRoute: OmniDevRoute
    @ObservedObject var manager: LocalStackManager

    var body: some View {
        List(selection: $selectedRoute) {
            Section {
                ForEach([OmniDevRoute.cockpit, .chat]) { route in
                    Label(route.title, systemImage: route.systemImage)
                        .tag(route)
                }
            }

            Section("Feature Agents") {
                ForEach(OmniDevRoute.modules) { route in
                    Label(route.title, systemImage: route.systemImage)
                        .tag(route)
                }
            }
        }
        .listStyle(.sidebar)
        .safeAreaInset(edge: .bottom) {
            EngineStatusCard(manager: manager)
                .padding(10)
        }
    }
}

/// Compact engine health readout pinned under the sidebar list.
private struct EngineStatusCard: View {
    @ObservedObject var manager: LocalStackManager

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(manager.state.title, systemImage: manager.state.systemImage)
                .font(.caption.weight(.semibold))
                .foregroundStyle(manager.state == .ready ? AnyShapeStyle(.green) : AnyShapeStyle(.primary))

            if !manager.backendHealthy {
                Text(manager.message)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack(spacing: 5) {
                StatusPill(title: "API", isReady: manager.backendHealthy)
                if !manager.aiModel.isEmpty {
                    StatusPill(title: manager.aiModel, isReady: true)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

private struct StatusPill: View {
    let title: String
    let isReady: Bool

    var body: some View {
        HStack(spacing: 5) {
            Circle()
                .fill(isReady ? .green : .orange)
                .frame(width: 6, height: 6)
            Text(title)
                .font(.caption2.weight(.semibold))
                .lineLimit(1)
        }
        .padding(.horizontal, 7)
        .padding(.vertical, 4)
        .background(.thinMaterial, in: Capsule())
    }
}
