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

const techStack = ["FastAPI", "Next.js", "OpenAI GPT-5", "AWS S3", "Playwright", "Supabase", "TypeScript", "Python"];

export default function Home() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [backendStatus, setBackendStatus] = useState<"loading" | "online" | "offline">("loading");
  const [githubStars, setGithubStars] = useState<number | null>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    fetch("/health")
      .then((res) => res.json())
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
    
    // Fetch GitHub stars (optional, won't break if it fails)
    fetch("https://api.github.com/repos/himanshu748/omnidev")
      .then((res) => res.json())
      .then((data) => setGithubStars(data.stargazers_count))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!user && !authLoading) {
      trackEvent("landing_view");
    }
  }, [user, authLoading]);

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-[#e55c1c]/20 border-t-[#e55c1c] rounded-full animate-spin" />
          <span className="text-gray-400 text-sm tracking-wide uppercase">Loading...</span>
        </div>
      </div>
    );
  }

  // Dashboard for logged-in users
  if (user) {
    return (
      <main className="min-h-screen bg-[#f5f5f0] text-[#0a0a0a]" id="main-content">
        <div className="fixed inset-0 grid-pattern pointer-events-none" />

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

  // Landing page - Hybrid Design (Warp dark hero + Factory AI light sections)
  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white" id="main-content">
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:px-4 focus:py-2 focus:bg-[#e55c1c] focus:text-white focus:rounded-lg focus:z-50"
      >
        Skip to content
      </a>

      {/* Dark Hero Section - Warp Inspired */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0a0a0a]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(229,92,28,0.1),transparent_70%)]" />
        
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]" />

        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-white/5" aria-label="Primary">
          <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-[#e55c1c] to-[#ff6b2b] rounded-lg flex items-center justify-center">
                <span className="text-black font-bold text-sm">O</span>
              </div>
              <span className="font-semibold text-lg tracking-tight">OmniDev</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <Link href="#features" className="text-sm text-gray-400 hover:text-white transition-colors">Features</Link>
              <Link href="#platform" className="text-sm text-gray-400 hover:text-white transition-colors">Platform</Link>
              <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="text-sm text-gray-400 hover:text-white transition-colors">GitHub</Link>
            </div>

            <div className="flex items-center gap-4">
              <Link href="/auth/login" className="text-sm text-gray-400 hover:text-white transition-colors">Log In</Link>
              <Link
                href="/auth/signup"
                className="px-5 py-2.5 rounded-lg bg-[#e55c1c] text-white font-semibold text-sm hover:bg-[#ff6b2b] transition-all"
                onClick={() => trackEvent("cta_signup_nav")}
              >
                Get Started
              </Link>
            </div>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 w-full pt-32 pb-20">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left - Text Content */}
            <motion.div
              initial={{ opacity: 0, y: reduceMotion ? 0 : 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.6 }}
            >
              {/* Announcement Banner */}
              <motion.div
                initial={{ opacity: 0, x: reduceMotion ? 0 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#e55c1c]/10 border border-[#e55c1c]/20 mb-8"
              >
                <span className="w-2 h-2 rounded-full bg-[#e55c1c] animate-pulse" />
                <span className="text-sm text-[#e55c1c] font-medium">Indie Dev Project • Open Source</span>
              </motion.div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-[1.05] tracking-tight">
                Everything you need.
                <br />
                <span className="bg-gradient-to-r from-[#e55c1c] to-[#ff6b2b] bg-clip-text text-transparent">
                  All in one place.
                </span>
              </h1>

              <p className="text-xl text-gray-400 mb-4 leading-relaxed max-w-xl">
                The unified AI developer platform. Chat, vision analysis, cloud automation, 
                and web scraping — no context switching, no fragmented workflows.
              </p>

              <p className="text-lg text-gray-500 mb-10 font-mono">
                Built by an indie developer to showcase full-stack capabilities.
              </p>

              {/* CTAs */}
              <div className="flex flex-wrap gap-4 mb-12">
                <Link
                  href="https://github.com/himanshu748/omnidev"
                  target="_blank"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-white font-semibold transition-all"
                  onClick={() => trackEvent("cta_github")}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  {githubStars !== null && (
                    <span className="text-sm">{githubStars} stars</span>
                  )}
                  <span>View on GitHub</span>
                </Link>
                <Link
                  href="/auth/signup"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-[#e55c1c] text-white font-semibold hover:bg-[#ff6b2b] transition-all"
                  onClick={() => trackEvent("cta_signup_hero")}
                >
                  Try it Free
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
              </div>

              {/* Tech Stack Pills */}
              <div className="flex flex-wrap gap-2">
                {techStack.slice(0, 6).map((tech) => (
                  <span
                    key={tech}
                    className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-gray-400 font-mono"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </motion.div>

            {/* Right - Terminal Demo */}
            <motion.div
              className="relative hidden lg:block"
              initial={{ opacity: 0, x: reduceMotion ? 0 : 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <div className="bg-[#0a0a0a] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
                {/* Terminal Header */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10 bg-[#111111]">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/50" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                    <div className="w-3 h-3 rounded-full bg-green-500/50" />
                  </div>
                  <span className="ml-4 text-xs text-gray-500 font-mono">omnidev-terminal</span>
                </div>

                {/* Terminal Content */}
                <div className="p-6 font-mono text-sm">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[#e55c1c]">$</span>
                      <span className="text-gray-300">omnidev chat "Explain Docker"</span>
                    </div>
                    <div className="text-gray-500 pl-4">
                      Docker is a containerization platform...
                    </div>
                    
                    <div className="flex items-center gap-2 mt-4">
                      <span className="text-[#e55c1c]">$</span>
                      <span className="text-gray-300">omnidev vision analyze image.jpg</span>
                    </div>
                    <div className="text-gray-500 pl-4">
                      ✓ Image analyzed: Contains text, objects detected
                    </div>

                    <div className="flex items-center gap-2 mt-4">
                      <span className="text-[#e55c1c]">$</span>
                      <span className="text-gray-300">omnidev devops list-instances</span>
                    </div>
                    <div className="text-gray-500 pl-4">
                      ✓ Found 3 EC2 instances running
                    </div>

                    <div className="flex items-center gap-2 mt-6">
                      <span className="text-[#e55c1c] animate-pulse">$</span>
                      <span className="text-gray-400">_</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating badges */}
              <div className="absolute -bottom-4 -left-4 bg-[#e55c1c] text-black px-4 py-2 rounded-lg text-xs font-bold">
                All-in-One
              </div>
              <div className="absolute -top-4 -right-4 bg-white/10 backdrop-blur-md border border-white/20 text-white px-4 py-2 rounded-lg text-xs font-mono">
                FastAPI + Next.js
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Light Section - Factory AI Inspired */}
      <section id="features" className="py-24 px-6 bg-[#f5f5f0] text-[#0a0a0a]">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="mb-16"
            initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <span className="section-label mb-6 block">Features</span>
            <h2 className="text-4xl md:text-5xl font-display mb-6 max-w-2xl">
              Six powerful tools.<br />
              <span className="text-[#e55c1c]">One unified platform.</span>
            </h2>
            <p className="text-lg text-[#666] font-mono max-w-xl">
              No more switching between tools. Everything you need for AI development, 
              cloud management, and automation in a single interface.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.id}
                className="feature-card group cursor-pointer"
                initial={{ opacity: 0, y: reduceMotion ? 0 : 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: reduceMotion ? 0 : i * 0.08 }}
                onClick={() => window.location.href = feature.href}
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
                Built to showcase<br />
                <span className="text-[#e55c1c]">full-stack expertise.</span>
              </h2>
              <p className="text-[#666] font-mono mb-8 leading-relaxed">
                An indie developer project demonstrating proficiency across the entire stack: 
                from AI integration and cloud services to modern web development and DevOps automation.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-[#f5f5f0] flex items-center justify-center shrink-0">
                    <span className="text-[#e55c1c]">✓</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">Open Source</h4>
                    <p className="text-sm text-[#666] font-mono">Full codebase available on GitHub</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-[#f5f5f0] flex items-center justify-center shrink-0">
                    <span className="text-[#e55c1c]">✓</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">Production Ready</h4>
                    <p className="text-sm text-[#666] font-mono">Deployed and fully functional</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-[#f5f5f0] flex items-center justify-center shrink-0">
                    <span className="text-[#e55c1c]">✓</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">Modern Stack</h4>
                    <p className="text-sm text-[#666] font-mono">FastAPI, Next.js, TypeScript, Python</p>
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
      <section className="py-24 px-6 bg-[#0a0a0a] text-white">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-display mb-6">
            Ready to explore?
          </h2>
          <p className="text-lg text-gray-400 font-mono mb-10 max-w-lg mx-auto">
            Try it free or check out the code. Built by an indie developer 
            passionate about creating unified developer experiences.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="https://github.com/himanshu748/omnidev"
              target="_blank"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-white font-semibold transition-all"
              onClick={() => trackEvent("cta_github_footer")}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              View on GitHub
            </Link>
            <Link
              href="/auth/signup"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-lg bg-[#e55c1c] text-white font-semibold hover:bg-[#ff6b2b] transition-all"
              onClick={() => trackEvent("cta_signup_footer")}
            >
              Try it Free
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5 bg-[#0a0a0a]">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-gradient-to-br from-[#e55c1c] to-[#ff6b2b] rounded flex items-center justify-center">
                <span className="text-black font-bold text-xs">O</span>
              </div>
              <span className="text-gray-400 font-mono text-sm">OmniDev v1.0</span>
            </div>
            
            <div className="flex items-center gap-8">
              <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="text-gray-400 hover:text-white text-sm font-mono transition-colors">
                GitHub
              </Link>
              <Link href="/auth/login" className="text-gray-400 hover:text-white text-sm font-mono transition-colors">
                Sign In
              </Link>
            </div>

            <span className="text-gray-600 text-sm font-mono">
              Built by <span className="text-[#e55c1c]">Himanshu Kumar</span> • 2024-2026
            </span>
          </div>
        </div>
      </footer>
    </main>
  );
}
