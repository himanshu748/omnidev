import AppKit
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    weak var stackManager: LocalStackManager?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
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

                Button("Open Cockpit in Browser") {
                    stackManager.openInBrowser(path: "/app")
                }
                .keyboardShortcut("b", modifiers: [.command, .shift])
            }
        }
    }
}
