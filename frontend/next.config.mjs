/** @type {import('next').NextConfig} */

// The backend exposes no CORS headers, so the browser cannot call it directly
// cross-origin. Instead we proxy same-origin `/api/*` and `/health` requests
// through the Next server to the backend. Target is configurable; the default
// works inside docker-compose (service name `backend`).
const API_PROXY_TARGET = process.env.API_PROXY_TARGET || "http://backend:8000";

const nextConfig = {
  reactStrictMode: true,
  // Allow team crest images served from the football data provider.
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "crests.football-data.org" },
    ],
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API_PROXY_TARGET}/api/:path*` },
      { source: "/health", destination: `${API_PROXY_TARGET}/health` },
    ];
  },
};

export default nextConfig;
