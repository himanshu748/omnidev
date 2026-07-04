"use client";

import "./scraper.css";
import { useState } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type LinkItem = {
  href: string;
  text: string;
  is_external: boolean;
};

type PageMetadata = {
  title: string;
  description: string;
  og_title: string;
  og_description: string;
  og_image: string;
  canonical: string;
  language: string;
  favicon: string;
  h1_tags: string[];
  meta_tags: Record<string, string>;
  word_count: number;
  load_time_ms: number;
  og_tags: Record<string, string>;
  twitter_tags: Record<string, string>;
  json_ld: Record<string, unknown>[];
};

type ArticleContent = {
  title: string;
  byline: string;
  excerpt: string;
  text: string;
  word_count: number;
};

type ScrapeResult = {
  url: string;
  title: string;
  status_code: number | null;
  content: string;
  screenshot_b64: string | null;
  pdf_b64: string | null;
  links: LinkItem[] | null;
  metadata: PageMetadata | null;
  markdown: string | null;
  article: ArticleContent | null;
  word_count: number | null;
  elapsed_ms: number | null;
};

type CrawlPage = {
  url: string;
  title: string;
  excerpt: string;
  depth: number;
  status_code: number | null;
};

type CrawlResult = {
  start_url: string;
  domain: string;
  pages: CrawlPage[];
  pages_crawled: number;
  elapsed_ms: number | null;
};

type ExtractMode =
  | "text"
  | "markdown"
  | "article"
  | "html"
  | "screenshot"
  | "links"
  | "metadata"
  | "pdf";

const MODES: { id: ExtractMode; name: string; hint: string }[] = [
  { id: "text", name: "📄 Text", hint: "Plain body text" },
  { id: "markdown", name: "📝 Markdown", hint: "Clean main content" },
  { id: "article", name: "📰 Article", hint: "Readable reader view" },
  { id: "html", name: "🌐 HTML", hint: "Full page source" },
  { id: "screenshot", name: "📸 Screenshot", hint: "Full-page PNG" },
  { id: "links", name: "🔗 Links", hint: "All hyperlinks" },
  { id: "metadata", name: "📊 Metadata", hint: "OG, Twitter, JSON-LD" },
  { id: "pdf", name: "📑 PDF", hint: "Printable document" },
];

const DEMO_URLS = [
  { label: "Example.com", url: "https://example.com" },
  { label: "Hacker News", url: "https://news.ycombinator.com" },
  { label: "Wikipedia", url: "https://en.wikipedia.org/wiki/Web_scraping" },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className={`scraperCopyBtn ${copied ? "copied" : ""}`}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
          /* clipboard blocked — no-op */
        }
      }}
    >
      {copied ? "✓ Copied" : "📋 Copy"}
    </button>
  );
}

