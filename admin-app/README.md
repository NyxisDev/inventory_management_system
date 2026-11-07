# Budmaster Admin

Quasar SPA for the employee inventory workspace.

## Local demo

From `admin-app/`, install the locked dependencies and start Quasar:

```sh
npm ci
npm run dev
```

Open the local address printed by Quasar and select **Open demo workspace**.

1. Go to **Stock operations → Receipt**, select a product and warehouse, then record a quantity.
2. Check the new balance in **Products** and the record in **Movement history**.
3. Switch **Preview role** to **Staff** in the navigation drawer. **Employees** and **Audit log** are administrator-only in the preview.

The demo uses sample records in memory. Reloading restores the sample data. The demo route is available in development mode. Connecting FastAPI, authenticating staff, uploading product photos and sharing live stock with the catalog are integration steps.

## Build

```sh
npm run build
```
