#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Bootstrap script for **CodexMCP**
# ---------------------------------------------------------------------------
#
# 1. Installs Node 18 via *nvm* (if available) or *fnm* fallback.
# 2. Fetches the OpenAI *Codex CLI* via **npm**.
# 3. Sets‑up a dedicated Python *virtual‑environment* using *venv* and installs
#    the required Python dependencies listed in *requirements.txt*.
# 4. Verifies that the OPENAI_API_KEY environment variable is exported.
#
# The script is idempotent – running it multiple times will not overwrite an
# existing virtual‑environment or duplicate global installations.
# ---------------------------------------------------------------------------

set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

info()  { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Node 18 + Codex CLI
# ---------------------------------------------------------------------------

if ! command -v node >/dev/null 2>&1; then
  info "Node not found – installing Node 18 via nvm …"

  if command -v nvm >/dev/null 2>&1; then
    nvm install 18
    nvm use 18
  elif command -v fnm >/dev/null 2>&1; then
    fnm install 18
    fnm use 18
  else
    error "Neither *nvm* nor *fnm* found – cannot install Node"
  fi
fi

# Update npm and grab Codex CLI.
if ! command -v codex >/dev/null 2>&1; then
  info "Installing OpenAI Codex CLI (global) …"
  npm i -g openai/codex/codex-cli
fi

# ---------------------------------------------------------------------------
# Python virtual‑environment
# ---------------------------------------------------------------------------

VENV_DIR="$HERE/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
  info "Creating Python virtual‑environment …"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r "$HERE/requirements.txt"

# ---------------------------------------------------------------------------
# Sanity‑check
# ---------------------------------------------------------------------------

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  error "OPENAI_API_KEY environment variable is *not* set – the Codex CLI will refuse to run"
fi

info "Setup complete – activate the virtual‑environment with: source $VENV_DIR/bin/activate"
