import Image from "next/image";
import Link from "next/link";
import { Space_Grotesk } from "next/font/google";
import {
  ArrowRight,
  ArrowUpRight,
  Code2,
  Database,
  Download,
  Eye,
  Globe,
  KeyRound,
  ShieldCheck,
  TerminalSquare,
  UserCheck,
} from "lucide-react";
import Reveal from "./components/Reveal";

const displayFont = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-landing-display",
});

const GITHUB_URL = "https://github.com/himanshu748/omnidev";
const DOWNLOAD_URL = `${GITHUB_URL}/releases/latest`;

const smallModules = [
  {
    title: "Code Gen",
    href: "/codegen",
    icon: Code2,
    body: "Full project scaffolds for React, Next.js, FastAPI, and more. Validated, sandboxed, never executed on your machine.",
  },
  {
    title: "Web Scraper",
    href: "/scraper",
    icon: Globe,
    body: "Playwright-powered extraction of text, links, metadata, PDFs, and screenshots.",
  },
  {
    title: "Cloud Storage",
    href: "/storage",
    icon: Database,
    body: "Browse S3 buckets, upload and delete objects, generate presigned links.",
  },
] as const;

export default function LandingPage() {
  return (
    <main className={`lpShell ${displayFont.variable}`}>
      <header className="lpNav">
        <div className="lpNavInner">
          <Link href="/" className="lpBrand" aria-label="OmniDev home">
            <Image src="/brand/omnidev-logo.png" alt="" width={30} height={30} priority />
            <span>OmniDev</span>
          </Link>
          <nav className="lpNavLinks" aria-label="Landing navigation">
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

      <section className="lpSection" id="modules">
        <div className="lpContainer">
          <Reveal>
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
          <span>OmniDev, MIT licensed.</span>
          <div className="lpFooterLinks">
            <a href={GITHUB_URL} target="_blank" rel="noreferrer">
              GitHub
            </a>
            <a href={`${GITHUB_URL}/tree/main/docs`} target="_blank" rel="noreferrer">
              Docs
            </a>
            <Link href="/app">Cockpit</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
