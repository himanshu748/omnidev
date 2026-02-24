"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ================================================================
   DATA
   ================================================================ */

const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "Process", href: "#process" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

const FEATURES = [
  {
    emoji: "🤖",
    title: "DevOps Agent",
    href: "/devops",
    desc: 'Manage AWS infrastructure with natural language — "List my EC2 instances", "Launch a t2.micro", "Show security groups".',
    flagship: true,
  },
  {
    emoji: "⚡",
    title: "Code Gen",
    href: "/codegen",
    desc: "Generate websites with Streamlit, React, Node, Python, or any framework. Context7 docs built-in; run in Vercel Sandbox. Site Review shows what the Code Gen UI looks like.",
    star: true,
  },
  {
    emoji: "🕷️",
    title: "Web Scraper",
    href: "/scraper",
    desc: "Playwright-powered scraping with stealth mode, Cloudflare bypass, custom JS execution, and full-page screenshots.",
  },
  {
    emoji: "🖼️",
    title: "Vision Lab",
    href: "/vision",
    desc: "Analyze images and extract text via OpenAI vision models. Upload a screenshot, get structured OCR or analysis back.",
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

const STEPS = [
  {
    num: "01",
    title: "Configure Once",
    body: "Add your OpenAI API key, AWS credentials, and optional IPInfo token to a single .env file. OmniDev wires everything behind one unified FastAPI backend — no boilerplate, no glue code.",
  },
  {
    num: "02",
    title: "Prompt or Trigger",
    body: "Use natural language to manage AWS resources, post a URL to scrape, upload an image for analysis, or call any endpoint directly from the interactive Swagger docs at /docs.",
  },
  {
    num: "03",
    title: "Ship Faster",
    body: "Get structured JSON results instantly. Pipe them into your frontend, CI/CD, or automation scripts. Focus on building product instead of integrating five different SDKs.",
  },
];

const TESTIMONIALS = [
  {
    quote:
      "OmniDev replaced three separate tools in my workflow. The DevOps agent alone saves me 30 minutes a day on AWS management.",
    name: "Alex Chen",
    role: "Indie Hacker",
    initials: "AC",
  },
  {
    quote:
      "The stealth scraper handles Cloudflare sites that broke every other tool I tried. Combined with Vision Lab for OCR, it's incredibly powerful.",
    name: "Priya Sharma",
    role: "Data Engineer",
    initials: "PS",
  },
  {
    quote:
      "Having everything in one FastAPI backend with typed schemas and auto-generated docs is a dream for solo developers.",
    name: "Marcus Rivera",
    role: "Fullstack Developer",
    initials: "MR",
  },
];

const PRICING = [
  {
    name: "Starter",
    price: 0,
    yearlyPrice: 0,
    sub: "Free forever",
    features: [
      "All 5 backend modules",
      "Single-user local setup",
      "Interactive OpenAPI docs",
      "Community support",
      "MIT licensed",
    ],
  },
  {
    name: "Pro Solo",
    price: 29,
    yearlyPrice: 23,
    sub: "per month",
    popular: true,
    features: [
      "Everything in Starter",
      "Priority feature updates",
      "Production-ready frontend",
      "Advanced prompt templates",
      "Direct support channel",
    ],
  },
  {
    name: "Scale",
    price: null,
    yearlyPrice: null,
    sub: "custom pricing",
    features: [
      "Multi-user support (roadmap)",
      "Role-based access control",
      "Observability & audit logs",
      "Custom integrations",
      "Dedicated engineering support",
    ],
  },
];

const FAQS = [
  {
    q: "Is OmniDev designed for solo developers?",
    a: "Yes. This version is intentionally optimized for solo developers — no database, no auth overhead, just fast local tooling. Multi-user support is on the roadmap.",
  },
  {
    q: "What backend stack does it use?",
    a: "Python 3.13 + FastAPI with async handlers, Pydantic schemas, OpenAI SDK, Playwright with stealth, boto3 for AWS, ipinfo for geolocation, and httpx for HTTP.",
  },
  {
    q: "Can I add dashboard pages to the frontend?",
    a: "Absolutely. The frontend uses Next.js 16 App Router, so you can add new routes under app/ and build full dashboard UIs that call the FastAPI backend.",
  },
  {
    q: "Do I need all the API keys to run it?",
    a: "No. Each module works independently. If you only need the scraper, just run the backend without OpenAI or AWS keys — those endpoints will simply return errors when called.",
  },
  {
    q: "Is the scraper able to bypass Cloudflare?",
    a: "It uses playwright-stealth with realistic browser fingerprints, custom user agents, and configurable wait strategies. It handles basic protections well; advanced CAPTCHAs may need proxy rotation.",
  },
];

const STACK_ITEMS = [
  { icon: "🐍", label: "Python" },
  { icon: "⚡", label: "FastAPI" },
  { icon: "▲", label: "Next.js 16" },
  { icon: "🧠", label: "OpenAI" },
  { icon: "🎭", label: "Playwright" },
  { icon: "☁️", label: "AWS boto3" },
  { icon: "🔄", label: "Framer Motion" },
  { icon: "📡", label: "httpx" },
  { icon: "🌐", label: "IPInfo" },
  { icon: "📝", label: "Pydantic" },
];

const COMPARISON_OURS = [
  "One unified backend for 5 AI/cloud services",
  "Natural language AWS management via GPT",
  "Stealth scraping with Cloudflare bypass",
  "Vision AI + OCR built in",
  "Typed schemas + auto-generated docs",
  "Zero-config local development",
];

const COMPARISON_OTHERS = [
  "Separate tools and accounts for each service",
  "Manual CLI or console for AWS",
  "Basic scraping that gets blocked instantly",
  "No built-in image analysis",
  "Untyped APIs, manual documentation",
  "Complex setup with multiple dependencies",
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
  const [activeStep, setActiveStep] = useState(0);
  const [yearly, setYearly] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const cardRefs = useRef<(HTMLElement | null)[]>([]);

  /* Navbar scroll effect */
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  /* Glow-card mouse tracking */
  const handleCardMouse = (e: React.MouseEvent<HTMLElement>, idx: number) => {
    const el = cardRefs.current[idx];
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
    el.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
  };

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
          <a href="http://localhost:8000/docs" className="btn btnPrimary navCta">
            Open API Docs
          </a>
        </div>
      </nav>

      <main>
        {/* ── Hero ──────────────────────────────────────── */}
        <section className="hero section">
          <div className="heroOrb heroOrb1" />
          <div className="heroOrb heroOrb2" />
          <div className="heroOrb heroOrb3" />
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
            <motion.div
              className="heroEyebrow"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              NEW GEN AI DEVELOPER PLATFORM
            </motion.div>

            <motion.h1
              className="heroTitle"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
            >
              Build Smarter. Ship Faster.{" "}
              <span className="gradientText">With OmniDev.</span>
            </motion.h1>

            <motion.p
              className="heroSub"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.25 }}
            >
              One platform to manage AWS in plain English, generate full-stack apps
              with live docs, scrape the web, analyze images, and more — open source and built for makers.
            </motion.p>

            <motion.div
              className="heroActions"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <a href="/devops" className="btn btnPrimary">
                Try DevOps Agent
              </a>
              <a href="#features" className="btn btnGhost">
                Explore Features
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
              <span className="sectionLabel">FEATURES</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Smarter Services, Built with AI
            </motion.h2>
            <motion.p
              className="sectionLead"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={2}
            >
              Everything you need to automate your developer workflow — without
              juggling disconnected tools and services.
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
                  Natural Language
                  <br />
                  <span className="gradientText">DevOps Automation</span>
                </h3>
                <p>
                  Send a plain-English command to the DevOps Agent. It parses
                  your intent with OpenAI, dispatches the matching AWS boto3
                  call, and returns a human-readable summary — all through one
                  POST endpoint.
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
              Our Simple &amp; Smart Process
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

        {/* ── Testimonials ─────────────────────────────── */}
        <section className="section sectionAlt">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">REVIEWS</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Trusted by Developers
            </motion.h2>

            <motion.div
              className="testimonialGrid"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={stagger}
            >
              {TESTIMONIALS.map((t, i) => (
                <motion.div
                  key={t.name}
                  className="testimonialCard"
                  variants={fadeUp}
                  custom={i}
                >
                  <div className="testimonialStars">★★★★★</div>
                  <blockquote>&ldquo;{t.quote}&rdquo;</blockquote>
                  <div className="testimonialAuthor">
                    <div className="testimonialAvatar">{t.initials}</div>
                    <div className="testimonialMeta">
                      <strong>{t.name}</strong>
                      <span>{t.role}</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── Pricing ──────────────────────────────────── */}
        <section id="pricing" className="section">
          <div className="container">
            <motion.div
              style={{ display: "flex", justifyContent: "center" }}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={0}
            >
              <span className="sectionLabel">PRICING</span>
            </motion.div>
            <motion.h2
              className="sectionTitle"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Flexible Plans for Everyone
            </motion.h2>

            <div className="pricingToggle">
              <span>Monthly</span>
              <button
                className={`toggleSwitch ${yearly ? "active" : ""}`}
                onClick={() => setYearly(!yearly)}
                aria-label="Toggle yearly pricing"
              >
                <div className="toggleKnob" />
              </button>
              <span>Yearly</span>
              <span className="saveBadge">Save 20%</span>
            </div>

            <motion.div
              className="priceGrid"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={stagger}
            >
              {PRICING.map((p, i) => (
                <motion.article
                  key={p.name}
                  className={`priceCard ${p.popular ? "popular" : ""}`}
                  variants={fadeUp}
                  custom={i}
                >
                  {p.popular && <span className="popularBadge">Popular</span>}
                  <p className="priceName">{p.name}</p>
                  <p className="priceAmount">
                    {p.price !== null ? (
                      <>
                        ${yearly ? p.yearlyPrice : p.price}
                        <span> /mo</span>
                      </>
                    ) : (
                      "Custom"
                    )}
                  </p>
                  <p className="priceSub">{p.sub}</p>
                  <ul className="priceFeatures">
                    {p.features.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                  <button className="btn btnPrimary btnBlock">Get Started</button>
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
              Ready to Build{" "}
              <span className="gradientText">Smarter</span>?
            </motion.h2>
            <motion.p
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={1}
            >
              Start with the backend foundation you already have, and layer this
              frontend into your production flow.
            </motion.p>
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={fadeUp}
              custom={2}
              style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}
            >
              <a href="http://localhost:8000/docs" className="btn btnPrimary">
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
                All-in-One AI Developer Platform. Built for solo developers who
                want to move fast without juggling five tools.
              </p>
            </div>
            <div className="footerCol">
              <h4>Platform</h4>
              <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="#faq">FAQ</a></li>
                <li><a href="http://localhost:8000/docs">API Docs</a></li>
              </ul>
            </div>
            <div className="footerCol">
              <h4>Modules</h4>
              <ul>
                <li><a href="/devops">DevOps Agent</a></li>
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
                <li><a href="https://platform.openai.com" target="_blank" rel="noopener">OpenAI API</a></li>
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
