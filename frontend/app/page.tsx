"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE } from "@/lib/api";

/* ================================================================
   DATA
   ================================================================ */

const NAV_LINKS = [
  { label: "Setup", href: "#setup" },
  { label: "Modules", href: "#features" },
  { label: "Process", href: "#process" },
  { label: "Proof", href: "#proof" },
];

const FEATURES = [
  {
    emoji: "🤖",
    title: "DevOps Agent",
    href: "/devops",
    desc: 'Run AWS commands from a local dashboard or API — "List my EC2 instances", "Show security groups", "Create an S3 bucket".',
    flagship: true,
  },
  {
    emoji: "⚡",
    title: "Code Gen",
    href: "/codegen",
    desc: "Generate app scaffolds with Gemini and Context7-backed docs, then inspect the result before wiring it into your workflow.",
    star: true,
  },
  {
    emoji: "🕷️",
    title: "Web Scraper",
    href: "/scraper",
    desc: "Playwright-powered scraping for metadata, links, PDFs, screenshots, and custom waits while keeping bot-protection limits explicit.",
  },
  {
    emoji: "🖼️",
    title: "Vision Lab",
    href: "/vision",
    desc: "Analyze images and extract text via AI vision models. Upload a screenshot, get structured OCR or analysis back.",
  },
  {
    emoji: "📦",
    title: "Cloud Storage",
    href: "/storage",
    desc: "Full S3 file manager API — list buckets, browse objects, upload files, generate presigned downloads, and delete.",
  },
  {
    emoji: "📍",
    title: "Location Services",
    href: "/location",
    desc: "IP geolocation, GPS reverse geocoding, and public IP detection — all through clean REST endpoints.",
  },
];

const MODULE_COUNT = FEATURES.length;

const LOCAL_COMMANDS = [
  "cd backend && python -m uvicorn app.main:app --reload",
  "cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev",
];

const CONFIG_ITEMS = [
  { label: "Default API", value: "http://localhost:8000" },
  { label: "Override", value: "NEXT_PUBLIC_API_URL" },
  { label: "Docs", value: "/docs" },
];

const STEPS = [
  {
    num: "01",
    title: "Run the API Locally",
    body: "Start the FastAPI backend on port 8000. The frontend points there by default, so local development works before you touch a hosted environment.",
  },
  {
    num: "02",
    title: "Configure Only What You Use",
    body: "Add Gemini, AWS, and optional IPInfo keys module by module. Missing credentials are surfaced by the relevant endpoint instead of blocking the whole app.",
  },
  {
    num: "03",
    title: "Point Hosted UI at Any API",
    body: "Set NEXT_PUBLIC_API_URL when deploying the frontend so the same dashboards can target a local tunnel, staging API, or production backend.",
  },
];

const PROOF_POINTS = [
  {
    metric: "6",
    label: "Working Modules",
    body: "DevOps, Code Gen, Scraper, Vision, Storage, and Location are wired through typed FastAPI routes and dedicated frontend pages.",
  },
  {
    metric: "2",
    label: "Runtime Surfaces",
    body: "A FastAPI backend exposes OpenAPI docs while the Next.js app gives each service a focused dashboard instead of a generic demo shell.",
  },
  {
    metric: "14+",
    label: "Tested Flows",
    body: "Backend pytest coverage and frontend Playwright specs cover health checks, mocked API flows, and the core module screens.",
  },
];

const RUNBOOK = [
  {
    title: "Install Both Sides",
    detail: "Install Python dependencies in `backend/` and Node dependencies in `frontend/`. Keep each runtime independent so failures are easier to isolate.",
  },
  {
    title: "Start Local API First",
    detail: "Run the FastAPI server on `http://localhost:8000`, then open the Next.js app. The frontend uses that URL unless `NEXT_PUBLIC_API_URL` is set.",
  },
  {
    title: "Deploy with an Explicit API",
    detail: "For Vercel, Netlify, or any hosted UI, set `NEXT_PUBLIC_API_URL` to the reachable backend URL before building.",
  },
];

