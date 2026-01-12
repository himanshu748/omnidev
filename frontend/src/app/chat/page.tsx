"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

export default function ChatPage() {
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
        <main className="min-h-screen flex flex-col">
            <div className="animated-bg" />

            {/* Header */}
            <header className="glass-card border-b border-[--border] sticky top-0 z-50">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <span className="text-xl">←</span>
                        <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                            TechTrainingPro
                        </span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">💬</span>
                        <span className="font-semibold">AI Chat</span>
                    </div>
                </div>
            </header>

            {/* Chat Container */}
            <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6 flex flex-col">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                    {messages.length === 0 ? (
                        <div className="text-center py-20">
                            <div className="text-6xl mb-4">🤖</div>
                            <h2 className="text-2xl font-bold mb-2">GPT-4o AI Chat</h2>
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
                                    <button
                                        key={suggestion}
                                        onClick={() => setInput(suggestion)}
                                        className="px-4 py-2 rounded-full text-sm border border-[--border] text-gray-400 hover:border-violet-500 hover:text-violet-400 transition-all"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div className={`chat-bubble ${message.role}`}>
                                    <div className="whitespace-pre-wrap">{message.content}</div>
                                    <div className={`text-xs mt-2 ${message.role === "user" ? "text-violet-200" : "text-gray-500"}`}>
                                        {message.timestamp.toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}

                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="chat-bubble assistant">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input Form */}
                <form onSubmit={sendMessage} className="glass-card p-4">
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 bg-[--card] border border-[--border] rounded-xl px-4 py-3 focus:outline-none focus:border-violet-500 transition-colors"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="glow-button text-white px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? <div className="spinner" /> : "Send"}
                        </button>
                    </div>
                </form>
            </div>
        </main>
    );
}
