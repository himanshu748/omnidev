"use client";

import { useState } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type DevOpsResult = {
  action: string;
  params: Record<string, unknown>;
  raw_result: unknown;
  summary: string;
  needs_confirmation: boolean;
};

type HistoryEntry = {
  command: string;
  action: string;
  timestamp: string;
};

const SUGGESTIONS = [
  "List my EC2 instances",
  "Show my S3 buckets",
  "Describe security groups",
  "Launch a t2.micro instance",
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

export default function DevOpsPage() {
  const [message, setMessage] = useState("");
  const [confirmDestructive, setConfirmDestructive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DevOpsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch(api("/api/devops/command"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message.trim(),
          confirm_destructive: confirmDestructive,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? `HTTP ${res.status}`);
        return;
      }
      setResult(data);
      setHistory((prev) => [
        {
          command: message.trim(),
          action: data.action,
          timestamp: new Date().toLocaleTimeString(),
        },
        ...prev.slice(0, 4),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <FeatureLayout
      title="DevOps Agent"
      description="Autonomous AWS infrastructure management powered by OpenAI & boto3. Speak naturally to your cloud."
      icon="🤖"
      endpoints={[{ method: "POST", path: "/api/devops/command" }]}
    >
      <div className="splitPanel">
        {/* ── Left: Command Input ── */}
        <div className="splitLeft">
          <div className="featureCard">
            <div className="cardHeader">
              <h2>
                <span className="cardIcon">💬</span>
                Natural Language Command
              </h2>
              <span className="cardHeaderBadge">AI-Powered</span>
            </div>
            <p className="featureCardSubtitle">
              An AI agent parses plain English for AWS operations.
            </p>
            <form className="featureForm" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="devops-message">Command</label>
                <div className="inputWithTag">
                  <input
                    id="devops-message"
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Prompt >List running EC2 instances in us-east-1"
                    required
                  />
                  <span className="inputTag">GPT-4.1</span>
                </div>
              </div>

              <div>
                <label style={{ marginBottom: 10 }}>Quick suggestions</label>
                <div className="suggestionChips">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      className="suggestionChip"
                      onClick={() => setMessage(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div className="featureFormRow">
                <input
                  id="devops-confirm"
                  type="checkbox"
                  checked={confirmDestructive}
                  onChange={(e) => setConfirmDestructive(e.target.checked)}
                />
                <label htmlFor="devops-confirm">
                  Confirm destructive actions
                </label>
              </div>

              <button
                type="submit"
                className="featureBtn featureBtnPrimary"
                disabled={loading || !message.trim()}
              >
                {loading ? (
                  <span className="loadingDot">Running</span>
                ) : (
                  "▶ Run Command"
                )}
              </button>
            </form>
          </div>

          {/* ── Recent Operations ── */}
          {history.length > 0 && (
            <div className="featureCard" style={{ marginTop: 20 }}>
              <h3 style={{ fontSize: "0.9rem", color: "var(--text-dim)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Recent Operations
              </h3>
              <div className="historyList">
                {history.map((h, i) => (
                  <div key={i} className="historyItem" onClick={() => setMessage(h.command)}>
                    <span className="historyAction">{h.action}</span>
                    <span className="historyCommand">{h.command}</span>
                    <span className="historyTime">{h.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Right: Output Console ── */}
        <div className="splitRight">
          <div className="consoleCard">
            <div className="consoleHeader">
              <div className="consoleDots">
                <span className="dot red" />
                <span className="dot yellow" />
                <span className="dot green" />
              </div>
              <span className="consoleTitle">Output Console</span>
              <span className="consoleStatus">
                {loading ? "RUNNING..." : result ? "200 OK" : error ? "ERROR" : "IDLE"}
              </span>
            </div>

            <div className="consoleBody">
              {!result && !error && !loading && (
                <div className="consolePlaceholder">
                  <span style={{ fontSize: "2rem", marginBottom: 12 }}>⚡</span>
                  <p>Run a command to see output here</p>
                  <p className="consolePlaceholderSub">Results will appear with syntax-highlighted JSON</p>
                </div>
              )}

              {loading && (
                <div className="consolePlaceholder">
                  <div className="consoleSpinner" />
                  <p>Processing command...</p>
                </div>
              )}

              {error && (
                <div className="consoleError">
                  <div className="consoleErrorHeader">
                    <span className="statusDot statusError" />
                    ERROR
                  </div>
                  <pre className="consoleErrorText">{error}</pre>
                </div>
              )}

              {result && (
                <>
                  <div className="consoleSection">
                    <span className="consoleSectionLabel">// Action</span>
                    <pre className="consoleActionValue">{result.action}</pre>
                  </div>

                  {result.summary && (
                    <div className="consoleSection">
                      <span className="consoleSectionLabel">// Summary</span>
                      <pre className="consoleSummary">{result.summary}</pre>
                    </div>
                  )}

                  {result.raw_result != null && (
                    <div className="consoleSection">
                      <span className="consoleSectionLabel">// API Response Payload</span>
                      <pre
                        className="consoleJson"
                        dangerouslySetInnerHTML={{
                          __html: syntaxHighlight(JSON.stringify(result.raw_result, null, 2)),
                        }}
                      />
                    </div>
                  )}

                  {result.needs_confirmation && (
                    <div className="consoleWarning">
                      <span className="warningIcon">⚠</span>
                      <div>
                        <strong>NOTE</strong>
                        <p>This is a destructive action. Enable confirmation and rerun.</p>
                      </div>
                    </div>
                  )}

                  <div className="consoleFooter">
                    <span className="statusDot statusOnline" />
                    <span>System Online</span>
                    <span className="consoleVersion">v0.2.0</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </FeatureLayout>
  );
}
