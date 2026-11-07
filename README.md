# Inventory Management System

Multi-warehouse inventory management with a public product catalog.

- **Staff** add products and record income, outcome, transfers and stock-taking per warehouse.
- **Admins** also manage employees and see an audit log of who changed what, and when.
- **Customers** browse the catalog with prices, photos and live stock per warehouse. They don't need an account.

## Tech stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
- **Database:** PostgreSQL 16
- **Frontend:** Vue 3 + Quasar 2 (admin app and SSR catalog site)
- **Deployment:** Docker Compose, nginx

## Structure

```
backend/     FastAPI REST API
admin-app/   Quasar app for employees
shop-site/   Quasar SSR public catalog
```

## Security

Passwords are stored as hashes. Access tokens are short-lived JWTs, and refresh tokens are rotated and kept in httpOnly cookies. Roles are checked on the backend. The audit log is append-only. Uploaded images are validated, and security headers are set.

## Checks

```bash
pip install -r backend/requirements-dev.txt   # ruff and ty
bash scripts/check.sh                         # ruff, ty and the frontend linters (--fix, --security)
```

The same checks run in GitHub Actions on every push and pull request.

## Status

Early development. See [ROADMAP.md](ROADMAP.md).

The code is generated step by step from the prompts in [docs/deepseek-prompts.md](docs/deepseek-prompts.md) (in Russian).
