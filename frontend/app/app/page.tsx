"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Archive,
  Bell,
  Boxes,
  Check,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Cloud,
  Code2,
  Command,
  Copy,
  Cpu,
  Database,
  ExternalLink,
  Eye,
  FileClock,
  GitBranch,
  Globe2,
  HardDrive,
  LayoutDashboard,
  Loader2,
  LockKeyhole,
  Play,
  Search,
  Send,
  Server,
  Settings,
  ShieldCheck,
  Sparkles,
  Sun,
  TerminalSquare,
  Workflow,
  X,
} from "lucide-react";
import { API_BASE } from "@/lib/api";
import ModelManager from "@/app/components/ModelManager";

type SetupStep = {
  id: number;
  label: string;
  status: "completed" | "active" | "pending";
};

type Approval = {
  risk: "Medium" | "Low";
  action: string;
  resource: string;
  service: string;
  updated: string;
  dryRun: string;
};

const setupSteps: SetupStep[] = [
  { id: 1, label: "Install OmniDev", status: "completed" },
  { id: 2, label: "Start Local API", status: "completed" },
  { id: 3, label: "Pull AI Models", status: "completed" },
  { id: 4, label: "Configure AWS Profile", status: "completed" },
  { id: 5, label: "Test Connection", status: "active" },
  { id: 6, label: "Enable Optional Tools", status: "pending" },
  { id: 7, label: "Set Up Notifications", status: "pending" },
  { id: 8, label: "Review & Finish", status: "pending" },
];

const modules = [
  {
    name: "DevOps Agent",
    href: "/devops",
    detail: "Operate AWS infrastructure with human-in-the-loop safety.",
    agent: "Cloud operator",
    accent: "blue",
    status: "Flagship",
    icon: Workflow,
  },
  {
    name: "Code Gen",
    href: "/codegen",
    detail: "Generate full projects, refactor code, and write tests with AI.",
    agent: "Project builder",
    accent: "purple",
    status: "Ready",
    icon: Code2,
  },
  {
    name: "Browser Automation Studio",
    href: "/scraper",
    detail: "Build reliable web automations and data pipelines.",
    agent: "Browser runner",
    accent: "cyan",
    status: "Ready",
    icon: Globe2,
  },
  {
    name: "Vision Lab",
    href: "/vision",
    detail: "Analyze images, extract text, and build computer vision workflows.",
    agent: "Vision analyst",
    accent: "violet",
    status: "Ready",
    icon: Eye,
  },
  {
    name: "S3 Manager",
    href: "/storage",
    detail: "Manage buckets, files, policies, and lifecycle rules.",
    agent: "Storage steward",
    accent: "green",
    status: "Ready",
    icon: Database,
  },
];

const approvals: Approval[] = [
  {
    risk: "Medium",
    action: "Modify IAM Policy",
    resource: "acme-saas-readonly",
    service: "IAM",
    updated: "1m ago",
    dryRun: "No changes",
  },
  {
    risk: "Low",
    action: "Create S3 Bucket",
    resource: "acme-saas-assets",
    service: "S3",
    updated: "3m ago",
    dryRun: "1 to create",
  },
  {
    risk: "Low",
    action: "Update Security Group",
    resource: "sg-acme-web",
    service: "EC2",
    updated: "5m ago",
    dryRun: "2 to modify",
  },
];

const operations = [
  { label: "Environments", icon: Cloud },
  { label: "Schedules", icon: FileClock },
  { label: "Secrets", icon: LockKeyhole },
  { label: "Connections", icon: GitBranch },
  { label: "Audit Log", icon: Archive },
];

const systems = [
  { label: "Models & Runtimes", icon: Boxes },
  { label: "Local Services", icon: Server },
  { label: "Settings", icon: Settings },
];

type HealthInfo = {
  status?: string;
  service?: string;
  ai_provider?: string;
  ai_model?: string;
};

type DevRoute = {
  method: "GET" | "POST";
  path: string;
  label: string;
  curl: (base: string) => string;
};

