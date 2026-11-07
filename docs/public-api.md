# Public API contract (catalog site)

What `shop-site` expects from `GET /api/v1/public/...`. It follows part 2 of `docs/deepseek-prompts.md` (section 8, public API). Items marked **addition** go beyond that spec; the backend implements all of them (`backend/app/services/public.py`).

Until the backend is ready the site runs on demo data (`MOCK_API=true`), implemented in `shop-site/src/mock/mock-api.js` with exactly these shapes. When the API is live, set `MOCK_API=false` and `API_URL` (for example `http://backend:8000`).

General rules:

- No auth. Only `is_published = true` and `is_archived = false` products. Only warehouses with `is_active` and `show_on_site`.
- Money and quantities are **decimal strings**, never floats: `"12.50"`, `"860.400"`.
- Dates are ISO 8601 with a time zone: `"2026-11-01T00:00:00Z"`.
- Errors: `{"detail": "..."}`. Unknown slug: `404`.
- No service fields: `created_by`, `updated_by`, `min_quantity`, `is_archived`, employee ids.
- `Cache-Control: public, max-age=60`.

## GET /api/v1/public/categories

Tree of categories that have published products.

```json
[
  {
    "id": 1,
    "name": "Building materials",
    "slug": "building-materials",
    "product_count": 9,
    "children": [
      { "id": 11, "name": "Bricks & blocks", "slug": "bricks-blocks", "product_count": 3, "children": [] }
    ]
  }
]
```

`product_count` (**addition**, optional): published products in the category including subcategories. The site hides the number when it is missing.

## GET /api/v1/public/products

Query parameters (all optional):

| Name | Meaning |
| --- | --- |
| `q` | Search in name and SKU |
| `category_slug` | Category including its subcategories. Unknown slug: `404` |
| `price_min`, `price_max` | Decimal, inclusive |
| `in_stock` | `true`: only products with total quantity > 0 |
| `sort` | `-created_at` (default), `price`, `-price`, `name` |
| `page`, `page_size` | Page from 1, size up to 100 (the site uses 12) |

```json
{
  "items": [
    {
      "id": 10,
      "slug": "pine-beam-100x100",
      "sku": "TM-4001",
      "name": "Pine beam 100×100 mm, kiln-dried",
      "price": "345.00",
      "unit": "m³",
      "category": {
        "name": "Timber",
        "slug": "timber",
        "parent": { "name": "Lumber & panels", "slug": "lumber-panels" }
      },
      "main_image": { "url": "/media/products/10/<uuid>.webp", "thumb_url": "/media/products/10/<uuid>_400.webp" },
      "total_quantity": "9.150",
      "created_at": "2026-10-27T00:00:00Z"
    }
  ],
  "total": 30,
  "page": 1,
  "page_size": 12
}
```

- `category` may be `null`. `category.parent` (**addition**) is used for breadcrumbs; `null` for a top-level category.
- `main_image` may be `null` (the site shows a placeholder). `thumb_url` is the 400 px version; the site falls back to `url`.
- `total_quantity`: sum over the warehouses shown on the site.

## GET /api/v1/public/products/{slug}

Everything from a list item, plus:

```json
{
  "description": "<p>Sanitized HTML</p>",
  "images": [
    { "url": "/media/products/10/<uuid>.webp", "thumb_url": "/media/products/10/<uuid>_400.webp", "is_main": true }
  ],
  "stock": [
    { "warehouse_name": "Central warehouse", "address": "Sample Street 12", "quantity": "6.750" }
  ]
}
```

- `description` may be `null`. The backend cleans it with bleach; the site cleans it again with DOMPurify.
- `stock` lists every warehouse shown on the site, also those with `"0.000"`.

## GET /api/v1/public/warehouses (**addition**)

For the Contacts page and the home page counter. Same filter as above (`is_active` and `show_on_site`).

```json
[{ "name": "Central warehouse", "address": "Sample Street 12, Industrial Zone" }]
```

If this endpoint is missing, the Contacts page shows "The list of warehouses is not available right now" and the rest of the site works.

## Image URLs

Relative URLs starting with `/media/` are served by nginx on both domains (proxied to the backend, cached 7 days). Absolute URLs also work.
