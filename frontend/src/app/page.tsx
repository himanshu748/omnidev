"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useAuth } from "./context/AuthContext";
import { trackEvent } from "./lib/analytics";

const features = [
  { id: "chat", title: "AI Chat", description: "GPT-5 Mini conversations", icon: "💬", href: "/chat", color: "from-blue-500 to-cyan-500" },
  { id: "vision", title: "Vision Lab", description: "Image analysis & OCR", icon: "🖼️", href: "/vision", color: "from-purple-500 to-pink-500" },
  { id: "devops", title: "DevOps Agent", description: "AWS cloud management", icon: "🛠️", href: "/devops", color: "from-orange-500 to-red-500" },
  { id: "scraper", title: "Web Scraper", description: "Playwright automation", icon: "🕷️", href: "/scraper", color: "from-green-500 to-emerald-500" },
  { id: "storage", title: "Cloud Storage", description: "S3 file manager", icon: "📦", href: "/storage", color: "from-indigo-500 to-blue-500" },
  { id: "location", title: "Location", description: "GPS & geolocation", icon: "📍", href: "/location", color: "from-yellow-500 to-orange-500" },
];

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

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-3 border-slate-300 border-t-slate-900 rounded-full animate-spin" />
          <span className="text-slate-600 text-sm font-medium">Loading...</span>
        </div>
      </div>
    );
  }

  // Dashboard for logged-in users
  if (user) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-900 to-slate-700 flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow">
                <span className="text-white font-bold text-lg">O</span>
              </div>
              <span className="text-xl font-bold text-slate-900">OmniDev</span>
            </Link>
            <div className="flex items-center gap-6">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
                backendStatus === "online" 
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                  : "bg-slate-100 text-slate-600 border border-slate-200"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === "online" ? "bg-emerald-500" : "bg-slate-400"}`} />
                {backendStatus === "online" ? "Online" : "Offline"}
              </div>
              <Link href="/settings" className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors">
                Settings
              </Link>
              <button 
                onClick={() => signOut()} 
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-3">Welcome back</h1>
            <p className="text-lg text-slate-600">Choose a tool to get started</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <Link
                  href={feature.href}
                  className="group block p-6 bg-white rounded-2xl border border-slate-200 hover:border-slate-300 hover:shadow-lg transition-all duration-200"
                >
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-2xl mb-4 shadow-sm group-hover:scale-105 transition-transform`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-1.5 group-hover:text-slate-700 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-600">{feature.description}</p>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </main>
    );
  }

  // Landing page - Modern, clean design
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-900 to-slate-700 flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">O</span>
            </div>
            <span className="text-xl font-bold text-slate-900">OmniDev</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              Features
            </Link>
            <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              GitHub
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              Sign In
            </Link>
            <Link
              href="/auth/signup"
              className="px-5 py-2.5 rounded-lg bg-slate-900 text-white font-semibold text-sm hover:bg-slate-800 transition-colors shadow-sm"
              onClick={() => trackEvent("cta_signup_nav")}
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 border border-slate-200 mb-8">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-sm font-medium text-slate-700">Open Source • Indie Dev Project</span>
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold text-slate-900 mb-6 leading-tight">
              Everything you need.
              <br />
              <span className="bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
                All in one place.
              </span>
            </h1>

            <p className="text-xl text-slate-600 mb-4 max-w-2xl mx-auto leading-relaxed">
              The unified AI developer platform. Chat, vision analysis, cloud automation, 
              and web scraping — no context switching, no fragmented workflows.
            </p>

            <p className="text-lg text-slate-500 mb-12 max-w-xl mx-auto">
              Built by an indie developer to showcase full-stack capabilities.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
              <Link
                href="https://github.com/himanshu748/omnidev"
                target="_blank"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-white border-2 border-slate-200 hover:border-slate-300 text-slate-900 font-semibold transition-all shadow-sm hover:shadow-md"
                onClick={() => trackEvent("cta_github")}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                {githubStars !== null && <span>{githubStars} stars</span>}
                <span>View on GitHub</span>
              </Link>
              <Link
                href="/auth/signup"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 transition-colors shadow-lg hover:shadow-xl"
                onClick={() => trackEvent("cta_signup_hero")}
              >
                Try it Free
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </Link>
            </div>

            {/* Tech Stack */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              {["FastAPI", "Next.js", "OpenAI", "AWS", "TypeScript", "Python"].map((tech) => (
                <span
                  key={tech}
                  className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-sm font-medium text-slate-700"
                >
                  {tech}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
              Six powerful tools.
              <br />
              <span className="text-slate-600">One unified platform.</span>
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              No more switching between tools. Everything you need for AI development, 
              cloud management, and automation in a single interface.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group"
              >
                <div className="p-6 bg-gradient-to-br from-slate-50 to-white rounded-2xl border border-slate-200 hover:border-slate-300 hover:shadow-lg transition-all duration-200 h-full">
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-2xl mb-4 shadow-sm group-hover:scale-105 transition-transform`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-600">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to explore?
            </h2>
            <p className="text-xl text-slate-300 mb-10 max-w-lg mx-auto">
              Try it free or check out the code. Built by an indie developer 
              passionate about creating unified developer experiences.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="https://github.com/himanshu748/omnidev"
                target="_blank"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold transition-all backdrop-blur-sm"
                onClick={() => trackEvent("cta_github_footer")}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                View on GitHub
              </Link>
              <Link
                href="/auth/signup"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-white text-slate-900 font-semibold hover:bg-slate-100 transition-colors shadow-lg"
                onClick={() => trackEvent("cta_signup_footer")}
              >
                Try it Free
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slate-900 to-slate-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">O</span>
            </div>
            <span className="text-slate-600 font-medium">OmniDev v1.0</span>
          </div>
          
          <div className="flex items-center gap-8">
            <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
              GitHub
            </Link>
            <Link href="/auth/login" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
              Sign In
            </Link>
          </div>

          <span className="text-sm text-slate-500">
            Built by <span className="text-slate-700 font-medium">Himanshu Kumar</span> • 2024-2026
          </span>
        </div>
      </footer>
    </main>
  );
}
