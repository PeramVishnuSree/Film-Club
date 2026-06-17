# syntax=docker/dockerfile:1

# ---- deps: install node_modules from a clean lockfile ----
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- builder: produce the standalone Next.js output ----
FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Baked into the client bundle at build time; override per-environment.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---- runner: minimal production image ----
FROM node:20-slim AS runner
WORKDIR /app
# Don't hardcode PORT: the standalone server reads $PORT at runtime (Render and
# other platforms inject it) and defaults to 3000 locally when unset.
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# The node base image already ships a non-root `node` user (UID 1000); reuse it
# rather than creating another user at the same UID (which collides).
USER node

# The standalone bundle includes a minimal server + traced node_modules.
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
