"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, Check, ExternalLink } from "lucide-react";
import { useState } from "react";

interface AWSGuideModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AWSGuideModal({ isOpen, onClose }: AWSGuideModalProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-[#1a1b26] border border-violet-500/30 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl shadow-violet-500/10"
                >
                    <div className="sticky top-0 bg-[#1a1b26]/95 backdrop-blur-md p-6 border-b border-violet-500/20 flex justify-between items-center">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                            How to Get AWS Access Keys
                        </h2>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="p-6 space-y-8">
                        {/* Step 1 */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold border border-violet-500/30">
                                    1
                                </div>
                                <h3 className="font-semibold text-lg">Log in to AWS Console</h3>
                            </div>
                            <div className="pl-11 text-gray-400">
                                <p className="mb-2">Go to the AWS Management Console and sign in.</p>
                                <a
                                    href="https://console.aws.amazon.com/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 text-sm"
                                >
                                    Open AWS Console <ExternalLink size={14} />
                                </a>
                            </div>
                        </div>

                        {/* Step 2 */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold border border-violet-500/30">
                                    2
                                </div>
                                <h3 className="font-semibold text-lg">Navigate to IAM (Identity and Access Management)</h3>
                            </div>
                            <div className="pl-11 text-gray-400">
                            <p>Search for <strong>&quot;IAM&quot;</strong> in the top search bar and select it.</p>
                            </div>
                        </div>

                        {/* Step 3 */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold border border-violet-500/30">
                                    3
                                </div>
                                <h3 className="font-semibold text-lg">Create a User</h3>
                            </div>
                            <div className="pl-11 text-gray-400 space-y-2">
                                <p>1. In the left navigation pane, choose <strong>Users</strong>.</p>
                                <p>2. Click <strong>Create user</strong>.</p>
                                <p>3. Enter a user name (e.g., <code>OmniDev-Agent</code>) and click Next.</p>
                            </div>
                        </div>

                        {/* Step 4 */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold border border-violet-500/30">
                                    4
                                </div>
                                <h3 className="font-semibold text-lg">Set Permissions</h3>
                            </div>
                            <div className="pl-11 text-gray-400 space-y-2">
                                <p>1. Select <strong>Attach policies directly</strong>.</p>
                                <p>2. Search for and select <strong>AdministratorAccess</strong> (easiest for testing) or specific permissions like <code>AmazonEC2FullAccess</code> and <code>AmazonS3FullAccess</code>.</p>
                                <p>3. Click <strong>Next</strong>, then <strong>Create user</strong>.</p>
                                <div className="bg-yellow-500/10 border border-yellow-500/20 p-3 rounded-lg text-sm text-yellow-200 mt-2">
                                    ⚠️ <strong>Note:</strong> AdministratorAccess grants full control. For production, apply least privilege permissions.
                                </div>
                            </div>
                        </div>

                        {/* Step 5 */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold border border-violet-500/30">
                                    5
                                </div>
                                <h3 className="font-semibold text-lg">Create Access Keys</h3>
                            </div>
                            <div className="pl-11 text-gray-400 space-y-2">
                                <p>1. Click on the newly created user name.</p>
                                <p>2. Go to the <strong>Security credentials</strong> tab.</p>
                                <p>3. Scroll down to <strong>Access keys</strong> and click <strong>Create access key</strong>.</p>
                                <p>4. Select <strong>Command Line Interface (CLI)</strong>, accept the confirmation, and click Next.</p>
                                <p>5. Click <strong>Create access key</strong>.</p>
                            </div>
                        </div>

                        {/* Step 6 */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold border border-violet-500/30">
                                    6
                                </div>
                                <h3 className="font-semibold text-lg">Copy Your Keys</h3>
                            </div>
                            <div className="pl-11 text-gray-400 space-y-4">
                                <p>You will see your <strong>Access Key ID</strong> and <strong>Secret Access Key</strong>. Copy them immediately as you won&apos;t be able to see the Secret Key again.</p>

                                <div className="p-4 bg-black/40 rounded-lg border border-white/10 space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-xs uppercase tracking-wider text-gray-500">Add to .env or Settings</span>
                                        <button
                                            onClick={() => handleCopy("AWS_ACCESS_KEY_ID=your_key\nAWS_SECRET_ACCESS_KEY=your_secret\nAWS_DEFAULT_REGION=ap-south-1")}
                                            className="text-xs flex items-center gap-1 text-violet-400 hover:text-violet-300"
                                        >
                                            {copied ? <Check size={12} /> : <Copy size={12} />}
                                            {copied ? "Copied!" : "Copy Template"}
                                        </button>
                                    </div>
                                    <pre className="text-sm font-mono text-cyan-300 overflow-x-auto">
                                        AWS_ACCESS_KEY_ID=AKIA...
                                        AWS_SECRET_ACCESS_KEY=wJalr...
                                        AWS_DEFAULT_REGION=ap-south-1
                                    </pre>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="sticky bottom-0 bg-[#1a1b26] p-6 border-t border-white/10 flex justify-end">
                        <button
                            onClick={onClose}
                            className="px-6 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            Close Guide
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
