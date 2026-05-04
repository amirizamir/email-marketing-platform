#!/usr/bin/env bash
# Used only during `docker build`. Retries registries if npm hits ETIMEDOUT / network errors.
set -u

attempt() {
  local reg="$1"
  echo ""
  echo ">>> Trying npm registry: ${reg}"
  npm config set registry "${reg}"

  if [ -f package-lock.json ]; then
    if npm ci --no-audit --no-fund; then
      return 0
    fi
    echo ">>> npm ci failed (lock may not match this mirror); trying npm install..."
  fi

  npm install --no-audit --no-fund
}

# Optional first choice from docker build-arg (see docker-compose NPM_REGISTRY)
if [ -n "${NPM_REGISTRY_OVERRIDE:-}" ]; then
  attempt "${NPM_REGISTRY_OVERRIDE}" && exit 0
fi

attempt "https://registry.npmjs.org" && exit 0
attempt "https://registry.npmmirror.com" && exit 0
attempt "https://registry.npmjs.org/" && exit 0

echo "ERROR: All npm registry attempts failed."
exit 1
