#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
npm ci --prefix frontend
VITE_API_URL="${VITE_API_URL-}" npm run build --prefix frontend

python -m py_compile backend/app.py backend/wsgi.py
