import Image from "next/image";
import Link from "next/link";
import { Space_Grotesk } from "next/font/google";
import {
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  Code2,
  Cpu,
  Database,
  Download,
  Eye,
  GitBranch,
  Globe,
  KeyRound,
  ScrollText,
  ShieldCheck,
  TerminalSquare,
  UserCheck,
  WifiOff,
} from "lucide-react";
import Reveal from "./components/Reveal";
import { LogoMark } from "./components/Logo";

const displayFont = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-landing-display",
});

const GITHUB_URL = "https://github.com/himanshu748/omnidev";
const DOWNLOAD_URL = `${GITHUB_URL}/releases/latest`;
const DOCS_URL = `${GITHUB_URL}/tree/main/docs`;
const ROADMAP_URL = `${GITHUB_URL}#roadmap`;

const heroSignals = [
  { icon: WifiOff, label: "Runs 100% offline" },
  { icon: KeyRound, label: "No account, no key, no bill" },
  { icon: BadgeCheck, label: "MIT licensed" },
  { icon: Cpu, label: "Powered by Gemma 4" },
] as const;

const steps = [
  {
    n: "01",
    title: "Install the app",
    body: "Grab the signed macOS build from GitHub Releases, or clone the repo. No installer telemetry, no license server.",
    code: ["$ git clone github.com/himanshu748/omnidev"],
  },
  {
    n: "02",
    title: "Pull a local model",
    body: "One Ollama command downloads Gemma 4 — the same edge model behind Google's AI Edge Gallery — for text, plans, and vision.",
    code: ["$ ollama pull gemma4:e4b"],
  },
  {
    n: "03",
    title: "Build and run",
    body: "One script boots the local backend and launches the native cockpit. Everything answers on 127.0.0.1.",
    code: ["$ ./script/build_and_run.sh", "Backend ready on 127.0.0.1:8010"],
  },
] as const;

const modules = [
  {
    title: "DevOps Agent",
    href: "/devops",
    icon: TerminalSquare,
    body: "Ask about EC2, S3, IAM, or RDS in plain English. OmniDev writes the exact boto3 plan and holds it until you approve — nothing runs behind your back.",
  },
  {
    title: "Vision Lab",
    href: "/vision",
    icon: Eye,
    body: "Image analysis, OCR, and visual Q&A on-device. Screenshots of your own infrastructure never need to leave the room.",
  },
  {
    title: "Code Gen",
    href: "/codegen",
    icon: Code2,
    body: "Full project scaffolds for React, Next.js, FastAPI, and more. Validated and sandboxed — generated code is written to disk, never executed for you.",
  },
  {
    title: "Web Scraper",
    href: "/scraper",
    icon: Globe,
    body: "Playwright-powered extraction of text, links, metadata, PDFs, and screenshots — with SSRF guards that refuse private and loopback targets.",
  },
  {
    title: "Cloud Storage",
    href: "/storage",
    icon: Database,
    body: "Browse S3 buckets, upload and delete objects, and generate presigned links, all from one panel with your own credentials.",
  },
] as const;

const smallModules = modules.slice(2);

const trust = [
  {
    icon: WifiOff,
    title: "Offline by default",
    body: "The model, the backend, and the UI are local processes bound to 127.0.0.1. Pull the network cable and OmniDev keeps working.",
  },
  {
    icon: KeyRound,
    title: "No keys to leak",
    body: "There is no OmniDev account and no API key for the AI itself. Cloud credentials stay on your machine and are only used for the AWS tools you opt into.",
  },
  {
    icon: UserCheck,
    title: "Human-in-the-loop",
    body: "Every destructive infrastructure action is planned, shown as an exact call, and blocked until you confirm. Approval is not optional.",
  },
  {
    icon: ShieldCheck,
    title: "Safe by construction",
    body: "The scraper enforces SSRF protection against private ranges, and code generation is sandbox-validated and never auto-run.",
  },
  {
    icon: ScrollText,
    title: "Open source, MIT",
    body: "Read every line, fork it, ship it. No black box between you and the model — the whole cockpit is on GitHub under MIT.",
  },
  {
    icon: Cpu,
    title: "Bring your own model",
    body: "Gemma 4 out of the box via Ollama. Prefer a hosted model? Add a free Gemini key and OmniDev switches providers automatically.",
  },
] as const;

