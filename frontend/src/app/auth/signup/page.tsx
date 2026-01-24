"use client";

import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const { signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    const { error } = await signUp(email, password);

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    setLoading(false);
    setSuccess(true);
    // Most Supabase projects require email confirmation by default.
    // Redirect to login so the user can continue after confirming.
    router.push("/auth/login?signup=success");
  };

  return (
    <main className="min-h-screen bg-[#f5f5f0] flex items-center justify-center px-4">
      {/* Background Pattern */}
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-12 sm:mb-16">
          <Link href="/" className="inline-flex items-center gap-3">
            <div className="w-10 h-10 bg-[#0a0a0a] rounded-xl flex items-center justify-center">
              <span className="text-[#f5f5f0] font-bold text-lg">O</span>
            </div>
            <span className="text-2xl font-bold tracking-tight">OmniDev</span>
          </Link>
        </div>

        {/* Signup Card */}
        <div className="bg-white border border-[#d4d4c8] rounded-2xl p-8 sm:p-10 shadow-sm">
          <h1 className="text-2xl sm:text-3xl font-display mb-3">Create account</h1>
          <p className="text-[#666] font-mono text-sm sm:text-base mb-8 sm:mb-10">Get started with OmniDev</p>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6 sm:mb-8 text-sm font-mono">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-xl mb-6 sm:mb-8 text-sm font-mono">
              Account created. Check your email to confirm, then sign in.
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2.5 sm:mb-3 text-[#0a0a0a]">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className="w-full px-4 py-3 rounded-xl bg-[#f5f5f0] border border-[#d4d4c8] text-[#0a0a0a] placeholder-[#999] focus:outline-none focus:border-[#0a0a0a] focus:ring-1 focus:ring-[#0a0a0a] transition-all font-mono text-sm"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2.5 sm:mb-3 text-[#0a0a0a]">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                className="w-full px-4 py-3 rounded-xl bg-[#f5f5f0] border border-[#d4d4c8] text-[#0a0a0a] placeholder-[#999] focus:outline-none focus:border-[#0a0a0a] focus:ring-1 focus:ring-[#0a0a0a] transition-all font-mono text-sm"
                placeholder="••••••••"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2.5 sm:mb-3 text-[#0a0a0a]">Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                className="w-full px-4 py-3 rounded-xl bg-[#f5f5f0] border border-[#d4d4c8] text-[#0a0a0a] placeholder-[#999] focus:outline-none focus:border-[#0a0a0a] focus:ring-1 focus:ring-[#0a0a0a] transition-all font-mono text-sm"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 sm:py-4 rounded-xl bg-[#0a0a0a] text-white font-semibold hover:bg-[#1a1a1a] transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Creating account...
                </span>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          <div className="mt-8 sm:mt-10 text-center text-sm font-mono">
            <span className="text-[#666]">Already have an account? </span>
            <Link href="/auth/login" className="text-[#e55c1c] hover:underline font-medium">
              Sign in
            </Link>
          </div>
        </div>

        {/* Back Link */}
        <div className="mt-10 sm:mt-12 text-center">
          <Link href="/" className="inline-flex items-center gap-2 text-[#666] hover:text-[#0a0a0a] text-sm font-mono transition-colors">
            <span>←</span>
            <span>Back to home</span>
          </Link>
        </div>
      </div>
    </main>
  );
}
