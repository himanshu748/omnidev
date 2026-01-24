import type { NextConfig } from "next";

const DEFAULT_LOCAL_BACKEND = "http://localhost:8000";
const DEFAULT_PROD_BACKEND = "https://omnidev-qbiv.onrender.com";

function getBackendBaseUrl() {
  // Prefer explicit override (works in both local + Vercel).
  const fromEnv = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL;
  const raw = fromEnv || (process.env.VERCEL ? DEFAULT_PROD_BACKEND : DEFAULT_LOCAL_BACKEND);
  return raw.replace(/\/+$/, "");
}

const nextConfig: NextConfig = {
  reactCompiler: true,
  async rewrites() {
    const backend = getBackendBaseUrl();
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backend}/health`,
      },
      {
        source: "/analytics/:path*",
        destination: `${backend}/analytics/:path*`,
      },
      {
        source: "/monitoring/:path*",
        destination: `${backend}/monitoring/:path*`,
      },
    ];
  },
};

export default nextConfig;