export default function LandingPage() {
  return (
    <main className={`lpShell ${displayFont.variable}`}>
      <header className="lpNav">
        <div className="lpNavInner">
          <Link href="/" className="lpBrand" aria-label="OmniDev home">
            <LogoMark size={26} style={{ color: "var(--lp-accent)" }} />
            <span>OmniDev</span>
          </Link>
          <nav className="lpNavLinks" aria-label="Landing navigation">
            <a href="#how">How it works</a>
            <a href="#modules">Modules</a>
            <a href="#offline">Offline AI</a>
            <a href={GITHUB_URL} target="_blank" rel="noreferrer">
              GitHub
            </a>
            <Link href="/app" className="lpNavCta">
              Open cockpit
            </Link>
          </nav>
        </div>
      </header>

      <section className="lpHero">
        <div className="lpContainer">
          <span className="lpHeroTag lpHeroIn">
            <span className="lpHeroDot" aria-hidden="true" />
            Native macOS app · fully offline
          </span>
          <h1 className="lpDisplay lpHeroIn">
            Your AI dev cockpit.
            <span>Nothing leaves your Mac.</span>
          </h1>
          <p className="lpHeroSub lpHeroIn2">
            One native macOS app for code generation, infrastructure, scraping,
            vision, and storage. Gemma 4 runs entirely on your machine.
          </p>
          <div className="lpHeroActions lpHeroIn3">
            <a href={DOWNLOAD_URL} className="lpBtnPrimary" target="_blank" rel="noreferrer">
              <Download size={18} aria-hidden="true" />
              Download for macOS
            </a>
            <Link href="/app" className="lpBtnGhost">
              Open cockpit
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
          </div>
          <ul className="lpHeroSignals lpHeroIn3" aria-label="What you get">
            {heroSignals.map(({ icon: Icon, label }) => (
              <li key={label}>
                <Icon size={15} aria-hidden="true" />
                {label}
              </li>
            ))}
          </ul>
        </div>
        <div className="lpContainer">
          <div className="lpHeroShot lpHeroIn4">
            <Image
              src="/screenshots/cockpit.png"
              alt="The OmniDev cockpit showing the DevOps Agent with a pending IAM approval"
              width={1440}
              height={1024}
              priority
            />
          </div>
        </div>
      </section>

      <section className="lpSection" id="privacy">
        <div className="lpContainer">
          <Reveal>
            <h2 className="lpDisplay">Private by architecture.</h2>
            <p className="lpSectionLede">
              OmniDev is not a cloud product with a desktop wrapper. The backend,
              the frontend, and the model all run as local processes you can see
              and stop.
            </p>
          </Reveal>
          <Reveal>
            <div className="lpPrivacyGrid">
              <div className="lpPrivacyItem">
                <h3>
                  <ShieldCheck size={19} aria-hidden="true" />
                  On-device AI
                </h3>
                <p>
                  Prompts, generated code, and analyzed images go to a local
                  Gemma 4 model through Ollama, not to an API on someone else&apos;s
                  computer.
                </p>
              </div>
              <div className="lpPrivacyItem">
                <h3>
                  <KeyRound size={19} aria-hidden="true" />
                  No accounts, no keys
                </h3>
                <p>
                  Works out of the box with no sign-up, no API key, and no usage
                  bill. Cloud credentials are only needed for the AWS tools you
                  choose to connect.
                </p>
              </div>
              <div className="lpPrivacyItem">
                <h3>
                  <UserCheck size={19} aria-hidden="true" />
                  You approve changes
                </h3>
                <p>
                  Destructive infrastructure actions are planned, shown to you,
                  and held until you explicitly confirm. Every time.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="lpSection" id="how">
        <div className="lpContainer">
          <Reveal>
            <span className="lpEyebrow">Get running</span>
            <h2 className="lpDisplay">Up in three commands.</h2>
            <p className="lpSectionLede">
              No onboarding wizard, no cloud project to provision. Clone, pull a
              model, run — the same flow whether you build from source or grab a
              release.
            </p>
          </Reveal>
          <Reveal>
            <ol className="lpSteps">
              {steps.map(({ n, title, body, code }) => (
                <li key={n} className="lpStep">
                  <span className="lpStepNum" aria-hidden="true">
                    {n}
                  </span>
                  <h3>{title}</h3>
                  <p>{body}</p>
                  <div className="lpStepCode">
                    {code.map((line) => (
                      <code key={line}>{line}</code>
                    ))}
                  </div>
                </li>
              ))}
            </ol>
          </Reveal>
        </div>
      </section>

      <section className="lpSection" id="modules">
        <div className="lpContainer">
          <Reveal>
            <span className="lpEyebrow">The modules</span>
            <h2 className="lpDisplay">One cockpit. Five tools.</h2>
            <p className="lpSectionLede">
              The tabs you keep open all day, rebuilt as native modules that
              share one local backend.
            </p>
          </Reveal>
          <Reveal>
            <div className="lpBento">
              <Link href="/devops" className="lpCell lpCellWide">
                <div className="lpCellShot" aria-hidden="true">
                  <Image
                    src="/screenshots/cockpit.png"
                    alt=""
                    width={1440}
                    height={1024}
                  />
                </div>
                <ArrowUpRight size={18} className="lpCellArrow" aria-hidden="true" />
                <h3>
                  <TerminalSquare size={19} aria-hidden="true" />
                  DevOps Agent
                </h3>
                <p>
                  Ask about EC2, S3, IAM, or RDS in plain English. Review the
                  exact boto3 plan before anything runs.
                </p>
              </Link>
              <Link href="/vision" className="lpCell lpCellTall lpCellTint">
                <div className="lpCellShot" aria-hidden="true">
                  <Image
                    src="/screenshots/vision.png"
                    alt=""
                    width={1440}
                    height={900}
                    style={{ objectPosition: "50% 62%" }}
                  />
                </div>
                <ArrowUpRight size={18} className="lpCellArrow" aria-hidden="true" />
                <h3>
                  <Eye size={19} aria-hidden="true" />
                  Vision Lab
                </h3>
                <p>
                  Image analysis, OCR, and visual Q&amp;A. Screenshots of your own
                  infrastructure never need to leave the room.
                </p>
              </Link>
              {smallModules.map(({ title, href, icon: Icon, body }) => (
                <Link key={title} href={href} className="lpCell">
                  {href === "/codegen" && (
                    <div className="lpCellShot" aria-hidden="true">
                      <Image
                        src="/screenshots/codegen.png"
                        alt=""
                        width={1440}
                        height={900}
                        style={{ objectPosition: "50% 12%", opacity: 0.22 }}
                      />
                    </div>
                  )}
                  <ArrowUpRight size={18} className="lpCellArrow" aria-hidden="true" />
                  <h3>
                    <Icon size={19} aria-hidden="true" />
                    {title}
                  </h3>
                  <p>{body}</p>
                </Link>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <section className="lpSection" id="offline">
        <div className="lpContainer">
          <div className="lpOfflineGrid">
            <Reveal className="lpOfflineCopy">
              <h2 className="lpDisplay">Fully offline with{" "}Gemma&nbsp;4.</h2>
              <p className="lpSectionLede">
                The same edge model behind Google&apos;s AI Edge Gallery, served
                locally by Ollama. Text, structured plans, and vision in a single
                9.6 GB download.
              </p>
              <p className="lpOfflineNote">
                Prefer a hosted model? Add a free Gemini key and OmniDev switches
                providers automatically.
              </p>
            </Reveal>
            <Reveal>
              <div className="lpTerminal" aria-label="Setup commands">
                <code>
                  <span className="lpPrompt">$ </span>
                  <span className="lpCmd">ollama pull gemma4:e4b</span>
                </code>
                <code>
                  <span className="lpPrompt">$ </span>
                  <span className="lpCmd">./script/build_and_run.sh</span>
                </code>
                <code>Backend ready on 127.0.0.1:8010</code>
                <code>OmniDev.app launched</code>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="lpSection" id="trust">
        <div className="lpContainer">
          <Reveal>
            <span className="lpEyebrow">Why local-first</span>
            <h2 className="lpDisplay">Trust you can verify.</h2>
            <p className="lpSectionLede">
              Every claim here maps to something in the repo — not a marketing
              promise. Local processes, human approval, and open code.
            </p>
          </Reveal>
          <Reveal>
            <div className="lpTrustGrid">
              {trust.map(({ icon: Icon, title, body }) => (
                <div key={title} className="lpTrustItem">
                  <h3>
                    <Icon size={18} aria-hidden="true" />
                    {title}
                  </h3>
                  <p>{body}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <section className="lpFinal">
        <div className="lpContainer">
          <Reveal>
            <h2 className="lpDisplay">Start with your machine.</h2>
            <p>
              Free and MIT licensed. macOS today, Windows and Linux packages
              next.
            </p>
            <div className="lpFinalActions">
              <a href={DOWNLOAD_URL} className="lpBtnPrimary" target="_blank" rel="noreferrer">
                <Download size={18} aria-hidden="true" />
                Download for macOS
              </a>
              <a href={GITHUB_URL} className="lpBtnGhost" target="_blank" rel="noreferrer">
                GitHub
                <ArrowUpRight size={17} aria-hidden="true" />
              </a>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="lpFooter">
        <div className="lpFooterInner">
          <div className="lpFooterBrand">
            <LogoMark size={22} style={{ color: "var(--lp-accent)" }} />
            <span>OmniDev, MIT licensed.</span>
          </div>
          <div className="lpFooterLinks">
            <a href={GITHUB_URL} target="_blank" rel="noreferrer">
              <GitBranch size={15} aria-hidden="true" />
              GitHub
            </a>
            <a href={DOCS_URL} target="_blank" rel="noreferrer">
              Docs
            </a>
            <a href={ROADMAP_URL} target="_blank" rel="noreferrer">
              Roadmap
            </a>
            <Link href="/app">Cockpit</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
