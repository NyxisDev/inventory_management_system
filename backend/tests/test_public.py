"""Public catalog API: visibility rules, shapes, no service fields, caching."""

from httpx import AsyncClient

SERVICE_FIELDS = ("created_by", "updated_by", "min_quantity", "is_archived", "employee")


async def _publish_with_stock(
    client: AsyncClient, headers: dict, product_id: int, warehouse_ids: tuple[int, int]
) -> None:
    main, second = warehouse_ids
    for warehouse, quantity in ((main, "4"), (second, "6.5")):
        response = await client.post(
            "/api/v1/stock/income",
            headers=headers,
            json={"product_id": product_id, "warehouse_id": warehouse, "quantity": quantity},
        )
        assert response.status_code == 201
    await client.patch(
        f"/api/v1/products/{product_id}", headers=headers, json={"is_published": True}
    )


async def test_health(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/health")).json() == {"status": "ok"}


async def test_unpublished_products_are_hidden(
    client: AsyncClient, admin_headers: dict, product_id: int
) -> None:
    listing = await client.get("/api/v1/public/products")
    assert listing.json()["total"] == 0
    detail = await client.get("/api/v1/public/products/cement-m500")
    assert detail.status_code == 404


async def test_published_product_shape(
    client: AsyncClient,
    admin_headers: dict,
    product_id: int,
    warehouse_ids: tuple[int, int],
) -> None:
    category = await client.post(
        "/api/v1/categories", headers=admin_headers, json={"name": "Building materials"}
    )
    sub = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Cement", "parent_id": category.json()["id"]},
    )
    await client.patch(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
        json={"category_id": sub.json()["id"]},
    )
    await _publish_with_stock(client, admin_headers, product_id, warehouse_ids)

    listing = await client.get("/api/v1/public/products")
    assert listing.headers["cache-control"] == "public, max-age=60"
    item = listing.json()["items"][0]
    assert item["price"] == "100.00"
    assert item["total_quantity"] == "10.500"
    assert item["category"] == {
        "name": "Cement",
        "slug": "cement",
        "parent": {"name": "Building materials", "slug": "building-materials"},
    }
    assert item["main_image"] is None

    detail = await client.get(f"/api/v1/public/products/{item['slug']}")
    body = detail.json()
    assert [row["quantity"] for row in body["stock"]] == ["4.000", "6.500"]
    for field in SERVICE_FIELDS:
        assert field not in detail.text

    # The category filter includes subcategories; an unknown category is 404
    parent_filter = await client.get(
        "/api/v1/public/products", params={"category_slug": "building-materials"}
    )
    assert parent_filter.json()["total"] == 1
    unknown = await client.get("/api/v1/public/products", params={"category_slug": "nope"})
    assert unknown.status_code == 404

    tree = (await client.get("/api/v1/public/categories")).json()
    assert tree[0]["product_count"] == 1
    assert tree[0]["children"][0]["slug"] == "cement"


async def test_hidden_warehouse_is_not_shown(
    client: AsyncClient,
    admin_headers: dict,
    product_id: int,
    warehouse_ids: tuple[int, int],
) -> None:
    await _publish_with_stock(client, admin_headers, product_id, warehouse_ids)
    _, second = warehouse_ids
    await client.patch(
        f"/api/v1/warehouses/{second}", headers=admin_headers, json={"show_on_site": False}
    )
    item = (await client.get("/api/v1/public/products")).json()["items"][0]
    assert item["total_quantity"] == "4.000"
    warehouses = (await client.get("/api/v1/public/warehouses")).json()
    assert [w["name"] for w in warehouses] == ["Main warehouse"]


async def test_filters_and_sorting(
    client: AsyncClient,
    admin_headers: dict,
    product_id: int,
    warehouse_ids: tuple[int, int],
) -> None:
    await _publish_with_stock(client, admin_headers, product_id, warehouse_ids)
    cheap = await client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={"sku": "SND-1", "name": "Sand", "price": "5.00", "is_published": True},
    )
    assert cheap.status_code == 201

    by_price = await client.get("/api/v1/public/products", params={"sort": "price"})
    assert [i["sku"] for i in by_price.json()["items"]] == ["SND-1", "CEM-500"]
    in_stock = await client.get("/api/v1/public/products", params={"in_stock": "true"})
    assert [i["sku"] for i in in_stock.json()["items"]] == ["CEM-500"]
    ranged = await client.get(
        "/api/v1/public/products", params={"price_min": "1", "price_max": "10"}
    )
    assert [i["sku"] for i in ranged.json()["items"]] == ["SND-1"]
    bad_sort = await client.get("/api/v1/public/products", params={"sort": "created_by"})
    assert bad_sort.status_code == 400
