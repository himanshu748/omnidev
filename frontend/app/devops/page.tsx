"use client";

import { useState, useRef, useEffect, useCallback } from "react";
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
  id: number;
  command: string;
  action: string;
  summary: string;
  result: DevOpsResult;
  timestamp: string;
  elapsed: number;
  isError: boolean;
};

const SUGGESTION_GROUPS = [
  {
    label: "EC2",
    icon: "🖥️",
    items: [
      "List my EC2 instances",
      "Show running instances in us-east-1",
      "Describe instance i-0abc123",
    ],
  },
  {
    label: "S3",
    icon: "📦",
    items: [
      "Show my S3 buckets",
      "List objects in my-bucket",
    ],
  },
  {
    label: "Networking",
    icon: "🔒",
    items: [
      "Describe security groups",
      "List IAM users",
      "Show my VPCs",
    ],
  },
  {
    label: "Databases",
    icon: "🗄️",
    items: [
      "Show my RDS instances",
      "Describe database mydb",
    ],
  },
  {
    label: "Monitoring",
    icon: "📊",
    items: [
      "List CloudWatch alarms",
      "Show alarms in ALARM state",
      "List my Lambda functions",
    ],
  },
  {
    label: "Dangerous",
    icon: "⚡",
    items: [
      "Launch a t2.micro instance",
      "Stop instance i-0abc123",
      "Create S3 bucket my-new-bucket",
    ],
  },
];

