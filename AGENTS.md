# AGENTS.md

Instructions for AI coding agents in this repository (Claude Code, Codex, Cursor, DeepSeek). This file is loaded in every session, so it stays short. Details are in separate files and are read on demand.

## Project

Multi-warehouse inventory management with a public product catalog. Staff record stock operations, admins also manage employees and see the audit log, customers browse the catalog without an account. Product context for design work: [PRODUCT.md](PRODUCT.md).

```
backend/            Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL 16
admin-app/          Vue 3 + Quasar 2 (Vite, <script setup>, Pinia, Vue Router, Axios), for employees
shop-site/          Vue 3 + Quasar 2 in SSR mode, public catalog
docker-compose.yml  postgres, backend, admin-app, shop-site, nginx
```

Do not change the stack or the database schema without the user's consent.

## Where things are (read on demand)

| Need | Where |
| --- | --- |
| Task spec per part (Russian, source of truth) | `docs/deepseek-prompts.md`. Never read it whole (~15k tokens). Find the part with Grep `^## Часть`, then Read with offset and limit. |
| Detailed rules: security, database, backend, audit log, frontend, design, deployment | `docs/agent-rules.md`. Grep `^## `, read one section. |
| Progress | `ROADMAP.md` |

Build order: parts 0 → 7 of the prompts, strictly in sequence. Each part ends with a "Проверь" line: run that check before calling the part done, then tick `ROADMAP.md`.

## Non-negotiables

- Money is `Decimal` / `NUMERIC(12,2)`, never `float`. Quantities are `NUMERIC(14,3)`.
- Stock changes only through stock operations, each writing a `stock_movements` row. Every employee action is written to `audit_log` in the same transaction.
- Roles are enforced on the backend in every endpoint (also against IDOR). The frontend only hides buttons.
- Passwords only as bcrypt/argon2 hashes. Never put passwords, hashes or tokens in logs, responses or `audit_log`.
- Access token lives in memory only (never localStorage). Refresh token is an httpOnly cookie, stored as a SHA-256 hash, rotated on use.
- SQL through the ORM with bound parameters, sort fields from an allow-list. All input through Pydantic with `extra='forbid'`.
- HTML descriptions are sanitized (bleach on the backend, DOMPurify on the frontend). Uploaded images are re-encoded with Pillow, with uuid names.
- Settings come from `.env`; commit only `.env.example`. No secrets in code or in the frontend.
- UI text and API errors are English, in vue-i18n (`en.js`). Code and comments are English. API errors look like `{"detail": "..."}`.
- Routers are thin, logic lives in `backend/app/services/`. Write complete files, no `...`.

When convenience conflicts with security, choose security and tell the user. Before backend, auth, upload or nginx work, read the Security section of `docs/agent-rules.md`.

## Design (approved, do not replace)

Dark theme with an orange accent, style reference https://budmaster.netlify.app/ (style only; copy no text, images or logo).

- Colours: page `#0b1121`, panels `#151d30`, text `#ffffff`, secondary text `#94a3b8`, border `rgba(255,255,255,0.1)`, primary orange `#ff8a00` (hover `#e57a00`), blue `#2563eb` for links and info.
- Fonts: Outfit 700 for headings, Inter 400/500/600 for text, base 16px.
- Buttons radius 8px, weight 600; primary is orange with a soft glow. Cards radius 16px, 1px border, no shadow; on hover an orange border and `translateY(-4px)`.
- Container max 1200px, header 80px, transitions `0.3s ease-in-out`, respect `prefers-reduced-motion`. The admin app is calmer than the site and has no scroll animations.
- All colours and sizes are variables in `quasar.variables.scss`. Contrast at least WCAG AA.

The full design spec (hero, badges, skeletons) is the Design section of `docs/agent-rules.md`.

## Design skills (local, git-ignored)

Installed in `.agents/skills/` (`.claude/skills/` is a junction to it). If missing, work without them and do not download anything.

| Skill | Use it for | Do not |
| --- | --- | --- |
| `ui-ux-pro-max` | One narrow lookup per question: `python .agents/skills/ui-ux-pro-max/scripts/search.py "<2-5 words>" --domain ux\|color\|typography\|style` or `--stack vue` | Do not run `--design-system` (the design is already decided). Do not read its `data/` files. |
| `impeccable` | A brand-new surface (home page, catalog listing, product page), and one `critique` or `polish` pass when a UI part is finished | Not for small tweaks, bug fixes or backend work. Load only the one reference file the command needs. `reference/new-work.md` is large. |
| `web-design-guidelines` | One accessibility/UX review of the changed files at the end of a UI part (needs network) | Not after every edit. |

Rules:

- `PRODUCT.md` already exists, so impeccable must not start its `init` interview. Run `.agents/skills/impeccable/scripts/impeccable.cmd context` once per session.
- Mode: catalog home page is *Persuade*; catalog listing, product page and the whole admin app are *Operate* (scanability and consistency over expression).
- The approved design above wins. Treat skill output as suggestions and review findings; show new visual ideas to the user before applying them.
- After the first catalog pages exist, run `impeccable document` once to create a compact `DESIGN.md`, so later runs reuse it instead of re-deriving the style.
- When the UI part is finished, run the mechanical detector once: `impeccable.cmd detect --json <changed files>`, then check the result at 375, 768 and 1280 px (Browser pane or Playwright) and say what could not be checked.

## Checks

Run `bash scripts/check.sh` before saying a part is done (`--fix` applies safe fixes and formats; `--security` adds `pip-audit` and `npm audit`). The same script runs in CI (`.github/workflows/ci.yml`).

- Backend: `ruff check`, `ruff format --check` and `ty check`, configured in `backend/pyproject.toml`. Install the tools with `pip install -r backend/requirements-dev.txt`; put the project's virtualenv in `backend/.venv` so ty can resolve imports.
- Rules that matter here: no `print` (use logging), timezone-aware datetimes only (`datetime.now(UTC)`), no `assert` outside tests, no string-built SQL, no hardcoded secrets, FastAPI dependencies via `Annotated`.
- Frontends: `npm run lint` (ESLint from Quasar), with `vue/no-v-html` kept as `error`.
- Fix the code, not the rules. Add a `# noqa: <code>` or a per-file ignore only with a one-line reason, and tell the user.

## Working efficiently

- One part per session. Start a new session or `/clear` between parts; carry state through `ROADMAP.md` and the code, not through chat history.
- Use Grep and ranged Read instead of reading whole files. Do not read lockfiles, `node_modules`, `dist`, `media` or skill data files.
- Batch visual checks instead of screenshotting after every small edit.
- Answer the user in the language they write in (usually Russian). Keep committed files in English, except `docs/deepseek-prompts.md`.
- Keep `README.md`, `ROADMAP.md`, `PRODUCT.md` and this file in sync with the real state of the project.
- Never commit `.env`, secrets, `media/`, `backups/` or the skills (see `.gitignore`).
- Commit and push only when the user asks. Remote: `https://github.com/NyxisDev/inventory_management_system`, branch `main`. Run `git pull` before pushing.
- Before declaring a part finished, run its "Проверь" check and the tests, and say plainly what was not verified.
