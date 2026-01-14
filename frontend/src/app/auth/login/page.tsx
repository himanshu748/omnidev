"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { signIn } = useAuth();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        const { error } = await signIn(email, password);

        if (error) {
            setError(error.message);
            setLoading(false);
        } else {
            router.push("/");
        }
    };

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

                {/* Login Card */}
                <div className="bg-[#0a0a0f] border border-[#39ff14]/20 rounded-2xl p-8">
                    <h1 className="text-2xl font-bold text-white mb-2">Welcome back</h1>
                    <p className="text-gray-500 mb-6">Sign in to your account</p>

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

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 rounded-xl font-semibold text-black bg-[#39ff14] hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {loading ? "Signing in..." : "Sign In"}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-gray-500 text-sm">
                        Don&apos;t have an account?{" "}
                        <Link href="/auth/signup" className="text-[#39ff14] hover:underline">
                            Sign up
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
