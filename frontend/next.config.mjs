/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow team crest images served from the football data provider.
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "crests.football-data.org" },
    ],
  },
};

export default nextConfig;
