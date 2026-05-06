"use client";

import { useState, useRef } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type VisionResult = {
  mode: string;
  result: string;
  model: string;
  tokens_used: number | null;
};

export default function VisionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [mode, setMode] = useState<"analyze" | "ocr" | "custom">("analyze");
  const [customPrompt, setCustomPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(f);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setElapsed(null);
    setLoading(true);
    const start = Date.now();
    try {
      const form = new FormData();
      form.append("image", file);
      form.append("mode", mode);
      if (mode === "custom" && customPrompt.trim()) {
        form.append("prompt", customPrompt.trim());
      }
      const res = await fetch(api("/api/vision/analyze"), {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      setElapsed(Date.now() - start);
      if (!res.ok) {
        setError(data.detail ?? `HTTP ${res.status}`);
        return;
      }
      setResult(data);
    } catch (err) {
      setElapsed(Date.now() - start);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <FeatureLayout
      title="Vision Lab"
      description="Analyze images, extract text via OCR, or ask custom questions — powered by AI Vision."
      icon="🖼️"
      endpoints={[{ method: "POST", path: "/api/vision/analyze" }]}
    >
      <div className="featureCard">
        <h2>
          <span className="cardIcon">📸</span>
          Upload &amp; Analyze
        </h2>
        <p className="featureCardSubtitle">
          Upload any image to get a detailed AI analysis, OCR text extraction, or answer custom questions about the image.
        </p>

        <form className="featureForm" onSubmit={handleSubmit}>
          {/* Upload area */}
          <div>
            <label htmlFor="vision-file">Image File</label>
            {!preview ? (
              <div
                style={{
                  border: "2px dashed var(--border)",
                  borderRadius: "var(--radius-xs)",
                  padding: "40px 24px",
                  textAlign: "center",
                  cursor: "pointer",
                  background: "rgba(6, 9, 15, 0.4)",
                  transition: "all 0.2s",
                }}
                onClick={() => fileRef.current?.click()}
              >
                <div style={{ fontSize: "2rem", marginBottom: 8, opacity: 0.5 }}>📁</div>
                <div style={{ color: "var(--text-dim)", fontSize: "0.9rem" }}>
                  Click to upload an image or drag & drop
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 4 }}>
                  PNG, JPG, GIF, WEBP supported
                </div>
              </div>
            ) : (
              <div style={{ position: "relative", borderRadius: "var(--radius-xs)", overflow: "hidden", border: "1px solid var(--border)" }}>
                <img
                  src={preview}
                  alt="Preview"
                  style={{ width: "100%", maxHeight: 300, objectFit: "contain", background: "rgba(0,0,0,0.3)" }}
                />
                <button
                  type="button"
                  onClick={() => { setFile(null); setPreview(null); setResult(null); }}
                  style={{
                    position: "absolute",
                    top: 8,
                    right: 8,
                    padding: "4px 12px",
                    borderRadius: 6,
                    border: "none",
                    background: "rgba(0,0,0,0.6)",
                    color: "#fff",
                    fontSize: "0.82rem",
                    cursor: "pointer",
                  }}
                >
                  ✕ Remove
                </button>
              </div>
            )}
            <input
              id="vision-file"
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              style={{ display: "none" }}
            />
          </div>

          {/* Mode selection */}
          <div>
            <label>Analysis Mode</label>
            <div className="modePills">
              {([
                { key: "analyze", label: "🔍 Analyze", desc: "Detailed description" },
                { key: "ocr", label: "📝 OCR", desc: "Extract text" },
                { key: "custom", label: "💬 Custom", desc: "Ask a question" },
              ] as const).map((m) => (
                <button
                  key={m.key}
                  type="button"
                  className={`modePill ${mode === m.key ? "active" : ""}`}
                  onClick={() => setMode(m.key)}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom prompt */}
          {mode === "custom" && (
            <div>
              <label htmlFor="vision-prompt">Custom Prompt</label>
              <textarea
                id="vision-prompt"
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="What objects are in this image? What colors do you see?"
                rows={3}
              />
            </div>
          )}

          <button
            type="submit"
            className="featureBtn featureBtnPrimary"
            disabled={loading || !file}
          >
            {loading ? (
              <span className="loadingDot">Analyzing</span>
            ) : (
              "🔮 Analyze Image"
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="featureResult featureError">
          <strong>⚠ Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="featureResult featureSuccess">
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <div className="resultRow" style={{ padding: "4px 0", border: "none" }}>
                <span className="resultLabel">Mode</span>
                <span className="resultValue" style={{ textTransform: "capitalize", color: "var(--accent)" }}>
                  {result.mode}
                </span>
              </div>
              <div className="resultRow" style={{ padding: "4px 0", border: "none" }}>
                <span className="resultLabel">Model</span>
                <span className="resultValue" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.82rem" }}>
                  {result.model}
                </span>
              </div>
              {result.tokens_used && (
                <div className="resultRow" style={{ padding: "4px 0", border: "none" }}>
                  <span className="resultLabel">Tokens</span>
                  <span className="resultValue">{result.tokens_used.toLocaleString()}</span>
                </div>
              )}
            </div>
            {elapsed != null && (
              <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                ⏱ {(elapsed / 1000).toFixed(1)}s
              </span>
            )}
          </div>
          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.75, color: "var(--text-dim)", borderTop: "1px solid rgba(42, 62, 102, 0.2)", paddingTop: 14 }}>
            {result.result}
          </div>
        </div>
      )}
    </FeatureLayout>
  );
}
