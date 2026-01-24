"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { AuthGuard } from "../components/AuthGuard";
import { buildAuthHeaders } from "../lib/api";

interface ScrapeResult {
    success: boolean;
    url: string;
    title: string;
    html: string;
    text: string;
    screenshot: string | null;
    error: string | null;
    engine: string;
    load_time_ms: number;
}

interface ScraperStatus {
    playwright: { available: boolean; browser_active: boolean };
}

export default function ScraperPage() {
    const [url, setUrl] = useState("");
    const [waitTime, setWaitTime] = useState(2000);
    const [captureScreenshot, setCaptureScreenshot] = useState(false);
    const [extractSelector, setExtractSelector] = useState("");

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ScrapeResult | null>(null);
    const [activeTab, setActiveTab] = useState<"text" | "html" | "screenshot">("text");
    const [status, setStatus] = useState<ScraperStatus | null>(null);

    const fetchStatus = async () => {
        try {
            const res = await fetch("/api/scraper/status", {
                headers: await buildAuthHeaders(),
            });
            const data = await res.json();
            setStatus(data);
        } catch {
            setStatus(null);
        }
    };

    const handleScrape = async () => {
        if (!url) return;
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch("/api/scraper/scrape", {
                method: "POST",
                headers: {
                    ...(await buildAuthHeaders()),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    url,
                    wait_time_ms: waitTime,
                    capture_screenshot: captureScreenshot,
                    extract_selector: extractSelector || undefined,
                }),
            });

            const data = await res.json();
            setResult(data);

            if (data.screenshot) setActiveTab("screenshot");
            else if (data.text) setActiveTab("text");
        } catch {
            setResult({
                success: false,
                url,
                title: "",
                html: "",
                text: "",
                screenshot: null,
                error: "Failed to connect to backend. Is it running?",
                engine: "playwright",
                load_time_ms: 0,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleExport = (format: "json" | "html" | "text") => {
        if (!result) return;
        let content: string, mimeType: string, filename: string;

        switch (format) {
            case "json":
                content = JSON.stringify(result, null, 2);
                mimeType = "application/json";
                filename = "scrape-result.json";
                break;
            case "html":
                content = result.html;
                mimeType = "text/html";
                filename = "scrape-result.html";
                break;
            case "text":
                content = result.text;
                mimeType = "text/plain";
                filename = "scrape-result.txt";
                break;
        }

        const blob = new Blob([content], { type: mimeType });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(blobUrl);
    };

    return (
        <AuthGuard>
            <main className="min-h-screen bg-[#f5f5f0] text-[#0a0a0a]">
                <div className="fixed inset-0 grid-pattern pointer-events-none" />

                {/* Navigation */}
                <nav className="fixed top-0 left-0 right-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md border-b border-[#d4d4c8]" aria-label="Primary">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-2 sm:gap-3">
                            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-[#0a0a0a] flex items-center justify-center font-bold text-[#f5f5f0] text-sm sm:text-base">
                                O
                            </div>
                            <span className="text-lg sm:text-xl font-semibold tracking-tight">OmniDev</span>
                        </Link>
                        <div className="flex items-center gap-2 sm:gap-4">
                            <button
                                onClick={fetchStatus}
                                className="btn-secondary text-sm px-3 sm:px-4 py-2"
                            >
                                Check Status
                            </button>
                            {status && (
                                <motion.span
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className={`px-3 py-1.5 rounded-full text-xs font-medium border ${status.playwright.available ? "border-[#0a0a0a] bg-white text-[#0a0a0a]" : "border-red-500/50 bg-red-500/10 text-red-600"}`}
                                >
                                    Playwright: {status.playwright.available ? "✓" : "✗"}
                                </motion.span>
                            )}
                        </div>
                    </div>
                </nav>

                {/* Main Content */}
                <div className="pt-24 pb-12 px-4 sm:px-6">
                    <div className="max-w-7xl mx-auto">
                        {/* Header */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="text-center mb-10"
                        >
                            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white border border-[#d4d4c8] mb-4">
                                <span className="text-2xl">🕷️</span>
                                <span className="text-[#0a0a0a] font-medium">Web Scraper</span>
                            </div>
                            <h1 className="text-3xl sm:text-4xl md:text-5xl font-display mb-4">
                                Browser automation.
                            </h1>
                            <p className="text-[#666] max-w-xl mx-auto text-sm sm:text-base">
                                Scrape any website with Playwright. Extract text, HTML, or capture screenshots with stealth mode.
                            </p>
                        </motion.div>

                        <div className="grid lg:grid-cols-2 gap-6">
                            {/* Configuration Panel */}
                            <motion.div
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.5, delay: 0.1 }}
                                className="app-panel p-6"
                            >
                                <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                    <span className="w-8 h-8 rounded-lg bg-[#0a0a0a] text-[#f5f5f0] flex items-center justify-center text-sm">⚙️</span>
                                    Configuration
                                </h2>

                                {/* URL Input */}
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-[#666] mb-2">Target URL</label>
                                    <input
                                        type="url"
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                        placeholder="https://example.com"
                                        className="app-input"
                                    />
                                </div>

                                {/* Engine Badge */}
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-[#666] mb-2">Scraping Engine</label>
                                    <div className="px-4 py-3 rounded-xl border border-[#d4d4c8] bg-[#fafaf5] text-[#0a0a0a] flex items-center justify-center gap-2">
                                        <span className="text-lg">🎭</span>
                                        Playwright (Stealth Mode)
                                    </div>
                                </div>

                                {/* Wait Time */}
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-gray-400 mb-2">
                                        Wait Time: <span className="text-[#0a0a0a] font-mono">{waitTime}ms</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="500"
                                        max="10000"
                                        step="500"
                                        value={waitTime}
                                        onChange={(e) => setWaitTime(Number(e.target.value))}
                                        className="w-full h-2 bg-[#ebebdf] rounded-lg appearance-none cursor-pointer accent-[#0a0a0a]"
                                    />
                                    <div className="flex justify-between text-xs text-[#999] mt-1">
                                        <span>500ms</span>
                                        <span>10s</span>
                                    </div>
                                </div>

                                {/* Extract Selector */}
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-gray-400 mb-2">
                                        CSS Selector <span className="text-gray-500">(optional)</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={extractSelector}
                                        onChange={(e) => setExtractSelector(e.target.value)}
                                        placeholder=".main-content, #article, body"
                                        className="app-input font-mono text-sm"
                                    />
                                </div>

                                {/* Screenshot Toggle */}
                                <div className="mb-6">
                                    <label className="flex items-center gap-3 cursor-pointer">
                                        <motion.div
                                            onClick={() => setCaptureScreenshot(!captureScreenshot)}
                                            className={`w-12 h-6 rounded-full transition-all relative ${captureScreenshot ? "bg-[#0a0a0a]" : "bg-[#ebebdf] border border-[#d4d4c8]"}`}
                                            whileTap={{ scale: 0.95 }}
                                        >
                                            <motion.div
                                                className="absolute top-0.5 w-5 h-5 rounded-full bg-white"
                                                animate={{ left: captureScreenshot ? "24px" : "2px" }}
                                                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                                            />
                                        </motion.div>
                                        <span className="text-[#0a0a0a]">Capture Screenshot</span>
                                    </label>
                                </div>

                                {/* Scrape Button */}
                                <motion.button
                                    onClick={handleScrape}
                                    disabled={!url || loading}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    className={`w-full py-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${loading
                                        ? "bg-[#ebebdf] cursor-not-allowed text-[#999]"
                                        : "bg-[#0a0a0a] text-[#f5f5f0] hover:opacity-90"
                                        }`}
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                                            Scraping...
                                        </>
                                    ) : (
                                        <>
                                            <span>🕷️</span>
                                            Start Scraping
                                        </>
                                    )}
                                </motion.button>
                            </motion.div>

                            {/* Results Panel */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.5, delay: 0.2 }}
                                className="app-panel p-6"
                            >
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-xl font-semibold flex items-center gap-2">
                                        <span className="w-8 h-8 rounded-lg bg-[#0a0a0a] text-[#f5f5f0] flex items-center justify-center text-sm">📄</span>
                                        Results
                                    </h2>
                                    {result && result.success && (
                                        <div className="flex gap-2">
                                            <button onClick={() => handleExport("json")} className="px-3 py-1.5 rounded-lg text-xs border border-[#d4d4c8] bg-white text-[#0a0a0a] hover:border-[#0a0a0a] transition-all">
                                                JSON
                                            </button>
                                            <button onClick={() => handleExport("html")} className="px-3 py-1.5 rounded-lg text-xs border border-[#d4d4c8] bg-white text-[#0a0a0a] hover:border-[#0a0a0a] transition-all">
                                                HTML
                                            </button>
                                            <button onClick={() => handleExport("text")} className="px-3 py-1.5 rounded-lg text-xs border border-[#d4d4c8] bg-white text-[#0a0a0a] hover:border-[#0a0a0a] transition-all">
                                                TXT
                                            </button>
                                        </div>
                                    )}
                                </div>

                                {!result ? (
                                    <div className="h-[400px] flex items-center justify-center text-[#666]">
                                        <div className="text-center">
                                            <span className="text-5xl mb-4 block opacity-30">🕸️</span>
                                            <p>Enter a URL and click &quot;Start Scraping&quot;</p>
                                        </div>
                                    </div>
                                ) : result.error ? (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="h-[400px] flex items-center justify-center"
                                    >
                                        <div className="text-center p-6 rounded-xl bg-red-500/10 border border-red-500/30">
                                            <span className="text-4xl mb-3 block">❌</span>
                                            <p className="text-red-400 font-medium mb-2">Scraping Failed</p>
                                            <p className="text-gray-400 text-sm">{result.error}</p>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                    >
                                        {/* Result Meta */}
                                        <div className="flex flex-wrap gap-2 mb-4">
                                            <span className="px-3 py-1 rounded-full text-xs border border-[#d4d4c8] bg-white">✓ Success</span>
                                            <span className="px-3 py-1 rounded-full text-xs border border-[#d4d4c8] bg-white font-mono">{result.engine}</span>
                                            <span className="px-3 py-1 rounded-full text-xs border border-[#d4d4c8] bg-white font-mono">{result.load_time_ms}ms</span>
                                        </div>

                                        {result.title && (
                                            <p className="text-[#0a0a0a] font-medium mb-4 truncate" title={result.title}>
                                                📑 {result.title}
                                            </p>
                                        )}

                                        {/* Tabs */}
                                        <div className="flex gap-2 mb-4 border-b border-[#d4d4c8] pb-2">
                                            <button
                                                onClick={() => setActiveTab("text")}
                                                className={`px-4 py-2 rounded-lg text-sm transition-all border ${activeTab === "text" ? "bg-[#0a0a0a] text-[#f5f5f0] border-[#0a0a0a]" : "bg-white text-[#666] border-[#d4d4c8] hover:border-[#0a0a0a]"}`}
                                            >
                                                Text
                                            </button>
                                            <button
                                                onClick={() => setActiveTab("html")}
                                                className={`px-4 py-2 rounded-lg text-sm transition-all border ${activeTab === "html" ? "bg-[#0a0a0a] text-[#f5f5f0] border-[#0a0a0a]" : "bg-white text-[#666] border-[#d4d4c8] hover:border-[#0a0a0a]"}`}
                                            >
                                                HTML
                                            </button>
                                            {result.screenshot && (
                                                <button
                                                    onClick={() => setActiveTab("screenshot")}
                                                    className={`px-4 py-2 rounded-lg text-sm transition-all border ${activeTab === "screenshot" ? "bg-[#0a0a0a] text-[#f5f5f0] border-[#0a0a0a]" : "bg-white text-[#666] border-[#d4d4c8] hover:border-[#0a0a0a]"}`}
                                                >
                                                    Screenshot
                                                </button>
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="h-[300px] overflow-auto rounded-xl bg-[#fafaf5] border border-[#d4d4c8] p-4">
                                            {activeTab === "text" && (
                                                <pre className="text-sm text-[#0a0a0a] whitespace-pre-wrap font-mono">
                                                    {result.text || "No text content extracted"}
                                                </pre>
                                            )}
                                            {activeTab === "html" && (
                                                <pre className="text-sm text-[#0a0a0a] whitespace-pre-wrap font-mono">
                                                    {result.html || "No HTML content"}
                                                </pre>
                                            )}
                                            {activeTab === "screenshot" && result.screenshot && (
                                                <img
                                                    src={`data:image/png;base64,${result.screenshot}`}
                                                    alt="Screenshot"
                                                    className="max-w-full rounded-lg"
                                                />
                                            )}
                                        </div>
                                    </motion.div>
                                )}
                            </motion.div>
                        </div>

                        {/* Back Link */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.4 }}
                            className="text-center mt-8"
                        >
                            <Link href="/" className="inline-flex items-center gap-2 text-[#666] hover:text-[#0a0a0a] transition-colors">
                                ← Back to Home
                            </Link>
                        </motion.div>
                    </div>
                </div>
            </main>
        </AuthGuard>
    );
}
