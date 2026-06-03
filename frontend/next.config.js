/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // If deployed via Docker Compose, backend is available at http://backend:8000
        // During local dev outside docker, you might use localhost
        destination: process.env.NODE_ENV === 'production' 
          ? "http://backend:8000/:path*" 
          : "http://localhost:8000/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
