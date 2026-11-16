import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: { proxyTimeout: 200000 },
  outputFileTracingRoot: process.cwd(),
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [{ source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` }];
  },
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
