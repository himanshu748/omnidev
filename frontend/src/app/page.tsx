"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useSettings } from "./hooks/useSettings";
import { useAuth } from "./context/AuthContext";

interface Feature {
  id: string;
  title: string;
  description: string;
  icon: string;
  href: string;
}

const features: Feature[] = [
  {
    id: "chat",
    title: "AI Chat",
    description: "GPT-4o Mini powered AI assistant with markdown support",
    icon: "💬",
    href: "/chat",
  },
  {
    id: "devops",
    title: "DevOps Agent",
    description: "Smart AI agent for AWS cloud management",
    icon: "🛠️",
    href: "/devops",
  },
  {
    id: "vision",
    title: "Vision Lab",
    description: "Image analysis with GPT-4o Mini Vision",
    icon: "🖼️",
    href: "/vision",
  },
  {
    id: "scraper",
    title: "Web Scraper",
    description: "Playwright browser automation with stealth mode",
    icon: "🕷️",
    href: "/scraper",
  },
  {
    id: "storage",
    title: "Cloud Storage",
    description: "S3 file manager with upload/download",
    icon: "📦",
    href: "/storage",
  },
  {
    id: "location",
    title: "Location Services",
    description: "GPS & IP geolocation with Google Maps",
    icon: "📍",
    href: "/location",
  },
];

const techStack = [
  "Next.js 16", "React 19", "FastAPI", "OpenAI GPT-4o Mini",
  "Playwright", "AWS boto3", "TypeScript", "Python 3.12", "Framer Motion"
];

