"use client";

import { useState, useRef, useEffect } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  model?: string;
};

export default function RAGPage() {
  const [ingestText, setIngestText] = useState("");
  const [ingestLoading, setIngestLoading] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<{ chunks_added: number; total_chunks: number } | null>(null);
  const [fileResult, setFileResult] = useState<{ chunks_added: number; total_chunks: number } | null>(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(5);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    if (!ingestText.trim() || ingestLoading) return;
    setIngestLoading(true);
    setError(null);
    setIngestResult(null);
    setFileResult(null);
    try {
      const res = await fetch(api("/api/rag/ingest"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: ingestText.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
      setIngestResult(data);
      setIngestText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed");
    } finally {
      setIngestLoading(false);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || fileLoading) return;
    setFileLoading(true);
    setError(null);
    setIngestResult(null);
    setFileResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(api("/api/rag/ingest/file"), {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
      setFileResult(data);
      e.target.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setFileLoading(false);
    }
  }

  async function handleChat(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim() || loading) return;
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: message.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setMessage("");
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(api("/api/rag/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.content, top_k: topK }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply,
          sources: data.sources_used,
          model: data.model,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Request failed"}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <FeatureLayout
      title="RAG Chatbot"
      description="Add documents (paste text or upload PDF/TXT), then ask questions. Answers are based only on your documents—no guessing from outside knowledge."
      icon="💬"
      endpoints={[
        { method: "POST", path: "/api/rag/ingest" },
        { method: "POST", path: "/api/rag/ingest/file" },
        { method: "POST", path: "/api/rag/chat" },
      ]}
    >
      {/* Ingest */}
      <div className="featureCard">
        <div className="cardHeader">
          <h2>
            <span className="cardIcon">📄</span>
            Add documents
          </h2>
        </div>
        <p className="featureCardSubtitle">
          Add documents so you can ask questions about them. Paste text or upload a PDF or text file.
        </p>

        <div className="featureForm">
          <div>
            <label htmlFor="rag-file">Upload document (PDF or TXT)</label>
            <input
              id="rag-file"
              type="file"
              accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
              onChange={handleFileUpload}
              disabled={fileLoading}
            />
            {fileResult && (
              <p style={{ fontSize: "0.85rem", color: "var(--emerald)", marginTop: 8 }}>
                Added {fileResult.chunks_added} chunk(s). Total: {fileResult.total_chunks}.
              </p>
            )}
          </div>

          <div className="ragIngestDivider">or paste text</div>

          <form onSubmit={handleIngest}>
            <div>
              <label htmlFor="rag-ingest">Paste document text</label>
              <textarea
                id="rag-ingest"
                value={ingestText}
                onChange={(e) => setIngestText(e.target.value)}
                placeholder="Paste paragraphs or long text from a document..."
                rows={4}
              />
            </div>
            <button type="submit" className="featureBtn featureBtnPrimary" disabled={ingestLoading || !ingestText.trim()}>
              {ingestLoading ? <span className="loadingDot">Adding</span> : "Add to knowledge base"}
            </button>
            {ingestResult && (
              <p style={{ fontSize: "0.85rem", color: "var(--emerald)", marginTop: 8 }}>
                Added {ingestResult.chunks_added} chunk(s). Total: {ingestResult.total_chunks}.
              </p>
            )}
          </form>
        </div>
      </div>

      {/* Chat */}
      <div className="featureCard">
        <div className="cardHeader">
          <h2>
            <span className="cardIcon">💬</span>
            Chat
          </h2>
        </div>
        <p className="featureCardSubtitle">
          Ask questions about your documents. Answers are based only on what you added above.
        </p>

        <div className="ragChatWrap">
          <div className="ragMessages">
            {messages.length === 0 && !loading && (
              <div className="emptyState">
                <div className="emptyIcon">💬</div>
                <p>Add documents above, then ask questions about them here.</p>
              </div>
            )}
            {messages.map((m) => (
              <div key={m.id} className={`ragMessage ${m.role}`}>
                <div className="ragMessageRole">{m.role === "user" ? "You" : "Assistant"}</div>
                <div className="ragMessageContent">{m.content}</div>
                {m.sources && m.sources.length > 0 && (
                  <details className="ragSources">
                    <summary>Sources ({m.sources.length})</summary>
                    <pre>{m.sources.slice(0, 3).map((s, i) => `${i + 1}. ${s.slice(0, 120)}${s.length > 120 ? "…" : ""}`).join("\n\n")}</pre>
                  </details>
                )}
                {m.model && <span className="ragModel">{m.model}</span>}
              </div>
            ))}
            {loading && (
              <div className="ragMessage assistant">
                <div className="ragMessageRole">Assistant</div>
                <div className="ragMessageContent loadingDot">Thinking…</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="ragForm" onSubmit={handleChat}>
            {error && (
              <div className="featureResult featureError" style={{ marginBottom: 12 }}>
                {error}
              </div>
            )}
            <div className="ragInputRow">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask a question..."
                className="ragInput"
                disabled={loading}
              />
              <button type="submit" className="featureBtn featureBtnPrimary" disabled={loading || !message.trim()}>
                Send
              </button>
            </div>
            <label className="ragTopK">
              Retrieve top{" "}
              <select value={topK} onChange={(e) => setTopK(Number(e.target.value))}>
                {[3, 5, 10, 15, 20].map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>{" "}
              chunks
            </label>
          </form>
        </div>
      </div>
    </FeatureLayout>
  );
}
