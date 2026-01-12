"use client";

import { useState, useRef } from "react";
import Link from "next/link";

interface AnalysisResult {
    analysis?: string;
    description?: string;
    text?: string;
    objects?: string;
    status?: string;
}

export default function VisionPage() {
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

            let endpoint = "analyze";
            if (analysisType === "describe") endpoint = "describe";
            else if (analysisType === "extract-text") endpoint = "extract-text";
            else if (analysisType === "identify-objects") endpoint = "identify-objects";

            const response = await fetch(`http://localhost:8000/api/vision/${endpoint}`, {
                method: "POST",
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
        <main className="min-h-screen">
            <div className="animated-bg" />

            {/* Header */}
            <header className="glass-card border-b border-[--border] sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <span className="text-xl">←</span>
                        <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                            OmniDev
                        </span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🖼️</span>
                        <span className="font-semibold">Vision Lab</span>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto px-6 py-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold mb-2">Vision Analysis Lab</h1>
                    <p className="text-gray-400">Upload an image and let GPT-4o Vision analyze it</p>
                </div>

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Upload Section */}
                    <div className="glass-card p-6">
                        <h2 className="text-lg font-semibold mb-4">Upload Image</h2>

                        {!preview ? (
                            <div
                                onClick={() => fileInputRef.current?.click()}
                                className="border-2 border-dashed border-[--border] rounded-xl p-12 text-center cursor-pointer hover:border-violet-500 transition-colors"
                            >
                                <div className="text-5xl mb-4">📤</div>
                                <p className="text-gray-400 mb-2">Click to upload or drag and drop</p>
                                <p className="text-sm text-gray-500">JPEG, PNG, WebP, GIF</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="relative rounded-xl overflow-hidden">
                                    <img
                                        src={preview}
                                        alt="Preview"
                                        className="w-full max-h-80 object-contain bg-[--card]"
                                    />
                                    <button
                                        onClick={clearImage}
                                        className="absolute top-2 right-2 w-8 h-8 bg-red-500/80 rounded-full flex items-center justify-center hover:bg-red-500 transition-colors"
                                    >
                                        ✕
                                    </button>
                                </div>

                                <p className="text-sm text-gray-400">
                                    {selectedFile?.name} ({((selectedFile?.size || 0) / 1024).toFixed(1)} KB)
                                </p>
                            </div>
                        )}

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/jpeg,image/png,image/webp,image/gif"
                            onChange={handleFileSelect}
                            className="hidden"
                        />

                        {preview && (
                            <div className="mt-6 space-y-4">
                                <div>
                                    <label className="text-sm text-gray-400 mb-2 block">Analysis Type</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {[
                                            { value: "analyze", label: "🔍 General Analysis" },
                                            { value: "describe", label: "📝 Detailed Description" },
                                            { value: "extract-text", label: "📄 Extract Text (OCR)" },
                                            { value: "identify-objects", label: "🎯 Identify Objects" },
                                        ].map((type) => (
                                            <button
                                                key={type.value}
                                                onClick={() => setAnalysisType(type.value as typeof analysisType)}
                                                className={`px-3 py-2 rounded-lg text-sm border transition-all ${analysisType === type.value
                                                    ? "border-violet-500 bg-violet-500/20 text-violet-400"
                                                    : "border-[--border] text-gray-400 hover:border-violet-500/50"
                                                    }`}
                                            >
                                                {type.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    onClick={analyzeImage}
                                    disabled={isLoading}
                                    className="glow-button text-white w-full py-3 disabled:opacity-50"
                                >
                                    {isLoading ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <div className="spinner" /> Analyzing...
                                        </span>
                                    ) : (
                                        "Analyze Image"
                                    )}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Results Section */}
                    <div className="glass-card p-6">
                        <h2 className="text-lg font-semibold mb-4">Analysis Results</h2>

                        {analysis ? (
                            <div className="prose prose-invert max-w-none">
                                <div className="bg-[--card] rounded-xl p-4 border border-[--border]">
                                    <div className="whitespace-pre-wrap text-gray-300">{analysis}</div>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-12 text-gray-500">
                                <div className="text-5xl mb-4">🔬</div>
                                <p>Upload an image and click &quot;Analyze&quot; to see results</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Features */}
                <div className="mt-12">
                    <h2 className="text-xl font-semibold mb-6 text-center">Powered by GPT-4o Vision</h2>
                    <div className="grid md:grid-cols-4 gap-4">
                        {[
                            { icon: "🔍", title: "Scene Analysis", desc: "Understand image context and content" },
                            { icon: "📝", title: "OCR", desc: "Extract text from images accurately" },
                            { icon: "🎯", title: "Object Detection", desc: "Identify and locate objects" },
                            { icon: "🎨", title: "Style Recognition", desc: "Detect colors, mood, and aesthetics" },
                        ].map((feature) => (
                            <div key={feature.title} className="glass-card p-4 text-center">
                                <div className="text-3xl mb-2">{feature.icon}</div>
                                <h3 className="font-medium mb-1">{feature.title}</h3>
                                <p className="text-xs text-gray-400">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </main>
    );
}