const jsonCurl = (base: string, path: string, body: Record<string, unknown>) =>
  `curl -X POST ${base}${path} -H 'Content-Type: application/json' -d '${JSON.stringify(body)}'`;

const devRoutes: DevRoute[] = [
  {
    method: "GET",
    path: "/health",
    label: "Service + AI provider status",
    curl: (base) => `curl ${base}/health`,
  },
  {
    method: "POST",
    path: "/api/devops/command",
    label: "Natural-language AWS command",
    curl: (base) =>
      jsonCurl(base, "/api/devops/command", {
        message: "List my EC2 instances",
        confirm_destructive: false,
      }),
  },
  {
    method: "POST",
    path: "/api/codegen/generate",
    label: "Generate project files",
    curl: (base) =>
      jsonCurl(base, "/api/codegen/generate", {
        prompt: "A todo app with dark mode",
        framework: "react",
      }),
  },
  {
    method: "POST",
    path: "/api/scraper/scrape",
    label: "Scrape a web page",
    curl: (base) =>
      jsonCurl(base, "/api/scraper/scrape", {
        url: "https://example.com",
        extract: "text",
        stealth: false,
      }),
  },
  {
    method: "POST",
    path: "/api/vision/analyze",
    label: "Analyze an image (multipart)",
    curl: (base) =>
      `curl -X POST ${base}/api/vision/analyze -F 'image=@screenshot.png' -F 'mode=describe'`,
  },
  {
    method: "GET",
    path: "/api/storage/buckets",
    label: "List S3 buckets",
    curl: (base) => `curl ${base}/api/storage/buckets`,
  },
  {
    method: "POST",
    path: "/api/preview/check",
    label: "Screenshot + check a website",
    curl: (base) =>
      jsonCurl(base, "/api/preview/check", {
        url: "https://example.com",
        desktop: true,
        mobile: false,
      }),
  },
];

