#!/usr/bin/env bash
# Minimal installation script for *CodexMCP*.

set -euo pipefail

NODE_SETUP_URL="https://deb.nodesource.com/setup_18.x"

if ! command -v node >/dev/null 2>&1; then
  echo "Installing Node 18 LTS …"
  curl -fsSL "$NODE_SETUP_URL" | sudo -E bash -
  sudo apt-get install -y nodejs
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "Installing Codex CLI …"
  npm i -g @openai/codex
fi

if ! python3.10 - <<PY 2>/dev/null; then echo "Python 3.10 not found – please install."; exit 1; fi
PY

python3.10 -m venv .venv
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install fastmcp python-dotenv rich

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: Please set OPENAI_API_KEY before running the server." >&2
  exit 1
fi

echo "Environment ready."
