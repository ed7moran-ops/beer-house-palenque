#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export FLASK_ENV="${FLASK_ENV:-production}"
export APP_ENV="${APP_ENV:-production}"
export DB_PATH="${DB_PATH:-$ROOT_DIR/data/beer_house.db}"
export UPLOAD_FOLDER="${UPLOAD_FOLDER:-$ROOT_DIR/data/uploads}"
export BACKUP_FOLDER="${BACKUP_FOLDER:-$ROOT_DIR/data/backups}"
export FRONTEND_DIST="${FRONTEND_DIST:-$ROOT_DIR/frontend/dist}"

mkdir -p "$(dirname "$DB_PATH")" "$UPLOAD_FOLDER" "$BACKUP_FOLDER"

exec gunicorn --chdir backend --bind "0.0.0.0:${PORT:-5000}" --workers "${WEB_CONCURRENCY:-1}" --timeout "${GUNICORN_TIMEOUT:-120}" wsgi:app
