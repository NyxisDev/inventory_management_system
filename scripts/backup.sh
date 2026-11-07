#!/usr/bin/env bash
# Backup: database dump + media archive into backups/, keeps the last 14 days.
# Run from anywhere: bash scripts/backup.sh
# Daily at 03:00 (crontab -e):
#   0 3 * * * cd /opt/inventory && bash scripts/backup.sh >> backups/backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."

KEEP_DAYS=14
STAMP="$(date +%Y-%m-%d_%H%M%S)"
mkdir -p backups
chmod 700 backups

echo "[$(date -Is)] backup ${STAMP} started"

# Custom format (-Fc): compressed, restorable with pg_restore.
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "backups/db_${STAMP}.dump"

docker compose exec -T backend tar -czf - -C /app media \
  > "backups/media_${STAMP}.tar.gz"

chmod 600 "backups/db_${STAMP}.dump" "backups/media_${STAMP}.tar.gz"

# Remove backups older than KEEP_DAYS days.
find backups -maxdepth 1 -type f \( -name 'db_*.dump' -o -name 'media_*.tar.gz' \) -mtime +"${KEEP_DAYS}" -delete

echo "[$(date -Is)] backup ${STAMP} done: backups/db_${STAMP}.dump, backups/media_${STAMP}.tar.gz"
