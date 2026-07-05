import AppKit
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    weak var stackManager: LocalStackManager?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)

        // Brand the Dock even for bare `swift run` builds without an .icns.
        if let iconURL = Bundle.module.url(forResource: "AppIcon", withExtension: "png"),
           let icon = NSImage(contentsOf: iconURL) {
            NSApp.applicationIconImage = icon
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        stackManager?.stopServicesSync()
    }
}

@main
struct OmniDevMacApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var stackManager = LocalStackManager()

    var body: some Scene {
        WindowGroup("OmniDev", id: "main") {
            ContentView(manager: stackManager)
                .frame(minWidth: 1080, minHeight: 720)
                .onAppear {
                    appDelegate.stackManager = stackManager
                    stackManager.startServicesIfNeeded()
                }
        }
        .commands {
            CommandMenu("OmniDev") {
                Button("Restart Local Services") {
                    stackManager.restartServices()
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])

                Button("Open Logs") {
                    stackManager.openLogs()
                }
                .keyboardShortcut("l", modifiers: [.command, .shift])

                Divider()

                Button("Setup Assistant…") {
                    NotificationCenter.default.post(name: .omniDevShowOnboarding, object: nil)
                }

                Button("Check for Updates…") {
                    Task { await UpdateChecker.checkForUpdates() }
                }

                Divider()

                Button("Open API Docs") {
                    stackManager.openAPIDocs()
                }
                .keyboardShortcut("b", modifiers: [.command, .shift])
            }
        }

        Settings {
            SettingsView(manager: stackManager)
        }

        MenuBarExtra {
            MenuBarContent(manager: stackManager)
        } label: {
            // square.inset.filled mirrors the LogoMark's nested-enclosure shape.
            Image(systemName: "square.inset.filled")
        }
    }
}

private struct MenuBarContent: View {
    @ObservedObject var manager: LocalStackManager
    @Environment(\.openWindow) private var openWindow

    var body: some View {
        Label(statusLine, systemImage: manager.state.systemImage)
        if !manager.aiModel.isEmpty {
            Text(modelLine)
        }

        Divider()

        Button("Open OmniDev") {
            openWindow(id: "main")
            NSApp.activate(ignoringOtherApps: true)
        }

        Button("Restart Local Services") {
            manager.restartServices()
        }

        Button("Open Logs") {
            manager.openLogs()
        }

        Divider()

        Button("Check for Updates…") {
            Task { await UpdateChecker.checkForUpdates() }
        }

        Button("Quit OmniDev") {
            NSApp.terminate(nil)
        }
    }

    private var statusLine: String {
        "Engine: \(manager.state.title)"
    }

    private var modelLine: String {
        manager.aiProvider == "ollama"
            ? "\(manager.aiModel) · local"
            : "\(manager.aiModel) · \(manager.aiProvider)"
    }
}
