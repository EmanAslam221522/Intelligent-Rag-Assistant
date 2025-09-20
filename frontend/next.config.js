/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  swcMinify: false,
  trailingSlash: false,
  experimental: {
    esmExternals: false,
    forceSwcTransforms: false,
  },
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      }
    }
    return config
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
