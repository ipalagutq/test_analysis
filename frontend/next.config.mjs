const isDev = process.env.NODE_ENV !== "production";

/** @type {import('next').NextConfig} */
const nextConfig = isDev
  ? {
      // dev only: the backend runs separately on :8000; the static export is served by FastAPI itself
      async rewrites() {
        return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
      },
    }
  : {
      output: "export",
      // emits review/index.html, which FastAPI StaticFiles(html=True) serves at /review/
      trailingSlash: true,
      images: { unoptimized: true },
    };

export default nextConfig;
