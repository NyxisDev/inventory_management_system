# syntax=docker/dockerfile:1
# Backend image (FastAPI). Kept in deploy/ so the backend folder stays code only.
# Build context is ./backend (see docker-compose.yml).
# Expects: backend/requirements.txt, backend/alembic.ini, backend/app/main.py with "app".
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /app/media && chown -R app:app /app/media

USER app
EXPOSE 8000

# Migrations first, then the API with 2 workers. The backend is reachable only
# through nginx on the internal network, so forwarded headers from it are trusted.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips='*'"]
