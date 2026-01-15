"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useAuth } from "./context/AuthContext";

export default function Home() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [backendStatus, setBackendStatus] = useState<"loading" | "online" | "offline">("loading");

  useEffect(() => {
    fetch("/health")
      .then((res) => res.json())
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-12 h-12 border-2 border-[#39ff14]/30 border-t-[#39ff14] rounded-full animate-spin" />
      </div>
    );
  }

  // LOGGED IN: Show Dashboard
  if (user) {
    const features = [
      { id: "chat", title: "AI Chat", description: "GPT-5 Mini powered conversations", icon: "💬", href: "/chat", color: "#39ff14" },
      { id: "vision", title: "Vision Lab", description: "Image analysis with AI", icon: "🖼️", href: "/vision", color: "#00d4ff" },
      { id: "devops", title: "DevOps Agent", description: "AWS cloud management", icon: "🛠️", href: "/devops", color: "#ff6b35" },
      { id: "scraper", title: "Web Scraper", description: "Playwright automation", icon: "🕷️", href: "/scraper", color: "#a855f7" },
      { id: "storage", title: "Cloud Storage", description: "S3 file manager", icon: "📦", href: "/storage", color: "#06b6d4" },
      { id: "location", title: "Location", description: "GPS & geolocation", icon: "📍", href: "/location", color: "#f59e0b" },
    ];

    return (
      <main className="min-h-screen bg-[#050505] text-white">
        {/* Background */}
        <div className="fixed inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-[linear-gradient(rgba(57,255,20,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(57,255,20,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />
        </div>

        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/60 border-b border-white/5">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#39ff14] flex items-center justify-center font-bold text-black">O</div>
              <span className="text-xl font-bold">OmniDev</span>
            </div>
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1.5 rounded-full text-xs font-medium ${backendStatus === "online" ? "bg-[#39ff14]/10 text-[#39ff14]" : "bg-white/5 text-gray-500"}`}>
                {backendStatus === "online" ? "● API Online" : "○ Offline"}
              </div>
              <Link href="/settings" className="px-4 py-2 rounded-lg border border-white/10 text-sm hover:bg-white/5 transition">
                ⚙️ Settings
              </Link>
              <button onClick={() => signOut()} className="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white transition">
                Logout
              </button>
            </div>
          </div>
        </nav>

        {/* Dashboard Content */}
        <div className="pt-28 pb-12 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
              <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
              <p className="text-gray-400">Select a tool to get started</p>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, i) => (
                <motion.div
                  key={feature.id}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Link
                    href={feature.href}
                    className="block p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/20 transition-all group"
                  >
                    <div
                      className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl mb-4"
                      style={{ background: `${feature.color}15`, border: `1px solid ${feature.color}30` }}
                    >
                      {feature.icon}
                    </div>
                    <h3 className="text-lg font-semibold mb-1 group-hover:text-[#39ff14] transition">{feature.title}</h3>
                    <p className="text-sm text-gray-500">{feature.description}</p>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  // NOT LOGGED IN: Show Marketing Page
  return (
    <main className="min-h-screen bg-[#050505] text-white relative overflow-x-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(57,255,20,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(57,255,20,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-[#39ff14]/5 rounded-full blur-[150px]" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/60 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#39ff14] flex items-center justify-center font-bold text-black">O</div>
            <span className="text-xl font-bold">OmniDev</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-gray-400 hover:text-white transition">Login</Link>
            <Link href="/auth/signup" className="px-4 py-2 rounded-lg bg-[#39ff14] text-black font-semibold text-sm hover:opacity-90 transition">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="inline-block mb-6">
            <span className="px-4 py-2 rounded-full text-sm font-medium bg-[#39ff14]/10 text-[#39ff14] border border-[#39ff14]/20">
              ✨ Powered by GPT-5 Mini
            </span>
          </motion.div>

          <motion.h1
            className="text-5xl md:text-7xl font-bold mb-6 leading-[1.1]"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            Build Faster.<br />
            <span className="text-[#39ff14]">Automate Smarter.</span>
          </motion.h1>

          <motion.p
            className="text-lg text-gray-400 max-w-2xl mx-auto mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            The all-in-one AI developer platform. Chat, vision analysis, cloud automation, and web scraping — unified in a beautiful interface.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Link href="/auth/signup" className="px-8 py-4 rounded-xl bg-[#39ff14] text-black font-semibold text-lg hover:opacity-90 transition shadow-lg shadow-[#39ff14]/20">
              Get Started Free →
            </Link>
            <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="px-8 py-4 rounded-xl border border-white/10 text-white font-semibold text-lg hover:bg-white/5 transition">
              ⭐ Star on GitHub
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            className="text-3xl md:text-4xl font-bold text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            Everything you need to <span className="text-[#39ff14]">ship faster</span>
          </motion.h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: "💬", title: "AI Chat", desc: "GPT-5 Mini conversations" },
              { icon: "🖼️", title: "Vision Lab", desc: "Image analysis & OCR" },
              { icon: "🛠️", title: "DevOps Agent", desc: "AWS cloud management" },
              { icon: "🕷️", title: "Web Scraper", desc: "Playwright automation" },
              { icon: "📦", title: "Cloud Storage", desc: "S3 file manager" },
              { icon: "📍", title: "Location", desc: "GPS & geolocation" },
            ].map((f, i) => (
              <motion.div
                key={f.title}
                className="p-6 rounded-2xl bg-white/[0.02] border border-white/5"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="text-3xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-semibold mb-1">{f.title}</h3>
                <p className="text-sm text-gray-500">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <motion.div
          className="max-w-3xl mx-auto text-center p-12 rounded-3xl bg-[#39ff14]/5 border border-[#39ff14]/20"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-gray-400 mb-8">Free forever for personal use.</p>
          <Link href="/auth/signup" className="inline-block px-10 py-4 rounded-xl bg-[#39ff14] text-black font-semibold text-lg hover:opacity-90 transition">
            Create Free Account →
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <span className="text-gray-500">OmniDev v1.0</span>
          <span className="text-gray-600 text-sm">Built by Himanshu Kumar • 2024-2026</span>
        </div>
      </footer>
    </main>
  );
}
