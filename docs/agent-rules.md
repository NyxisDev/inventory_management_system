# Agent rules: detailed reference

Detailed rules moved out of `AGENTS.md` so that they are not loaded in every session. Read only the section you need: find it with Grep `^## ` and open it with Read (offset and limit). The Russian prompts in `docs/deepseek-prompts.md` stay the source of truth; if they disagree with this file, ask the user.

## Security (required in every task)

If convenience conflicts with security, choose security and tell the user.

**Passwords and login**
- Hash with bcrypt (cost 12) or argon2id. Minimum 10 characters, at least one letter and one digit. Never store, log or return a plain password or hash.
- Login returns the same error ("Invalid username or password") and takes about the same time whether or not the username exists. Verify a hash even when the user is missing.
- 5 failed attempts block the account for 15 minutes, per username (`failed_login_attempts`, `locked_until`) and per IP (slowapi, 429). The block message must not reveal whether the username exists.
- An inactive employee gets 403.

**Tokens**
- Access token: JWT HS256, 15 minutes, only `sub` (employee id) and `role` inside, `exp` always checked. `JWT_SECRET` is at least 32 bytes from `.env`; the app refuses to start if it is empty, short or the default.
- A token issued before `password_changed_at` is invalid. The employee must still be `is_active` on every request.
- Refresh token: `secrets.token_urlsafe(48)`. Only its SHA-256 hash is stored (`refresh_tokens`). Cookie is httpOnly, Secure, SameSite=Strict, path `/api/v1/auth`, 7 days. Rotate on every refresh. Reuse of an old token revokes all of the employee's tokens.
- `/auth/refresh` requires the header `X-Requested-With: XMLHttpRequest` (CSRF protection).
- Deactivating an employee, changing or resetting a password revokes all their refresh tokens.
- Frontend: keep the access token in memory only (Pinia), never in localStorage or sessionStorage. Admin app signs out after 30 minutes of inactivity.

**Access control and input**
- Check roles on the backend in every endpoint. The frontend only hides buttons. Check that the object exists and is accessible (IDOR).
- SQL: ORM and bound parameters only. Sort fields come from an allow-list.
- All input goes through Pydantic: string lengths, number ranges, `model_config extra='forbid'`.
- XSS: sanitize product description HTML with bleach on the backend (allow `p, br, b, strong, i, em, ul, ol, li, h3, h4, a[href]`) and DOMPurify on the frontend. `v-html` only for the product description.
- CSV export: escape cells that start with `=`, `+`, `-` or `@`.

**Files**
- Check the real image type with Pillow, re-encode (this strips EXIF and harmful content), limit pixels (`Image.MAX_IMAGE_PIXELS`).
- jpg / png / webp only, up to 5 MB each. Resize to 1600 px, save as webp, plus a 400 px thumbnail.
- File name is a uuid4. Never build a path from user input. Size limit in both nginx and the backend. Nothing in `media/` is executable.

**Infrastructure**
- nginx headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, HSTS in production.
- CORS: only the exact domains from `.env`. Never `*` together with credentials.
- Rate limit (slowapi): strict on login and refresh, about 120 requests per minute per IP on the public API.
- Production: `DEBUG` off, `/docs` and `/openapi.json` off (`ENABLE_DOCS=false`), no stack traces in responses (details only in the server log).
- Never write passwords, hashes or tokens to server logs or `audit_log`.
- The app connects to PostgreSQL as `app_user` (no superuser, no CREATE). Migrations use `app_owner`. `app_user` has only SELECT and INSERT on `audit_log`. The database port is not exposed.
- Docker containers do not run as root. `.env` is in `.gitignore`.
- `pip-audit` and `npm audit` must show no critical vulnerabilities.
- The admin app is hidden from search engines (`X-Robots-Tag: noindex` and `robots.txt`).

## Database

