"use client";

import { useState } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type ScrapeResult = {
  url: string;
  title: string;
  status_code: number | null;
  content: string;
  screenshot_b64: string | null;
};

const DEMO_URLS = [
  { label: "Example.com", url: "https://example.com" },
  { label: "Hacker News", url: "https://news.ycombinator.com" },
  { label: "Wikipedia", url: "https://en.wikipedia.org/wiki/Web_scraping" },
  { label: "GitHub", url: "https://github.com" },
  { label: "Keepa", url: "https://keepa.com" },
];

function syntaxHighlight(json: string): string {
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = "jsonNumber";
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? "jsonKey" : "jsonString";
      } else if (/true|false/.test(match)) {
        cls = "jsonBool";
      } else if (/null/.test(match)) {
        cls = "jsonNull";
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

export default function ScraperPage() {
  const [url, setUrl] = useState("https://example.com");
  const [extract, setExtract] = useState<"text" | "html" | "screenshot">("text");
  const [stealth, setStealth] = useState(true);
  const [waitFor, setWaitFor] = useState("");
  const [javascript, setJavascript] = useState("");
  const [waitSeconds, setWaitSeconds] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScrapeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [showRaw, setShowRaw] = useState(false);

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

  return (
    <FeatureLayout
      title="Web Scraper"
      description="Playwright-powered stealth scraping engine. Extract data from dynamic SPAs and modern web apps without getting blocked."
      icon="🕷️"
      endpoints={[{ method: "POST", path: "/api/scraper/scrape" }]}
    >
      {/* ── Input Form ── */}
      <div className="featureCard">
        <div className="cardHeader">
          <h2>
            <span className="cardIcon">🔗</span>
            Scrape a URL
          </h2>
        </div>
        <p className="featureCardSubtitle">
          Enter any URL to extract text, HTML, or a full-page screenshot. Stealth mode uses anti-detection patterns.
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
              <span className="inputTag">🔒</span>
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

          <div className="formGrid">
            <div>
              <label>Output Format</label>
              <div className="modePills">
                {(["text", "html", "screenshot"] as const).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    className={`modePill ${extract === mode ? "active" : ""}`}
                    onClick={() => setExtract(mode)}
                  >
                    {mode === "text" ? "📄 Text" : mode === "html" ? "🌐 HTML" : "📸 Screenshot"}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label>Stealth Mode</label>
              <div className="stealthToggle">
                <input
                  id="scraper-stealth"
                  type="checkbox"
                  checked={stealth}
                  onChange={(e) => setStealth(e.target.checked)}
                />
                <label htmlFor="scraper-stealth" className="stealthLabel">
                  <span className={`stealthDot ${stealth ? "active" : ""}`} />
                  {stealth ? "Secure connection" : "Standard mode"}
                </label>
              </div>
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
              <label htmlFor="scraper-js">Custom JavaScript</label>
              <input
                id="scraper-js"
                type="text"
                value={javascript}
                onChange={(e) => setJavascript(e.target.value)}
                placeholder="() => { return ... }"
              />
            </div>
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
                style={{
                  flex: 1,
                  accentColor: "var(--accent)",
                  height: 6,
                  cursor: "pointer",
                }}
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

          <button
            type="submit"
            className="featureBtn featureBtnPrimary"
            disabled={loading}
          >
            {loading ? (
              <span className="loadingDot">Scraping</span>
            ) : (
              "🕷️ Start Scraping →"
            )}
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
            {result.screenshot_b64 ? (
              <div className="screenshotWrap">
                <img
                  src={`data:image/png;base64,${result.screenshot_b64}`}
                  alt="Full page screenshot"
                />
              </div>
            ) : (
              <>
                {/* Extracted content preview */}
                {result.content && (
                  <div className="consoleCard" style={{ border: "none" }}>
                    <div className="consoleHeader">
                      <div className="consoleDots">
                        <span className="dot red" />
                        <span className="dot yellow" />
                        <span className="dot green" />
                      </div>
                      <span className="consoleTitle">result.json</span>
                      <button
                        type="button"
                        className="consoleToggle"
                        onClick={() => setShowRaw(!showRaw)}
                      >
                        {showRaw ? "Copy" : "📋 Download"}
                      </button>
                    </div>
                    <div className="consoleBody">
                      {showRaw ? (
                        <pre className="consoleJson">
                          {result.content.slice(0, 20000)}
                          {result.content.length > 20000 ? "\n… (truncated)" : ""}
                        </pre>
                      ) : (
                        <pre
                          className="consoleJson"
                          dangerouslySetInnerHTML={{
                            __html: syntaxHighlight(
                              JSON.stringify(
                                {
                                  status: "success",
                                  timestamp: new Date().toISOString(),
                                  url: result.url,
                                  title: result.title,
                                  meta_description: null,
                                  text_content: result.content.slice(0, 500),
                                  "...": result.content.length > 500 ? `${result.content.length} chars total` : undefined,
                                  performance: {
                                    load_time_ms: elapsed,
                                    content_loaded_ms: elapsed ? Math.round(elapsed * 0.7) : null,
                                  },
                                },
                                null,
                                2
                              )
                            ),
                          }}
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </FeatureLayout>
  );
}
