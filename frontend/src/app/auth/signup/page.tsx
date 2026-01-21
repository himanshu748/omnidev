"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "../../context/AuthContext";

export default function SignupPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const { signUp } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

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
        } else {
            setSuccess(true);
            setLoading(false);
        }
    };

    if (success) {
        return (
            <main className="min-h-screen bg-[#050505] flex items-center justify-center px-4">
                <div className="fixed inset-0 pointer-events-none">
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(57,255,20,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(57,255,20,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
                </div>
                <div className="w-full max-w-md relative z-10 text-center">
                    <div className="w-20 h-20 rounded-full bg-[#39ff14]/20 flex items-center justify-center mx-auto mb-6">
                        <span className="text-4xl">✓</span>
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">Check your email</h1>
                    <p className="text-gray-400 mb-6">
                        We&apos;ve sent you a confirmation link at <span className="text-[#39ff14]">{email}</span>
                    </p>
                    <Link
                        href="/auth/login"
                        className="inline-block px-6 py-3 bg-[#39ff14] text-black font-semibold rounded-xl hover:opacity-90 transition-opacity"
                    >
                        Go to Login
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#050505] flex items-center justify-center px-4">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(57,255,20,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(57,255,20,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
            </div>

            <div className="w-full max-w-md relative z-10">
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-2">
                        <div className="w-12 h-12 rounded-xl bg-[#39ff14] flex items-center justify-center font-bold text-black text-xl">
                            O
                        </div>
                        <span className="text-2xl font-bold text-[#39ff14]">OmniDev</span>
                    </Link>
                </div>

                {/* Signup Card */}
                <div className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-2xl p-8">
                    <h1 className="text-2xl font-bold text-white mb-2">Create account</h1>
                    <p className="text-gray-500 mb-6">Get started with OmniDev</p>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                                className="w-full bg-[#050505] border border-[#39ff14]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#39ff14] transition-colors"
                            />
                        </div>

                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                className="w-full bg-[#050505] border border-[#39ff14]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#39ff14] transition-colors"
                            />
                        </div>

                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">Confirm Password</label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                className="w-full bg-[#050505] border border-[#39ff14]/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#39ff14] transition-colors"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 rounded-xl font-semibold text-black bg-[#39ff14] hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {loading ? "Creating account..." : "Create Account"}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-gray-500 text-sm">
                        Already have an account?{" "}
                        <Link href="/auth/login" className="text-[#39ff14] hover:underline">
                            Sign in
                        </Link>
                    </div>
                </div>

                {/* Back to home */}
                <div className="text-center mt-6">
                    <Link href="/" className="text-gray-500 hover:text-[#39ff14] transition-colors text-sm">
                        ← Back to home
                    </Link>
                </div>
            </div>
        </main>
    );
}