Schema is defined in Part 1 of the prompts and must not change without asking. Tables: `employees`, `refresh_tokens`, `categories`, `warehouses`, `products`, `product_images`, `stock`, `stock_movements`, `audit_log`.

- Extension `pg_trgm`; enums `employee_role`, `movement_type`, `audit_action`.
- `updated_at` is maintained by the `set_updated_at()` trigger.
- `audit_log` is append-only: the trigger `forbid_audit_change()` blocks UPDATE and DELETE.
- Migrations are Alembic (async template). The first migration creates everything, including triggers, via `op.execute`.
- `python -m app.seed` creates the first admin from `ADMIN_USERNAME` / `ADMIN_PASSWORD`, the "Main warehouse" warehouse and 2 categories. It must be safe to run twice.

## Backend rules

- Stock operations run in one transaction. Lock the `stock` row with `SELECT ... FOR UPDATE`; create it with 0 if missing.
- Outcome larger than the stock returns 409 "Not enough stock in this warehouse".
- Operations on an archived product or an inactive warehouse return 409. A transfer to the same warehouse is rejected.
- Deleting a product that has movements archives it (`is_archived=true`, `is_published=false`). Without movements it is deleted.
- Employees are never deleted, only deactivated. An admin cannot deactivate or demote themselves or the last active admin (409).
- Warehouses are never deleted, only deactivated.
- A category with products or subcategories cannot be deleted (409). Slugs are generated with python-slugify (Cyrillic is transliterated); add `-2`, `-3` on conflict.
- Public API returns only `is_published=true` and `is_archived=false` products, and stock only for warehouses that are `is_active` and `show_on_site`. It never returns `created_by`, `updated_by`, `min_quantity`, `is_archived` or employee ids. Send `Cache-Control: public, max-age=60`.
- `GET /api/v1/health` returns `{"status": "ok"}`.
- Tests use pytest and `httpx.AsyncClient` with a separate test database.

## Audit log rules

- `log_action` writes in the same session and transaction as the change and never commits itself. A failed action (for example a 409) leaves no record.
- `create`: `old_data` null, `new_data` the full object. `update`: only changed fields in both; no change means no record. `delete`: full object in `old_data`.
- Mask `password`, `password_hash` and tokens as `***` (`mask_sensitive`).
- Stock operations write `entity_type="stock"`, `entity_id="{product_id}:{warehouse_id}"`. A transfer writes two records.
- IP comes from `X-Forwarded-For` only when `TRUST_PROXY` is on, otherwise from `request.client.host`.
- The audit API is admin-only and read-only (no PUT / PATCH / DELETE). Each entry has `changes: [{field, old, new}]` and an English `summary`. CSV export uses UTF-8 with BOM and the `;` delimiter.

## Frontend rules

**Admin app**
- Axios with `withCredentials: true` and `X-Requested-With: XMLHttpRequest`. On 401, call `/auth/refresh` once and retry; parallel requests share one refresh. If it fails, sign out and go to `/login`.
- Route meta `requiresAuth` / `requiresAdmin` with a global guard. "Employees" and "Audit log" are visible to admins only.
- Server-side pagination and sorting in tables, search debounce 300 ms, filters kept in the URL query.
- Dangerous actions (archive, deactivate, outcome, delete photo) need confirmation.
- Validate all forms, show loading states and empty states ("No products yet").
- Format numbers with `Intl.NumberFormat`; dates as `dd.MM.yyyy HH:mm` in local time.
- Light/dark theme switch, saved. Works on desktop, tablet and phone.
- Sign-out in one tab ends the session in all tabs (BroadcastChannel).
- No secrets in the frontend (everything in `VITE_*` is public). Never print tokens to the console. Use `autocomplete="current-password"` / `"new-password"`.

