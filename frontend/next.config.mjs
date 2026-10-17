/** @type {import('next').NextConfig} */
// The browser calls /api/* on this site; Next.js forwards it to the FastAPI service.
// One origin for the user = no CORS setup needed on Render.
const API_ORIGIN = (process.env.API_ORIGIN ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

const nextConfig = {
  reactStrictMode: true,
  // Render's free backend sleeps when idle and takes ~50 s to wake; wait for it.
  experimental: { proxyTimeout: 90_000 },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${API_ORIGIN}/api/:path*` }];
  },
};
export default nextConfig;
