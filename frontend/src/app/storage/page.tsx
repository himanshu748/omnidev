"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { AuthGuard } from "../components/AuthGuard";
import { buildAuthHeaders } from "../lib/api";

interface Bucket {
    name: string;
    created: string;
}

interface S3Object {
    key: string;
    size: number;
    last_modified: string;
}

export default function StoragePage() {
    const [buckets, setBuckets] = useState<Bucket[]>([]);
    const [selectedBucket, setSelectedBucket] = useState<string | null>(null);
    const [objects, setObjects] = useState<S3Object[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        fetchBuckets();
    }, []);

    const fetchBuckets = async () => {
        try {
            const res = await fetch("/api/storage/buckets", {
                headers: await buildAuthHeaders(),
            });
            const data = await res.json();
            setBuckets(data.buckets || []);
        } catch {
            console.error("Failed to fetch buckets");
        } finally {
            setLoading(false);
        }
    };

    const fetchObjects = async (bucketName: string) => {
        setSelectedBucket(bucketName);
        setLoading(true);
        try {
            const res = await fetch(`/api/storage/buckets/${bucketName}/objects`, {
                headers: await buildAuthHeaders(),
            });
            const data = await res.json();
            setObjects(data.objects || []);
        } catch {
            console.error("Failed to fetch objects");
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !selectedBucket) return;

        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);
        formData.append("bucket_name", selectedBucket);

        try {
            await fetch("/api/storage/upload", {
                method: "POST",
                headers: await buildAuthHeaders(),
                body: formData,
            });
            fetchObjects(selectedBucket);
        } catch {
            console.error("Upload failed");
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const handleDelete = async (key: string) => {
        if (!selectedBucket || !confirm(`Delete ${key}?`)) return;

        try {
            await fetch(`/api/storage/delete/${selectedBucket}/${key}`, {
                method: "DELETE",
                headers: await buildAuthHeaders(),
            });
            fetchObjects(selectedBucket);
        } catch {
            console.error("Delete failed");
        }
    };

    const handleDownload = async (key: string) => {
        if (!selectedBucket) return;
        try {
            const res = await fetch(`/api/storage/download/${selectedBucket}/${key}`, {
                headers: await buildAuthHeaders(),
            });
            if (!res.ok) {
                return;
            }
            const blob = await res.blob();
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = blobUrl;
            link.download = key.split("/").pop() || key;
            link.click();
            URL.revokeObjectURL(blobUrl);
        } catch {
            console.error("Download failed");
        }
    };

    const formatSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <AuthGuard>
            <main className="min-h-screen">
                <div className="animated-bg" />

                <header className="glass-card border-b border-[--border] sticky top-0 z-50">
                    <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                            <span className="text-xl">←</span>
                            <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">
                                OmniDev
                            </span>
                        </Link>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl">📦</span>
                            <span className="font-semibold">Cloud Storage</span>
                        </div>
                    </div>
                </header>

                <div className="max-w-6xl mx-auto px-6 py-8">
                    <div className="grid lg:grid-cols-3 gap-6">
                        {/* Buckets List */}
                        <div className="glass-card p-6">
                            <h2 className="text-lg font-semibold mb-4">S3 Buckets</h2>
                            {loading && !selectedBucket ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="spinner" />
                                </div>
                            ) : buckets.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <p>No buckets found</p>
                                    <p className="text-xs mt-2">Configure AWS credentials</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {buckets.map((bucket) => (
                                        <button
                                            key={bucket.name}
                                            onClick={() => fetchObjects(bucket.name)}
                                            className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${selectedBucket === bucket.name
                                                ? "border-violet-500 bg-violet-500/10"
                                                : "border-[--border] hover:border-violet-500/50"
                                                }`}
                                        >
                                            <div className="font-medium">{bucket.name}</div>
                                            <div className="text-xs text-gray-500 mt-1">
                                                Created: {new Date(bucket.created).toLocaleDateString()}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Objects List */}
                        <div className="lg:col-span-2 glass-card p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">
                                    {selectedBucket ? `Files in ${selectedBucket}` : "Select a Bucket"}
                                </h2>
                                {selectedBucket && (
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={uploading}
                                        className="glow-button text-white px-4 py-2 text-sm disabled:opacity-50"
                                    >
                                        {uploading ? "Uploading..." : "Upload File"}
                                    </button>
                                )}
                            </div>

                            <input
                                ref={fileInputRef}
                                type="file"
                                onChange={handleUpload}
                                className="hidden"
                            />

                            {!selectedBucket ? (
                                <div className="text-center py-12 text-gray-500">
                                    <div className="text-5xl mb-4">📂</div>
                                    <p>Select a bucket to view files</p>
                                </div>
                            ) : loading ? (
                                <div className="flex items-center justify-center py-12">
                                    <div className="spinner" />
                                </div>
                            ) : objects.length === 0 ? (
                                <div className="text-center py-12 text-gray-500">
                                    <p>No files in this bucket</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {objects.map((obj) => (
                                        <div
                                            key={obj.key}
                                            className="flex items-center justify-between px-4 py-3 rounded-xl border border-[--border] hover:border-violet-500/30 transition-all"
                                        >
                                            <div className="flex items-center gap-3">
                                                <span className="text-xl">📄</span>
                                                <div>
                                                    <div className="font-medium">{obj.key}</div>
                                                    <div className="text-xs text-gray-500">
                                                        {formatSize(obj.size)} • {new Date(obj.last_modified).toLocaleString()}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => handleDownload(obj.key)}
                                                    className="px-3 py-1 rounded-lg text-sm border border-[--border] hover:border-cyan-500 hover:text-cyan-400 transition-all"
                                                >
                                                    Download
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(obj.key)}
                                                    className="px-3 py-1 rounded-lg text-sm border border-[--border] hover:border-red-500 hover:text-red-400 transition-all"
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </AuthGuard>
    );
}
