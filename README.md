# Inventory Management System

Multi-warehouse inventory management with a public product catalog.

- **Staff** add products and record income, outcome, transfers and stock-taking per warehouse.
- **Admins** also manage employees and see an audit log of who changed what, and when.
- **Customers** browse the catalog with prices, photos and live stock per warehouse. They don't need an account.

## Tech stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
- **Database:** PostgreSQL 16
- **Frontend:** Vue 3 + Quasar 2 (admin app and SSR catalog site), Node.js 24
- **Deployment:** Docker Compose, nginx, Caddy for HTTPS

## Structure

```
backend/                FastAPI REST API
admin-app/              Quasar app for employees
shop-site/              Quasar SSR public catalog
nginx/                  entry point config (templates + snippets)
deploy/                 Dockerfiles for backend and admin app, Caddyfile
scripts/                checks, backup and restore
docker-compose.yml      db, backend, admin-app, shop-site, nginx
docker-compose.https.yml  production add-on: HTTPS with Let's Encrypt (Caddy)
docker-compose.demo.yml   catalog only, on demo data
docker-compose.dev.yml    development: publishes the database on localhost
docs/public-api.md      the public API the catalog reads
```

## Quick look: the catalog on demo data

Needs only Node.js 24 (or Docker). No database, no backend.

```bash
cd shop-site
npm ci
npm run dev        # http://localhost:9100
```

With Docker instead: `make demo` and open http://localhost:8080.

Without `API_URL` the catalog runs on built-in demo products (`MOCK_API=true`). All products, prices, stock and addresses in it are made up.

## Run everything with Docker

Needs Docker with Compose v2 and `make` (on Windows use the `docker compose` commands from the `Makefile`).

```bash
cp .env.example .env    # then change every value marked MUST BE CHANGED
make up                 # build and start
make seed               # create the first admin from ADMIN_USERNAME / ADMIN_PASSWORD
```

- Catalog: http://localhost:8080
- Admin app: http://localhost:8081

Data lives in the Docker volumes `pgdata` and `media`, so `make down` and `make up` keep products and photos. The database port is never published.

## Development without Docker

Only the database runs in Docker; the apps run with hot reload.

The backend reads the root `.env` and then `backend/.env`, which overrides it for running on the host: copy `backend/.env.example` to `backend/.env` and put the `APP_USER_PASSWORD` / `APP_OWNER_PASSWORD` values into its URLs (host `localhost` instead of `db`).

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db   # PostgreSQL on 127.0.0.1:5432
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt   # Linux/macOS: .venv/bin/
.venv/Scripts/alembic upgrade head           # migrations, as app_owner
.venv/Scripts/python -m app.seed             # first admin, warehouse, 2 categories (safe to repeat)
uvicorn app.main:app --reload                # http://localhost:8000
cd admin-app && npm run dev                  # proxies /api to :8000
cd shop-site && API_URL=http://localhost:8000 MOCK_API=false npm run dev
```

The catalog dev server (port 9100) forwards `/api` and `/media` to `API_URL`.

## Deploy on a VPS (Ubuntu 24.04)

1. Install Docker: `curl -fsSL https://get.docker.com | sh`, then add your user to the `docker` group.
2. Point two DNS A records to the server, for example `shop.example.com` and `admin.example.com`.
3. Open only ports 22, 80 and 443: `ufw allow OpenSSH && ufw allow 80,443/tcp && ufw enable`.
4. Clone the project to `/opt/inventory`, create `.env` from `.env.example`, set strong secrets, the domains, `ACME_EMAIL`, `SITE_URL=https://shop.example.com`, `CORS_ORIGINS` with both HTTPS addresses and `COOKIE_SECURE=true`. Keep `BIND_ADDRESS=127.0.0.1`.
5. Start with HTTPS: `make https`. Caddy gets Let's Encrypt certificates, renews them and redirects HTTP to HTTPS.
6. Create the first admin: `make seed`.
7. Schedule backups (see below).

Update to a new version:

```bash
git pull
make https     # rebuilds the images; the backend applies migrations on start
```

## Backups

`make backup` writes `backups/db_<date>.dump` and `backups/media_<date>.tar.gz` and deletes backups older than 14 days. Daily at 03:00:

```bash
crontab -e
0 3 * * * cd /opt/inventory && bash scripts/backup.sh >> backups/backup.log 2>&1
```

Restore (replaces the current data, asks for confirmation):

```bash
make restore DB=backups/db_2026-11-07_030000.dump MEDIA=backups/media_2026-11-07_030000.tar.gz
```

Copy `backups/` to another machine as well; a backup on the same disk does not survive a disk failure.

## Security

Passwords are stored as hashes. Access tokens are short-lived JWTs, and refresh tokens are rotated and kept in httpOnly cookies. Roles are checked on the backend. The audit log is append-only. Uploaded images are validated. nginx and the catalog send security headers (CSP with a per-request nonce on the catalog, `X-Frame-Options`, `nosniff`, HSTS through Caddy); the admin app is hidden from search engines. All containers run as non-root users.

## Checks

```bash
pip install -r backend/requirements-dev.txt   # ruff and ty
bash scripts/check.sh                         # ruff, ty and the frontend linters (--fix, --security)
```

The same checks run in GitHub Actions on every push and pull request.

## Status

Early development. See [ROADMAP.md](ROADMAP.md).

The code is generated step by step from the prompts in [docs/deepseek-prompts.md](docs/deepseek-prompts.md) (in Russian).
