"use client";

import Link from "next/link";
import { useState } from "react";

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
    selenium: { available: boolean; driver_active: boolean };
}

export default function ScraperPage() {
    // Form state
    const [url, setUrl] = useState("");
    const [engine, setEngine] = useState<"playwright" | "selenium">("playwright");
    const [waitTime, setWaitTime] = useState(2000);
    const [captureScreenshot, setCaptureScreenshot] = useState(false);
    const [extractSelector, setExtractSelector] = useState("");

    // UI state
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ScrapeResult | null>(null);
    const [activeTab, setActiveTab] = useState<"text" | "html" | "screenshot">("text");
    const [status, setStatus] = useState<ScraperStatus | null>(null);

    const fetchStatus = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/scraper/status");
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
            const res = await fetch("http://localhost:8000/api/scraper/scrape", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url,
                    engine,
                    wait_time_ms: waitTime,
                    capture_screenshot: captureScreenshot,
                    extract_selector: extractSelector || undefined,
                }),
            });

            const data = await res.json();
            setResult(data);

            if (data.screenshot) {
                setActiveTab("screenshot");
            } else if (data.text) {
                setActiveTab("text");
            }
        } catch (error) {
            setResult({
                success: false,
                url,
                title: "",
                html: "",
                text: "",
                screenshot: null,
                error: "Failed to connect to backend. Is it running?",
                engine,
                load_time_ms: 0,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleExport = (format: "json" | "html" | "text") => {
        if (!result) return;

        let content: string;
        let mimeType: string;
        let filename: string;

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
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <main className="min-h-screen relative">
            {/* Animated Background */}
            <div className="animated-bg" />

            {/* Navigation */}
            <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-[--border]">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <span className="text-2xl">🚀</span>
                        <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                            OmniDev
                        </span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={fetchStatus}
                            className="px-4 py-2 rounded-lg border border-[--border] text-sm text-gray-400 hover:text-white hover:border-violet-500 transition-all"
                        >
                            Check Status
                        </button>
                        {status && (
                            <div className="flex gap-2">
                                <span className={`status-badge ${status.playwright.available ? 'success' : 'error'}`}>
                                    Playwright: {status.playwright.available ? "✓" : "✗"}
                                </span>
                                <span className={`status-badge ${status.selenium.available ? 'success' : 'error'}`}>
                                    Selenium: {status.selenium.available ? "✓" : "✗"}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <div className="pt-24 pb-12 px-6">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="text-center mb-10">
                        <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-gradient-to-r from-red-500/20 to-rose-500/20 border border-red-500/30 mb-4">
                            <span className="text-2xl">🕷️</span>
                            <span className="text-red-400 font-medium">Web Scraper</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold mb-4">
                            <span className="bg-gradient-to-r from-red-500 via-rose-500 to-pink-500 bg-clip-text text-transparent">
                                Browser Automation
                            </span>
                        </h1>
                        <p className="text-gray-400 max-w-xl mx-auto">
                            Scrape any website with Selenium or Playwright. Extract text, HTML, or capture screenshots with anti-detection capabilities.
                        </p>
                    </div>

                    <div className="grid lg:grid-cols-2 gap-6">
                        {/* Configuration Panel */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-gradient-to-r from-violet-500 to-purple-600 flex items-center justify-center text-sm">⚙️</span>
                                Configuration
                            </h2>

                            {/* URL Input */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-400 mb-2">Target URL</label>
                                <input
                                    type="url"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    placeholder="https://example.com"
                                    className="w-full px-4 py-3 rounded-xl bg-[--card-bg] border border-[--border] text-white placeholder-gray-500 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 transition-all outline-none"
                                />
                            </div>

                            {/* Engine Selection */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-400 mb-2">Scraping Engine</label>
                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        onClick={() => setEngine("playwright")}
                                        className={`px-4 py-3 rounded-xl border transition-all flex items-center justify-center gap-2 ${engine === "playwright"
                                                ? "border-violet-500 bg-violet-500/20 text-white"
                                                : "border-[--border] text-gray-400 hover:border-gray-600"
                                            }`}
                                    >
                                        <span className="text-lg">🎭</span>
                                        Playwright
                                    </button>
                                    <button
                                        onClick={() => setEngine("selenium")}
                                        className={`px-4 py-3 rounded-xl border transition-all flex items-center justify-center gap-2 ${engine === "selenium"
                                                ? "border-emerald-500 bg-emerald-500/20 text-white"
                                                : "border-[--border] text-gray-400 hover:border-gray-600"
                                            }`}
                                    >
                                        <span className="text-lg">🔧</span>
                                        Selenium
                                    </button>
                                </div>
                            </div>

                            {/* Wait Time */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Wait Time: <span className="text-white">{waitTime}ms</span>
                                </label>
                                <input
                                    type="range"
                                    min="500"
                                    max="10000"
                                    step="500"
                                    value={waitTime}
                                    onChange={(e) => setWaitTime(Number(e.target.value))}
                                    className="w-full h-2 bg-[--card-bg] rounded-lg appearance-none cursor-pointer accent-violet-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
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
                                    className="w-full px-4 py-3 rounded-xl bg-[--card-bg] border border-[--border] text-white placeholder-gray-500 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 transition-all outline-none font-mono text-sm"
                                />
                            </div>

                            {/* Screenshot Toggle */}
                            <div className="mb-6">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <div
                                        onClick={() => setCaptureScreenshot(!captureScreenshot)}
                                        className={`w-12 h-6 rounded-full transition-all relative ${captureScreenshot ? "bg-violet-500" : "bg-[--card-bg] border border-[--border]"
                                            }`}
                                    >
                                        <div
                                            className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all ${captureScreenshot ? "left-6" : "left-0.5"
                                                }`}
                                        />
                                    </div>
                                    <span className="text-gray-300">Capture Screenshot</span>
                                </label>
                            </div>

                            {/* Scrape Button */}
                            <button
                                onClick={handleScrape}
                                disabled={!url || loading}
                                className={`w-full py-4 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2 ${loading
                                        ? "bg-gray-600 cursor-not-allowed"
                                        : "glow-button hover:scale-[1.02]"
                                    }`}
                            >
                                {loading ? (
                                    <>
                                        <div className="spinner" />
                                        Scraping...
                                    </>
                                ) : (
                                    <>
                                        <span>🕷️</span>
                                        Start Scraping
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Results Panel */}
                        <div className="glass-card p-6 rounded-2xl">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-semibold flex items-center gap-2">
                                    <span className="w-8 h-8 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 flex items-center justify-center text-sm">📄</span>
                                    Results
                                </h2>
                                {result && result.success && (
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleExport("json")}
                                            className="px-3 py-1.5 rounded-lg text-xs bg-violet-500/20 text-violet-400 hover:bg-violet-500/30 transition-all"
                                        >
                                            JSON
                                        </button>
                                        <button
                                            onClick={() => handleExport("html")}
                                            className="px-3 py-1.5 rounded-lg text-xs bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-all"
                                        >
                                            HTML
                                        </button>
                                        <button
                                            onClick={() => handleExport("text")}
                                            className="px-3 py-1.5 rounded-lg text-xs bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition-all"
                                        >
                                            TXT
                                        </button>
                                    </div>
                                )}
                            </div>

                            {!result ? (
                                <div className="h-[400px] flex items-center justify-center text-gray-500">
                                    <div className="text-center">
                                        <span className="text-5xl mb-4 block opacity-30">🕸️</span>
                                        <p>Enter a URL and click "Start Scraping"</p>
                                    </div>
                                </div>
                            ) : result.error ? (
                                <div className="h-[400px] flex items-center justify-center">
                                    <div className="text-center p-6 rounded-xl bg-red-500/10 border border-red-500/30">
                                        <span className="text-4xl mb-3 block">❌</span>
                                        <p className="text-red-400 font-medium mb-2">Scraping Failed</p>
                                        <p className="text-gray-400 text-sm">{result.error}</p>
                                    </div>
                                </div>
                            ) : (
                                <div>
                                    {/* Result Meta */}
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        <span className="px-3 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-400">
                                            ✓ Success
                                        </span>
                                        <span className="px-3 py-1 rounded-full text-xs bg-violet-500/20 text-violet-400">
                                            {result.engine}
                                        </span>
                                        <span className="px-3 py-1 rounded-full text-xs bg-cyan-500/20 text-cyan-400">
                                            {result.load_time_ms}ms
                                        </span>
                                    </div>

                                    {/* Title */}
                                    {result.title && (
                                        <p className="text-white font-medium mb-4 truncate" title={result.title}>
                                            📑 {result.title}
                                        </p>
                                    )}

                                    {/* Tabs */}
                                    <div className="flex gap-2 mb-4 border-b border-[--border] pb-2">
                                        <button
                                            onClick={() => setActiveTab("text")}
                                            className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === "text"
                                                    ? "bg-violet-500/20 text-violet-400"
                                                    : "text-gray-400 hover:text-white"
                                                }`}
                                        >
                                            Text
                                        </button>
                                        <button
                                            onClick={() => setActiveTab("html")}
                                            className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === "html"
                                                    ? "bg-cyan-500/20 text-cyan-400"
                                                    : "text-gray-400 hover:text-white"
                                                }`}
                                        >
                                            HTML
                                        </button>
                                        {result.screenshot && (
                                            <button
                                                onClick={() => setActiveTab("screenshot")}
                                                className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === "screenshot"
                                                        ? "bg-emerald-500/20 text-emerald-400"
                                                        : "text-gray-400 hover:text-white"
                                                    }`}
                                            >
                                                Screenshot
                                            </button>
                                        )}
                                    </div>

                                    {/* Content */}
                                    <div className="h-[300px] overflow-auto rounded-xl bg-[--card-bg] border border-[--border] p-4">
                                        {activeTab === "text" && (
                                            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                                                {result.text || "No text content extracted"}
                                            </pre>
                                        )}
                                        {activeTab === "html" && (
                                            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
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
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Back Link */}
                    <div className="text-center mt-8">
                        <Link
                            href="/"
                            className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                        >
                            ← Back to Home
                        </Link>
                    </div>
                </div>
            </div>
        </main>
    );
}
