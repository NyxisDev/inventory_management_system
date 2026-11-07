# Roadmap

- [x] **Database:** PostgreSQL schema, SQLAlchemy models, Alembic migrations, seed admin
- [x] **Backend API:** auth with roles, employees, categories, warehouses, products, photos, stock operations, public API
- [x] **Audit log:** record every employee action with old and new values, viewer and CSV export
- [ ] **Admin app:** Quasar UI for products, stock, employees and the audit log
  - [x] Connected to the API: sign-in with refresh rotation, roles, products, photos, stock operations, movements, directories, employees, audit log
  - [ ] Server-side pagination and URL filters in tables (lists are loaded whole for now), rich-text description editor
- [ ] **Catalog site:** Quasar SSR with categories, search, filters and stock per warehouse
  - [x] All pages, design, SEO (meta, JSON-LD, sitemap, robots, real 404), CSP with nonce; runs on demo data (`MOCK_API=true`)
  - [x] Language switcher and Slovak translation of every page (`?lang=`, cookie, Accept-Language; hreflang and sitemap alternates)
  - [x] Check against the real public API (`docs/public-api.md`): publish a product, see it on the site (SSR), unpublish hides it
- [ ] **Deployment:** Docker Compose, nginx, HTTPS, backups
  - [x] Compose files, Dockerfiles, nginx, Caddy (HTTPS), `.env.example`, backup/restore, Makefile, README
  - [ ] Run on a machine with Docker once the backend and admin app exist; `down`/`up` keeps data
- [ ] **Security audit:** OWASP review, security tests, dependency checks

## Later

- [ ] Slovak interface for the admin app; Ukrainian for both apps
- [ ] Barcode scanning
- [ ] CSV import/export
- [ ] Low-stock notifications
