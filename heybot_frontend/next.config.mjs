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
        destination: 'http://localhost:8080/security-analysis/:path*',
      },
      {
        source: '/deepseek-message/:path*',
        destination: 'http://localhost:8080/deepseek-message/:path*',
      },
      {
        source: '/api/commits',
        destination: 'http://localhost:8080/security-analysis/latest',
      },
    ]
  },
}

export default nextConfig
