"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

interface Feature {
  id: string;
  title: string;
  description: string;
  icon: string;
  href: string;
  gradient: string;
}

const features: Feature[] = [
  {
    id: "chat",
    title: "AI Chat",
    description: "Powered by Gemini 2.0 - multimodal AI assistant",
    icon: "💬",
    href: "/chat",
    gradient: "from-violet-500 to-purple-600",
  },
  {
    id: "devops",
    title: "DevOps Agent",
    description: "Smart AI agent for AWS cloud management",
    icon: "🛠️",
    href: "/devops",
    gradient: "from-cyan-500 to-blue-600",
  },
  {
    id: "vision",
    title: "Vision Lab",
    description: "Image analysis with Gemini Vision AI",
    icon: "🖼️",
    href: "/vision",
    gradient: "from-amber-500 to-orange-600",
  },
  {
    id: "storage",
    title: "Cloud Storage",
    description: "S3 file manager with upload/download",
    icon: "📦",
    href: "/storage",
    gradient: "from-emerald-500 to-green-600",
  },
  {
    id: "location",
    title: "Location Services",
    description: "Geolocation and reverse geocoding",
    icon: "📍",
    href: "/location",
    gradient: "from-rose-500 to-pink-600",
  },
];

interface ServiceStatus {
  gemini: string;
  aws: string;
  vision: string;
}

export default function Home() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => {
        setStatus(data.services);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen relative">
      {/* Animated Background */}
      <div className="animated-bg" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-[--border]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚀</span>
            <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
              TechTrainingPro
            </span>
          </div>
          <div className="flex items-center gap-4">
            {loading ? (
              <div className="spinner" />
            ) : status ? (
              <div className="flex items-center gap-2">
                <span className={`status-badge ${status.gemini === 'configured' ? 'success' : 'warning'}`}>
                  AI: {status.gemini}
                </span>
                <span className={`status-badge ${status.aws === 'configured' ? 'success' : 'warning'}`}>
                  AWS: {status.aws}
                </span>
              </div>
            ) : (
              <span className="status-badge error">Backend offline</span>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="bg-gradient-to-r from-violet-500 via-cyan-500 to-violet-500 bg-clip-text text-transparent animate-gradient">
              Technical Training
            </span>
            <br />
            <span className="text-white">Reimagined</span>
          </h1>
          <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
            A modern full-stack platform powered by <strong className="text-violet-400">Google Gemini 2.0</strong>,
            featuring intelligent DevOps automation, multimodal AI, and cloud management.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link href="/chat" className="glow-button text-white">
              Start Chatting →
            </Link>
            <Link
              href="/devops"
              className="px-6 py-3 rounded-xl border border-[--border] text-gray-300 hover:border-violet-500 hover:text-white transition-all"
            >
              DevOps Agent
            </Link>
          </div>
        </div>
      </section>

      {/* Tech Stack Badges */}
      <section className="py-8 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap gap-3 justify-center">
            {["Next.js 15", "FastAPI", "Gemini 2.0", "TailwindCSS", "AWS (boto3)", "TypeScript"].map((tech) => (
              <span
                key={tech}
                className="px-4 py-2 rounded-full text-sm border border-[--border] text-gray-400 hover:border-violet-500 hover:text-violet-400 transition-all"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            Features & Capabilities
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <Link
                key={feature.id}
                href={feature.href}
                className="feature-card glass-card p-6 group"
              >
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-2 group-hover:text-violet-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-400 text-sm">{feature.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            What&apos;s New in v2.0
          </h2>
          <div className="glass-card p-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[--border]">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Feature</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">v1.0 (2024)</th>
                  <th className="text-left py-3 px-4 text-violet-400 font-medium">v2.0 (2026)</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {[
                  ["UI Framework", "Tkinter Desktop", "Next.js + React 19"],
                  ["AI Model", "Cohere (basic)", "Gemini 2.0 (multimodal)"],
                  ["DevOps", "Manual boto3 calls", "AI-Powered Agent"],
                  ["Vision", "Google Vision labels", "Gemini Vision + OCR"],
                  ["Deployment", "None", "Docker + CI/CD ready"],
                ].map(([feature, old, newVal]) => (
                  <tr key={feature} className="border-b border-[--border] hover:bg-[--card-hover]">
                    <td className="py-3 px-4 text-white">{feature}</td>
                    <td className="py-3 px-4 text-gray-500">{old}</td>
                    <td className="py-3 px-4 text-emerald-400">{newVal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-[--border]">
        <div className="max-w-6xl mx-auto text-center text-gray-500 text-sm">
          <p>
            TechTrainingPro v2.0 — Built with ❤️ using Next.js, FastAPI & Gemini AI
          </p>
          <p className="mt-2">
            Original project by Himanshu Kumar & team (2024) • Modernized 2026
          </p>
        </div>
      </footer>
    </main>
  );
}
