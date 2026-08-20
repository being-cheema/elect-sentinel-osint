#!/usr/bin/env bash
# ==============================================================================
# ELECT-SENTINEL OSINT Platform - Launcher Script
# ==============================================================================

set -e

PORT=${PORT:-8000}
HOST=${HOST:-"0.0.0.0"}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================================"
echo "🛡️  ELECT-SENTINEL OSINT: Starting Election Intelligence Platform..."
echo "======================================================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install fastapi uvicorn pydantic jinja2 requests feedparser python-multipart networkx scikit-learn
fi

echo "Starting FastAPI Server on http://localhost:$PORT ..."
exec ./venv/bin/uvicorn backend.server:app --host "$HOST" --port "$PORT" --reload
