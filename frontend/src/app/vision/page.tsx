"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { AuthGuard } from "../components/AuthGuard";
import { buildAuthHeaders } from "../lib/api";
import { useSettings } from "../hooks/useSettings";

interface AnalysisResult {
    analysis?: string;
    description?: string;
    text?: string;
    objects?: string;
    status?: string;
}

export default function VisionPage() {
    const { settings } = useSettings();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [analysis, setAnalysis] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [analysisType, setAnalysisType] = useState<"analyze" | "describe" | "extract-text" | "identify-objects">("analyze");
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setPreview(URL.createObjectURL(file));
            setAnalysis(null);
        }
    };

    const analyzeImage = async () => {
        if (!selectedFile) return;

        setIsLoading(true);
        setAnalysis(null);

        try {
            const formData = new FormData();
            formData.append("file", selectedFile);
            if (settings.openaiApiKey) {
                formData.append("api_key", settings.openaiApiKey);
            }

            let endpoint = "analyze";
            if (analysisType === "describe") endpoint = "describe";
            else if (analysisType === "extract-text") endpoint = "extract-text";
            else if (analysisType === "identify-objects") endpoint = "identify-objects";

            const response = await fetch(`/api/vision/${endpoint}`, {
                method: "POST",
                headers: await buildAuthHeaders(),
                body: formData,
            });

            const data: AnalysisResult = await response.json();
            setAnalysis(data.analysis || data.description || data.text || data.objects || "No analysis available");
        } catch {
            setAnalysis("❌ Failed to analyze image. Make sure the backend is running.");
        } finally {
            setIsLoading(false);
        }
    };

    const clearImage = () => {
        setSelectedFile(null);
        setPreview(null);
        setAnalysis(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    return (
        <AuthGuard>
            <main className="min-h-screen bg-[#f5f5f0] text-[#0a0a0a]">
                <div className="fixed inset-0 grid-pattern pointer-events-none" />

                {/* Header */}
                <header className="sticky top-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md border-b border-[#d4d4c8]">
                    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                            <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
                                <span className="text-[#f5f5f0] font-bold text-sm">O</span>
                            </div>
                            <span className="font-semibold text-lg tracking-tight">OmniDev</span>
                        </Link>
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🖼️</span>
                            <span className="font-semibold">Vision Lab</span>
                            <span className="app-badge font-mono">GPT-5 Mini</span>
                        </div>
                    </div>
                </header>

                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                    <motion.div
                        className="text-center mb-8"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <h1 className="text-3xl sm:text-4xl font-display mb-2">Vision Analysis</h1>
                        <p className="text-[#666]">Upload an image and run a quick analysis.</p>
                    </motion.div>

                    <div className="grid lg:grid-cols-2 gap-8">
                        {/* Upload Section */}
                        <motion.div
                            className="app-panel p-6"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                        >
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-[#0a0a0a] text-[#f5f5f0] flex items-center justify-center text-sm">📤</span>
                                Upload Image
                            </h2>

                            <AnimatePresence mode="wait">
                                {!preview ? (
                                    <motion.div
                                        key="upload"
                                        onClick={() => fileInputRef.current?.click()}
                                        className="border-2 border-dashed border-[#d4d4c8] rounded-xl p-12 text-center cursor-pointer hover:border-[#0a0a0a] transition-colors bg-white"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        whileHover={{ scale: 1.02 }}
                                    >
                                        <div className="text-5xl mb-4">📤</div>
                                        <p className="text-[#666] mb-2">Click to upload or drag and drop</p>
                                        <p className="text-sm text-[#999]">JPEG, PNG, WebP, GIF</p>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="preview"
                                        className="space-y-4"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                    >
                                        <div className="relative rounded-xl overflow-hidden">
                                            <img
                                                src={preview}
                                                alt="Preview"
                                                className="w-full max-h-80 object-contain bg-[#050505]"
                                            />
                                            <motion.button
                                                onClick={clearImage}
                                                className="absolute top-2 right-2 w-8 h-8 bg-red-500/80 rounded-full flex items-center justify-center hover:bg-red-500 transition-colors"
                                                whileHover={{ scale: 1.1 }}
                                                whileTap={{ scale: 0.9 }}
                                            >
                                                ✕
                                            </motion.button>
                                        </div>

                                        <p className="text-sm text-gray-400">
                                            {selectedFile?.name} ({((selectedFile?.size || 0) / 1024).toFixed(1)} KB)
                                        </p>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/gif"
                                onChange={handleFileSelect}
                                className="hidden"
                            />

                            {preview && (
                                <motion.div
                                    className="mt-6 space-y-4"
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <div>
                                        <label className="text-sm text-[#666] mb-2 block">Analysis Type</label>
                                        <div className="grid grid-cols-2 gap-2">
                                            {[
                                                { value: "analyze", label: "🔍 General Analysis" },
                                                { value: "describe", label: "📝 Detailed Description" },
                                                { value: "extract-text", label: "📄 Extract Text (OCR)" },
                                                { value: "identify-objects", label: "🎯 Identify Objects" },
                                            ].map((type) => (
                                                <motion.button
                                                    key={type.value}
                                                    onClick={() => setAnalysisType(type.value as typeof analysisType)}
                                                    className={`px-3 py-2 rounded-lg text-sm border transition-all bg-white ${analysisType === type.value
                                                        ? "border-[#0a0a0a] text-[#0a0a0a]"
                                                        : "border-[#d4d4c8] text-[#666] hover:border-[#0a0a0a]"
                                                        }`}
                                                    whileHover={{ scale: 1.02 }}
                                                    whileTap={{ scale: 0.98 }}
                                                >
                                                    {type.label}
                                                </motion.button>
                                            ))}
                                        </div>
                                    </div>

                                    <motion.button
                                        onClick={analyzeImage}
                                        disabled={isLoading}
                                        className="w-full py-3 rounded-xl bg-[#0a0a0a] text-[#f5f5f0] font-semibold disabled:opacity-50"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        {isLoading ? (
                                            <span className="flex items-center justify-center gap-2">
                                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analyzing...
                                            </span>
                                        ) : (
                                            "Analyze Image"
                                        )}
                                    </motion.button>
                                </motion.div>
                            )}
                        </motion.div>

                        {/* Results Section */}
                        <motion.div
                            className="app-panel p-6"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                        >
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-[#0a0a0a] text-[#f5f5f0] flex items-center justify-center text-sm">📊</span>
                                Analysis Results
                            </h2>

                            <AnimatePresence mode="wait">
                                {analysis ? (
                                    <motion.div
                                        key="result"
                                        className="max-w-none"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                    >
                                        <div className="rounded-xl p-4 border border-[#d4d4c8] bg-[#fafaf5]">
                                            <div className="whitespace-pre-wrap text-[#0a0a0a]">{analysis}</div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="empty"
                                        className="text-center py-12 text-[#666]"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                    >
                                        <div className="text-5xl mb-4">🔬</div>
                                        <p>Upload an image and click &quot;Analyze&quot; to see results</p>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    </div>

                    {/* Features */}
                    <motion.div
                        className="mt-12"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                    >
                        <h2 className="text-xl font-display mb-6 text-center">What you can do</h2>
                        <div className="grid md:grid-cols-4 gap-4">
                            {[
                                { icon: "🔍", title: "Scene Analysis", desc: "Understand image context and content" },
                                { icon: "📝", title: "OCR", desc: "Extract text from images accurately" },
                                { icon: "🎯", title: "Object Detection", desc: "Identify and locate objects" },
                                { icon: "🎨", title: "Style Recognition", desc: "Detect colors, mood, and aesthetics" },
                            ].map((feature, i) => (
                                <motion.div
                                    key={feature.title}
                                    className="feature-card text-center !p-5"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.5 + i * 0.1 }}
                                    whileHover={{ scale: 1.03 }}
                                >
                                    <div className="text-3xl mb-2">{feature.icon}</div>
                                    <h3 className="font-medium mb-1">{feature.title}</h3>
                                    <p className="text-xs text-[#666]">{feature.desc}</p>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </main>
        </AuthGuard>
    );
}
