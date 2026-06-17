import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle so the production Docker image only
  // needs the standalone output plus static assets.
  output: "standalone",

  // Baseline security headers for every response served by the Next.js server.
  // (The backend sets its own headers for API responses.) The CSP allows TMDB
  // images and connections to the configured API origin.
  async headers() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const csp = [
      "default-src 'self'",
      "img-src 'self' https://image.tmdb.org data:",
      // Next.js injects small inline runtime scripts/styles.
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "font-src 'self' data:",
      `connect-src 'self' ${apiOrigin}`,
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; ");
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