export default function Home() {
  const { isAiConfigured, isAwsConfigured } = useSettings();
  const { user, loading: authLoading, signOut } = useAuth();
  const [backendStatus, setBackendStatus] = useState<"loading" | "online" | "offline">("loading");
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <main className="min-h-screen bg-[#050505] text-white relative overflow-hidden">
      {/* Animated Grid Background - Neon Green */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(57,255,20,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(57,255,20,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
        <motion.div
          className="absolute w-[600px] h-[600px] rounded-full blur-[120px] opacity-20"
          style={{
            background: "radial-gradient(circle, #39ff14 0%, transparent 70%)",
          }}
          animate={{
            left: mousePos.x - 300,
            top: mousePos.y - 300,
          }}
          transition={{ type: "spring", damping: 30, stiffness: 200 }}
        />
      </div>

      {/* Floating Orbs - Neon Green */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute top-20 left-20 w-72 h-72 bg-[#39ff14]/10 rounded-full blur-[100px]"
          animate={{ y: [0, -20, 0], rotate: [0, 1, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-40 right-20 w-96 h-96 bg-[#39ff14]/10 rounded-full blur-[120px]"
          animate={{ y: [0, -20, 0], rotate: [0, -1, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-64 h-64 bg-[#32CD32]/10 rounded-full blur-[80px]"
          animate={{ scale: [1, 1.1, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/40 border-b border-[#39ff14]/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-3">
            <motion.div
              className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-[#39ff14] flex items-center justify-center font-bold text-black text-sm sm:text-base"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              O
            </motion.div>
            <span className="text-lg sm:text-xl font-bold text-[#39ff14]">
              OmniDev
            </span>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Status Indicators */}
            <div className="hidden sm:flex items-center gap-2">
              <div className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-xs font-medium border ${backendStatus === "online"
                ? "border-[#39ff14]/50 bg-[#39ff14]/10 text-[#39ff14]"
                : backendStatus === "offline"
                  ? "border-red-500/50 bg-red-500/10 text-red-400"
                  : "border-white/20 bg-white/5 text-gray-400"
                }`}>
                {backendStatus === "loading" ? "..." : backendStatus === "online" ? "● API" : "○ Offline"}
              </div>
              <div className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-xs font-medium border ${isAiConfigured
                ? "border-[#39ff14]/50 bg-[#39ff14]/10 text-[#39ff14]"
                : "border-white/20 bg-white/5 text-gray-500"
                }`}>
                {isAiConfigured ? "● AI" : "○ AI"}
              </div>
              <div className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-xs font-medium border ${isAwsConfigured
                ? "border-[#39ff14]/50 bg-[#39ff14]/10 text-[#39ff14]"
                : "border-white/20 bg-white/5 text-gray-500"
                }`}>
                {isAwsConfigured ? "● AWS" : "○ AWS"}
              </div>
            </div>
            <Link
              href="/settings"
              className="px-3 sm:px-4 py-2 rounded-xl border border-[#39ff14]/30 hover:border-[#39ff14] hover:bg-[#39ff14]/10 transition-all flex items-center gap-2 text-[#39ff14]"
            >
              <span>⚙️</span>
              <span className="hidden sm:inline text-sm">Settings</span>
            </Link>
            {/* Auth Buttons */}
            {!authLoading && (
              user ? (
                <motion.button
                  onClick={() => signOut()}
                  className="px-3 sm:px-4 py-2 rounded-xl border border-red-500/30 hover:border-red-500 hover:bg-red-500/10 transition-all text-red-400 text-sm"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Logout
                </motion.button>
              ) : (
                <Link
                  href="/auth/login"
                  className="px-3 sm:px-4 py-2 rounded-xl bg-[#39ff14] text-black font-semibold hover:opacity-90 transition-all text-sm"
                >
                  Login
                </Link>
              )
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto text-center">
          {/* Title */}
          <motion.h1
            className="text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold mb-4 sm:mb-6 leading-tight"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="block text-white mb-2">Developer</span>
            <span className="block text-[#39ff14]">
              Powerhouse
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="text-base sm:text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-8 sm:mb-10 leading-relaxed px-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            A full-stack AI platform featuring <span className="text-[#39ff14]">GPT-4o Mini</span>,
            cloud automation, browser scraping, and vision analysis —
            all in one <span className="text-[#39ff14]">beautiful interface</span>.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="/chat"
                className="block px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-semibold text-black hover:opacity-90 transition-opacity text-center"
                style={{ background: "#39ff14" }}
              >
                Start Chatting →
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="/settings"
                className="block px-6 sm:px-8 py-3 sm:py-4 rounded-xl border border-[#39ff14]/30 text-[#39ff14] hover:bg-[#39ff14]/10 transition-all text-center"
              >
                Configure APIs
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Tech Stack Marquee */}
      <section className="py-6 sm:py-10 border-y border-[#39ff14]/10 overflow-hidden">
        <div className="flex animate-marquee whitespace-nowrap">
          {[...techStack, ...techStack].map((tech, i) => (
            <span key={i} className="mx-4 sm:mx-8 text-gray-500 text-sm sm:text-lg font-medium">
              {tech}
            </span>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-12 sm:py-20 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="text-center mb-10 sm:mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4">
              <span className="text-[#39ff14]">Powerful</span> Features
            </h2>
            <p className="text-gray-500 text-sm sm:text-base max-w-xl mx-auto px-4">
              Everything you need to build, automate, and manage modern applications
            </p>
          </motion.div>

          <motion.div
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {features.map((feature) => (
              <motion.div key={feature.id} variants={itemVariants}>
                <Link
                  href={feature.href}
                  className="group block p-4 sm:p-6 rounded-2xl border border-white/5 bg-white/[0.02] backdrop-blur-sm hover:border-[#39ff14]/30 hover:bg-[#39ff14]/5 transition-all duration-300"
                >
                  {/* Icon */}
                  <motion.div
                    className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-[#39ff14]/20 flex items-center justify-center text-xl sm:text-2xl mb-3 sm:mb-4 group-hover:bg-[#39ff14]/30 transition-all duration-300"
                    whileHover={{ scale: 1.1 }}
                  >
                    {feature.icon}
                  </motion.div>

                  {/* Content */}
                  <h3 className="text-lg sm:text-xl font-semibold mb-1 sm:mb-2 group-hover:text-[#39ff14] transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-gray-500 text-xs sm:text-sm leading-relaxed">
                    {feature.description}
                  </p>

                  {/* Arrow */}
                  <div className="mt-3 sm:mt-4 text-gray-500 group-hover:text-[#39ff14] transition-colors text-sm">
                    Open →
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 border-t border-[#39ff14]/10">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {[
              { value: "6+", label: "Modules" },
              { value: "1", label: "AI Model" },
              { value: "∞", label: "Possibilities" },
              { value: "100%", label: "Configurable" },
            ].map((stat) => (
              <motion.div key={stat.label} className="text-center" variants={itemVariants}>
                <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-[#39ff14] mb-1 sm:mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-500 text-xs sm:text-sm uppercase tracking-wider">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            className="relative p-8 sm:p-12 rounded-3xl border border-[#39ff14]/20 bg-[#39ff14]/5 overflow-hidden"
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <h2 className="relative text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4">
              Ready to <span className="text-[#39ff14]">explore</span>?
            </h2>
            <p className="relative text-gray-400 text-sm sm:text-base mb-6 sm:mb-8 max-w-lg mx-auto">
              Configure your API keys and unlock the full potential of OmniDev
            </p>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="/settings"
                className="relative inline-flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-semibold text-black hover:opacity-90 transition-opacity"
                style={{ background: "#39ff14" }}
              >
                ⚙️ Open Settings
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-6 sm:py-8 px-4 sm:px-6 border-t border-[#39ff14]/10">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 sm:w-6 sm:h-6 rounded bg-[#39ff14]" />
            <span className="text-gray-500 text-xs sm:text-sm">OmniDev v4.0</span>
          </div>
          <p className="text-gray-600 text-xs sm:text-sm text-center">
            Built by <span className="text-white">Himanshu Kumar</span> • 2024-2026
          </p>
          <div className="flex items-center gap-4">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-[#39ff14] transition-colors text-xs sm:text-sm">
              GitHub
            </a>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-[#39ff14] transition-colors text-xs sm:text-sm">
              LinkedIn
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
