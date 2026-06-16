import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle so the production Docker image only
  // needs the standalone output plus static assets.
  output: "standalone",
};

export default nextConfig;