const FAQS = [
  {
    q: "Is OmniDev designed for solo developers?",
    a: "Yes. This version is intentionally optimized for local solo development — no database, no auth overhead, just focused dashboards backed by a FastAPI server you control.",
  },
  {
    q: "What backend stack does it use?",
    a: "Python 3.13 + FastAPI with async handlers, Pydantic schemas, Google Gemini SDK, Playwright with stealth, boto3 for AWS, ipinfo for geolocation, and httpx for HTTP.",
  },
  {
    q: "Can I add dashboard pages to the frontend?",
    a: "Absolutely. The frontend uses Next.js 16 App Router, so you can add new routes under app/ and build full dashboard UIs that call the FastAPI backend.",
  },
  {
    q: "Do I need all the API keys to run it?",
    a: "No. Each module works independently. If you only need the scraper, start the backend without AI or AWS keys; AI and AWS endpoints will report missing credentials only when called.",
  },
  {
    q: "Can the scraper handle protected sites?",
    a: "It uses playwright-stealth, realistic browser fingerprints, custom user agents, proxies, and configurable wait strategies. Advanced bot protections and CAPTCHAs can still block automation.",
  },
];

const STACK_ITEMS = [
  { icon: "🐍", label: "Python" },
  { icon: "⚡", label: "FastAPI" },
  { icon: "▲", label: "Next.js 16" },
  { icon: "🧠", label: "Gemini AI" },
  { icon: "🎭", label: "Playwright" },
  { icon: "☁️", label: "AWS boto3" },
  { icon: "🔄", label: "Framer Motion" },
  { icon: "📡", label: "httpx" },
  { icon: "🌐", label: "IPInfo" },
  { icon: "📝", label: "Pydantic" },
];

const COMPARISON_OURS = [
  `One local FastAPI backend for ${MODULE_COUNT} AI/cloud modules`,
  "Configurable API URL for hosted frontends",
  "Natural-language AWS management via Gemini",
  "Browser automation with screenshots, PDFs, links, and metadata",
  "Typed schemas and auto-generated OpenAPI docs",
  "Module-level credentials instead of all-or-nothing setup",
];

const COMPARISON_OTHERS = [
  "Disconnected scripts for each workflow",
  "Frontend hard-coded to one backend URL",
  "Manual CLI or console work for AWS",
  "Scraping, OCR, storage, and geo split across tools",
  "Untyped APIs and hand-written docs",
  "Credential setup hidden until runtime failures",
];

/* ================================================================
   ANIMATION VARIANTS
   ================================================================ */

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      delay: i * 0.08,
      ease: [0.25, 0.1, 0.25, 1] as [number, number, number, number],
    },
  }),
};

const stagger = {
  visible: { transition: { staggerChildren: 0.08 } },
};

/* ================================================================
   COMPONENT
   ================================================================ */

