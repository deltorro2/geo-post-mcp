#!/usr/bin/env bash
# Run the geo-post-mcp server over HTTP

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# HTTP server settings
MCP_HOST="${MCP_HOST:-0.0.0.0}"
MCP_PORT="${MCP_PORT:-8005}"

# Settings file (can be overridden via env var)
SETTINGS_FILE="${SETTINGS_FILE:-${SCRIPT_DIR}/geo-post-mcp-settings.json}"

# Database password (read from env, never hardcoded)
export PGPASSWORD="${PGPASSWORD:-}"

cd "$SCRIPT_DIR"

PYTHONPATH="$SCRIPT_DIR" python -c "
from src.server import mcp
mcp.run(transport='http', host='${MCP_HOST}', port=${MCP_PORT})
" --sett "$SETTINGS_FILE"
