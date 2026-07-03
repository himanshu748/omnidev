import Image from "next/image";
import Link from "next/link";
import {
  Apple,
  ArrowRight,
  Check,
  Code2,
  Download,
  FileArchive,
  Eye,
  Globe2,
  Laptop,
  Monitor,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  Workflow,
} from "lucide-react";

const modules = [
  {
    title: "DevOps Agent",
    body: "Ask about AWS, preview boto3 plans, and approve changes before anything runs.",
    icon: Workflow,
    accent: "blue",
  },
  {
    title: "Code Gen",
    body: "Generate serious project scaffolds with docs-aware AI and inspect files before use.",
    icon: Code2,
    accent: "purple",
  },
  {
    title: "Browser Automation Studio",
    body: "Turn scraping and browser runs into repeatable local workflows.",
    icon: Globe2,
    accent: "cyan",
  },
  {
    title: "Vision Lab",
    body: "Analyze images, extract OCR, and debug screenshots from one focused lab.",
    icon: Eye,
    accent: "violet",
  },
];

const platforms = [
  {
    name: "macOS",
    detail: "Download the native macOS shell for Apple Silicon and Intel Macs.",
    icon: Apple,
    status: "Developer preview",
  },
  {
    name: "Windows",
    detail: "Desktop packaging target for modern Windows developer machines.",
    icon: Monitor,
    status: "Planned package",
  },
  {
    name: "Linux",
    detail: "Desktop packaging target for workstation and container-first setups.",
    icon: Laptop,
    status: "Planned package",
  },
];

const downloadStats = [
  {
    label: "Format",
    value: ".app zip",
  },
  {
    label: "Runtime",
    value: "Sidecars",
  },
  {
    label: "Mode",
    value: "Native shell",
  },
];

const trustPoints = [
  "Local-first by default",
  "Human approval for risky actions",
  "Module-level credentials",
  "FastAPI + Next.js foundation",
];

