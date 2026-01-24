"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useAuth } from "./context/AuthContext";
import { trackEvent } from "./lib/analytics";

const features = [
  { id: "chat", title: "AI Chat", description: "GPT-5 Mini powered conversations", icon: "💬", href: "/chat" },
  { id: "vision", title: "Vision Lab", description: "Image analysis with AI", icon: "🖼️", href: "/vision" },
  { id: "devops", title: "DevOps Agent", description: "AWS cloud management", icon: "🛠️", href: "/devops" },
  { id: "scraper", title: "Web Scraper", description: "Playwright automation", icon: "🕷️", href: "/scraper" },
  { id: "storage", title: "Cloud Storage", description: "S3 file manager", icon: "📦", href: "/storage" },
  { id: "location", title: "Location", description: "GPS & geolocation", icon: "📍", href: "/location" },
];

const techStack = ["FastAPI", "Next.js", "OpenAI", "AWS S3", "Playwright", "Supabase"];

export default function Home() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [backendStatus, setBackendStatus] = useState<"loading" | "online" | "offline">("loading");
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    fetch("/health")
      .then((res) => res.json())
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    if (!user && !authLoading) {
      trackEvent("landing_view");
    }
  }, [user, authLoading]);

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#f5f5f0] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-[#e55c1c]/20 border-t-[#e55c1c] rounded-full animate-spin" />
          <span className="text-[#666] text-sm tracking-wide uppercase">Loading...</span>
        </div>
      </div>
    );
  }

  // Dashboard for logged-in users
  if (user) {
    return (
      <main className="min-h-screen bg-[#f5f5f0] text-[#0a0a0a]" id="main-content">
        {/* Background */}
        <div className="fixed inset-0 grid-pattern pointer-events-none" />

        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md border-b border-[#d4d4c8]">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
                <span className="text-[#f5f5f0] font-bold text-sm">O</span>
              </div>
              <span className="font-semibold text-lg tracking-tight">OmniDev</span>
            </div>
            <div className="flex items-center gap-6">
              <div className={`flex items-center gap-2 text-xs uppercase tracking-wider ${
                backendStatus === "online" ? "text-green-600" : "text-[#666]"
              }`}>
                <span className={`w-2 h-2 rounded-full ${backendStatus === "online" ? "bg-green-500" : "bg-gray-400"}`} />
                {backendStatus === "online" ? "Online" : "Offline"}
              </div>
              <Link href="/settings" className="nav-link">Settings</Link>
              <button onClick={() => signOut()} className="nav-link text-[#666]">
                Sign Out
              </button>
            </div>
          </div>
        </nav>

        {/* Dashboard Content */}
        <div className="pt-28 pb-16 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: reduceMotion ? 0 : 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.4 }}
              className="mb-12"
            >
              <span className="section-label mb-6 block">Dashboard</span>
              <h1 className="text-4xl md:text-5xl font-display mb-4">Welcome back</h1>
              <p className="text-[#666] text-lg">Select a tool to get started.</p>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {features.map((feature, i) => (
                <motion.div
                  key={feature.id}
                  initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: reduceMotion ? 0 : i * 0.06, duration: 0.4 }}
                >
                  <Link href={feature.href} className="feature-card block group">
                    <span className="text-3xl mb-4 block">{feature.icon}</span>
                    <h3 className="text-lg font-semibold mb-1 group-hover:text-[#e55c1c] transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-[#666]">{feature.description}</p>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  // Landing page for visitors - Factory AI inspired
  return (
    <main className="min-h-screen bg-[#f5f5f0] text-[#0a0a0a] relative" id="main-content">
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:px-4 focus:py-2 focus:bg-[#e55c1c] focus:text-white focus:rounded-lg focus:z-50"
      >
        Skip to content
      </a>

      {/* Background Pattern */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md border-b border-[#d4d4c8]/50" aria-label="Primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
              <span className="text-[#f5f5f0] font-bold text-sm">O</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">OmniDev</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="nav-link">Features</Link>
            <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="nav-link">Docs</Link>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <Link href="/auth/login" className="nav-link hidden sm:block">Log In</Link>
            <Link
              href="/auth/signup"
              className="btn-primary text-sm px-4 py-2 sm:px-5 sm:py-2.5"
              onClick={() => trackEvent("cta_signup_nav")}
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 sm:pt-40 pb-18 sm:pb-24 px-4 sm:px-6 min-h-[88vh] flex items-center">
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left - Text Content */}
            <motion.div
              initial={{ opacity: 0, y: reduceMotion ? 0 : 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.6 }}
            >
              <span className="section-label mb-6 sm:mb-8 block">All-in-one</span>
              
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display mb-6 sm:mb-8 leading-[0.95]">
                Build, ship,<br />
                automate —<br />
                in one place.
              </h1>

              <p className="text-lg sm:text-xl text-[#666] leading-relaxed max-w-xl mb-4 sm:mb-5">
                A clean, opinionated workspace that combines AI chat, vision, scraping, and cloud tooling — without context switching.
              </p>
              <p className="text-base sm:text-lg text-[#666] leading-relaxed max-w-xl mb-10 sm:mb-12">
                Designed for demos, prototypes, and real workflows. Fast UI, simple auth, and a backend you can deploy anywhere.
              </p>

              <div className="flex flex-wrap gap-3 sm:gap-4">
                <Link
                  href="/auth/signup"
                  className="btn-primary inline-flex items-center gap-2 text-base px-6 py-3"
                  onClick={() => trackEvent("cta_signup_hero")}
                >
                  Get Started Free
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
                <Link
                  href="https://github.com/himanshu748/omnidev"
                  target="_blank"
                  className="btn-secondary inline-flex items-center gap-2 text-base px-6 py-3"
                  onClick={() => trackEvent("cta_github")}
                >
                  View on GitHub
                </Link>
              </div>

              <div className="mt-10 sm:mt-12 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-[#666]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#e55c1c]" />
                  <span className="font-mono">FastAPI + Next.js</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#e55c1c]" />
                  <span className="font-mono">Supabase Auth</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#e55c1c]" />
                  <span className="font-mono">Render backend</span>
                </div>
              </div>
            </motion.div>

            {/* Right - 3D Network Visualization */}
            <motion.div
              className="relative"
              initial={{ opacity: 0, x: reduceMotion ? 0 : 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: reduceMotion ? 0 : 0.3, duration: 0.6 }}
            >
              <div className="relative w-full aspect-[1/1] max-w-[520px] mx-auto lg:max-w-none" aria-hidden="true">
                <div className="absolute inset-0 rounded-[32px] bg-white/50 border border-[#d4d4c8]/60 shadow-[0_12px_60px_rgba(10,10,10,0.08)]" />
                <svg className="w-full h-full" viewBox="0 0 500 500" fill="none" preserveAspectRatio="xMidYMid meet">
                  <defs>
                    <linearGradient id="heroGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#e55c1c" stopOpacity="0.6" />
                      <stop offset="100%" stopColor="#e55c1c" stopOpacity="0.2" />
                    </linearGradient>
                    <filter id="heroGlow">
                      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                      <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                      </feMerge>
                    </filter>
                    <radialGradient id="nodeGradient">
                      <stop offset="0%" stopColor="#e55c1c" stopOpacity="1" />
                      <stop offset="100%" stopColor="#e55c1c" stopOpacity="0.3" />
                    </radialGradient>
                  </defs>

                  {/* Background grid for depth */}
                  <g opacity="0.08">
                    {Array.from({ length: 10 }).map((_, i) => (
                      <line
                        key={`h-${i}`}
                        x1="0"
                        y1={i * 50}
                        x2="500"
                        y2={i * 50}
                        stroke="#0a0a0a"
                        strokeWidth="1"
                      />
                    ))}
                    {Array.from({ length: 10 }).map((_, i) => (
                      <line
                        key={`v-${i}`}
                        x1={i * 50}
                        y1="0"
                        x2={i * 50}
                        y2="500"
                        stroke="#0a0a0a"
                        strokeWidth="1"
                      />
                    ))}
                  </g>

                  {/* 3D Connection paths with varying opacity for depth */}
                  <path
                    d="M120 180 Q250 150 380 200"
                    stroke="url(#heroGradient)"
                    strokeWidth="3"
                    fill="none"
                    opacity="0.5"
                    filter="url(#heroGlow)"
                  />
                  <path
                    d="M100 250 Q250 220 400 280"
                    stroke="#e55c1c"
                    strokeWidth="2.5"
                    fill="none"
                    opacity="0.4"
                    filter="url(#heroGlow)"
                  />
                  <path
                    d="M150 320 Q250 290 350 350"
                    stroke="url(#heroGradient)"
                    strokeWidth="2"
                    fill="none"
                    opacity="0.3"
                  />
                  <path
                    d="M80 200 L250 180 L420 240"
                    stroke="#d4d4c8"
                    strokeWidth="1.5"
                    strokeDasharray="5 5"
                    fill="none"
                    opacity="0.25"
                  />
                  <path
                    d="M180 120 L280 160 L220 240"
                    stroke="#d4d4c8"
                    strokeWidth="1.5"
                    strokeDasharray="5 5"
                    fill="none"
                    opacity="0.25"
                  />

                  {/* Back layer nodes (smaller, lighter) */}
                  <circle cx="200" cy="120" r="5" fill="#d4d4c8" opacity="0.3" />
                  <circle cx="350" cy="140" r="5" fill="#d4d4c8" opacity="0.3" />
                  <circle cx="150" cy="280" r="5" fill="#d4d4c8" opacity="0.3" />
                  <circle cx="380" cy="300" r="5" fill="#d4d4c8" opacity="0.3" />
                  <circle cx="250" cy="380" r="5" fill="#d4d4c8" opacity="0.3" />

                  {/* Middle layer nodes */}
                  <circle cx="250" cy="200" r="10" fill="url(#nodeGradient)" opacity="0.6" filter="url(#heroGlow)" />
                  <circle cx="150" cy="250" r="10" fill="url(#nodeGradient)" opacity="0.6" filter="url(#heroGlow)" />
                  <circle cx="350" cy="280" r="10" fill="url(#nodeGradient)" opacity="0.6" filter="url(#heroGlow)" />

                  {/* Front layer nodes (larger, brighter) */}
                  <circle cx="180" cy="180" r="16" fill="#e55c1c" filter="url(#heroGlow)" />
                  <circle cx="320" cy="220" r="16" fill="#e55c1c" filter="url(#heroGlow)" />
                  <circle cx="250" cy="320" r="16" fill="#e55c1c" filter="url(#heroGlow)" />

                  {/* Node labels with 3D effect */}
                  <text x="180" y="175" fontSize="11" fill="#0a0a0a" fontWeight="700" textAnchor="middle">AI</text>
                  <text x="320" y="215" fontSize="11" fill="#0a0a0a" fontWeight="700" textAnchor="middle">DevOps</text>
                  <text x="250" y="315" fontSize="11" fill="#0a0a0a" fontWeight="700" textAnchor="middle">Vision</text>
                </svg>

                {/* Floating 3D Cards with rotation */}
                <motion.div
                  className="absolute top-[15%] right-[8%] bg-white/95 backdrop-blur-md border border-[#d4d4c8] rounded-xl px-4 py-3 shadow-xl"
                  style={{ transform: 'perspective(1000px) rotateY(-5deg) rotateX(2deg)' }}
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#e55c1c]" />
                    <span className="text-xs uppercase tracking-wider text-[#0a0a0a] font-semibold">AI Chat</span>
                  </div>
                </motion.div>
                <motion.div
                  className="absolute top-[42%] right-[3%] bg-white/95 backdrop-blur-md border border-[#d4d4c8] rounded-xl px-4 py-3 shadow-xl"
                  style={{ transform: 'perspective(1000px) rotateY(5deg) rotateX(-2deg)' }}
                  animate={{ y: [0, 8, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#e55c1c]" />
                    <span className="text-xs uppercase tracking-wider text-[#0a0a0a] font-semibold">DevOps</span>
                  </div>
                </motion.div>
                <motion.div
                  className="absolute bottom-[22%] right-[12%] bg-white/95 backdrop-blur-md border border-[#d4d4c8] rounded-xl px-4 py-3 shadow-xl"
                  style={{ transform: 'perspective(1000px) rotateY(-3deg) rotateX(3deg)' }}
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#e55c1c]" />
                    <span className="text-xs uppercase tracking-wider text-[#0a0a0a] font-semibold">Vision</span>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tech Stack Marquee */}
      <section className="py-16 sm:py-20 border-y border-[#d4d4c8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-8 sm:gap-12">
            <span className="section-label whitespace-nowrap flex-shrink-0">Built With</span>
            <div className="marquee-container flex-1 overflow-hidden">
              <div className="marquee-content">
                {[...techStack, ...techStack].map((tech, i) => (
                  <span key={i} className="text-[#666] font-mono text-sm sm:text-base whitespace-nowrap px-6 sm:px-8">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 sm:py-32 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="mb-16 sm:mb-20"
            initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <span className="section-label mb-6 sm:mb-8 block">Features</span>
            <h2 className="text-4xl md:text-5xl font-display mb-6 sm:mb-8 max-w-2xl">
              The core tools you’ll demo.
            </h2>
            <p className="text-base sm:text-lg text-[#666] max-w-xl leading-relaxed">
              A tight set of workflows — built to look good on stage, and still hold up under real usage.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {features.map((feature, i) => (
              <motion.div
                key={feature.id}
                className="feature-card group"
                initial={{ opacity: 0, y: reduceMotion ? 0 : 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: reduceMotion ? 0 : i * 0.08 }}
              >
                <div className="flex items-start justify-between mb-5">
                  <span className="text-3xl">{feature.icon}</span>
                  <span className="text-xs text-[#999] font-mono uppercase tracking-wider">0{i + 1}</span>
                </div>
                <h3 className="text-xl font-semibold mb-3 group-hover:text-[#e55c1c] transition-colors">
                  {feature.title}
                </h3>
                <p className="text-[#666] font-mono text-sm leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 sm:py-32 px-4 sm:px-6">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <span className="section-label justify-center mb-6 sm:mb-8 block">Get Started</span>
          <h2 className="text-4xl md:text-5xl font-display mb-8 sm:mb-10 leading-tight">
            Ready to build the<br />software of the future?
          </h2>
          <p className="text-lg sm:text-xl text-[#666] mb-12 sm:mb-14 max-w-lg mx-auto leading-relaxed">
            Free forever for personal use. Start building today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/signup"
              className="btn-primary inline-flex items-center justify-center gap-2 text-base px-8 py-3.5"
              onClick={() => trackEvent("cta_signup_footer")}
            >
              Get Started Free
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
            <Link
              href="/auth/login"
              className="btn-secondary inline-flex items-center justify-center text-base px-8 py-3.5"
            >
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-20 sm:py-24 px-4 sm:px-6 border-t border-[#d4d4c8] bg-gradient-to-b from-white to-[#fafaf5]">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 sm:gap-16 mb-16 sm:mb-20">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-[#0a0a0a] rounded-xl flex items-center justify-center shadow-sm">
                  <span className="text-[#f5f5f0] font-bold text-base">O</span>
                </div>
                <span className="font-bold text-xl tracking-tight">OmniDev</span>
              </div>
              <p className="text-[#666] text-sm sm:text-base leading-relaxed mb-8 max-w-sm">
                AI-powered developer platform. Build faster, automate smarter. 
                All your development tools in one unified interface.
              </p>
              <div className="flex items-center gap-3 sm:gap-4">
                <a 
                  href="https://github.com/himanshu748" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-lg border border-[#d4d4c8] flex items-center justify-center text-[#666] hover:text-[#0a0a0a] hover:border-[#0a0a0a] transition-all"
                  aria-label="GitHub"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                </a>
                <a 
                  href="https://linkedin.com/in/himanshu748" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-lg border border-[#d4d4c8] flex items-center justify-center text-[#666] hover:text-[#0a0a0a] hover:border-[#0a0a0a] transition-all"
                  aria-label="LinkedIn"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </a>
                <a 
                  href="mailto:jhahimanshu653@gmail.com" 
                  className="w-9 h-9 rounded-lg border border-[#d4d4c8] flex items-center justify-center text-[#666] hover:text-[#0a0a0a] hover:border-[#0a0a0a] transition-all"
                  aria-label="Email"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="font-semibold mb-6 text-sm uppercase tracking-wider text-[#0a0a0a]">Product</h4>
              <div className="flex flex-col gap-3 sm:gap-4">
                <Link href="/auth/signup" className="text-[#666] hover:text-[#0a0a0a] text-sm transition-colors">
                  Get Started
                </Link>
                <Link href="/auth/login" className="text-[#666] hover:text-[#0a0a0a] text-sm transition-colors">
                  Sign In
                </Link>
                <Link href="#features" className="text-[#666] hover:text-[#0a0a0a] text-sm transition-colors">
                  Features
                </Link>
              </div>
            </div>

            {/* Resources */}
            <div>
              <h4 className="font-semibold mb-6 text-sm uppercase tracking-wider text-[#0a0a0a]">Resources</h4>
              <div className="flex flex-col gap-3 sm:gap-4">
                <a 
                  href="https://github.com/himanshu748/omnidev" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-[#666] hover:text-[#0a0a0a] text-sm transition-colors"
                >
                  GitHub Repository
                </a>
                <a 
                  href="https://github.com/himanshu748" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-[#666] hover:text-[#0a0a0a] text-sm transition-colors"
                >
                  @himanshu748
                </a>
                <a 
                  href="mailto:jhahimanshu653@gmail.com" 
                  className="text-[#666] hover:text-[#0a0a0a] text-sm transition-colors"
                >
                  Contact
                </a>
              </div>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-10 sm:pt-12 border-t border-[#d4d4c8] flex flex-col sm:flex-row items-center justify-between gap-4 sm:gap-6">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 sm:gap-3">
              <span className="text-[#999] text-sm">© 2024-2026</span>
              <span className="text-[#666] font-semibold text-sm">OmniDev</span>
              <span className="text-[#999] text-sm">•</span>
              <span className="text-[#666] text-sm">Built by Himanshu Kumar</span>
            </div>
            <div className="flex items-center gap-6">
              <span className="text-[#999] text-sm font-mono">v1.0</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