**Catalog site**
- Quasar SSR so products are found by search engines; data must be present in the server HTML. Tell the user before writing code if SSR becomes too complex.
- Uses only `/api/v1/public/...`. No sign-in, cart or orders.
- All filters and the page number live in the URL query so a link can be shared.
- SEO: `useMeta` on every page, JSON-LD `schema.org/Product` on product pages, `/sitemap.xml`, `/robots.txt`, real HTTP 404.
- Sanitize product HTML with `isomorphic-dompurify` before `v-html`.
- ESLint (from Quasar) must keep `vue/no-v-html` as `error`. The single exception is the product description, with an inline `eslint-disable-next-line` and a comment saying the HTML is sanitized.
- Currency comes from the `CURRENCY` env variable (default EUR).

## Design (admin app and catalog site)

Reference: https://budmaster.netlify.app/. Take only the style. Do not copy its text, images or logo; use placeholders for photos.

- Dark theme. Page background `#0b1121`, section and panel background `#151d30`, text `#ffffff`, secondary text `#94a3b8`, borders `rgba(255,255,255,0.1)`.
- Primary colour (buttons, accents, active items, prices): orange `#ff8a00`, hover `#e57a00`. Secondary accent: blue `#2563eb` (links, info).
- Fonts from Google Fonts: Outfit 700 for headings (h1 about 3.2rem with letter-spacing -0.02em, h2 about 2.5rem, h3 1.25rem), Inter 400/500/600 for text, base size 16px.
- Buttons: radius 8px, weight 600. Primary is orange with white text and `box-shadow: 0 4px 14px rgba(255,138,0,0.3)`. Secondary is transparent with a 1px `rgba(255,255,255,0.1)` border.
- Cards: radius 16px, 1px border, no shadow. On hover: orange border and `translateY(-4px)`.
- Images and carousels have 16px radius; slide indicators are dots with an orange active one.
- Container max 1200px, header height 80px, animations `0.3s ease-in-out`, fade-up on scroll (catalog site only; the admin app has none). Respect `prefers-reduced-motion`.
- Put colours and sizes in variables (`quasar.variables.scss`: `$primary #ff8a00`, `$dark #151d30`, `$dark-page #0b1121`, `$info #2563eb`, plus CSS variables). Enable Quasar Dark mode.
- Text contrast at least WCAG AA. White text on orange buttons is bold and at least 16px.
- Admin app is calmer than the site: readable tables and forms for long work sessions.
- Catalog home page: full-screen hero with a construction photo under a 70% `#0b1121` overlay, two-line heading (second line orange), grey subtitle separated by "•", buttons "View catalog" (orange) and "Contact us" (outline). Sections alternate `#0b1121` / `#151d30`. "In stock" is a green badge, "Out of stock" is grey. Show skeletons while loading and a placeholder image for products without a photo.


## Deployment

- `docker-compose.yml`: `db` (postgres:16, volume, healthcheck, no public port), `backend` (python:3.12-slim, runs `alembic upgrade head`, then uvicorn with 2 workers, media volume), `admin-app` (node:24 build, unprivileged nginx with SPA fallback), `shop-site` (`quasar build -m ssr`, `node dist/ssr/index.js` on node:24; Quasar app-vite 3 needs Node 22.22+ or 24), `nginx` as the single entry point.
- Domains: `shop.<domain>` goes to shop-site, `admin.<domain>` to admin-app, `/api` and `/media` on both go to backend. Local run: `localhost:8080` (site) and `localhost:8081` (admin).
- nginx: `client_max_body_size 25m`, `/media` cache 7 days, gzip, HTTPS with Let's Encrypt (certbot or Caddy).
- Root `.env.example` lists every variable with a comment. `JWT_SECRET` and the DB password are marked "MUST BE CHANGED" with `openssl rand -hex 32`.
- Backups: daily `pg_dump` plus a `media` archive into `backups/`, keep 14 days, `restore.sh` to restore.
- `Makefile` (or `scripts/`): `up`, `down`, `logs`, `migrate`, `seed`, `test`, `backup`, `security-check`.
