"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import FeatureLayout from "../components/FeatureLayout";
import { api } from "@/lib/api";

type BucketInfo = { name: string; creation_date: string | null };
type FileInfo = { key: string; size: number; last_modified: string | null; storage_class: string };

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatDate(d: string | null): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function fileExtIcon(key: string): string {
  const ext = key.split(".").pop()?.toLowerCase() || "";
  if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext)) return "🖼️";
  if (["mp4", "mov", "avi", "mkv"].includes(ext)) return "🎬";
  if (["pdf"].includes(ext)) return "📄";
  if (["zip", "tar", "gz"].includes(ext)) return "📦";
  if (["json", "xml", "csv"].includes(ext)) return "📊";
  if (["js", "ts", "py", "rb"].includes(ext)) return "💻";
  return "📄";
}

export default function StoragePage() {
  const [buckets, setBuckets] = useState<BucketInfo[]>([]);
  const [selectedBucket, setSelectedBucket] = useState<string>("");
  const [prefix, setPrefix] = useState("");
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loadingBuckets, setLoadingBuckets] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Upload
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadBucket, setUploadBucket] = useState<string>("");
  const [uploadKey, setUploadKey] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Download
  const [downloadLinks, setDownloadLinks] = useState<Record<string, string>>({});

  const clearMsg = () => { setError(null); setMessage(null); };

  const loadBuckets = useCallback(async () => {
    clearMsg();
    setLoadingBuckets(true);
    try {
      const res = await fetch(api("/api/storage/buckets"));
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Failed to load buckets"); return; }
      setBuckets(data.buckets ?? []);
      if (!selectedBucket && data.buckets?.length) {
        setSelectedBucket(data.buckets[0].name);
        setUploadBucket(data.buckets[0].name);
      }
    } catch { setError("Failed to connect to backend"); }
    finally { setLoadingBuckets(false); }
  }, [selectedBucket]);

  const loadFiles = useCallback(async (bucket: string) => {
    if (!bucket) return;
    clearMsg();
    setLoadingFiles(true);
    try {
      const url = api(`/api/storage/files/${bucket}`) + (prefix ? `?prefix=${encodeURIComponent(prefix)}` : "");
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Failed to load files"); return; }
      setFiles(data.files ?? []);
    } catch { setError("Failed to load files"); }
    finally { setLoadingFiles(false); }
  }, [prefix]);

  useEffect(() => { loadBuckets(); }, []);
  useEffect(() => { if (selectedBucket) loadFiles(selectedBucket); }, [selectedBucket]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile) return;
    const bucket = uploadBucket || selectedBucket;
    const key = uploadKey || uploadFile.name;
    if (!bucket) { setError("No bucket selected"); return; }
    clearMsg();
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", uploadFile);
      form.append("bucket", bucket);
      form.append("key", key);
      const res = await fetch(api("/api/storage/upload"), { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Upload failed"); return; }
      setMessage(`✅ Uploaded ${key} to ${bucket}`);
      setUploadFile(null);
      setUploadKey("");
      if (fileRef.current) fileRef.current.value = "";
      if (bucket === selectedBucket) loadFiles(bucket);
    } catch { setError("Upload failed"); }
    finally { setUploading(false); }
  }

  async function handleDownload(bucket: string, key: string) {
    clearMsg();
    try {
      const res = await fetch(api(`/api/storage/download/${bucket}/${key}`));
      const data = await res.json();
      if (!res.ok) { setError(data.detail ?? "Download failed"); return; }
      setDownloadLinks(prev => ({ ...prev, [`${bucket}/${key}`]: data.download_url }));
    } catch { setError("Failed to generate download link"); }
  }

  async function handleDelete(bucket: string, key: string) {
    if (!confirm(`Delete ${key} from ${bucket}?`)) return;
    clearMsg();
    try {
      const res = await fetch(api(`/api/storage/delete/${bucket}/${key}`), { method: "DELETE" });
      if (!res.ok) { const d = await res.json(); setError(d.detail ?? "Delete failed"); return; }
      setMessage(`🗑️ Deleted ${key}`);
      if (bucket === selectedBucket) loadFiles(bucket);
    } catch { setError("Delete failed"); }
  }

  return (
    <FeatureLayout
      title="Cloud Storage"
      description="Browse, upload, download, and delete files in your S3 buckets with a beautiful file manager."
      icon="📦"
      endpoints={[
        { method: "GET", path: "/api/storage/buckets" },
        { method: "GET", path: "/api/storage/files/{bucket}" },
        { method: "POST", path: "/api/storage/upload" },
        { method: "DELETE", path: "/api/storage/delete/{bucket}/{key}" },
      ]}
    >
      {error && <div className="featureResult featureError" style={{ marginBottom: 16 }}><strong>⚠</strong> {error}</div>}
      {message && <div className="featureResult featureSuccess" style={{ marginBottom: 16 }}>{message}</div>}

      {/* Bucket selector */}
      <div className="featureCard">
        <h2>
          <span className="cardIcon">🪣</span>
          Buckets
        </h2>
        <p className="featureCardSubtitle">Select a bucket to browse its contents, or refresh the list.</p>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <select
            className="featureForm"
            value={selectedBucket}
            onChange={(e) => { setSelectedBucket(e.target.value); setUploadBucket(e.target.value); setFiles([]); }}
            style={{
              flex: 1,
              minWidth: 200,
              padding: "10px 14px",
              borderRadius: "var(--radius-xs)",
              border: "1px solid var(--border)",
              background: "rgba(6, 9, 15, 0.6)",
              color: "var(--text)",
              fontSize: "0.92rem",
            }}
          >
            {buckets.length === 0 && <option value="">No buckets found</option>}
            {buckets.map(b => (
              <option key={b.name} value={b.name}>{b.name}</option>
            ))}
          </select>
          <button className="featureBtn featureBtnSecondary" onClick={() => loadBuckets()} disabled={loadingBuckets}>
            {loadingBuckets ? "Loading…" : "🔄 Refresh"}
          </button>
        </div>

        {buckets.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
            {buckets.map(b => (
              <span key={b.name} style={{
                padding: "4px 12px",
                borderRadius: 999,
                fontSize: "0.8rem",
                border: `1px solid ${b.name === selectedBucket ? "var(--accent)" : "var(--border)"}`,
                background: b.name === selectedBucket ? "var(--accent-soft)" : "transparent",
                color: b.name === selectedBucket ? "var(--accent)" : "var(--text-muted)",
                cursor: "pointer",
              }}
                onClick={() => { setSelectedBucket(b.name); setUploadBucket(b.name); setFiles([]); }}
              >
                🪣 {b.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* File browser */}
      {selectedBucket && (
        <div className="featureCard">
          <h2>
            <span className="cardIcon">📂</span>
            Files in <span style={{ color: "var(--accent)", fontFamily: "'JetBrains Mono', monospace" }}>{selectedBucket}</span>
          </h2>
          <div className="featureCardSubtitle" style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 14 }}>
            <input
              type="text"
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              placeholder="Filter by prefix..."
              style={{
                padding: "8px 12px",
                borderRadius: "var(--radius-xs)",
                border: "1px solid var(--border)",
                background: "rgba(6, 9, 15, 0.6)",
                color: "var(--text)",
                fontSize: "0.85rem",
                flex: 1,
              }}
            />
            <button className="featureBtn featureBtnSecondary" onClick={() => loadFiles(selectedBucket)} disabled={loadingFiles} style={{ padding: "8px 14px", fontSize: "0.85rem" }}>
              {loadingFiles ? "…" : "🔍 Filter"}
            </button>
          </div>

          {loadingFiles ? (
            <div className="emptyState"><p className="featureLoading">Loading files…</p></div>
          ) : files.length === 0 ? (
            <div className="emptyState">
              <div className="emptyIcon">📭</div>
              <p>No files found{prefix ? ` with prefix "${prefix}"` : ""}.</p>
            </div>
          ) : (
            <ul className="fileList">
              {files.map((f) => {
                const dlKey = `${selectedBucket}/${f.key}`;
                return (
                  <li key={f.key} className="fileItem">
                    <div className="fileIcon">{fileExtIcon(f.key)}</div>
                    <div className="fileName">{f.key}</div>
                    <div className="fileMeta">{formatBytes(f.size)}</div>
                    <div className="fileMeta">{formatDate(f.last_modified)}</div>
                    <div className="fileActions">
                      {downloadLinks[dlKey] ? (
                        <a href={downloadLinks[dlKey]} target="_blank" rel="noopener noreferrer" className="featureBtn featureBtnSecondary" style={{ padding: "6px 12px", fontSize: "0.78rem" }}>
                          ⬇ Open
                        </a>
                      ) : (
                        <button className="featureBtn featureBtnSecondary" onClick={() => handleDownload(selectedBucket, f.key)} style={{ padding: "6px 12px", fontSize: "0.78rem" }}>
                          🔗 Link
                        </button>
                      )}
                      <button className="featureBtn featureBtnDanger" onClick={() => handleDelete(selectedBucket, f.key)} style={{ padding: "6px 12px", fontSize: "0.78rem" }}>
                        🗑️
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}

      {/* Upload */}
      <div className="featureCard">
        <h2>
          <span className="cardIcon">⬆️</span>
          Upload File
        </h2>
        <p className="featureCardSubtitle">Upload a file to any S3 bucket with a custom key.</p>

        <form className="featureForm" onSubmit={handleUpload}>
          <div className="formGrid">
            <div>
              <label htmlFor="upload-bucket">Target Bucket</label>
              <select
                id="upload-bucket"
                value={uploadBucket || selectedBucket}
                onChange={(e) => setUploadBucket(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  borderRadius: "var(--radius-xs)",
                  border: "1px solid var(--border)",
                  background: "rgba(6, 9, 15, 0.6)",
                  color: "var(--text)",
                  fontSize: "0.92rem",
                }}
              >
                {buckets.map((b) => (
                  <option key={b.name} value={b.name}>{b.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="upload-key">Key (path)</label>
              <input
                id="upload-key"
                type="text"
                value={uploadKey}
                onChange={(e) => setUploadKey(e.target.value)}
                placeholder="path/to/file.txt"
              />
            </div>
          </div>

          <div>
            <label htmlFor="upload-file">File</label>
            <input
              id="upload-file"
              ref={fileRef}
              type="file"
              onChange={(e) => {
                const f = e.target.files?.[0];
                setUploadFile(f ?? null);
                if (f && !uploadKey) setUploadKey(f.name);
              }}
            />
          </div>

          <button
            type="submit"
            className="featureBtn featureBtnPrimary"
            disabled={uploading || !uploadFile}
          >
            {uploading ? (
              <span className="loadingDot">Uploading</span>
            ) : (
              "📤 Upload File"
            )}
          </button>
        </form>
      </div>
    </FeatureLayout>
  );
}