export default function HomePage() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const docsHref = `${API_BASE}/docs`;
  const cardRefs = useRef<(HTMLElement | null)[]>([]);

  /* Navbar scroll effect */
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth > 640) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  /* Glow-card mouse tracking */
  const handleCardMouse = (e: React.MouseEvent<HTMLElement>, idx: number) => {
    const el = cardRefs.current[idx];
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
    el.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
  };

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <>
      {/* ── Navbar ─────────────────────────────────────── */}
      <nav className={`navbar ${scrolled ? "scrolled" : ""}`}>
        <div className="navInner">
          <a href="#" className="navLogo">
            Omni<span>Dev</span>
          </a>
          <ul className="navLinks">
            {NAV_LINKS.map((l) => (
              <li key={l.href}>
                <a href={l.href}>{l.label}</a>
              </li>
            ))}
          </ul>
          <div className="navActions">
            <a href={docsHref} className="btn btnPrimary navCta">
              Open API Docs
            </a>
            <button
              type="button"
              className={`mobileMenuBtn ${mobileMenuOpen ? "open" : ""}`}
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu-panel"
            >
              <span />
              <span />
              <span />
            </button>
          </div>
        </div>
      </nav>
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            id="mobile-menu-panel"
            className="mobileMenuPanel"
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
          >
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href} onClick={closeMobileMenu}>
                {l.label}
              </a>
            ))}
            <a href={docsHref} className="btn btnPrimary" onClick={closeMobileMenu}>
              Open API Docs
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      <main>
        {/* ── Hero ──────────────────────────────────────── */}
        <section className="hero section">
          <div className="heroImageLayer" aria-hidden>
            <img src="/images/omni-hero-bg.svg" alt="" />
          </div>
          <div className="heroShapes" aria-hidden>
            <svg viewBox="0 0 1200 800" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="heroLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity="0" />
                  <stop offset="50%" stopColor="var(--accent)" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                </linearGradient>
                <radialGradient id="heroDotGrad" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                </radialGradient>
              </defs>
              <circle cx="150" cy="120" r="120" fill="url(#heroDotGrad)" />
              <circle cx="1050" cy="650" r="180" fill="url(#heroDotGrad)" />
              <line x1="0" y1="400" x2="1200" y2="400" stroke="url(#heroLineGrad)" strokeWidth="1" opacity="0.6" />
              <line x1="600" y1="0" x2="600" y2="800" stroke="url(#heroLineGrad)" strokeWidth="1" opacity="0.4" />
            </svg>
          </div>

          <div className="heroContent container">
            <div className="heroIntro">
              <motion.div
                className="heroEyebrow"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
              >
                LOCAL-FIRST AI DEVELOPER WORKBENCH
              </motion.div>

              <motion.h1
                className="heroTitle"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.1 }}
              >
                OmniDev runs on your machine first.
              </motion.h1>

              <motion.p
                className="heroSub"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.25 }}
              >
                A local FastAPI backend and focused Next.js dashboards for AWS
                automation, code generation, scraping, vision, storage, and
                location tools. Deploy the UI later by setting one API URL.
              </motion.p>
            </div>

            <div
              className="localSetupPanel"
              id="setup"
            >
              <div className="localSetupHeader">
                <span className="statusDot" />
                <div>
                  <strong>Local API target</strong>
                  <p>Frontend requests currently point to:</p>
                </div>
                <code>{API_BASE}</code>
              </div>
              <div className="localCommandList" aria-label="Local startup commands">
                {LOCAL_COMMANDS.map((command) => (
                  <code key={command}>{command}</code>
                ))}
              </div>
              <div className="localConfigGrid">
                {CONFIG_ITEMS.map((item) => (
                  <div key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
            </div>

            <motion.div
              className="heroActions"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <a href="/devops" className="btn btnPrimary">
                Try DevOps Agent
              </a>
              <a href={docsHref} className="btn btnGhost">
                Open API Docs
              </a>
              <a href="#setup" className="btn btnGhost">
                Configure API
              </a>
            </motion.div>

            <motion.div
              className="heroStack"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              {STACK_ITEMS.slice(0, 7).map((s) => (
                <div key={s.label} className="heroStackItem">
                  <span>{s.icon}</span> {s.label}
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── Marquee ──────────────────────────────────── */}
        <div className="marqueeWrap">
          <div className="marqueeTrack">
            {[...STACK_ITEMS, ...STACK_ITEMS].map((s, i) => (
              <div key={i} className="marqueeItem">
                <span>{s.icon}</span> {s.label}
              </div>
            ))}
          </div>
        </div>

        {/* ── Features ─────────────────────────────────── */}
        <section id="features" className="section">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">MODULES</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Modules That Work as Local Tools
            </motion.h2>
            <motion.p
              className="sectionLead"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={2}
            >
              Each module has a dashboard, typed API route, and clear dependency
              boundary so you can run only the pieces you actually need.
            </motion.p>

            <motion.div
              className="featureGrid"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={stagger}
            >
              {FEATURES.map((f, i) => (
                <motion.a
                  key={f.title}
                  href={f.href}
                  className="glowCard"
                  variants={fadeUp}
                  custom={i}
                  ref={(el) => { cardRefs.current[i] = el; }}
                  onMouseMove={(e) => handleCardMouse(e, i)}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div className="cardEmoji">{f.emoji}</div>
                  <h3>
                    {f.title}
                    {"flagship" in f && (f as { flagship?: boolean }).flagship && (
                      <span className="featureFlagshipBadge">Flagship</span>
                    )}
                    {"star" in f && (f as { star?: boolean }).star && (
                      <span className="featureStarBadge">★ Star</span>
                    )}
                  </h3>
                  <p>{f.desc}</p>
                </motion.a>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── Code Demo ────────────────────────────────── */}
        <section className="section sectionAlt">
          <div className="container">
            <motion.div
              className="codeDemoWrap"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              variants={stagger}
            >
              <motion.div className="codeDemoText" variants={fadeUp} custom={0}>
                <span className="sectionLabel">DEVELOPER EXPERIENCE</span>
                <h3>
                  API-first
                  <br />
                  <span className="gradientText">DevOps Automation</span>
                </h3>
                <p>
                  Send a plain-English command to the local DevOps Agent. It
                  parses intent with Gemini, dispatches the matching AWS boto3
                  call, and returns a human-readable summary through one POST
                  endpoint.
                </p>
              </motion.div>

              <motion.div className="codeBlock" variants={fadeUp} custom={1}>
                <div className="codeBlockHeader">
                  <span className="codeDot" />
                  <span className="codeDot" />
                  <span className="codeDot" />
                </div>
                <div className="codeBlockBody">
                  <pre>
                    <code
                      dangerouslySetInnerHTML={{
                        __html: [
                          `${ln(1)}${kw("import")} ${vr("httpx")}`,
                          `${ln(2)}`,
                          `${ln(3)}${cm("# Talk to AWS in plain English")}`,
                          `${ln(4)}${vr("resp")} = ${vr("httpx")}.${fn("post")}(`,
                          `${ln(5)}    ${st('"http://localhost:8000/api/devops/command"')},`,
                          `${ln(6)}    ${vr("json")}=${pr("{")}`,
                          `${ln(7)}        ${st('"message"')}: ${st('"List my EC2 instances"')},`,
                          `${ln(8)}    ${pr("}")}`,
                          `${ln(9)})`,
                          `${ln(10)}`,
                          `${ln(11)}${vr("data")} = ${vr("resp")}.${fn("json")}()`,
                          `${ln(12)}${kw("print")}(${vr("data")}[${st('"summary"')}])`,
                          `${ln(13)}${cm("# → You have 3 running EC2 instances...")}`,
                          `${ln(14)}${cm("#   i-0abc12 (t2.micro, running)")}`,
                          `${ln(15)}${cm("#   i-0def34 (t3.medium, running)")}`,
                        ].join("\n"),
                      }}
                    />
                  </pre>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* ── Process ──────────────────────────────────── */}
        <section id="process" className="section">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">PROCESS</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Local First, Hosted When Ready
            </motion.h2>

            <div className="stepTabs">
              {STEPS.map((s, i) => (
                <button
                  key={s.num}
                  className={`stepTab ${activeStep === i ? "stepTabActive" : ""}`}
                  onClick={() => setActiveStep(i)}
                >
                  STEP {i + 1}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={activeStep}
                className="stepContent"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.35 }}
              >
                <div className="stepNumber">{STEPS[activeStep].num}</div>
                <div className="stepBody">
                  <h3>{STEPS[activeStep].title}</h3>
                  <p>{STEPS[activeStep].body}</p>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </section>

        {/* ── Proof ────────────────────────────────────── */}
        <section id="proof" className="section sectionAlt">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">PROOF</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Built Like a Real Developer Tool
            </motion.h2>
            <motion.p
              className="sectionLead"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={2}
            >
              OmniDev is strongest when it shows the actual engineering: typed
              backend modules, focused dashboards, and tests around the core
              flows.
            </motion.p>

            <motion.div
              className="proofGrid"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={stagger}
            >
              {PROOF_POINTS.map((point, i) => (
                <motion.div
                  key={point.label}
                  className="proofCard"
                  variants={fadeUp}
                  custom={i}
                >
                  <strong>{point.metric}</strong>
                  <h3>{point.label}</h3>
                  <p>{point.body}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── Runbook ──────────────────────────────────── */}
        <section className="section">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">RUNBOOK</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              From Clone to Useful in Minutes
            </motion.h2>

            <motion.div
              className="runbookGrid"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={stagger}
            >
              {RUNBOOK.map((step, i) => (
                <motion.article
                  key={step.title}
                  className="runbookCard"
                  variants={fadeUp}
                  custom={i}
                >
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <h3>{step.title}</h3>
                  <p>{step.detail}</p>
                </motion.article>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── FAQ ──────────────────────────────────────── */}
        <section id="faq" className="section sectionAlt">
          <div className="narrow">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">FAQ</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Frequently Asked Questions
            </motion.h2>

            <div className="faqList">
              {FAQS.map((f, i) => (
                <motion.div
                  key={i}
                  className="faqItem"
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, amount: 0.2 }}
                  variants={fadeUp}
                  custom={i}
                >
                  <button
                    className="faqQuestion"
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    aria-expanded={openFaq === i}
                  >
                    {f.q}
                    <span
                      className="faqChevron"
                      style={{
                        transform: openFaq === i ? "rotate(180deg)" : "rotate(0)",
                      }}
                    >
                      ▾
                    </span>
                  </button>
                  <AnimatePresence initial={false}>
                    {openFaq === i && (
                      <motion.div
                        className="faqAnswer"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                      >
                        <p>{f.a}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Comparison ───────────────────────────────── */}
        <section className="section">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">COMPARISON</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Why Choose OmniDev
            </motion.h2>

            <motion.div
              className="comparisonGrid"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.15 }}
              variants={stagger}
            >
              <motion.div
                className="comparisonCol ours"
                variants={fadeUp}
                custom={0}
              >
                <p className="comparisonColTitle">OmniDev</p>
                <ul className="comparisonList">
                  {COMPARISON_OURS.map((c) => (
                    <li key={c}>
                      <span className="checkIcon">✓</span> {c}
                    </li>
                  ))}
                </ul>
              </motion.div>
              <motion.div
                className="comparisonCol others"
                variants={fadeUp}
                custom={1}
              >
                <p className="comparisonColTitle">Others</p>
                <ul className="comparisonList">
                  {COMPARISON_OTHERS.map((c) => (
                    <li key={c}>
                      <span className="crossIcon">✕</span> {c}
                    </li>
                  ))}
                </ul>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────── */}
        <section className="section sectionAlt ctaSection">
          <div className="narrow">
            <motion.h2
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              Start Local, Then Wire the Host.
            </motion.h2>
            <motion.p
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Keep <code>localhost:8000</code> for development. Set{" "}
              <code>NEXT_PUBLIC_API_URL</code> when the frontend needs to talk
              to a remote backend.
            </motion.p>
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={2}
              style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}
            >
              <a href={docsHref} className="btn btnPrimary">
                Open API Docs
              </a>
              <a href="#features" className="btn btnGhost">
                Explore Features
              </a>
            </motion.div>
          </div>
        </section>
      </main>

      {/* ── Footer ─────────────────────────────────────── */}
      <footer className="footer">
        <div className="container">
          <div className="footerGrid">
            <div className="footerBrand">
              <a href="#" className="navLogo">
                Omni<span>Dev</span>
              </a>
              <p>
                Local-first AI developer workbench. Built for solo developers
                who want one configurable API behind focused dashboards.
              </p>
            </div>
            <div className="footerCol">
              <h4>Platform</h4>
              <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#proof">Proof</a></li>
                <li><a href="#faq">FAQ</a></li>
                <li><a href={docsHref}>API Docs</a></li>
              </ul>
            </div>
            <div className="footerCol">
              <h4>Modules</h4>
              <ul>
                <li><a href="/devops">DevOps Agent</a></li>
                <li><a href="/codegen">Code Gen</a></li>
                <li><a href="/scraper">Web Scraper</a></li>
                <li><a href="/vision">Vision Lab</a></li>
                <li><a href="/storage">Cloud Storage</a></li>
                <li><a href="/location">Location</a></li>
              </ul>
            </div>
            <div className="footerCol">
              <h4>Stack</h4>
              <ul>
                <li><a href="https://fastapi.tiangolo.com" target="_blank" rel="noopener">FastAPI</a></li>
                <li><a href="https://nextjs.org" target="_blank" rel="noopener">Next.js 16</a></li>
                <li><a href="https://aistudio.google.com" target="_blank" rel="noopener">Gemini AI</a></li>
                <li><a href="https://playwright.dev" target="_blank" rel="noopener">Playwright</a></li>
              </ul>
            </div>
          </div>
          <div className="footerBottom">
            <span>&copy; {new Date().getFullYear()} OmniDev. Built for builders.</span>
            <div className="footerSocials">
              <a href="https://github.com" target="_blank" rel="noopener" aria-label="GitHub">GitHub</a>
              <a href="https://twitter.com" target="_blank" rel="noopener" aria-label="Twitter">Twitter</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}

/* ================================================================
   Syntax-highlight helpers (inline, no deps)
   ================================================================ */

function ln(n: number) {
  return `<span class="codeLineNum">${String(n).padStart(2)}</span>`;
}
function kw(s: string) {
  return `<span class="codeKeyword">${s}</span>`;
}
function fn(s: string) {
  return `<span class="codeFunc">${s}</span>`;
}
function st(s: string) {
  return `<span class="codeStr">${s}</span>`;
}
function cm(s: string) {
  return `<span class="codeComment">${s}</span>`;
}
function vr(s: string) {
  return `<span class="codeVar">${s}</span>`;
}
function pr(s: string) {
  return `<span class="codeProp">${s}</span>`;
}
