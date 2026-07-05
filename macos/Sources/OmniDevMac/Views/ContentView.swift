import SwiftUI

struct ContentView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var selectedRoute: OmniDevRoute = .cockpit
    @State private var showOnboarding = false
    @AppStorage(AppSettings.onboardingCompletedKey) private var onboardingCompleted = false

    var body: some View {
        NavigationSplitView {
            SidebarView(selectedRoute: $selectedRoute, manager: manager)
                .navigationSplitViewColumnWidth(min: 230, ideal: 250, max: 290)
        } detail: {
            detail
                .background(.background)
                .toolbar {
                    ToolbarItemGroup {
                        Button {
                            manager.restartServices()
                        } label: {
                            Label("Restart", systemImage: "arrow.clockwise")
                        }

                        Button {
                            manager.openAPIDocs()
                        } label: {
                            Label("API Docs", systemImage: "doc.text.magnifyingglass")
                        }
                    }
                }
        }
        .sheet(isPresented: $showOnboarding, onDismiss: {
            onboardingCompleted = true
        }) {
            OnboardingView(manager: manager)
        }
        .onChange(of: manager.backendHealthy) { healthy in
            if healthy && !onboardingCompleted {
                showOnboarding = true
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .omniDevShowOnboarding)) { _ in
            showOnboarding = true
        }
    }

    @ViewBuilder
    private var detail: some View {
        if !manager.backendHealthy && selectedRoute != .cockpit {
            StartingView(manager: manager)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else {
            switch selectedRoute {
            case .cockpit:
                CockpitView(manager: manager, selectedRoute: $selectedRoute)
            case .chat:
                ChatView(manager: manager)
            case .devops:
                DevOpsView(manager: manager)
            case .codegen:
                CodeGenView(manager: manager)
            case .scraper:
                ScraperView(manager: manager)
            case .vision:
                VisionView(manager: manager)
            case .storage:
                StorageView(manager: manager)
            case .mcp:
                MCPMarketplaceView(manager: manager)
            }
        }
    }
}

extension Notification.Name {
    /// Posted by the menu bar / app menu to reopen the setup assistant.
    static let omniDevShowOnboarding = Notification.Name("omniDevShowOnboarding")
}
