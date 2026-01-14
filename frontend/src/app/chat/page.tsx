"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { MarkdownRenderer } from "../components/MarkdownRenderer";
import { useSettings } from "../hooks/useSettings";

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

            const response = await fetch("http://localhost:8000/api/ai/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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
        <main className="min-h-screen flex flex-col bg-[#050505]">
            <div className="animated-bg" />

            {/* Header */}
            <header className="glass-card border-b border-[#39ff14]/10 sticky top-0 z-50 backdrop-blur-xl bg-black/40">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <span className="text-xl">←</span>
                        <span className="text-xl font-bold text-[#39ff14]">
                            OmniDev
                        </span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">💬</span>
                        <span className="font-semibold text-white">AI Chat</span>
                        <span className="ml-2 px-2 py-1 rounded-full text-xs bg-[#39ff14]/20 text-[#39ff14] border border-[#39ff14]/30">
                            GPT-5 Nano
                        </span>
                    </div>
                </div>
            </header>

            {/* Chat Container */}
            <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6 flex flex-col">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                    <AnimatePresence>
                        {messages.length === 0 ? (
                            <motion.div
                                className="text-center py-20"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5 }}
                            >
                                <div className="text-6xl mb-4">🤖</div>
                                <h2 className="text-2xl font-bold mb-2 text-[#39ff14]">GPT-5 Nano AI Chat</h2>
                                <p className="text-gray-400 max-w-md mx-auto">
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
                                            className="px-4 py-2 rounded-full text-sm border border-[#39ff14]/30 text-gray-400 hover:border-[#39ff14] hover:text-[#39ff14] transition-all"
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
                                    <div className={`chat-bubble ${message.role}`}>
                                        {message.role === "assistant" ? (
                                            <MarkdownRenderer content={message.content} />
                                        ) : (
                                            <div className="whitespace-pre-wrap">{message.content}</div>
                                        )}
                                        <div className={`text-xs mt-2 ${message.role === "user" ? "text-[#39ff14]/70" : "text-gray-500"}`}>
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
                            <div className="chat-bubble assistant">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input Form */}
                <motion.form
                    onSubmit={sendMessage}
                    className="glass-card p-4 border border-[#39ff14]/20 rounded-2xl bg-[#0a0a0f]"
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
                            className="flex-1 bg-[#050505] border border-[#39ff14]/20 rounded-xl px-4 py-3 focus:outline-none focus:border-[#39ff14] transition-colors text-white placeholder-gray-500"
                            disabled={isLoading}
                        />
                        <motion.button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="px-6 py-3 rounded-xl bg-[#39ff14] text-black font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            {isLoading ? <div className="spinner" /> : "Send"}
                        </motion.button>
                    </div>
                </motion.form>
            </div>
        </main>
    );
}
