#!/usr/bin/env bash
# Restore the database (and optionally photos) from backups/.
# Usage: bash scripts/restore.sh backups/db_<stamp>.dump [backups/media_<stamp>.tar.gz]
# WARNING: replaces the current data. Make a fresh backup first.
set -euo pipefail
cd "$(dirname "$0")/.."

DB_DUMP="${1:-}"
MEDIA_ARCHIVE="${2:-}"

if [ -z "$DB_DUMP" ] || [ ! -f "$DB_DUMP" ]; then
  echo "Usage: bash scripts/restore.sh backups/db_<stamp>.dump [backups/media_<stamp>.tar.gz]"
  exit 2
fi
if [ -n "$MEDIA_ARCHIVE" ] && [ ! -f "$MEDIA_ARCHIVE" ]; then
  echo "Media archive not found: $MEDIA_ARCHIVE"
  exit 2
fi

read -r -p "This replaces the current database. Type 'restore' to continue: " answer
if [ "$answer" != "restore" ]; then
  echo "Cancelled."
  exit 1
fi

echo "Stopping the API so nothing writes during the restore..."
docker compose stop backend

echo "Restoring the database from $DB_DUMP ..."
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --role=app_owner' \
  < "$DB_DUMP"

if [ -n "$MEDIA_ARCHIVE" ]; then
  echo "Restoring photos from $MEDIA_ARCHIVE ..."
  docker compose run --rm --no-deps -T --entrypoint sh backend \
    -c 'find /app/media -mindepth 1 -delete && tar -xzf - -C /app' < "$MEDIA_ARCHIVE"
fi

docker compose start backend
echo "Restore finished."
