import SwiftUI

struct ContentView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var selectedRoute: OmniDevRoute = .cockpit
    @State private var webLoading = false
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
                        if webLoading && !selectedRoute.isNative {
                            ProgressView()
                                .controlSize(.small)
                        }

                        Button {
                            manager.restartServices()
                        } label: {
                            Label("Restart", systemImage: "arrow.clockwise")
                        }

                        Button {
                            manager.openInBrowser(path: selectedRoute.path)
                        } label: {
                            Label("Open in Browser", systemImage: "safari")
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
        switch selectedRoute {
        case .cockpit:
            CockpitView(manager: manager, selectedRoute: $selectedRoute)
        case .chat:
            ChatView(manager: manager)
        default:
            ZStack {
                WebCockpitView(url: manager.pageURL(for: selectedRoute), isLoading: $webLoading)
                    .opacity(manager.frontendReady ? 1 : 0)

                if !manager.frontendReady {
                    StartingView(manager: manager)
                }
            }
        }
    }
}

extension Notification.Name {
    /// Posted by the menu bar / app menu to reopen the setup assistant.
    static let omniDevShowOnboarding = Notification.Name("omniDevShowOnboarding")
}
