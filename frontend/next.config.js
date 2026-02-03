/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use standalone for Docker; Vercel uses its own serverless build
  ...(process.env.VERCEL ? {} : { output: "standalone" }),
  async rewrites() {
    // Only proxy to external API if NEXT_PUBLIC_API_URL is set
    // Otherwise, use Next.js API routes (serverless functions)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (apiUrl) {
      return [
        {
          source: "/api/v1/:path*",
          destination: `${apiUrl}/api/v1/:path*`,
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
