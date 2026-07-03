import SwiftUI

struct ContentView: View {
    @ObservedObject var manager: LocalStackManager
    @State private var selectedRoute: OmniDevRoute = .cockpit
    @State private var webLoading = false

    var body: some View {
        NavigationSplitView {
            SidebarView(selectedRoute: $selectedRoute, manager: manager)
                .navigationSplitViewColumnWidth(min: 230, ideal: 250, max: 290)
        } detail: {
            ZStack {
                WebCockpitView(url: manager.pageURL(for: selectedRoute), isLoading: $webLoading)
                    .opacity(manager.frontendReady ? 1 : 0)

                if !manager.frontendReady {
                    StartingView(manager: manager)
                }
            }
            .background(.background)
            .toolbar {
                ToolbarItemGroup {
                    if webLoading {
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
    }
}