function formatElapsed(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

let nextId = 1;

export default function DevOpsPage() {
  const [message, setMessage] = useState("");
  const [confirmDestructive, setConfirmDestructive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeEntry, setActiveEntry] = useState<HistoryEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [expandedJson, setExpandedJson] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeSuggestionGroup, setActiveSuggestionGroup] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const consoleBodyRef = useRef<HTMLDivElement>(null);

  // Keyboard shortcut: CMD+Enter
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        const form = document.getElementById("devops-form") as HTMLFormElement;
        if (form) form.requestSubmit();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleCopyJson = useCallback(() => {
    if (!activeEntry?.result.raw_result) return;
    navigator.clipboard.writeText(
      JSON.stringify(activeEntry.result.raw_result, null, 2)
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [activeEntry]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim() || loading) return;
    setError(null);
    setActiveEntry(null);
    setExpandedJson(false);
    setLoading(true);
    const start = Date.now();
    try {
      const res = await fetch(api("/api/devops/command"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message.trim(),
          confirm_destructive: confirmDestructive,
        }),
      });
      const elapsed = Date.now() - start;
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? `HTTP ${res.status}`);
        return;
      }
      const rawResult = data.raw_result;
      const isResultError =
        rawResult !== null &&
        typeof rawResult === "object" &&
        !Array.isArray(rawResult) &&
        "error" in rawResult;
      const entry: HistoryEntry = {
        id: nextId++,
        command: message.trim(),
        action: data.action,
        summary: data.summary,
        result: data,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
        elapsed,
        isError: isResultError,
      };
      setActiveEntry(entry);
      setHistory((prev) => [entry, ...prev.slice(0, 9)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function replayCommand(entry: HistoryEntry) {
    setMessage(entry.command);
    setActiveEntry(entry);
    setExpandedJson(false);
    inputRef.current?.focus();
  }

  const isDangerous =
    ["terminate", "delete", "stop", "reboot", "launch", "create"].some((word) =>
      message.toLowerCase().includes(word)
    );

  return (
    <FeatureLayout
      title="DevOps Agent"
      description="Autonomous AWS infrastructure management powered by AI & boto3. Speak naturally to your cloud."
      icon="🤖"
      endpoints={[{ method: "POST", path: "/api/devops/command" }]}
    >
      {/* ── Status Bar ── */}
      <div className="devopsStatusBar">
        <div className="devopsStatusLeft">
          <span className={`devopsStatusDot ${loading ? "pulse" : ""}`} />
          <span className="devopsStatusText">
            {loading ? "Processing..." : "Agent Ready"}
          </span>
        </div>
        <div className="devopsStatusRight">
          <span className="devopsStatusEndpoint">
            <span className="devopsMethodBadge">POST</span>
            /api/devops/command
          </span>
        </div>
      </div>

      <div className="devopsSplitPanel">
        {/* ═══════════════════════════════════════════════ LEFT: Command Panel ═══════════════════════════════════════════════ */}
        <div className="devopsLeftCol">
          {/* Command Card */}
          <div className="devopsCommandCard">
            <div className="devopsCommandCardInner">
              {/* Card Header */}
              <div className="devopsCardHead">
                <div>
                  <h2 className="devopsCardTitle">
                    <span className="devopsCardTitleIcon">💬</span>
                    Natural Language Command
                  </h2>
                  <p className="devopsCardSubtitle">
                    AI agent parses plain English for AWS operations.
                  </p>
                </div>
                <div className="devopsBoltIcon">⚡</div>
              </div>

              {/* Form */}
              <form id="devops-form" onSubmit={handleSubmit}>
                {/* Input Area */}
                <div className="devopsInputWrap">
                  <span className="devopsInputPrefix">Prompt &gt;</span>
                  <input
                    ref={inputRef}
                    id="devops-message"
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="e.g. List my EC2 instances"
                    className="devopsInput"
                    autoComplete="off"
                  />
                  <span className="devopsInputShortcut">⌘ Enter</span>
                </div>

                {/* Danger Warning */}
                {isDangerous && !confirmDestructive && (
                  <div className="devopsDangerHint">
                    <span>⚠️</span>
                    <span>
                      This looks like a destructive action. Enable{" "}
                      <strong>&quot;Confirm destructive&quot;</strong> below.
                    </span>
                  </div>
                )}

                {/* Suggestion Chips */}
                <div className="devopsSuggestionArea">
                  <div className="devopsSuggestionTabs">
                    {SUGGESTION_GROUPS.map((g, i) => (
                      <button
                        key={g.label}
                        type="button"
                        className={`devopsSugTab ${activeSuggestionGroup === i ? "active" : ""}`}
                        onClick={() => setActiveSuggestionGroup(i)}
                      >
                        <span>{g.icon}</span>
                        <span>{g.label}</span>
                      </button>
                    ))}
                  </div>
                  <div className="devopsSuggestionChips">
                    {SUGGESTION_GROUPS[activeSuggestionGroup].items.map((s) => (
                      <button
                        key={s}
                        type="button"
                        className="devopsSugChip"
                        onClick={() => {
                          setMessage(s);
                          inputRef.current?.focus();
                        }}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="devopsDivider" />

                {/* Controls */}
                <div className="devopsControls">
                  <label className="devopsCheckLabel">
                    <input
                      type="checkbox"
                      checked={confirmDestructive}
                      onChange={(e) => setConfirmDestructive(e.target.checked)}
                      className="devopsCheckbox"
                    />
                    <span className="devopsCheckCustom" />
                    <span>Confirm destructive actions</span>
                  </label>
                  <button
                    type="submit"
                    className="devopsRunBtn"
                    disabled={loading || !message.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="devopsRunSpinner" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <span>▶</span>
                        Run Command
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* History Panel */}
          {history.length > 0 && (
            <div className="devopsHistoryCard">
              <h3 className="devopsHistoryTitle">Recent Operations</h3>
              <div className="devopsHistoryList">
                {history.map((h) => (
                  <div
                    key={h.id}
                    className={`devopsHistoryItem ${activeEntry?.id === h.id ? "active" : ""}`}
                    onClick={() => replayCommand(h)}
                  >
                    <div className="devopsHistoryLeft">
                      <span
                        className={`devopsHistoryDot ${h.isError ? "error" : ""}`}
                      />
                      <span className="devopsHistoryAction">{h.action}</span>
                      <span className="devopsHistoryCmd">{h.command}</span>
                    </div>
                    <div className="devopsHistoryRight">
                      <span className="devopsHistoryElapsed">
                        {formatElapsed(h.elapsed)}
                      </span>
                      <span className="devopsHistoryTime">{h.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ═══════════════════════════════════════════════ RIGHT: Console ═══════════════════════════════════════════════ */}
        <div className="devopsRightCol">
          <div className="devopsConsole">
            {/* Console Header */}
            <div className="devopsConsoleHead">
              <div className="devopsConsoleHeadLeft">
                <span className="devopsTermIcon">⬛</span>
                <span className="devopsConsoleLabel">Output Console</span>
              </div>
              <div className="devopsConsoleHeadRight">
                {activeEntry && (
                  <span className="devopsActionBadge">
                    Action: {activeEntry.action}
                  </span>
                )}
                <div className="devopsConsoleDots">
                  <span className="cdot red" />
                  <span className="cdot yellow" />
                  <span className="cdot green" />
                </div>
              </div>
            </div>

            {/* Console Body */}
            <div className="devopsConsoleBody" ref={consoleBodyRef}>
              {/* IDLE STATE */}
              {!activeEntry && !error && !loading && (
                <div className="devopsIdleState">
                  <div className="devopsIdleIcon">
                    <span>🤖</span>
                  </div>
                  <h3>DevOps Agent Ready</h3>
                  <p>
                    Type a natural language command and press{" "}
                    <kbd>⌘ Enter</kbd> to execute.
                  </p>
                  <div className="devopsIdleExamples">
                    <code>&quot;List my EC2 instances&quot;</code>
                    <code>&quot;Show S3 buckets&quot;</code>
                    <code>&quot;Describe security groups&quot;</code>
                  </div>
                </div>
              )}

              {/* LOADING STATE */}
              {loading && (
                <div className="devopsLoadingState">
                  <div className="devopsAIAvatar processing">
                    <span>🤖</span>
                  </div>
                  <div className="devopsLoadingContent">
                    <div className="devopsLoadingLabel">
                      Agent is processing your request...
                    </div>
                    <div className="devopsTypingIndicator">
                      <span />
                      <span />
                      <span />
                    </div>
                    <div className="devopsLoadingCommand">
                      <span className="devopsLoadingPrefix">$</span>
                      {message}
                    </div>
                  </div>
                </div>
              )}

              {/* ERROR STATE */}
              {error && (
                <div className="devopsErrorBlock">
                  <div className="devopsErrorHead">
                    <span className="statusDot statusError" />
                    <span>ERROR</span>
                  </div>
                  <pre className="devopsErrorText">{error}</pre>
                  <button
                    className="devopsRetryBtn"
                    onClick={() => {
                      setError(null);
                      inputRef.current?.focus();
                    }}
                  >
                    ↻ Retry
                  </button>
                </div>
              )}

              {/* RESULT STATE */}
              {activeEntry && (
                <div className="devopsResultWrap">
                  {/* Summary */}
                  <div className="devopsSummaryBlock">
                    <div className="devopsAIAvatar">
                      <span>🤖</span>
                    </div>
                    <div className="devopsSummaryContent">
                      <div className="devopsSummaryMeta">
                        <span className="devopsSummaryAgent">
                          OmniDev Agent
                        </span>
                        <span className="devopsSummaryTime">
                          {activeEntry.timestamp} ·{" "}
                          {formatElapsed(activeEntry.elapsed)}
                        </span>
                      </div>
                      <p className="devopsSummaryText">
                        {activeEntry.summary ||
                          `Executed action: ${activeEntry.action}`}
                      </p>
                    </div>
                  </div>

                  {/* JSON Payload */}
                  {activeEntry.result.raw_result != null && (
                    <div className="devopsJsonBlock">
                      <div className="devopsJsonHeader">
                        <span className="devopsJsonLabel">
                          // API Response Payload
                        </span>
                        <div className="devopsJsonActions">
                          <button
                            className="devopsJsonToggle"
                            onClick={() => setExpandedJson((p) => !p)}
                          >
                            {expandedJson ? "▾ Collapse" : "▸ Expand"}
                          </button>
                          <button
                            className="devopsJsonCopy"
                            onClick={handleCopyJson}
                          >
                            {copied ? "✓ Copied" : "📋 Copy"}
                          </button>
                        </div>
                      </div>
                      <div className="devopsJsonMeta">
                        <span className={activeEntry.isError ? "devopsJsonStatus error" : "devopsJsonStatus"}>
                          {activeEntry.isError ? "AWS ERROR" : "200 OK"}
                        </span>
                        <span className="devopsJsonElapsed">
                          {formatElapsed(activeEntry.elapsed)}
                        </span>
                      </div>
                      <pre className={`devopsJsonPre ${expandedJson ? "expanded" : ""}`}>
                        {JSON.stringify(activeEntry.result.raw_result, null, 2)}
                      </pre>
                    </div>
                  )}

                  {/* Destructive Warning */}
                  {activeEntry.result.needs_confirmation && (
                    <div className="devopsWarningBlock">
                      <span className="devopsWarningIcon">⚠️</span>
                      <div>
                        <strong>Destructive Action Required</strong>
                        <p>
                          Enable &quot;Confirm destructive actions&quot; and
                          re-run.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Console Footer */}
            <div className="devopsConsoleFooter">
              <span className="devopsFooterLeft">
                <span
                  className={`statusDot ${error ? "statusError" : "statusOnline"}`}
                />
                <span>{error ? "Error" : "System Online"}</span>
              </span>
              <span className="devopsFooterRight">
                <span>Gemini · boto3</span>
                <span className="devopsFooterVersion">v0.2.0</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </FeatureLayout>
  );
}
