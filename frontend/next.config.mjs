/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    const publicApiUrl = process.env.NEXT_PUBLIC_API_URL || '/api'
    if (/^https?:\/\//i.test(publicApiUrl)) {
      return []
    }

    const target = (process.env.INTERNAL_API_URL || 'http://localhost:8000').replace(/\/$/, '')
    return [
      {
        source: '/api/:path*',
        destination: `${target}/:path*`,
      },
    ]
  },
}

export default nextConfig