export default function LandingPage() {
  return (
    <main className="landingShell">
      <header className="landingNav">
        <Link href="/" className="landingBrand" aria-label="OmniDev home">
          <Image
            className="landingBrandMark"
            src="/brand/omnidev-logo.png"
            alt=""
            width={42}
            height={42}
            priority
          />
          <span>
            <strong>OmniDev</strong>
            <small>Local AI Developer App</small>
          </span>
        </Link>

        <nav aria-label="Landing navigation">
          <a href="#modules">Agents</a>
          <a href="#platforms">Platforms</a>
          <a href="#security">Local-first</a>
        </nav>

        <Link href="/app" className="landingNavCta">
          Open cockpit
        </Link>
      </header>

      <section className="landingHero">
        <div className="landingHeroCopy">
          <p className="landingEyebrow">
            <Sparkles size={16} aria-hidden="true" />
            Local-first AI developer workbench
          </p>
          <h1>Download the local app for building with AI.</h1>
          <p>
            OmniDev is a native-shell cockpit for DevOps agents, code
            generation, browser automation, OCR, and S3 workflows. It starts on
            your machine, keeps risky actions behind review, and gives local
            developers one beautiful place to work.
          </p>

          <div className="landingActions">
            <a href="/downloads/OmniDev-macOS.zip" className="landingPrimary" download>
              <Download size={18} aria-hidden="true" />
              Download macOS app
            </a>
            <Link href="/app" className="landingSecondary">
              Open web cockpit <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <a href="#platforms" className="landingTextLink">
              Platform notes
            </a>
          </div>

          <div className="landingTrustRow" id="security">
            {trustPoints.map((point) => (
              <span key={point}>
                <Check size={15} aria-hidden="true" />
                {point}
              </span>
            ))}
          </div>
        </div>

        <div className="landingPreview" aria-label="OmniDev app preview">
          <div className="previewTopbar">
            <span />
            <div>
              <TerminalSquare size={16} aria-hidden="true" />
              Ask OmniDev anything...
            </div>
            <strong>Agent</strong>
          </div>
          <div className="previewBody">
            <aside>
              <strong>OmniDev</strong>
              <span className="previewActive">Command Center</span>
              <span>DevOps Agent</span>
              <span>Code Gen</span>
              <span>Browser Studio</span>
              <span>Vision Lab</span>
            </aside>
            <section>
              <div className="previewHeader">
                <div>
                  <small>Command cockpit</small>
                  <h2>Human-in-loop cloud automation.</h2>
                </div>
                <span>Local API connected</span>
              </div>
              <div className="previewGrid">
                <div className="previewSetup">
                  <h3>Setup</h3>
                  {["Install OmniDev", "Start Local API", "Configure AWS", "Test Connection"].map((item, index) => (
                    <p key={item}>
                      <Check size={14} aria-hidden="true" />
                      <span>{item}</span>
                      <em>{index < 3 ? "Done" : "Next"}</em>
                    </p>
                  ))}
                </div>
                <div className="previewAgent">
                  <h3>DevOps Agent</h3>
                  <div className="previewPrompt">Create an S3 bucket for prod assets</div>
                  <div className="previewApproval">
                    <span>Medium risk</span>
                    <strong>Modify IAM Policy</strong>
                    <small>Dry-run passed. Waiting for approval.</small>
                  </div>
                  <button type="button">Approve in app</button>
                </div>
              </div>
            </section>
          </div>
        </div>
      </section>

      <section className="landingDownloadBand" aria-label="Download OmniDev app">
        <div>
          <p className="landingEyebrow">
            <FileArchive size={16} aria-hidden="true" />
            Downloadable app
          </p>
          <h2>Native macOS shell today. Windows and Linux packages next.</h2>
          <p>
            The current download is a SwiftUI/WebKit macOS developer preview
            that starts the local FastAPI backend and Next.js cockpit together.
          </p>
        </div>
        <div className="landingDownloadPanel">
          <div className="landingDownloadIcon" aria-hidden="true">
            <Apple size={30} />
          </div>
          <div>
            <strong>OmniDev for macOS</strong>
            <span>Native shell developer preview</span>
          </div>
          <div className="landingDownloadStats">
            {downloadStats.map(({ label, value }) => (
              <p key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </p>
            ))}
          </div>
          <a href="/downloads/OmniDev-macOS.zip" className="landingPrimary" download>
            <Download size={18} aria-hidden="true" />
            Download
          </a>
        </div>
      </section>

      <section className="landingSection" id="modules">
        <div className="landingSectionHead">
          <p className="landingEyebrow">Feature agents</p>
          <h2>One focused agent for each developer workflow.</h2>
        </div>
        <div className="landingModuleGrid">
          {modules.map(({ title, body, icon: Icon, accent }) => (
            <article key={title} className={`landingModule ${accent}`}>
              <span>
                <Icon size={22} aria-hidden="true" />
              </span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landingSplit">
        <div>
          <p className="landingEyebrow">Agent mode</p>
          <h2>Let it plan the work. Keep the final say.</h2>
          <p>
            OmniDev can answer questions in Ask mode, then switch into Agent
            mode to draft steps, run safe previews, and queue approvals for boto3
            actions. Risky operations stay human-approved.
          </p>
        </div>
        <div className="landingPlanCard">
          {[
            ["Understand", "Parse the request and choose the right module."],
            ["Plan", "Draft commands, parameters, and expected changes."],
            ["Dry-run", "Validate impact before touching infrastructure."],
            ["Approve", "Wait for your explicit review before execution."],
          ].map(([label, body], index) => (
            <div key={label}>
              <span>{index + 1}</span>
              <strong>{label}</strong>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landingSection" id="platforms">
        <div className="landingSectionHead">
          <p className="landingEyebrow">
            <Download size={16} aria-hidden="true" />
            Platform availability
          </p>
          <h2>Designed to run where developers actually work.</h2>
          <p>
            OmniDev runs as a local FastAPI + Next.js stack today. The macOS
            developer app is available now, with Windows and Linux packages kept
            as the next packaging targets.
          </p>
        </div>

        <div className="platformGrid">
          {platforms.map(({ name, detail, icon: Icon, status }) => (
            <article key={name} className="platformCard">
              <Icon size={24} aria-hidden="true" />
              <h3>{name}</h3>
              <p>{detail}</p>
              <span>{status}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="landingFinalCta">
        <div>
          <p className="landingEyebrow">
            <ShieldCheck size={16} aria-hidden="true" />
            Local-first, not lock-in-first
          </p>
          <h2>Start with your machine. Add hosting later.</h2>
          <p>
            Run the backend locally, connect only the modules you need, and point
            the hosted UI at any reachable API when you are ready.
          </p>
        </div>
        <div className="landingActions">
          <a href="/downloads/OmniDev-macOS.zip" className="landingPrimary" download>
            <Download size={18} aria-hidden="true" />
            Download app
          </a>
          <a
            href="https://github.com/himanshu748/omnidev"
            className="landingSecondary"
            target="_blank"
            rel="noreferrer"
          >
            <Code2 size={18} aria-hidden="true" />
            GitHub
          </a>
        </div>
      </section>
    </main>
  );
}
