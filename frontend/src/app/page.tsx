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

  const stats = [
    { value: "GPT-5", label: "AI Model" },
    { value: "6+", label: "Tools" },
    { value: "100%", label: "Open Source" },
    { value: "∞", label: "Possibilities" },
  ];

  const features = [
    {
      icon: "💬",
      title: "AI Chat",
      description: "Have intelligent conversations powered by GPT-5 Mini with markdown support and code highlighting.",
      color: "#39ff14",
    },
    {
      icon: "🖼️",
      title: "Vision Analysis",
      description: "Upload images and get detailed AI-powered analysis, OCR, and object detection.",
      color: "#00d4ff",
    },
    {
      icon: "🛠️",
      title: "DevOps Agent",
      description: "Manage your AWS infrastructure with natural language commands.",
      color: "#ff6b35",
    },
    {
      icon: "🕷️",
      title: "Web Scraper",
      description: "Extract data from any website with Playwright-powered stealth scraping.",
      color: "#a855f7",
    },
  ];

  const steps = [
    { number: "01", title: "Sign Up", description: "Create a free account in seconds" },
    { number: "02", title: "Add API Key", description: "Connect your OpenAI or AWS credentials" },
    { number: "03", title: "Start Building", description: "Access all tools from one dashboard" },
  ];

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
            <div className="w-10 h-10 rounded-xl bg-[#39ff14] flex items-center justify-center font-bold text-black">
              O
            </div>
            <span className="text-xl font-bold">OmniDev</span>
          </div>
          <div className="flex items-center gap-6">
            <div className={`px-3 py-1.5 rounded-full text-xs font-medium ${backendStatus === "online"
                ? "bg-[#39ff14]/10 text-[#39ff14] border border-[#39ff14]/30"
                : "bg-white/5 text-gray-500 border border-white/10"
              }`}>
              {backendStatus === "online" ? "● Online" : "○ Offline"}
            </div>
            {!authLoading && (
              user ? (
                <div className="flex items-center gap-4">
                  <Link href="/chat" className="text-sm text-gray-400 hover:text-white transition">
                    Dashboard
                  </Link>
                  <button
                    onClick={() => signOut()}
                    className="text-sm text-gray-400 hover:text-white transition"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <Link href="/auth/login" className="text-sm text-gray-400 hover:text-white transition">
                    Login
                  </Link>
                  <Link
                    href="/auth/signup"
                    className="px-4 py-2 rounded-lg bg-[#39ff14] text-black font-semibold text-sm hover:opacity-90 transition"
                  >
                    Get Started
                  </Link>
                </div>
              )
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-block mb-6"
          >
            <span className="px-4 py-2 rounded-full text-sm font-medium bg-[#39ff14]/10 text-[#39ff14] border border-[#39ff14]/20">
              ✨ Powered by GPT-5 Mini
            </span>
          </motion.div>

          <motion.h1
            className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 leading-[1.1] tracking-tight"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Build Faster.
            <br />
            <span className="text-[#39ff14]">Automate Smarter.</span>
          </motion.h1>

          <motion.p
            className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            The all-in-one AI developer platform. Chat, vision analysis, cloud automation,
            and web scraping — unified in a beautiful interface.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link
              href={user ? "/chat" : "/auth/signup"}
              className="px-8 py-4 rounded-xl bg-[#39ff14] text-black font-semibold text-lg hover:opacity-90 transition shadow-lg shadow-[#39ff14]/20"
            >
              Get Started Free →
            </Link>
            <Link
              href="https://github.com/himanshu748/omnidev"
              target="_blank"
              className="px-8 py-4 rounded-xl border border-white/10 text-white font-semibold text-lg hover:bg-white/5 transition flex items-center justify-center gap-2"
            >
              <span>⭐</span> Star on GitHub
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                className="text-center"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="text-3xl md:text-4xl font-bold text-[#39ff14] mb-1">{stat.value}</div>
                <div className="text-sm text-gray-500">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem → Solution */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Stop juggling <span className="text-gray-500">10 different tools</span>
            </h2>
            <p className="text-gray-500 text-lg max-w-xl mx-auto">
              OmniDev brings everything you need into one powerful dashboard
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Without */}
            <motion.div
              className="p-8 rounded-2xl bg-red-500/5 border border-red-500/20"
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="text-red-400 font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">😩</span> Without OmniDev
              </div>
              <ul className="space-y-3 text-gray-400">
                <li className="flex items-start gap-3"><span className="text-red-400">✗</span> Switching between ChatGPT, AWS Console, Postman...</li>
                <li className="flex items-start gap-3"><span className="text-red-400">✗</span> Copy-pasting API keys everywhere</li>
                <li className="flex items-start gap-3"><span className="text-red-400">✗</span> No context between tools</li>
                <li className="flex items-start gap-3"><span className="text-red-400">✗</span> Paying for multiple subscriptions</li>
              </ul>
            </motion.div>

            {/* With */}
            <motion.div
              className="p-8 rounded-2xl bg-[#39ff14]/5 border border-[#39ff14]/20"
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="text-[#39ff14] font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">🚀</span> With OmniDev
              </div>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-start gap-3"><span className="text-[#39ff14]">✓</span> All tools in one beautiful interface</li>
                <li className="flex items-start gap-3"><span className="text-[#39ff14]">✓</span> Configure once, use everywhere</li>
                <li className="flex items-start gap-3"><span className="text-[#39ff14]">✓</span> Seamless workflow between features</li>
                <li className="flex items-start gap-3"><span className="text-[#39ff14]">✓</span> 100% open source & free</li>
              </ul>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Bento Grid */}
      <section className="py-24 px-6 bg-white/[0.01]">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Everything you need to <span className="text-[#39ff14]">ship faster</span>
            </h2>
            <p className="text-gray-500 text-lg">Powerful features, beautifully designed</p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                className="group p-8 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <div
                  className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl mb-6"
                  style={{ background: `${feature.color}15`, border: `1px solid ${feature.color}30` }}
                >
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>

          <motion.div
            className="text-center mt-12"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            <Link
              href={user ? "/chat" : "/auth/signup"}
              className="inline-flex items-center gap-2 text-[#39ff14] hover:underline font-medium"
            >
              Explore all 6+ tools →
            </Link>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Get started in <span className="text-[#39ff14]">3 minutes</span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                className="text-center"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
              >
                <div className="text-5xl font-bold text-[#39ff14]/20 mb-4">{step.number}</div>
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-gray-500">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-6">
        <motion.div
          className="max-w-4xl mx-auto text-center p-12 rounded-3xl bg-gradient-to-b from-[#39ff14]/10 to-transparent border border-[#39ff14]/20"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl md:text-5xl font-bold mb-4">
            Ready to supercharge your workflow?
          </h2>
          <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
            Join developers who are building faster with OmniDev. Free forever for personal use.
          </p>
          <Link
            href={user ? "/chat" : "/auth/signup"}
            className="inline-block px-10 py-4 rounded-xl bg-[#39ff14] text-black font-semibold text-lg hover:opacity-90 transition shadow-lg shadow-[#39ff14]/20"
          >
            Start Building Today →
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#39ff14]" />
            <span className="text-gray-500">OmniDev v1.0</span>
          </div>
          <p className="text-gray-600 text-sm">
            Built by <span className="text-white">Himanshu Kumar</span> • 2024-2026
          </p>
          <div className="flex items-center gap-6">
            <Link href="https://github.com/himanshu748/omnidev" target="_blank" className="text-gray-500 hover:text-white transition">
              GitHub
            </Link>
            <Link href="/settings" className="text-gray-500 hover:text-white transition">
              Settings
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
