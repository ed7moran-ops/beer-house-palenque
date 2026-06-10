#!/usr/bin/env bash
set -euo pipefail

: "${APP_URL:?Set APP_URL, for example https://beer-house-palenque.onrender.com}"
: "${ADMIN_USERNAME:=admin}"
: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD for the production admin account}"
BACKUP_DIR="${BACKUP_DIR:-./production-backups}"
mkdir -p "$BACKUP_DIR"

LOGIN_JSON=$(curl -fsS -X POST "$APP_URL/api/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}")
TOKEN=$(python -c 'import json,sys; print(json.load(sys.stdin)["token"])' <<< "$LOGIN_JSON")
CREATE_JSON=$(curl -fsS -X POST "$APP_URL/api/backups" -H "Authorization: Bearer $TOKEN")
FILENAME=$(python -c 'import json,sys; print(json.load(sys.stdin)["filename"])' <<< "$CREATE_JSON")
curl -fsS "$APP_URL/api/backups/$FILENAME?token=$TOKEN" -o "$BACKUP_DIR/$FILENAME"
printf 'Backup saved to %s\n' "$BACKUP_DIR/$FILENAME"
