# syntax=docker/dockerfile:1.4
#
# Fixes common cloud build failures: ETIMEDOUT to registry.npmjs.org
# 1) docker-install-deps.sh — retries official npm + npmmirror
# 2) Optional: set NPM_REGISTRY in .env for your region / corp mirror
# (Avoid RUN --network=host: Docker Desktop / many CI builders disallow the
#  network.host BuildKit entitlement unless explicitly enabled.)
#
# Requires BuildKit: DOCKER_BUILDKIT=1 (default on modern Docker)

ARG NEXT_PUBLIC_API_URL=

FROM node:20-bookworm-slim AS deps
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json* .npmrc ./
COPY docker-install-deps.sh /tmp/docker-install-deps.sh
RUN chmod +x /tmp/docker-install-deps.sh

# Build-arg passed into the script (empty = skip)
ARG NPM_REGISTRY
ENV NPM_REGISTRY_OVERRIDE=${NPM_REGISTRY}

RUN --mount=type=cache,target=/root/.npm,id=npm-cache \
    /tmp/docker-install-deps.sh

FROM node:20-bookworm-slim AS builder
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM node:20-bookworm-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
