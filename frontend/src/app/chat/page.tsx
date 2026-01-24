"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { MarkdownRenderer } from "../components/MarkdownRenderer";
import { AuthGuard } from "../components/AuthGuard";
import { useSettings } from "../hooks/useSettings";
import { buildAuthHeaders } from "../lib/api";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

export default function ChatPage() {
    const { settings } = useSettings();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async (e: React.FormEvent) => {
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
            const history = messages.map((m) => ({
                role: m.role,
                content: m.content,
            }));

            const response = await fetch("/api/ai/chat", {
                method: "POST",
                headers: {
                    ...(await buildAuthHeaders()),
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: userMessage.content,
                    history,
                    api_key: settings.openaiApiKey || undefined,
                }),
            });

            const data = await response.json();

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: data.response,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "❌ Failed to connect to the backend. Make sure the server is running on http://localhost:8000",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <AuthGuard>
            <main className="min-h-screen bg-[#f5f5f0] text-[#0a0a0a]">
                <div className="fixed inset-0 grid-pattern pointer-events-none" />

                {/* Header */}
                <header className="sticky top-0 z-50 bg-[#f5f5f0]/90 backdrop-blur-md border-b border-[#d4d4c8]">
                    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                            <div className="w-8 h-8 bg-[#0a0a0a] rounded-lg flex items-center justify-center">
                                <span className="text-[#f5f5f0] font-bold text-sm">O</span>
                            </div>
                            <span className="font-semibold text-lg tracking-tight">OmniDev</span>
                        </Link>
                        <div className="flex items-center gap-2">
                            <span className="text-xl">💬</span>
                            <span className="font-semibold">AI Chat</span>
                            <span className="app-badge font-mono">GPT-5 Mini</span>
                        </div>
                    </div>
                </header>

                {/* Chat Container */}
                <div className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-6 flex flex-col">
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                        <AnimatePresence>
                            {messages.length === 0 ? (
                                <motion.div
                                    className="text-center py-16"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.5 }}
                                >
                                    <div className="text-6xl mb-5">🤖</div>
                                    <h2 className="text-2xl sm:text-3xl font-display mb-3">Chat with GPT‑5 Mini</h2>
                                    <p className="text-[#666] max-w-md mx-auto leading-relaxed">
                                        Start a conversation! I can help with coding, cloud computing,
                                        technical questions, and more.
                                    </p>
                                    <div className="flex flex-wrap gap-2 justify-center mt-6">
                                        {[
                                            "Explain Docker containers",
                                            "Write a Python function",
                                            "What is AWS Lambda?",
                                            "Help me with React hooks",
                                        ].map((suggestion) => (
                                            <motion.button
                                                key={suggestion}
                                                onClick={() => setInput(suggestion)}
                                                className="px-4 py-2 rounded-full text-sm border border-[#d4d4c8] text-[#666] hover:border-[#0a0a0a] hover:text-[#0a0a0a] transition-all bg-white"
                                                whileHover={{ scale: 1.05 }}
                                                whileTap={{ scale: 0.95 }}
                                            >
                                                {suggestion}
                                            </motion.button>
                                        ))}
                                    </div>
                                </motion.div>
                            ) : (
                                messages.map((message) => (
                                    <motion.div
                                        key={message.id}
                                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.3 }}
                                    >
                                        <div
                                            className={[
                                                "max-w-[85%] rounded-2xl px-4 py-3 border shadow-sm",
                                                message.role === "user"
                                                    ? "bg-[#0a0a0a] text-[#f5f5f0] border-[#0a0a0a]"
                                                    : "bg-white text-[#0a0a0a] border-[#d4d4c8]",
                                            ].join(" ")}
                                        >
                                            {message.role === "assistant" ? (
                                                <MarkdownRenderer content={message.content} />
                                            ) : (
                                                <div className="whitespace-pre-wrap">{message.content}</div>
                                            )}
                                            <div className={`text-xs mt-2 ${message.role === "user" ? "text-[#f5f5f0]/70" : "text-[#999]"}`}>
                                                {message.timestamp.toLocaleTimeString()}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))
                            )}
                        </AnimatePresence>

                        {isLoading && (
                            <motion.div
                                className="flex justify-start"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                            >
                                <div className="bg-white border border-[#d4d4c8] rounded-2xl px-4 py-3 shadow-sm">
                                    <div className="text-sm text-[#666]">Thinking…</div>
                                </div>
                            </motion.div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Form */}
                    <motion.form
                        onSubmit={sendMessage}
                        className="app-panel p-4"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <div className="flex gap-3">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Type your message..."
                                className="app-input flex-1"
                                disabled={isLoading}
                            />
                            <motion.button
                                type="submit"
                                disabled={isLoading || !input.trim()}
                                className="px-6 py-3 rounded-xl bg-[#0a0a0a] text-[#f5f5f0] font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {isLoading ? "Sending..." : "Send"}
                            </motion.button>
                        </div>
                    </motion.form>
                </div>
            </main>
        </AuthGuard>
    );
}
