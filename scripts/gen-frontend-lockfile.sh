#!/usr/bin/env sh
# Run from repo root on any machine with Docker (generates frontend/package-lock.json).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm \
  -v "$ROOT/frontend:/app" \
  -w /app \
  node:20-bookworm-slim \
  bash -lc "npm install --package-lock-only --no-audit --no-fund && ls -la package-lock.json"
echo "Created $ROOT/frontend/package-lock.json — commit it for reproducible Docker builds."
