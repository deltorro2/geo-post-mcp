#!/usr/bin/env bash
# Run the geo-post-mcp server over HTTP

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# HTTP server settings
MCP_HOST="${MCP_HOST:-0.0.0.0}"
MCP_PORT="${MCP_PORT:-8005}"

# Settings file (can be overridden via env var)
SETTINGS_FILE="${SETTINGS_FILE:-${SCRIPT_DIR}/geo-post-mcp-settings.json}"

# Python interpreter. `python` may be a zsh alias that does not exist in this
# bash script's PATH; prefer a project venv, then python3, then python.
if [ -n "${PYTHON:-}" ]; then
    :
elif [ -x "${SCRIPT_DIR}/.venv/bin/python" ]; then
    PYTHON="${SCRIPT_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "ERROR: no python interpreter found (set PYTHON=/path/to/python)" >&2
    exit 1
fi

# Database password. The app reads POSTGISMCPPASS; PGPASSWORD is kept for psql.
export POSTGISMCPPASS="${POSTGISMCPPASS:-${PGPASSWORD:-}}"
export PGPASSWORD="${PGPASSWORD:-${POSTGISMCPPASS:-}}"

cd "$SCRIPT_DIR"

echo "Starting geo-post-mcp on http://${MCP_HOST}:${MCP_PORT}/mcp/ (interpreter: ${PYTHON})" >&2
echo "Logs go to the 'log_file' in ${SETTINGS_FILE} (set log_file to \"\" for console)." >&2

PYTHONPATH="$SCRIPT_DIR" "$PYTHON" -c "
from src.server import mcp
mcp.run(transport='http', host='${MCP_HOST}', port=${MCP_PORT})
" --sett "$SETTINGS_FILE"
