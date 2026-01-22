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
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md" aria-label="Primary">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
              <span className="text-[#f5f5f0] font-bold text-sm">O</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">OmniDev</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="nav-link">Features</Link>
            <Link href="#platform" className="nav-link">Platform</Link>
            <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="nav-link">Docs</Link>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="nav-link hidden sm:block">Log In</Link>
            <Link
              href="/auth/signup"
              className="btn-primary"
              onClick={() => trackEvent("cta_signup_nav")}
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 min-h-[85vh] flex items-center">
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left - Text Content */}
            <motion.div
              initial={{ opacity: 0, y: reduceMotion ? 0 : 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.6 }}
            >
              <span className="section-label mb-8 block">Platform</span>
              
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display mb-8 leading-[0.95]">
                AI-Powered<br />
                Developer<br />
                Platform
              </h1>

              <div className="space-y-4 mb-10 max-w-lg">
                <p className="text-lg text-[#666] font-mono leading-relaxed">
                  The only all-in-one platform that handles everything from AI chat to cloud automation.
                </p>
                <p className="text-[#666] font-mono leading-relaxed">
                  From code assistance to DevOps — delegate complete tasks like deployments, 
                  image analysis, and web scraping without switching tools.
                </p>
              </div>

              {/* CLI Install */}
              <div className="bg-white border border-[#d4d4c8] rounded-xl p-1 mb-8 max-w-md">
                <div className="flex items-center gap-2 px-3 py-1 border-b border-[#e8e8dc]">
                  <span className="text-xs uppercase tracking-wider text-[#666] font-medium">Quick Start</span>
                </div>
                <div className="code-block !bg-[#0a0a0a] !rounded-lg m-1">
                  <code className="text-sm">
                    <span className="text-[#e55c1c]">$</span> npx create-omnidev-app my-project
                  </code>
                </div>
              </div>

              <div className="flex flex-wrap gap-4">
                <Link
                  href="/auth/signup"
                  className="btn-primary inline-flex items-center gap-2"
                  onClick={() => trackEvent("cta_signup_hero")}
                >
                  Start Building
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
                <Link
                  href="https://github.com/himanshu748/omnidev"
                  target="_blank"
                  className="btn-secondary inline-flex items-center gap-2"
                  onClick={() => trackEvent("cta_github")}
                >
                  View on GitHub
                </Link>
              </div>
            </motion.div>

            {/* Right - Visual/Graphic */}
            <motion.div
              className="hidden lg:block relative"
              initial={{ opacity: 0, x: reduceMotion ? 0 : 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: reduceMotion ? 0 : 0.3, duration: 0.6 }}
            >
              <div className="relative">
                {/* Connection Lines SVG */}
                <svg className="w-full h-auto" viewBox="0 0 400 400" fill="none">
                  {/* Grid of dots */}
                  {Array.from({ length: 8 }).map((_, row) =>
                    Array.from({ length: 8 }).map((_, col) => (
                      <circle
                        key={`${row}-${col}`}
                        cx={50 + col * 45}
                        cy={50 + row * 45}
                        r={row === 2 && col === 3 || row === 4 && col === 5 || row === 1 && col === 6 ? 8 : 3}
                        fill={row === 2 && col === 3 || row === 4 && col === 5 || row === 1 && col === 6 ? "#e55c1c" : "#d4d4c8"}
                      />
                    ))
                  )}
                  {/* Connection lines */}
                  <path
                    d="M185 140 L275 185 L320 95"
                    stroke="#d4d4c8"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                    fill="none"
                  />
                  <path
                    d="M185 140 L275 230"
                    stroke="#e55c1c"
                    strokeWidth="2"
                    fill="none"
                  />
                  <path
                    d="M275 185 L320 230 L275 275"
                    stroke="#d4d4c8"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                    fill="none"
                  />
                </svg>

                {/* Floating Labels */}
                <div className="absolute top-[20%] right-[10%] bg-white border border-[#d4d4c8] rounded-lg px-4 py-2 shadow-sm">
                  <span className="text-xs uppercase tracking-wider text-[#666]">AI Chat</span>
                </div>
                <div className="absolute top-[45%] right-[5%] bg-white border border-[#d4d4c8] rounded-lg px-4 py-2 shadow-sm">
                  <span className="text-xs uppercase tracking-wider text-[#666]">DevOps</span>
                </div>
                <div className="absolute bottom-[25%] right-[15%] bg-white border border-[#d4d4c8] rounded-lg px-4 py-2 shadow-sm">
                  <span className="text-xs uppercase tracking-wider text-[#666]">Vision</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tech Stack Marquee */}
      <section className="py-12 border-y border-[#d4d4c8]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center gap-8">
            <span className="section-label whitespace-nowrap">Built With</span>
            <div className="marquee-container flex-1">
              <div className="marquee-content">
                {[...techStack, ...techStack].map((tech, i) => (
                  <span key={i} className="text-[#666] font-mono text-sm whitespace-nowrap">{tech}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="mb-16"
            initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <span className="section-label mb-6 block">Features</span>
            <h2 className="text-4xl md:text-5xl font-display mb-6 max-w-2xl">
              Everything you need to ship faster.
            </h2>
            <p className="text-lg text-[#666] font-mono max-w-xl">
              Six powerful tools unified in one platform. No context switching, no fragmented workflows.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.id}
                className="feature-card group cursor-default"
                initial={{ opacity: 0, y: reduceMotion ? 0 : 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: reduceMotion ? 0 : i * 0.08 }}
              >
                <div className="flex items-start justify-between mb-4">
                  <span className="text-3xl">{feature.icon}</span>
                  <span className="text-xs text-[#999] font-mono uppercase">0{i + 1}</span>
                </div>
                <h3 className="text-xl font-semibold mb-2 group-hover:text-[#e55c1c] transition-colors">
                  {feature.title}
                </h3>
                <p className="text-[#666] font-mono text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform Section */}
      <section id="platform" className="py-24 px-6 bg-white border-y border-[#d4d4c8]">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <span className="section-label mb-6 block">Platform</span>
              <h2 className="text-4xl md:text-5xl font-display mb-6">
                AI that works with you, not against you.
              </h2>
              <p className="text-[#666] font-mono mb-8 leading-relaxed">
                OmniDev is designed to enhance your workflow — secure, scalable, and ready 
                to integrate with your existing development tools. Built with modern 
                technologies that developers trust.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-[#f5f5f0] flex items-center justify-center shrink-0">
                    <span className="text-[#e55c1c]">✓</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">Open Source</h4>
                    <p className="text-sm text-[#666] font-mono">Full transparency with MIT license</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-[#f5f5f0] flex items-center justify-center shrink-0">
                    <span className="text-[#e55c1c]">✓</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">Self-Hostable</h4>
                    <p className="text-sm text-[#666] font-mono">Deploy on your own infrastructure</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-[#f5f5f0] flex items-center justify-center shrink-0">
                    <span className="text-[#e55c1c]">✓</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">API-First</h4>
                    <p className="text-sm text-[#666] font-mono">RESTful APIs with full documentation</p>
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              className="relative"
              initial={{ opacity: 0, x: reduceMotion ? 0 : 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="bg-[#0a0a0a] rounded-2xl p-6 text-white font-mono text-sm">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                  <span className="w-3 h-3 rounded-full bg-[#febc2e]" />
                  <span className="w-3 h-3 rounded-full bg-[#28c840]" />
                  <span className="ml-4 text-[#666] text-xs">api-example.py</span>
                </div>
                <pre className="text-[#888] overflow-x-auto">
                  <code>{`from omnidev import Client

client = Client(api_key="your-key")

# AI Chat
response = client.chat.send(
    message="Explain Docker"
)

# Vision Analysis  
analysis = client.vision.analyze(
    image_url="https://..."
)

# DevOps Command
result = client.devops.execute(
    command="list-instances"
)`}</code>
                </pre>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <span className="section-label justify-center mb-8">Get Started</span>
          <h2 className="text-4xl md:text-5xl font-display mb-6">
            Ready to build the<br />software of the future?
          </h2>
          <p className="text-lg text-[#666] font-mono mb-10 max-w-lg mx-auto">
            Free forever for personal use. Start building today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/signup"
              className="btn-primary inline-flex items-center justify-center gap-2"
              onClick={() => trackEvent("cta_signup_footer")}
            >
              Start Building
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
            <Link
              href="/auth/login"
              className="btn-secondary inline-flex items-center justify-center"
            >
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-[#d4d4c8]">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-[#0a0a0a] rounded flex items-center justify-center">
                <span className="text-[#f5f5f0] font-bold text-xs">O</span>
              </div>
              <span className="text-[#666] font-mono text-sm">OmniDev v1.0</span>
            </div>
            
            <div className="flex items-center gap-8">
              <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="text-[#666] hover:text-[#0a0a0a] text-sm font-mono">
                GitHub
              </Link>
              <Link href="/auth/login" className="text-[#666] hover:text-[#0a0a0a] text-sm font-mono">
                Sign In
              </Link>
            </div>

            <span className="text-[#999] text-sm font-mono">
              Built by Himanshu Kumar • 2024-2026
            </span>
          </div>
        </div>
      </footer>
    </main>
  );
}
