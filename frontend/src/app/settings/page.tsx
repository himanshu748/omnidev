"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSettings } from "../hooks/useSettings";
import { createClient } from "../lib/supabase";
import { buildAuthHeaders } from "../lib/api";

export default function SettingsPage() {
    const router = useRouter();
    const supabase = createClient();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const { settings, isLoaded, saveSettings, clearSettings, isAiConfigured, isAwsConfigured, isLocationConfigured } = useSettings();
    const [saved, setSaved] = useState(false);
    const [apiKeyStatus, setApiKeyStatus] = useState<"idle" | "saving" | "error" | "success">("idle");
    const isApiKeyConfigured = Boolean(settings.apiAccessKey);

    // Auth check - redirect to login if not authenticated
    useEffect(() => {
        const checkAuth = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push('/auth/login?redirect=/settings');
            } else {
                setIsAuthenticated(true);
            }
        };
        checkAuth();
    }, [router, supabase.auth]);

    // Local state for form
    const [openaiKey, setOpenaiKey] = useState("");
    const [awsAccessKey, setAwsAccessKey] = useState("");
    const [awsSecretKey, setAwsSecretKey] = useState("");
    const [awsRegion, setAwsRegion] = useState("ap-south-1");
    const [googleKey, setGoogleKey] = useState("");
    const [apiAccessKey, setApiAccessKey] = useState("");

    // Sync local state when settings load
    useState(() => {
        if (isLoaded) {
            setOpenaiKey(settings.openaiApiKey);
            setAwsAccessKey(settings.awsAccessKeyId);
            setAwsSecretKey(settings.awsSecretAccessKey);
            setAwsRegion(settings.awsRegion);
            setGoogleKey(settings.googleMapsApiKey);
            setApiAccessKey(settings.apiAccessKey);
        }
    });

    const handleSave = () => {
        saveSettings({
            openaiApiKey: openaiKey,
            awsAccessKeyId: awsAccessKey,
            awsSecretAccessKey: awsSecretKey,
            awsRegion: awsRegion,
            googleMapsApiKey: googleKey,
            apiAccessKey: apiAccessKey,
        });
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const handleClear = () => {
        clearSettings();
        setOpenaiKey("");
        setAwsAccessKey("");
        setAwsSecretKey("");
        setAwsRegion("ap-south-1");
        setGoogleKey("");
        setApiAccessKey("");
    };

    const generateApiKey = async () => {
        setApiKeyStatus("saving");
        try {
            const headers = await buildAuthHeaders(false);
            const response = await fetch("/api/auth/api-key", {
                method: "POST",
                headers,
            });
            if (!response.ok) {
                setApiKeyStatus("error");
                return;
            }
            const data = await response.json();
            setApiAccessKey(data.api_key);
            saveSettings({ apiAccessKey: data.api_key });
            setApiKeyStatus("success");
            setTimeout(() => setApiKeyStatus("idle"), 2000);
        } catch {
            setApiKeyStatus("error");
        }
    };

    const awsRegions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
    ];

    // Show loading while checking auth
    if (isAuthenticated === null) {
        return (
            <main className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="text-4xl mb-4">🔐</div>
                    <p className="text-gray-400">Verifying authentication...</p>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen">
            <div className="animated-bg" />

            <header className="glass-card border-b border-[--border] sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <span className="text-xl">←</span>
                        <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                            OmniDev
                        </span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">⚙️</span>
                        <span className="font-semibold">Settings</span>
                    </div>
                </div>
            </header>

            <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
                {/* Status Overview */}
                <div className="glass-card p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        🔌 Connection Status
                    </h2>
                    <div className="grid grid-cols-4 gap-4">
                        <div className={`p-4 rounded-xl border ${isAiConfigured ? "border-neon-cyan bg-neon-cyan/10" : "border-[--border]"}`}>
                            <div className="text-2xl mb-2">🤖</div>
                            <div className="font-medium">AI (OpenAI)</div>
                            <div className={`text-sm ${isAiConfigured ? "text-neon-cyan" : "text-gray-500"}`}>
                                {isAiConfigured ? "✓ Configured" : "Not set"}
                            </div>
                        </div>
                        <div className={`p-4 rounded-xl border ${isAwsConfigured ? "border-neon-magenta bg-neon-magenta/10" : "border-[--border]"}`}>
                            <div className="text-2xl mb-2">☁️</div>
                            <div className="font-medium">AWS</div>
                            <div className={`text-sm ${isAwsConfigured ? "text-neon-magenta" : "text-gray-500"}`}>
                                {isAwsConfigured ? "✓ Configured" : "Not set"}
                            </div>
                        </div>
                        <div className={`p-4 rounded-xl border ${isLocationConfigured ? "border-emerald-500 bg-emerald-500/10" : "border-[--border]"}`}>
                            <div className="text-2xl mb-2">📍</div>
                            <div className="font-medium">Location</div>
                            <div className={`text-sm ${isLocationConfigured ? "text-emerald-400" : "text-gray-500"}`}>
                                {isLocationConfigured ? "✓ Google API" : "Using free API"}
                            </div>
                        </div>
                        <div className={`p-4 rounded-xl border ${isApiKeyConfigured ? "border-blue-500 bg-blue-500/10" : "border-[--border]"}`}>
                            <div className="text-2xl mb-2">🔐</div>
                            <div className="font-medium">API Key</div>
                            <div className={`text-sm ${isApiKeyConfigured ? "text-blue-400" : "text-gray-500"}`}>
                                {isApiKeyConfigured ? "✓ Ready" : "Not set"}
                            </div>
                        </div>
                    </div>
                </div>

                {/* AI Configuration */}
                <div className="glass-card p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        🤖 AI Configuration
                    </h2>
                    <p className="text-gray-400 text-sm mb-4">
                        Configure your OpenAI API key for AI Chat and Vision features.
                    </p>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">OpenAI API Key</label>
                            <input
                                type="password"
                                value={openaiKey}
                                onChange={(e) => setOpenaiKey(e.target.value)}
                                placeholder="sk-..."
                                className="w-full bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-neon-cyan transition-colors font-mono text-sm"
                            />
                            <p className="text-xs text-gray-500 mt-2">
                                Get your key from{" "}
                                <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-neon-cyan hover:underline">
                                    OpenAI Platform
                                </a>
                            </p>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        🔐 API Access
                    </h2>
                    <p className="text-gray-400 text-sm mb-4">
                        Use this key to authorize API requests tied to your account.
                    </p>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">API Access Key</label>
                            <input
                                type="password"
                                value={apiAccessKey}
                                onChange={(e) => setApiAccessKey(e.target.value)}
                                placeholder="Generate or paste your key"
                                className="w-full bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-neon-cyan transition-colors font-mono text-sm"
                            />
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={generateApiKey}
                                className="px-4 py-2 rounded-lg border border-neon-cyan/40 text-neon-cyan hover:bg-neon-cyan/10 transition-colors text-sm"
                            >
                                {apiKeyStatus === "saving" ? "Generating..." : "Generate API Key"}
                            </button>
                            {apiKeyStatus === "success" && (
                                <span className="text-xs text-emerald-400">Saved</span>
                            )}
                            {apiKeyStatus === "error" && (
                                <span className="text-xs text-red-400">Failed</span>
                            )}
                        </div>
                    </div>
                </div>

                {/* AWS Configuration */}
                <div className="glass-card p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        ☁️ AWS Configuration
                    </h2>
                    <p className="text-gray-400 text-sm mb-4">
                        Configure AWS credentials for DevOps Agent and Cloud Storage.
                    </p>
                    <div className="space-y-4">
                        <div className="grid md:grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-gray-400 mb-2 block">Access Key ID</label>
                                <input
                                    type="text"
                                    value={awsAccessKey}
                                    onChange={(e) => setAwsAccessKey(e.target.value)}
                                    placeholder="AKIA..."
                                    className="w-full bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-neon-magenta transition-colors font-mono text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-sm text-gray-400 mb-2 block">Secret Access Key</label>
                                <input
                                    type="password"
                                    value={awsSecretKey}
                                    onChange={(e) => setAwsSecretKey(e.target.value)}
                                    placeholder="Your secret key..."
                                    className="w-full bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-neon-magenta transition-colors font-mono text-sm"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="text-sm text-gray-400 mb-2 block">Region</label>
                            <select
                                value={awsRegion}
                                onChange={(e) => setAwsRegion(e.target.value)}
                                className="w-full bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-neon-magenta transition-colors"
                            >
                                {awsRegions.map(region => (
                                    <option key={region} value={region}>{region}</option>
                                ))}
                            </select>
                        </div>
                        <p className="text-xs text-gray-500">
                            Create credentials in{" "}
                            <a href="https://console.aws.amazon.com/iam/" target="_blank" rel="noopener noreferrer" className="text-neon-magenta hover:underline">
                                AWS IAM Console
                            </a>
                        </p>
                    </div>
                </div>

                {/* Google Maps Configuration */}
                <div className="glass-card p-6">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        📍 Location Configuration
                    </h2>
                    <p className="text-gray-400 text-sm mb-4">
                        Optional: Add Google Maps API for better geocoding results.
                    </p>
                    <div>
                        <label className="text-sm text-gray-400 mb-2 block">Google Maps API Key</label>
                        <input
                            type="password"
                            value={googleKey}
                            onChange={(e) => setGoogleKey(e.target.value)}
                            placeholder="AIza..."
                            className="w-full bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors font-mono text-sm"
                        />
                        <p className="text-xs text-gray-500 mt-2">
                            Get key from{" "}
                            <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">
                                Google Cloud Console
                            </a>
                        </p>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                    <button
                        onClick={handleSave}
                        className="flex-1 glow-button text-white py-4 text-lg font-semibold"
                    >
                        {saved ? "✓ Saved!" : "💾 Save All Settings"}
                    </button>
                    <button
                        onClick={handleClear}
                        className="px-6 py-4 rounded-xl border border-red-500/50 text-red-400 hover:bg-red-500/10 transition-all"
                    >
                        Clear All
                    </button>
                </div>

                {/* Security Note */}
                <div className="glass-card p-4 border-amber-500/30 bg-amber-500/5">
                    <div className="flex items-start gap-3">
                        <span className="text-xl">🔒</span>
                        <div>
                            <h3 className="font-medium text-amber-400 mb-1">Security Note</h3>
                            <p className="text-sm text-gray-400">
                                API keys are stored locally in your browser only. They are never sent to our servers.
                                For production use, configure keys via environment variables instead.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
