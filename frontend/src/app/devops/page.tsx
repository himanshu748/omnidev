"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import AWSGuideModal from "../../views/AWSGuideModal";
import { AuthGuard } from "../components/AuthGuard";

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
        // Fetch agent capabilities on mount
        fetch("/api/devops/capabilities")
            .then((res) => res.json())
            .then((data) => setCapabilities(data))
            .catch(console.error);
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
                headers: { "Content-Type": "application/json" },
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
            <main className="min-h-screen flex">
                <div className="animated-bg" />

                {/* Sidebar */}
                <aside className="w-72 glass-card border-r border-[--border] p-6 hidden lg:block">
                    <Link href="/" className="flex items-center gap-2 mb-8 hover:opacity-80 transition-opacity">
                        <span>←</span>
                        <span className="font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                            OmniDev
                        </span>
                    </Link>

                    <div className="mb-8">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>🛠️</span> DevOps Agent
                        </h3>
                        {capabilities && (
                            <div className="space-y-3 text-sm">
                                <div className="flex items-center gap-2">
                                    <span className={`status-badge ${capabilities.ai_enabled ? 'success' : 'warning'}`}>
                                        AI: {capabilities.ai_enabled ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`status-badge ${capabilities.aws_configured ? 'success' : 'warning'}`}>
                                        AWS: {capabilities.aws_configured ? 'Connected' : 'Not configured'}
                                    </span>
                                </div>
                                <p className="text-gray-400">Region: {capabilities.region}</p>
                            </div>
                        )}

                        <button
                            onClick={() => setShowAwsGuide(true)}
                            className="mt-4 w-full py-2 px-3 rounded-lg border border-violet-500/30 text-violet-400 text-sm hover:bg-violet-500/10 hover:border-violet-500 transition-all flex items-center justify-center gap-2"
                        >
                            <span>🔑</span> Get AWS API Keys
                        </button>
                        <AWSGuideModal isOpen={showAwsGuide} onClose={() => setShowAwsGuide(false)} />
                    </div>

                    <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-3">Capabilities</h4>
                        <div className="space-y-4">
                            {capabilities?.capabilities.map((cap) => (
                                <div key={cap.category}>
                                    <h5 className="text-sm font-medium text-violet-400 mb-1">{cap.category}</h5>
                                    <ul className="text-xs text-gray-500 space-y-1">
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
                    <header className="glass-card border-b border-[--border] lg:hidden">
                        <div className="px-6 py-4 flex items-center justify-between">
                            <Link href="/" className="flex items-center gap-2">
                                <span>←</span>
                                <span className="font-bold text-violet-400">Back</span>
                            </Link>
                            <span className="font-semibold">🛠️ DevOps Agent</span>
                        </div>
                    </header>

                    {/* Terminal */}
                    <div className="flex-1 p-6 flex flex-col">
                        <div className="terminal flex-1 flex flex-col">
                            <div className="terminal-header">
                                <div className="terminal-dot bg-red-500"></div>
                                <div className="terminal-dot bg-yellow-500"></div>
                                <div className="terminal-dot bg-green-500"></div>
                                <span className="text-sm text-gray-400 ml-2">DevOps Agent Terminal</span>
                            </div>

                            <div className="terminal-body flex-1 overflow-y-auto">
                                {messages.length === 0 ? (
                                    <div className="text-center py-10">
                                        <div className="text-5xl mb-4">🤖</div>
                                        <h2 className="text-xl font-bold mb-2">Smart DevOps Agent</h2>
                                        <p className="text-gray-400 text-sm max-w-md mx-auto mb-6">
                                            I&apos;m your AI-powered cloud assistant. Ask me to manage your EC2 instances,
                                            S3 buckets, check costs, or troubleshoot issues.
                                        </p>
                                        <div className="flex flex-wrap gap-2 justify-center">
                                            {quickCommands.map((cmd) => (
                                                <button
                                                    key={cmd}
                                                    onClick={() => setInput(cmd)}
                                                    className="px-3 py-1.5 rounded-lg text-xs border border-[--border] text-gray-400 hover:border-cyan-500 hover:text-cyan-400 transition-all"
                                                >
                                                    {cmd}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {messages.map((message) => (
                                            <div key={message.id}>
                                                {message.role === "user" ? (
                                                    <div className="flex items-start gap-2">
                                                        <span className="text-cyan-400">$</span>
                                                        <span className="text-white">{message.content}</span>
                                                    </div>
                                                ) : (
                                                    <div className="pl-4 border-l-2 border-violet-500/30">
                                                        <div className="text-gray-300 whitespace-pre-wrap">{message.content}</div>
                                                        <div className="text-xs text-gray-500 mt-1">
                                                            {message.timestamp.toLocaleTimeString()}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}

                                        {isLoading && (
                                            <div className="flex items-center gap-2 text-gray-400">
                                                <div className="spinner" />
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
                                <div className="flex-1 flex items-center gap-2 bg-[--card] border border-[--border] rounded-xl px-4">
                                    <span className="text-cyan-400">$</span>
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
                                    className="glow-button text-white px-6 disabled:opacity-50 disabled:cursor-not-allowed"
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
