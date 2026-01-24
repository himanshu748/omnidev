"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import AWSGuideModal from "../../views/AWSGuideModal";
import { AuthGuard } from "../components/AuthGuard";
import { buildAuthHeaders } from "../lib/api";

interface Message {
    id: string;
    role: "user" | "agent";
    content: string;
    timestamp: Date;
    context?: Record<string, unknown>;
}

interface Capabilities {
    name: string;
    version: string;
    ai_enabled: boolean;
    aws_configured: boolean;
    region: string;
    capabilities: Array<{
        category: string;
        actions: string[];
    }>;
}

export default function DevOpsPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
    const [showAwsGuide, setShowAwsGuide] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const loadCapabilities = async () => {
            try {
                const res = await fetch("/api/devops/capabilities", {
                    headers: await buildAuthHeaders(),
                });
                const data = await res.json();
                setCapabilities(data);
            } catch (error) {
                console.error(error);
            }
        };
        loadCapabilities();
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendCommand = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch("/api/devops/command", {
                method: "POST",
                headers: {
                    ...(await buildAuthHeaders()),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ command: userMessage.content }),
            });

            const data = await response.json();

            const agentMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "agent",
                content: data.response,
                timestamp: new Date(),
                context: data.context,
            };

            setMessages((prev) => [...prev, agentMessage]);
        } catch {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "agent",
                content: "❌ Failed to connect to DevOps Agent. Make sure the backend is running.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const quickCommands = [
        "List my EC2 instances",
        "Show S3 buckets",
        "What can you help me with?",
        "Infrastructure status",
    ];

    return (
        <AuthGuard>
            <main className="min-h-screen flex bg-[#f5f5f0] text-[#0a0a0a]">
                <div className="fixed inset-0 grid-pattern pointer-events-none" />

                {/* Sidebar */}
                <aside className="w-72 bg-white border-r border-[#d4d4c8] p-6 hidden lg:block">
                    <Link href="/" className="flex items-center gap-3 mb-8 hover:opacity-80 transition-opacity">
                        <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
                            <span className="text-[#f5f5f0] font-bold text-sm">O</span>
                        </div>
                        <span className="font-semibold text-lg tracking-tight">OmniDev</span>
                    </Link>

                    <div className="mb-8">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>🛠️</span> DevOps Agent
                        </h3>
                        {capabilities && (
                            <div className="space-y-3 text-sm">
                                <div className="flex items-center gap-2">
                                    <span className={`px-3 py-1 rounded-full text-xs border ${capabilities.ai_enabled ? "border-[#0a0a0a] bg-[#fafaf5]" : "border-[#d4d4c8] bg-white text-[#666]"}`}>
                                        AI: {capabilities.ai_enabled ? "Active" : "Inactive"}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`px-3 py-1 rounded-full text-xs border ${capabilities.aws_configured ? "border-[#0a0a0a] bg-[#fafaf5]" : "border-[#d4d4c8] bg-white text-[#666]"}`}>
                                        AWS: {capabilities.aws_configured ? "Connected" : "Not configured"}
                                    </span>
                                </div>
                                <p className="text-[#666]">Region: <span className="font-mono">{capabilities.region}</span></p>
                            </div>
                        )}

                        <button
                            onClick={() => setShowAwsGuide(true)}
                            className="mt-4 w-full py-2 px-3 rounded-lg border border-[#d4d4c8] bg-white text-sm hover:border-[#0a0a0a] transition-all flex items-center justify-center gap-2"
                        >
                            <span>🔑</span> Get AWS API Keys
                        </button>
                        <AWSGuideModal isOpen={showAwsGuide} onClose={() => setShowAwsGuide(false)} />
                    </div>

                    <div>
                        <h4 className="text-sm font-medium text-[#666] mb-3">Capabilities</h4>
                        <div className="space-y-4">
                            {capabilities?.capabilities.map((cap) => (
                                <div key={cap.category}>
                                    <h5 className="text-sm font-medium mb-1">{cap.category}</h5>
                                    <ul className="text-xs text-[#666] space-y-1">
                                        {cap.actions.map((action) => (
                                            <li key={action}>• {action}</li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <div className="flex-1 flex flex-col">
                    {/* Header (Mobile) */}
                    <header className="lg:hidden sticky top-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md border-b border-[#d4d4c8]">
                        <div className="px-4 py-4 flex items-center justify-between">
                            <Link href="/" className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
                                    <span className="text-[#f5f5f0] font-bold text-sm">O</span>
                                </div>
                                <span className="font-semibold">OmniDev</span>
                            </Link>
                            <span className="font-semibold">🛠️ DevOps Agent</span>
                        </div>
                    </header>

                    {/* Terminal */}
                    <div className="flex-1 p-4 sm:p-6 flex flex-col">
                        <div className="app-panel flex-1 flex flex-col overflow-hidden">
                            <div className="px-4 py-3 border-b border-[#d4d4c8] bg-white flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                                <div className="w-3 h-3 rounded-full bg-green-500" />
                                <span className="text-sm text-[#666] ml-2">DevOps Agent</span>
                            </div>

                            <div className="flex-1 overflow-y-auto bg-[#0a0a0a] text-[#f5f5f0]">
                                {messages.length === 0 ? (
                                    <div className="text-center py-10">
                                        <div className="text-5xl mb-4">🤖</div>
                                        <h2 className="text-xl font-semibold mb-2">Smart DevOps Agent</h2>
                                        <p className="text-[#f5f5f0]/70 text-sm max-w-md mx-auto mb-6">
                                            I&apos;m your AI-powered cloud assistant. Ask me to manage your EC2 instances,
                                            S3 buckets, check costs, or troubleshoot issues.
                                        </p>
                                        <div className="flex flex-wrap gap-2 justify-center">
                                            {quickCommands.map((cmd) => (
                                                <button
                                                    key={cmd}
                                                    onClick={() => setInput(cmd)}
                                                    className="px-3 py-1.5 rounded-lg text-xs border border-white/15 text-[#f5f5f0]/80 hover:border-white/40 transition-all"
                                                >
                                                    {cmd}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-4 p-4">
                                        {messages.map((message) => (
                                            <div key={message.id}>
                                                {message.role === "user" ? (
                                                    <div className="flex items-start gap-2">
                                                        <span className="text-[#e55c1c] font-mono">$</span>
                                                        <span className="text-[#f5f5f0]">{message.content}</span>
                                                    </div>
                                                ) : (
                                                    <div className="pl-4 border-l-2 border-white/15">
                                                        <div className="text-[#f5f5f0]/90 whitespace-pre-wrap">{message.content}</div>
                                                        <div className="text-xs text-[#f5f5f0]/60 mt-1">
                                                            {message.timestamp.toLocaleTimeString()}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}

                                        {isLoading && (
                                            <div className="flex items-center gap-2 text-[#f5f5f0]/70">
                                                <div className="w-4 h-4 border-2 border-white/25 border-t-white rounded-full animate-spin" />
                                                <span>Processing command...</span>
                                            </div>
                                        )}

                                        <div ref={messagesEndRef} />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Input */}
                        <form onSubmit={sendCommand} className="mt-4">
                            <div className="flex gap-3">
                                <div className="flex-1 flex items-center gap-2 bg-white border border-[#d4d4c8] rounded-xl px-4">
                                    <span className="text-[#e55c1c] font-mono">$</span>
                                    <input
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        placeholder="Enter command..."
                                        className="flex-1 bg-transparent py-3 focus:outline-none"
                                        disabled={isLoading}
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={isLoading || !input.trim()}
                                    className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Execute
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </main>
        </AuthGuard>
    );
}
