"use client";

import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const { error } = await signIn(email, password);
    
    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    const redirect = new URLSearchParams(window.location.search).get("redirect") || "/";
    router.push(redirect);
  };

  return (
    <main className="min-h-screen bg-[#f5f5f0] px-4">
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      <div className="relative z-10 min-h-screen max-w-6xl mx-auto flex items-center py-10">
        <div className="w-full grid lg:grid-cols-2 gap-10 lg:gap-14 items-stretch">
          {/* Left: Form */}
          <div className="w-full max-w-md mx-auto lg:mx-0">
            <div className="mb-8">
              <Link href="/" className="inline-flex items-center gap-3">
                <div className="w-10 h-10 bg-[#0a0a0a] rounded-xl flex items-center justify-center">
                  <span className="text-[#f5f5f0] font-bold text-lg">O</span>
                </div>
                <span className="text-2xl font-bold tracking-tight">OmniDev</span>
              </Link>
            </div>

            <div className="bg-white border border-[#d4d4c8] rounded-2xl p-7 sm:p-8 shadow-sm">
              <div className="mb-6">
                <h1 className="text-2xl sm:text-3xl font-display mb-2">Sign in</h1>
                <p className="text-[#666] text-sm sm:text-base">
                  Welcome back. Use your account to access the tools.
                </p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-5 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium mb-2 text-[#0a0a0a]">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    className="app-input font-mono text-sm"
                    placeholder="you@example.com"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-[#0a0a0a]">Password</label>
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="text-xs font-mono text-[#666] hover:text-[#0a0a0a]"
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    className="app-input font-mono text-sm"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-[#0a0a0a] text-white font-semibold hover:bg-[#1a1a1a] transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Signing in...
                    </span>
                  ) : (
                    "Sign In"
                  )}
                </button>
              </form>

              <div className="mt-6 text-sm">
                <span className="text-[#666]">Don&apos;t have an account? </span>
                <Link href="/auth/signup" className="text-[#e55c1c] hover:underline font-medium">
                  Sign up
                </Link>
              </div>
            </div>

            <div className="mt-8 text-center lg:text-left">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-[#666] hover:text-[#0a0a0a] text-sm font-mono transition-colors"
              >
                <span>←</span>
                <span>Back to home</span>
              </Link>
            </div>
          </div>

          {/* Right: Brand panel (desktop) */}
          <div className="hidden lg:block">
            <div className="h-full app-panel p-8 flex flex-col justify-between bg-gradient-to-b from-white to-[#fafaf5]">
              <div>
                <span className="section-label mb-6 block">OmniDev</span>
                <h2 className="text-4xl font-display mb-4 leading-[1.0]">
                  Build, ship,
                  <br />
                  automate — in one place.
                </h2>
                <p className="text-[#666] leading-relaxed max-w-md">
                  AI chat, vision, scraping, and cloud tooling — designed for demos and real workflows.
                </p>

                <div className="mt-8 space-y-3 text-sm text-[#666]">
                  <div className="flex items-center gap-3">
                    <span className="w-2 h-2 rounded-full bg-[#e55c1c]" />
                    <span className="font-mono">FastAPI + Next.js</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="w-2 h-2 rounded-full bg-[#e55c1c]" />
                    <span className="font-mono">Supabase Auth</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="w-2 h-2 rounded-full bg-[#e55c1c]" />
                    <span className="font-mono">Render backend</span>
                  </div>
                </div>
              </div>

              <div className="pt-8 border-t border-[#d4d4c8] flex items-center justify-between text-xs text-[#999] font-mono">
                <span>Production</span>
                <span>v1.0</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
