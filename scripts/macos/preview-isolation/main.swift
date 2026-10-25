// Loads untrusted HTML in a WKWebView configured like the Code Gen preview
// and makes it try to reach a loopback server through a hostname, an IP, and
// every common request type. Usage: preview-isolation <port> <filtered|unfiltered>
import AppKit
import WebKit

let arguments = CommandLine.arguments
guard arguments.count == 3, let port = Int(arguments[1]) else {
    FileHandle.standardError.write("usage: preview-isolation <port> <filtered|unfiltered>\n".data(using: .utf8)!)
    exit(2)
}
let filtered = arguments[2] == "filtered"

let html = """
<!doctype html><html><head></head><body>
<script>
const H = "http://preview.omnidev.test:\(port)";
const IP = "http://127.0.0.1:\(port)";
function img(url) {
  return new Promise(r => {
    const i = new Image();
    i.onload = () => r("loaded"); i.onerror = () => r("error");
    i.src = url; setTimeout(() => r("timeout"), 4000);
  });
}
async function run() {
  const frame = document.createElement("iframe"); frame.src = H + "/iframe"; document.body.appendChild(frame);
  const script = document.createElement("script"); script.src = H + "/script"; document.head.appendChild(script);
  const link = document.createElement("link"); link.rel = "stylesheet"; link.href = H + "/style"; document.head.appendChild(link);
  try { new WebSocket("ws://preview.omnidev.test:\(port)/ws"); } catch (e) {}
  try { navigator.sendBeacon(H + "/beacon", "x"); } catch (e) {}
  const results = {
    fetchHost: await fetch(H + "/fetch").then(() => "ok", () => "error"),
    fetchIP: await fetch(IP + "/fetch-ip").then(() => "ok", () => "error"),
    post: await fetch(H + "/api/agent/sandbox", {method: "POST", body: "{}"}).then(() => "ok", () => "error"),
    img: await img(H + "/img"),
    cdn: await fetch("https://cdn.jsdelivr.net/npm/left-pad@1.3.0/package.json")
      .then(r => r.ok ? "ok" : "status " + r.status, () => "error"),
  };
  setTimeout(() => webkit.messageHandlers.done.postMessage(JSON.stringify(results)), 2000);
}
run();
</script></body></html>
"""

final class Harness: NSObject, WKScriptMessageHandler {
    var webView: WKWebView?
    var window: NSWindow?

    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        print("results: \(message.body)")
        let body = (message.body as? String) ?? ""
        // In filtered mode the allowlisted CDN must still work.
        if filtered && !body.contains("\"cdn\":\"ok\"") {
            print("FAIL: allowlisted CDN fetch did not succeed")
            exit(1)
        }
        exit(0)
    }

    func start(rules: WKContentRuleList?) {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.userContentController.add(self, name: "done")
        if let rules { configuration.userContentController.add(rules) }
        let webView = WKWebView(frame: NSRect(x: 0, y: 0, width: 400, height: 300), configuration: configuration)
        let window = NSWindow(contentRect: webView.frame, styleMask: [.borderless], backing: .buffered, defer: false)
        window.contentView = webView
        window.orderBack(nil)
        self.webView = webView
        self.window = window
        webView.loadHTMLString(html, baseURL: nil)
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
let harness = Harness()

DispatchQueue.main.async {
    guard filtered else {
        harness.start(rules: nil)
        return
    }
    WKContentRuleListStore.default().compileContentRuleList(
        forIdentifier: PreviewNetworkPolicy.identifier,
        encodedContentRuleList: PreviewNetworkPolicy.contentRuleList
    ) { rules, error in
        guard let rules else {
            print("FAIL: rule list did not compile: \(String(describing: error))")
            exit(1)
        }
        harness.start(rules: rules)
    }
}
DispatchQueue.main.asyncAfter(deadline: .now() + 60) {
    print("FAIL: timed out")
    exit(1)
}
app.run()
