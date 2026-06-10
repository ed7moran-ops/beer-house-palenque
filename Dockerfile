FROM node:20.19-bookworm-slim AS frontend-build
WORKDIR /app
COPY frontend/package*.json frontend/
RUN npm ci --prefix frontend
COPY frontend frontend
RUN VITE_API_URL="" npm run build --prefix frontend

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    FLASK_ENV=production \
    DB_PATH=/app/data/beer_house.db \
    UPLOAD_FOLDER=/app/data/uploads \
    BACKUP_FOLDER=/app/data/backups \
    FRONTEND_DIST=/app/frontend/dist \
    WEB_CONCURRENCY=1 \
    PORT=5000
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY scripts scripts
COPY --from=frontend-build /app/frontend/dist frontend/dist
RUN python -m py_compile backend/app.py backend/wsgi.py \
    && mkdir -p /app/data/uploads /app/data/backups

EXPOSE 5000
CMD ["./scripts/start_production.sh"]