export default function HomePage() {
  const [mode, setMode] = useState<"ask" | "agent">("agent");
  const [selectedApproval, setSelectedApproval] = useState(approvals[0]);
  const [command, setCommand] = useState("");
  const [approved, setApproved] = useState(false);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [devPanelOpen, setDevPanelOpen] = useState(false);
  const [answer, setAnswer] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [askedQuestion, setAskedQuestion] = useState("");

  async function askOmniDev(message: string) {
    const question = message.trim();
    if (!question || asking) return;
    setAsking(true);
    setAnswer("");
    setAskError(null);
    setAskedQuestion(question);
    try {
      const res = await fetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      if (!res.ok || !res.body) {
        let detail = `HTTP ${res.status}`;
        try {
          detail = (await res.json())?.detail ?? detail;
        } catch {
          /* keep default */
        }
        setAskError(detail);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) continue;
          let ev: Record<string, unknown>;
          try {
            ev = JSON.parse(line);
          } catch {
            continue;
          }
          if (typeof ev.delta === "string") setAnswer((prev) => prev + ev.delta);
          else if (ev.error) setAskError(String(ev.error));
        }
      }
    } catch (err) {
      setAskError(String(err));
    } finally {
      setAsking(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as HealthInfo;
        if (!cancelled) {
          setHealth(data);
          setBackendOnline(true);
        }
      } catch {
        // Backend unreachable — show Offline, no console spam.
        if (!cancelled) {
          setHealth(null);
          setBackendOnline(false);
        }
      }
    }

    checkHealth();
    const timer = setInterval(checkHealth, 30_000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  function copyText(text: string, key: string) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        setCopiedKey(key);
        setTimeout(() => setCopiedKey((prev) => (prev === key ? null : prev)), 1600);
      })
      .catch(() => {});
  }

  const completedCount = setupSteps.filter((step) => step.status === "completed").length;
  const progress = Math.round((completedCount / setupSteps.length) * 100);

  const commandHint = useMemo(() => {
    if (mode === "agent") {
      return "Agent mode will plan, dry-run, and ask before changing infrastructure.";
    }

    return "Ask mode answers questions and previews commands without taking action.";
  }, [mode]);

  return (
    <main className="cockpitShell">
      <aside className="cockpitSidebar" aria-label="OmniDev navigation">
        <div className="cockpitBrand">
          <Image
            className="brandMark"
            src="/brand/omnidev-logo.png"
            alt=""
            width={36}
            height={36}
            priority
          />
          <div>
            <strong>OmniDev</strong>
            <span>AI Developer Cockpit</span>
          </div>
        </div>

        <section className="sidebarSection">
          <div className="sidebarKicker">Setup progress</div>
          <div className="setupProgressMeta">
            <span>{completedCount} / {setupSteps.length} completed</span>
            <span>{progress}%</span>
          </div>
          <div className="setupProgressTrack" aria-hidden="true">
            <span style={{ width: `${progress}%` }} />
          </div>
        </section>

        <nav className="sidebarNav">
          <Link href="/app" className="sidebarLink active">
            <LayoutDashboard size={18} />
            <span>Command Center</span>
          </Link>
          <Link href="/devops" className="sidebarLink">
            <Workflow size={18} />
            <span>DevOps Agent</span>
            <small>Flagship</small>
          </Link>
        </nav>

        <section className="sidebarSection">
          <div className="sidebarKicker">Feature agents</div>
          <nav className="sidebarNav compact">
            {modules.slice(1).map((module) => {
              const Icon = module.icon;
              return (
                <Link key={module.name} href={module.href} className="sidebarLink">
                  <Icon size={17} />
                  <span>{module.name}</span>
                  <i className={`navSignal ${module.accent}`} aria-hidden="true" />
                </Link>
              );
            })}
          </nav>
        </section>

        <section className="sidebarSection">
          <div className="sidebarKicker">Operations</div>
          <nav className="sidebarNav compact">
            {operations.map(({ label, icon: Icon }) => (
              <a key={label} href="#approvals" className="sidebarLink muted">
                <Icon size={17} />
                <span>{label}</span>
              </a>
            ))}
          </nav>
        </section>

        <section className="sidebarSection">
          <div className="sidebarKicker">System</div>
          <nav className="sidebarNav compact">
            {systems.map(({ label, icon: Icon }) => (
              <a key={label} href="#runtime" className="sidebarLink muted">
                <Icon size={17} />
                <span>{label}</span>
              </a>
            ))}
          </nav>
        </section>

        <div className="localCard">
          <div>
            <CircleDot size={15} />
            <span>OmniDev Local</span>
            <strong>Connected</strong>
          </div>
          <div>
            <Cpu size={15} />
            <span>Ollama</span>
            <strong>Running</strong>
          </div>
          <div>
            <HardDrive size={15} />
            <span>Docker</span>
            <strong>Running</strong>
          </div>
          <footer>
            <span>v1.2.0</span>
            <a href={API_BASE} target="_blank" rel="noreferrer">
              View logs
            </a>
          </footer>
        </div>

        <button type="button" className="accountButton">
          <span>SB</span>
          <div>
            <strong>Solo Builder</strong>
            <small>Pro Plan</small>
          </div>
          <ChevronDown size={16} />
        </button>
      </aside>

      <section className="cockpitStage">
        <header className="cockpitTopbar">
          <form
            className="commandSearch"
            onSubmit={(event) => {
              event.preventDefault();
              askOmniDev(command);
            }}
          >
            <Search size={18} aria-hidden="true" />
            <input
              value={command}
              onChange={(event) => setCommand(event.target.value)}
              placeholder='Ask OmniDev anything... e.g. "How do I make a boto3 client?"'
              aria-label="Ask OmniDev anything"
            />
            {asking ? <Loader2 size={15} className="askSpin" /> : <kbd>⏎</kbd>}
          </form>

          <div className="modeSwitch" aria-label="Assistant mode">
            <button
              type="button"
              className={mode === "ask" ? "active" : ""}
              onClick={() => setMode("ask")}
            >
              Ask
            </button>
            <button
              type="button"
              className={mode === "agent" ? "active" : ""}
              onClick={() => setMode("agent")}
            >
              Agent
            </button>
          </div>

          <div className="topbarActions">
            <button type="button" aria-label="Switch theme">
              <Sun size={18} />
            </button>
            <button type="button" aria-label="Notifications">
              <Bell size={18} />
            </button>
            <button type="button" className="avatarButton" aria-label="Account">
              SB
              <span />
            </button>
          </div>
        </header>

        <div className="cockpitMain">
          <div className="cockpitContent">
            <section className="backendStrip" aria-label="Backend status">
              <span
                className={`backendChip status ${
                  backendOnline === null ? "checking" : backendOnline ? "online" : "offline"
                }`}
              >
                <i aria-hidden="true" />
                Backend{" "}
                {backendOnline === null ? "Checking…" : backendOnline ? "Online" : "Offline"}
              </span>
              <span className="backendChip">
                <Cpu size={14} aria-hidden="true" />
                {backendOnline && health?.ai_provider
                  ? `${health.ai_provider} · ${health.ai_model ?? "unknown model"}`
                  : "AI provider unavailable"}
              </span>
              <span className="backendChip apiBase">
                <Server size={14} aria-hidden="true" />
                <code>{API_BASE}</code>
                <button
                  type="button"
                  onClick={() => copyText(API_BASE, "api-base")}
                  aria-label="Copy API base URL"
                  title="Copy API base URL"
                >
                  {copiedKey === "api-base" ? <Check size={13} /> : <Copy size={13} />}
                </button>
              </span>
            </section>

            <ModelManager />

            {(asking || answer || askError) && (
              <section className="askPanel" aria-label="OmniDev answer" aria-live="polite">
                <div className="askPanelHead">
                  <span className="askPanelQ">
                    <Sparkles size={14} aria-hidden="true" /> {askedQuestion}
                  </span>
                  <button
                    type="button"
                    className="askPanelClose"
                    onClick={() => {
                      setAnswer("");
                      setAskError(null);
                      setAskedQuestion("");
                    }}
                    aria-label="Dismiss answer"
                  >
                    <X size={14} />
                  </button>
                </div>
                {askError ? (
                  <p className="askPanelError">{askError}</p>
                ) : (
                  <div className="askPanelBody">
                    {answer}
                    {asking && <span className="askCaret" aria-hidden="true" />}
                  </div>
                )}
              </section>
            )}

            <section className="cockpitIntro">
              <div>
                <p className="eyebrow">Command cockpit</p>
                <h1>Your local-first AI operations center.</h1>
                <p>
                  Start setup, ask about infrastructure, preview every boto3 plan,
                  and approve only the actions you trust.
                </p>
              </div>

              <div className="runtimeGrid" id="runtime">
                <div className="runtimeTile success">
                  <ShieldCheck size={22} />
                  <div>
                    <strong>Local API</strong>
                    <span>Connected</span>
                  </div>
                </div>
                <div className="runtimeTile success">
                  <Settings size={22} />
                  <div>
                    <strong>Runtime</strong>
                    <span>All systems go</span>
                  </div>
                </div>
                <div className="runtimeTile">
                  <Globe2 size={22} />
                  <div>
                    <strong>Models</strong>
                    <span>3 active</span>
                  </div>
                </div>
                <div className="runtimeTile">
                  <Database size={22} />
                  <div>
                    <strong>Storage</strong>
                    <span>2.4 GB / 50 GB</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="workspaceGrid">
              <div className="setupPanel">
                <div className="panelHeader">
                  <div>
                    <h2>OmniDev Setup</h2>
                    <span>{completedCount} / {setupSteps.length} completed</span>
                  </div>
                </div>
                <ol className="setupList">
                  {setupSteps.map((step) => (
                    <li key={step.id} className={step.status}>
                      <span className="stepIndex">
                        {step.status === "completed" ? <Check size={15} /> : step.id}
                      </span>
                      <strong>{step.label}</strong>
                      <em>{step.status === "completed" ? "Completed" : step.status === "active" ? "In progress" : "Pending"}</em>
                    </li>
                  ))}
                </ol>
                <button type="button" className="primaryButton">
                  Start setup
                </button>
                <a className="docsLink" href={API_BASE + "/docs"} target="_blank" rel="noreferrer">
                  View setup docs <ExternalLink size={14} />
                </a>
              </div>

              <div className="agentPanel">
                <div className="panelHeader">
                  <div>
                    <h2>
                      DevOps Agent <span>Flagship</span>
                    </h2>
                    <p>{commandHint}</p>
                  </div>
                </div>

                <form
                  className="agentComposer"
                  onSubmit={(event) => {
                    event.preventDefault();
                    setSelectedApproval(approvals[0]);
                    setApproved(false);
                  }}
                >
                  <input
                    value={command}
                    onChange={(event) => setCommand(event.target.value)}
                    placeholder="Ask about EC2, S3, IAM, RDS, CloudWatch..."
                    aria-label="DevOps command"
                  />
                  <button type="submit" aria-label="Send command">
                    <Send size={18} />
                  </button>
                </form>

                <div className="agentModeRow">
                  <div className="modeSwitch embedded">
                    <button
                      type="button"
                      className={mode === "ask" ? "active" : ""}
                      onClick={() => setMode("ask")}
                    >
                      Ask
                    </button>
                    <button
                      type="button"
                      className={mode === "agent" ? "active" : ""}
                      onClick={() => setMode("agent")}
                    >
                      Agent
                    </button>
                  </div>
                  <span>Human approval required before execution</span>
                </div>

                <div className="agentStats">
                  <div>
                    <CircleDot size={16} />
                    <span>Active plan</span>
                    <strong>acme-saas-infra.json</strong>
                  </div>
                  <div>
                    <FileClock size={16} />
                    <span>Last run</span>
                    <strong>2m ago</strong>
                  </div>
                  <div>
                    <ShieldCheck size={16} />
                    <span>Success rate</span>
                    <strong>98.7%</strong>
                  </div>
                  <div>
                    <Cloud size={16} />
                    <span>Est. monthly cost</span>
                    <strong>$18.42</strong>
                  </div>
                </div>

                <div className="approvalsPanel" id="approvals">
                  <div className="panelHeader slim">
                    <div>
                      <h2>Approvals</h2>
                      <nav aria-label="Approval filters">
                        <button type="button" className="active">Pending (3)</button>
                        <button type="button">Approved</button>
                        <button type="button">History</button>
                      </nav>
                    </div>
                    <button type="button" className="secondaryButton">
                      View all approvals <ExternalLink size={14} />
                    </button>
                  </div>

                  <div className="approvalTable" role="table" aria-label="Pending approvals">
                    <div className="approvalRow header" role="row">
                      <span>Risk</span>
                      <span>Action</span>
                      <span>Resource</span>
                      <span>Service</span>
                      <span>Updated</span>
                      <span>Dry-run</span>
                    </div>
                    {approvals.map((approval) => (
                      <button
                        type="button"
                        key={approval.action}
                        className={`approvalRow ${selectedApproval.action === approval.action ? "selected" : ""}`}
                        onClick={() => {
                          setSelectedApproval(approval);
                          setApproved(false);
                        }}
                      >
                        <span>
                          <i className={approval.risk.toLowerCase()} aria-hidden="true" />
                          {approval.risk}
                        </span>
                        <span>{approval.action}</span>
                        <span>{approval.resource}</span>
                        <span>{approval.service}</span>
                        <span>{approval.updated}</span>
                        <span>{approval.dryRun}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            <section className="modulesPanel">
              <div className="panelHeader slim">
                <h2>Feature Agents</h2>
              </div>
              <div className="moduleRows">
                {modules.map((module) => {
                  const Icon = module.icon;
                  return (
                    <Link key={module.name} href={module.href} className={`moduleRow ${module.accent}`}>
                      <span className="moduleIcon">
                        <Icon size={22} />
                      </span>
                      <span className="moduleCopy">
                        <strong>
                          {module.name}
                          {module.status === "Flagship" && <em>Flagship</em>}
                        </strong>
                        <span className="moduleAgent">{module.agent}</span>
                        <small>{module.detail}</small>
                      </span>
                      <span className={module.status === "Archived" ? "moduleState archived" : "moduleState"}>
                        {module.status === "Archived" ? "Archived" : "Open"}
                      </span>
                      <ChevronRight size={18} />
                    </Link>
                  );
                })}
              </div>
            </section>

            <section className="devToolsPanel">
              <button
                type="button"
                className="devToolsToggle"
                onClick={() => setDevPanelOpen((open) => !open)}
                aria-expanded={devPanelOpen}
              >
                <TerminalSquare size={16} aria-hidden="true" />
                <span>For developers</span>
                <small>{devRoutes.length} API routes · copy-paste curl</small>
                <ChevronDown
                  size={15}
                  className={`devToolsChevron ${devPanelOpen ? "open" : ""}`}
                  aria-hidden="true"
                />
              </button>

              {devPanelOpen && (
                <div className="devRouteList">
                  {devRoutes.map((route) => (
                    <div key={route.path} className="devRoute">
                      <span className={`devMethod ${route.method.toLowerCase()}`}>
                        {route.method}
                      </span>
                      <code className="devRoutePath">{route.path}</code>
                      <span className="devRouteLabel">{route.label}</span>
                      <button
                        type="button"
                        className="devRouteCopy"
                        onClick={() => copyText(route.curl(API_BASE), route.path)}
                        aria-label={`Copy curl for ${route.path}`}
                      >
                        {copiedKey === route.path ? (
                          <>
                            <Check size={12} /> Copied
                          </>
                        ) : (
                          <>
                            <Copy size={12} /> curl
                          </>
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          <aside className="approvalDrawer" aria-label="Selected approval details">
            <button type="button" className="drawerClose" aria-label="Close approval details">
              <X size={19} />
            </button>
            <header>
              <h2>{selectedApproval.action}</h2>
              <span className={`riskBadge ${selectedApproval.risk.toLowerCase()}`}>
                {selectedApproval.risk} risk
              </span>
              <span className="serviceBadge">{selectedApproval.service}</span>
            </header>

            <section className="drawerSection">
              <h3>Overview</h3>
              <dl className="detailList">
                <div>
                  <dt>Policy</dt>
                  <dd>{selectedApproval.resource}</dd>
                </div>
                <div>
                  <dt>Change</dt>
                  <dd>Update</dd>
                </div>
                <div>
                  <dt>Requested by</dt>
                  <dd>You</dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{selectedApproval.updated}</dd>
                </div>
              </dl>
            </section>

            <section className="drawerSection">
              <h3>Plan (boto3)</h3>
              <pre className="planBlock">{`iam = boto3.client("iam")

iam.create_policy_version(
    PolicyArn="arn:aws:iam::123456789012:policy/${selectedApproval.resource}",
    PolicyDocument=json.dumps(policy_document),
    SetAsDefault=True
)`}</pre>
              <a href="/devops">View full plan</a>
            </section>

            <section className="drawerSection">
              <h3>Resource impact</h3>
              <dl className="detailList compactDetails">
                <div>
                  <dt>Resource</dt>
                  <dd>{selectedApproval.resource}</dd>
                </div>
                <div>
                  <dt>Affected principals</dt>
                  <dd>4 users, 2 roles</dd>
                </div>
                <div>
                  <dt>Permission changes</dt>
                  <dd>Read-only, no elevated access</dd>
                </div>
              </dl>
            </section>

            <section className="drawerSection">
              <h3>Dry-run summary</h3>
              <p>No changes to existing permissions. New version will not affect active sessions.</p>
              <div className="validationLine">
                <Check size={16} />
                Validation passed
              </div>
            </section>

            <section className="drawerSection">
              <h3>Risk notes</h3>
              <p>This action is scoped to read-only access. No write or destructive actions detected.</p>
            </section>

            <footer className="drawerActions">
              <button
                type="button"
                className="secondaryButton"
                onClick={() => setApproved(false)}
              >
                Reject
              </button>
              <button
                type="button"
                className="primaryButton"
                onClick={() => setApproved(true)}
              >
                {approved ? "Approved" : "Approve"}
              </button>
            </footer>

            {approved && (
              <p className="approvedNote" role="status">
                Approval recorded. OmniDev will keep the action queued until you run it.
              </p>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
}