export default function ScraperPage() {
  const [tab, setTab] = useState<"scrape" | "crawl">("scrape");

  // Scrape state
  const [url, setUrl] = useState("https://example.com");
  const [extract, setExtract] = useState<ExtractMode>("text");
  const [stealth, setStealth] = useState(true);
  const [waitFor, setWaitFor] = useState("");
  const [javascript, setJavascript] = useState("");
  const [waitSeconds, setWaitSeconds] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScrapeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  // Crawl state
  const [crawlUrl, setCrawlUrl] = useState("https://example.com");
  const [maxPages, setMaxPages] = useState(5);
  const [maxDepth, setMaxDepth] = useState(1);
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [crawlResult, setCrawlResult] = useState<CrawlResult | null>(null);
  const [crawlError, setCrawlError] = useState<string | null>(null);
  const [crawlElapsed, setCrawlElapsed] = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setElapsed(null);
    setShowRaw(false);
    setLoading(true);
    const start = Date.now();
    try {
      const body: Record<string, unknown> = {
        url: url.trim(),
        extract,
        stealth,
        wait_for: waitFor.trim() || undefined,
        javascript: javascript.trim() || undefined,
        wait_seconds: waitSeconds > 0 ? waitSeconds : undefined,
      };
      const res = await fetch(api("/api/scraper/scrape"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setElapsed(Date.now() - start);
      if (!res.ok) {
        setError(data.detail ?? `HTTP ${res.status}`);
        return;
      }
      setResult(data);
    } catch (err) {
      setElapsed(Date.now() - start);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleCrawl(e: React.FormEvent) {
    e.preventDefault();
    setCrawlError(null);
    setCrawlResult(null);
    setCrawlElapsed(null);
    setCrawlLoading(true);
    const start = Date.now();
    try {
      const res = await fetch(api("/api/scraper/crawl"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: crawlUrl.trim(),
          max_pages: maxPages,
          max_depth: maxDepth,
        }),
      });
      const data = await res.json();
      setCrawlElapsed(Date.now() - start);
      if (!res.ok) {
        setCrawlError(data.detail ?? `HTTP ${res.status}`);
        return;
      }
      setCrawlResult(data);
    } catch (err) {
      setCrawlElapsed(Date.now() - start);
      setCrawlError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setCrawlLoading(false);
    }
  }

  return (
    <FeatureLayout
      title="Web Scraper"
      description="Playwright-powered browser extraction for pages you are authorized to inspect. Capture text, Markdown, articles, HTML, screenshots, links, metadata, and PDFs — or crawl a domain shallowly."
      icon="🕷️"
      endpoints={[
        { method: "POST", path: "/api/scraper/scrape" },
        { method: "POST", path: "/api/scraper/crawl" },
      ]}
    >
      {/* ── Tab switch ── */}
      <div className="scraperTabs">
        <button
          type="button"
          className={`scraperTab ${tab === "scrape" ? "active" : ""}`}
          onClick={() => setTab("scrape")}
        >
          🔗 Scrape a page
        </button>
        <button
          type="button"
          className={`scraperTab ${tab === "crawl" ? "active" : ""}`}
          onClick={() => setTab("crawl")}
        >
          🕸️ Crawl a domain
        </button>
      </div>

      {tab === "scrape" && (
        <>
          {/* ── Input Form ── */}
          <div className="featureCard">
            <div className="cardHeader">
              <h2>
                <span className="cardIcon">🔗</span>
                Scrape a URL
              </h2>
            </div>
            <p className="featureCardSubtitle">
              Extract text, Markdown, a readable article, HTML, screenshots, links, enriched SEO
              metadata, or PDF from a page you have permission to inspect. Compatibility mode
              adjusts browser fingerprints for modern sites; it is not a bypass guarantee.
            </p>

            <form className="featureForm" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="scraper-url">Target URL</label>
                <div className="inputWithTag">
                  <input
                    id="scraper-url"
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://"
                    required
                  />
                  <span className="inputTag">URL</span>
                </div>
              </div>

              <div>
                <label style={{ marginBottom: 10 }}>Quick demo URLs</label>
                <div className="suggestionChips">
                  {DEMO_URLS.map((d) => (
                    <button
                      key={d.url}
                      type="button"
                      className="suggestionChip"
                      onClick={() => setUrl(d.url)}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label>Output Format</label>
                <div className="scraperModeGrid">
                  {MODES.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      className={`scraperModeBtn ${extract === mode.id ? "active" : ""}`}
                      onClick={() => setExtract(mode.id)}
                    >
                      <span className="modeName">{mode.name}</span>
                      <span className="modeHint">{mode.hint}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="formGrid">
                <div>
                  <label htmlFor="scraper-wait">Wait for selector</label>
                  <input
                    id="scraper-wait"
                    type="text"
                    value={waitFor}
                    onChange={(e) => setWaitFor(e.target.value)}
                    placeholder=".main-content"
                  />
                </div>
                <div>
                  <label>Compatibility mode</label>
                  <div className="stealthToggle">
                    <input
                      id="scraper-stealth"
                      type="checkbox"
                      checked={stealth}
                      onChange={(e) => setStealth(e.target.checked)}
                    />
                    <label htmlFor="scraper-stealth" className="stealthLabel">
                      <span className={`stealthDot ${stealth ? "active" : ""}`} />
                      {stealth ? "Fingerprint adjustments on" : "Standard browser context"}
                    </label>
                  </div>
                </div>
              </div>

              <div className="formGrid">
                <div>
                  <label htmlFor="scraper-js">Custom JavaScript</label>
                  <input
                    id="scraper-js"
                    type="text"
                    value={javascript}
                    onChange={(e) => setJavascript(e.target.value)}
                    placeholder="() => { return ... }"
                  />
                </div>
                <div>
                  <label htmlFor="scraper-delay">
                    Wait after load
                    <span style={{ fontWeight: 400, color: "var(--text-muted)", marginLeft: 8, fontSize: "0.82rem" }}>
                      {waitSeconds}s
                    </span>
                  </label>
                  <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                    <input
                      id="scraper-delay"
                      type="range"
                      min={0}
                      max={30}
                      step={1}
                      value={waitSeconds}
                      onChange={(e) => setWaitSeconds(Number(e.target.value))}
                      style={{ flex: 1, accentColor: "var(--accent)", height: 6, cursor: "pointer" }}
                    />
                    <span style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: "0.9rem",
                      color: waitSeconds > 0 ? "var(--accent)" : "var(--text-muted)",
                      minWidth: 36,
                      textAlign: "right",
                    }}>
                      {waitSeconds}s
                    </span>
                  </div>
                </div>
              </div>

              <button type="submit" className="featureBtn featureBtnPrimary" disabled={loading}>
                {loading ? <span className="loadingDot">Scraping</span> : "🕷️ Start Scraping →"}
              </button>
            </form>
          </div>

          {/* ── Error ── */}
          {error && (
            <div className="featureResult featureError">
              <strong>⚠ Error:</strong> {error}
              {elapsed != null && (
                <span style={{ float: "right", fontSize: "0.8rem", opacity: 0.7 }}>{elapsed}ms</span>
              )}
            </div>
          )}

          {/* ── Empty state ── */}
          {!result && !error && !loading && (
            <div className="featureResult">
              <div className="scraperEmpty">
                <div className="emptyIcon">🕸️</div>
                <div className="emptyText">Pick an output format and a URL, then start scraping.</div>
              </div>
            </div>
          )}

          {/* ── Results ── */}
          {result && (
            <div className="scraperResult">
              {/* Status Header */}
              <div className="scraperResultHeader">
                <div className="scraperStatusRow">
                  <span className={`statusDot ${result.status_code && result.status_code < 400 ? "statusOnline" : "statusError"}`} />
                  <span className="scraperStatusCode">
                    HTTP {result.status_code ?? "—"} {result.status_code && result.status_code < 400 ? "OK" : ""}
                  </span>
                  {elapsed != null && (
                    <span className="scraperElapsed">{(elapsed / 1000).toFixed(2)}s</span>
                  )}
                </div>
                <div className="scraperMeta">
                  <span className="scraperTitle">{result.title || "(untitled)"}</span>
                  <span className="scraperUrl">{result.url}</span>
                </div>
              </div>

              {/* Content Body */}
              <div className="scraperResultBody">
                {/* Screenshot */}
                {result.screenshot_b64 && (
                  <div className="screenshotWrap">
                    <img src={`data:image/png;base64,${result.screenshot_b64}`} alt="Full page screenshot" />
                  </div>
                )}

                {/* PDF */}
                {result.pdf_b64 && (
                  <div style={{ padding: 24, textAlign: "center" }}>
                    <p style={{ color: "var(--text-dim)", marginBottom: 16 }}>📑 PDF generated successfully</p>
                    <a
                      href={`data:application/pdf;base64,${result.pdf_b64}`}
                      download={`${result.title || "page"}.pdf`}
                      className="featureBtn featureBtnPrimary"
                      style={{ display: "inline-flex", textDecoration: "none" }}
                    >
                      📥 Download PDF
                    </a>
                  </div>
                )}

                {/* Article (reader view) */}
                {result.article && (
                  <div className="consoleCard" style={{ border: "none" }}>
                    <div className="consoleHeader">
                      <div className="consoleDots">
                        <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
                      </div>
                      <span className="consoleTitle">
                        Article{result.article.word_count ? ` · ${result.article.word_count} words` : ""}
                      </span>
                      <CopyButton text={result.article.text} />
                    </div>
                    <div className="consoleBody">
                      <div className="scraperArticle">
                        <div className="articleTitle">{result.article.title || result.title || "(untitled)"}</div>
                        {result.article.byline && (
                          <div className="articleByline">✍ {result.article.byline}</div>
                        )}
                        <div className="articleBody">{result.article.text}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Markdown */}
                {result.markdown && !result.article && (
                  <div className="consoleCard" style={{ border: "none" }}>
                    <div className="consoleHeader">
                      <div className="consoleDots">
                        <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
                      </div>
                      <span className="consoleTitle">
                        content.md{result.word_count ? ` · ${result.word_count} words` : ""}
                      </span>
                      <CopyButton text={result.markdown} />
                    </div>
                    <div className="consoleBody">
                      <pre className="scraperMono">{result.markdown}</pre>
                    </div>
                  </div>
                )}

                {/* Links */}
                {result.links && (
                  <div className="consoleCard" style={{ border: "none" }}>
                    <div className="consoleHeader">
                      <div className="consoleDots">
                        <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
                      </div>
                      <span className="consoleTitle">{result.links.length} links found</span>
                    </div>
                    <div className="consoleBody" style={{ maxHeight: 500 }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                        <thead>
                          <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                            <th style={{ padding: "8px 12px", color: "var(--accent)" }}>Text</th>
                            <th style={{ padding: "8px 12px", color: "var(--accent)" }}>URL</th>
                            <th style={{ padding: "8px 12px", color: "var(--accent)" }}>Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.links.map((link, i) => (
                            <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                              <td style={{ padding: "6px 12px", color: "var(--text-dim)", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{link.text || "—"}</td>
                              <td style={{ padding: "6px 12px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72rem", color: "var(--text-muted)", maxWidth: 350, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                <a href={link.href} target="_blank" rel="noopener noreferrer" style={{ color: "inherit" }}>{link.href}</a>
                              </td>
                              <td style={{ padding: "6px 12px" }}>
                                <span style={{ fontSize: "0.68rem", padding: "2px 8px", borderRadius: 4, background: link.is_external ? "rgba(251,191,36,0.1)" : "rgba(52,211,153,0.1)", color: link.is_external ? "var(--amber)" : "var(--emerald)", border: `1px solid ${link.is_external ? "rgba(251,191,36,0.2)" : "rgba(52,211,153,0.2)"}` }}>
                                  {link.is_external ? "External" : "Internal"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Metadata — labeled cards + OG/Twitter/JSON-LD */}
                {result.metadata && (
                  <div className="consoleCard" style={{ border: "none" }}>
                    <div className="consoleHeader">
                      <div className="consoleDots">
                        <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
                      </div>
                      <span className="consoleTitle">SEO &amp; Page Metadata</span>
                      <CopyButton text={JSON.stringify(result.metadata, null, 2)} />
                    </div>
                    <div className="consoleBody" style={{ padding: 0 }}>
                      <MetadataView meta={result.metadata} />
                    </div>
                  </div>
                )}

                {/* Text / HTML content */}
                {result.content && !result.screenshot_b64 && !result.pdf_b64 && !result.links && !result.metadata && !result.markdown && !result.article && (
                  <div className="consoleCard" style={{ border: "none" }}>
                    <div className="consoleHeader">
                      <div className="consoleDots">
                        <span className="dot red" /><span className="dot yellow" /><span className="dot green" />
                      </div>
                      <span className="consoleTitle">result.json{result.word_count ? ` · ${result.word_count} words` : ""}</span>
                      <button type="button" className="consoleToggle" onClick={() => setShowRaw(!showRaw)}>
                        {showRaw ? "Formatted" : "📋 Raw"}
                      </button>
                      <CopyButton text={result.content} />
                    </div>
                    <div className="consoleBody">
                      {showRaw ? (
                        <pre className="scraperMono">
                          {result.content.slice(0, 20000)}
                          {result.content.length > 20000 ? "\n… (truncated)" : ""}
                        </pre>
                      ) : (
                        <pre className="consoleJson">
                          {JSON.stringify(
                            {
                              status: "success",
                              timestamp: new Date().toISOString(),
                              url: result.url,
                              title: result.title,
                              word_count: result.word_count,
                              text_content: result.content.slice(0, 500),
                              "...": result.content.length > 500 ? `${result.content.length} chars total` : undefined,
                              performance: { elapsed_ms: result.elapsed_ms ?? elapsed },
                            },
                            null,
                            2
                          )}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {tab === "crawl" && (
        <>
          <div className="featureCard">
            <div className="cardHeader">
              <h2>
                <span className="cardIcon">🕸️</span>
                Shallow domain crawl
              </h2>
            </div>
            <p className="featureCardSubtitle">
              Follow same-domain links from a start URL and collect a title + excerpt for each page.
              Bounded to {maxPages} page{maxPages === 1 ? "" : "s"} and depth {maxDepth}. Every
              discovered URL is SSRF-validated before it is visited.
            </p>

            <form className="featureForm" onSubmit={handleCrawl}>
              <div>
                <label htmlFor="crawl-url">Start URL</label>
                <div className="inputWithTag">
                  <input
                    id="crawl-url"
                    type="url"
                    value={crawlUrl}
                    onChange={(e) => setCrawlUrl(e.target.value)}
                    placeholder="https://"
                    required
                  />
                  <span className="inputTag">URL</span>
                </div>
              </div>

              <div className="formGrid">
                <div>
                  <label htmlFor="crawl-pages">
                    Max pages
                    <span style={{ fontWeight: 400, color: "var(--accent)", marginLeft: 8, fontSize: "0.82rem" }}>
                      {maxPages}
                    </span>
                  </label>
                  <input
                    id="crawl-pages"
                    type="range"
                    min={1}
                    max={10}
                    step={1}
                    value={maxPages}
                    onChange={(e) => setMaxPages(Number(e.target.value))}
                    style={{ width: "100%", accentColor: "var(--accent)", height: 6, cursor: "pointer" }}
                  />
                </div>
                <div>
                  <label htmlFor="crawl-depth">
                    Max depth
                    <span style={{ fontWeight: 400, color: "var(--accent)", marginLeft: 8, fontSize: "0.82rem" }}>
                      {maxDepth}
                    </span>
                  </label>
                  <input
                    id="crawl-depth"
                    type="range"
                    min={0}
                    max={2}
                    step={1}
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(Number(e.target.value))}
                    style={{ width: "100%", accentColor: "var(--accent)", height: 6, cursor: "pointer" }}
                  />
                </div>
              </div>

              <button type="submit" className="featureBtn featureBtnPrimary" disabled={crawlLoading}>
                {crawlLoading ? <span className="loadingDot">Crawling</span> : "🕸️ Start Crawl →"}
              </button>
            </form>
          </div>

          {crawlError && (
            <div className="featureResult featureError">
              <strong>⚠ Error:</strong> {crawlError}
              {crawlElapsed != null && (
                <span style={{ float: "right", fontSize: "0.8rem", opacity: 0.7 }}>{crawlElapsed}ms</span>
              )}
            </div>
          )}

          {!crawlResult && !crawlError && !crawlLoading && (
            <div className="featureResult">
              <div className="scraperEmpty">
                <div className="emptyIcon">🕸️</div>
                <div className="emptyText">Enter a start URL and crawl a handful of same-domain pages.</div>
              </div>
            </div>
          )}

          {crawlResult && (
            <div className="scraperResult">
              <div className="scraperResultHeader">
                <div className="scraperStatusRow">
                  <span className="statusDot statusOnline" />
                  <span className="scraperStatusCode">
                    {crawlResult.pages_crawled} page{crawlResult.pages_crawled === 1 ? "" : "s"} · {crawlResult.domain}
                  </span>
                  {crawlElapsed != null && (
                    <span className="scraperElapsed">{(crawlElapsed / 1000).toFixed(2)}s</span>
                  )}
                </div>
              </div>
              <div className="scraperResultBody">
                {crawlResult.pages.length === 0 ? (
                  <div className="scraperEmpty">
                    <div className="emptyText">No pages could be crawled from this URL.</div>
                  </div>
                ) : (
                  <div className="crawlList">
                    {crawlResult.pages.map((p, i) => (
                      <div key={i} className="crawlItem">
                        <div className="crawlItemHead">
                          <span className="crawlItemTitle">{p.title || "(untitled)"}</span>
                          <span className="crawlDepthBadge">depth {p.depth}</span>
                          {p.status_code != null && (
                            <span className="crawlDepthBadge">HTTP {p.status_code}</span>
                          )}
                        </div>
                        <a href={p.url} target="_blank" rel="noopener noreferrer" className="crawlItemUrl">
                          {p.url}
                        </a>
                        {p.excerpt && <div className="crawlItemExcerpt">{p.excerpt}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </FeatureLayout>
  );
}

function MetadataView({ meta }: { meta: PageMetadata }) {
  const cards: { label: string; value: React.ReactNode }[] = [];
  const push = (label: string, value: string | number | undefined, isLink = false) => {
    if (value === undefined || value === null || value === "") return;
    cards.push({
      label,
      value: isLink ? (
        <a href={String(value)} target="_blank" rel="noopener noreferrer">{String(value)}</a>
      ) : (
        String(value)
      ),
    });
  };
  push("Title", meta.title);
  push("Description", meta.description);
  push("Language", meta.language);
  push("Word count", meta.word_count);
  push("Canonical", meta.canonical, true);
  push("Favicon", meta.favicon, true);
  push("OG Title", meta.og_title);
  push("OG Description", meta.og_description);

  const hasOg = meta.og_tags && Object.keys(meta.og_tags).length > 0;
  const hasTwitter = meta.twitter_tags && Object.keys(meta.twitter_tags).length > 0;
  const hasJsonLd = meta.json_ld && meta.json_ld.length > 0;

  return (
    <>
      <div className="scraperMetaGrid">
        {cards.map((c, i) => (
          <div key={i} className="scraperMetaCard">
            <div className="metaLabel">{c.label}</div>
            <div className="metaValue">{c.value}</div>
          </div>
        ))}
        {meta.og_image && (
          <div className="scraperMetaCard" style={{ gridColumn: "1 / -1" }}>
            <div className="metaLabel">OG Image</div>
            <div className="metaValue">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={meta.og_image} alt="Open Graph preview" className="scraperMetaImg" />
            </div>
          </div>
        )}
      </div>

      {hasOg && (
        <div className="scraperKvBlock">
          <h4>Open Graph</h4>
          <table className="scraperKvTable">
            <tbody>
              {Object.entries(meta.og_tags).map(([k, v]) => (
                <tr key={k}><td className="k">{k}</td><td className="v">{v}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {hasTwitter && (
        <div className="scraperKvBlock">
          <h4>Twitter Card</h4>
          <table className="scraperKvTable">
            <tbody>
              {Object.entries(meta.twitter_tags).map(([k, v]) => (
                <tr key={k}><td className="k">{k}</td><td className="v">{v}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {hasJsonLd && (
        <div className="scraperKvBlock">
          <h4>JSON-LD ({meta.json_ld.length})</h4>
          <pre className="scraperMono">{JSON.stringify(meta.json_ld, null, 2)}</pre>
        </div>
      )}

      {meta.h1_tags && meta.h1_tags.length > 0 && (
        <div className="scraperKvBlock">
          <h4>H1 Tags ({meta.h1_tags.length})</h4>
          <table className="scraperKvTable">
            <tbody>
              {meta.h1_tags.map((h, i) => (
                <tr key={i}><td className="k">h1</td><td className="v">{h}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
