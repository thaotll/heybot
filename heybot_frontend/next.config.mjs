/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/security-analysis/:path*',
        destination: 'http://localhost:8000/security-analysis/:path*',
      },
    ]
  },
}

export default nextConfig
