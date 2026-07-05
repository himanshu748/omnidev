import SwiftUI

struct SidebarView: View {
    @Binding var selectedRoute: OmniDevRoute
    @ObservedObject var manager: LocalStackManager

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 10) {
                LogoMarkView(size: 38)

                VStack(alignment: .leading, spacing: 1) {
                    Text("OmniDev")
                        .font(.headline)
                    Text("Local-first AI cockpit")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.top, 6)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("Feature Agents")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)

                ForEach(OmniDevRoute.allCases) { route in
                    Button {
                        selectedRoute = route
                    } label: {
                        HStack(spacing: 10) {
                            Image(systemName: route.systemImage)
                                .frame(width: 20)
                            VStack(alignment: .leading, spacing: 1) {
                                Text(route.title)
                                    .font(.subheadline)
                                Text(route.subtitle)
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                        }
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .padding(.vertical, 7)
                    .padding(.horizontal, 8)
                    .background(
                        selectedRoute == route
                            ? AnyShapeStyle(.selection.opacity(0.24))
                            : AnyShapeStyle(.clear),
                        in: RoundedRectangle(cornerRadius: 8, style: .continuous)
                    )
                }
            }

            Spacer()

            VStack(alignment: .leading, spacing: 10) {
                Label(manager.state.title, systemImage: manager.state.systemImage)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(manager.state == .ready ? .green : .primary)

                Text(manager.message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                HStack {
                    StatusPill(title: "API", isReady: manager.backendHealthy)
                    StatusPill(title: "UI", isReady: manager.frontendReady)
                }

                HStack {
                    Button("Restart") {
                        manager.restartServices()
                    }
                    Button("Logs") {
                        manager.openLogs()
                    }
                }
                .buttonStyle(.bordered)
            }
            .padding(12)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
        }
        .padding(14)
    }
}

private struct StatusPill: View {
    let title: String
    let isReady: Bool

    var body: some View {
        HStack(spacing: 5) {
            Circle()
                .fill(isReady ? .green : .orange)
                .frame(width: 7, height: 7)
            Text(title)
                .font(.caption.weight(.semibold))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 5)
        .background(.thinMaterial, in: Capsule())
    }
}
