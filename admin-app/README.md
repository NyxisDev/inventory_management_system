# Budmaster Admin

Quasar SPA for the employee inventory workspace.

## Local development

The app talks to the FastAPI backend. In development the Quasar dev server proxies `/api` and
`/media` to `http://127.0.0.1:8000` (override with `API_PROXY_TARGET`), so the httpOnly refresh
cookie works as on one domain.

1. Start the database and the backend (see the root `README.md`), create the first admin with
   `python -m app.seed`.
2. From `admin-app/`:

   ```sh
   npm ci
   npm run dev      # http://localhost:9000
   ```

3. Sign in with the admin account. Staff accounts are created on the **Employees** page.

How it works:

- `src/boot/axios.js`: API client with cookies and `X-Requested-With`; on 401 it refreshes the
  access token once (parallel requests share one refresh) and retries, otherwise signs out.
- `src/stores/auth.js`: access token in memory only, session restored from the refresh cookie on
  start, sign-out after 30 minutes of inactivity, sign-out in one tab ends all tabs.
- `src/stores/inventory.js`: data from the API (products, stock, movements, directories, audit).
- Routes use `meta.requiresAuth` / `meta.requiresAdmin`; the backend checks every permission.

## Build

```sh
npm run build
```
