import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/health",
        destination: "http://localhost:8000/health",
      },
      {
        source: "/analytics/:path*",
        destination: "http://localhost:8000/analytics/:path*",
      },
      {
        source: "/monitoring/:path*",
        destination: "http://localhost:8000/monitoring/:path*",
      },
    ];
  },
};

export default nextConfig;
