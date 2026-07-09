import SwiftUI

/// Native web scraper: SSRF-guarded extraction in every mode the backend
/// supports, plus the bounded same-domain crawl.
struct ScraperView: View {
    @ObservedObject var manager: LocalStackManager
    @StateObject private var scrapeRun = ModuleRun<BackendClient.ScrapeResult>()
    @StateObject private var crawlRun = ModuleRun<BackendClient.CrawlResult>()
    @State private var url = ""
    @State private var extract = "markdown"
    @State private var mode: Mode = .scrape
    @State private var maxPages = 5
    @State private var maxDepth = 1

    enum Mode: String, CaseIterable {
        case scrape = "Scrape"
        case crawl = "Crawl"
    }

    private static let extractModes = [
        "markdown", "text", "article", "links", "metadata", "html", "screenshot", "pdf",
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ModuleCard {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(spacing: 10) {
                            TextField("https://example.com", text: $url)
                                .textFieldStyle(.roundedBorder)
                                .onSubmit(execute)

                            Picker("", selection: $mode) {
                                ForEach(Mode.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                            }
                            .pickerStyle(.segmented)
                            .frame(width: 160)

                            Button {
                                execute()
                            } label: {
                                if isRunning {
                                    ProgressView().controlSize(.small)
                                } else {
                                    Text("Run")
                                }
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.omniAccent)
                            .disabled(url.trimmingCharacters(in: .whitespaces).isEmpty || isRunning)
                        }

                        if mode == .scrape {
                            Picker("Extract", selection: $extract) {
                                ForEach(Self.extractModes, id: \.self) { Text($0).tag($0) }
                            }
                            .frame(width: 260)
                        } else {
                            HStack(spacing: 18) {
                                Stepper("Max pages: \(maxPages)", value: $maxPages, in: 1...10)
                                Stepper("Max depth: \(maxDepth)", value: $maxDepth, in: 0...2)
                            }
                            .font(.callout)
                        }
                    }
                }

                if let error = scrapeRun.error ?? crawlRun.error {
                    ErrorBanner(message: error)
                }

                if mode == .scrape, let result = scrapeRun.output {
                    scrapeResult(result)
                } else if mode == .crawl, let result = crawlRun.output {
                    crawlResult(result)
                }
            }
            .padding(22)
        }
        .background(.background)
        .navigationTitle("Web Scraper")
        .navigationSubtitle("Playwright extraction with an SSRF guard on every navigation.")
    }

    private var isRunning: Bool { scrapeRun.isRunning || crawlRun.isRunning }

    @ViewBuilder
    private func scrapeResult(_ result: BackendClient.ScrapeResult) -> some View {
        ModuleCard(title: result.title.isEmpty ? result.url : result.title) {
            if let base64 = result.screenshotB64,
               let data = Data(base64Encoded: base64),
               let image = NSImage(data: data) {
                ScrollView {
                    Image(nsImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                }
                .frame(maxHeight: 480)
            } else if let base64 = result.pdfB64 {
                Button("Save PDF…") {
                    savePDF(base64: base64)
                }
            } else if let links = result.links {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(links.prefix(80)) { link in
                        HStack(spacing: 8) {
                            Image(systemName: (link.isExternal ?? false) ? "arrow.up.right.square" : "link")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(link.text.isEmpty ? link.href : link.text)
                                .font(.caption)
                                .lineLimit(1)
                            Text(link.href)
                                .font(.caption2.monospaced())
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                                .textSelection(.enabled)
                        }
                    }
                }
            } else if let metadata = result.metadata {
                VStack(alignment: .leading, spacing: 6) {
                    metaRow("Title", metadata.title)
                    metaRow("Description", metadata.description)
                    metaRow("Canonical", metadata.canonical)
                    metaRow("Language", metadata.language)
                    metaRow("Words", String(metadata.wordCount))
                    metaRow("H1", metadata.h1Tags.joined(separator: " · "))
                }
            } else if let article = result.article {
                VStack(alignment: .leading, spacing: 8) {
                    if !article.byline.isEmpty {
                        Text(article.byline)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    MonoResult(text: article.text, maxHeight: 460)
                }
            } else {
                MonoResult(text: result.markdown ?? result.content, maxHeight: 460)
            }
        }
    }

    private func crawlResult(_ result: BackendClient.CrawlResult) -> some View {
        ModuleCard(title: "\(result.pagesCrawled) pages on \(result.domain)") {
            VStack(alignment: .leading, spacing: 10) {
                ForEach(result.pages) { page in
                    VStack(alignment: .leading, spacing: 2) {
                        HStack(spacing: 8) {
                            TagView(text: "depth \(page.depth)", color: .secondary)
                            Text(page.title.isEmpty ? page.url : page.title)
                                .font(.callout.weight(.medium))
                                .lineLimit(1)
                        }
                        Text(page.excerpt)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                }
            }
        }
    }

    private func metaRow(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text(label)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 90, alignment: .leading)
            Text(value.isEmpty ? "—" : value)
                .font(.caption)
                .textSelection(.enabled)
        }
    }

    private func execute() {
        let target = url.trimmingCharacters(in: .whitespaces)
        guard !target.isEmpty else { return }
        let client = manager.backendClient
        if mode == .scrape {
            let extract = extract
            scrapeRun.run {
                try await client.scrape(url: target, extract: extract)
            }
        } else {
            let pages = maxPages
            let depth = maxDepth
            crawlRun.run {
                try await client.crawl(url: target, maxPages: pages, maxDepth: depth)
            }
        }
    }

    private func savePDF(base64: String) {
        guard let data = Data(base64Encoded: base64) else { return }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "scrape.pdf"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        try? data.write(to: url)
    }
}
