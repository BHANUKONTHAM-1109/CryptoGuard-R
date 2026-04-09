#!/bin/bash
# CryptoGuard-R - Startup Script
# Run from project root: ./run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load .env if exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run FastAPI with uvicorn
cd backend
uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --reload
