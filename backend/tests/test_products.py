"""Products, categories, warehouses and photos."""

import io

from httpx import AsyncClient
from PIL import Image


async def test_staff_creates_product(client: AsyncClient, staff_headers: dict) -> None:
    response = await client.post(
        "/api/v1/products",
        headers=staff_headers,
        json={
            "sku": "BR-1",
            "name": "Brick red",
            "price": "0.85",
            "unit": "pcs",
            "description": '<p onclick="x()">Solid <script>alert(1)</script>'
            '<a href="javascript:alert(1)">bad</a> <b>brick</b></p>',
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["price"] == "0.85"
    assert body["total_quantity"] == "0.000"
    assert body["created_by"] is not None
    assert "<script" not in body["description"]
    assert "onclick" not in body["description"]
    assert "javascript:" not in body["description"]
    assert "<b>brick</b>" in body["description"]


async def test_staff_cannot_create_warehouse(client: AsyncClient, staff_headers: dict) -> None:
    response = await client.post("/api/v1/warehouses", headers=staff_headers, json={"name": "X"})
    assert response.status_code == 403
    assert (await client.get("/api/v1/warehouses", headers=staff_headers)).status_code == 200


async def test_slugs_are_unique_and_transliterated(
    client: AsyncClient, admin_headers: dict
) -> None:
    first = await client.post("/api/v1/categories", headers=admin_headers, json={"name": "Цемент"})
    second = await client.post("/api/v1/categories", headers=admin_headers, json={"name": "Цемент"})
    assert first.json()["slug"] == "tsement"
    assert second.json()["slug"] == "tsement-2"


async def test_category_with_children_cannot_be_deleted(
    client: AsyncClient, admin_headers: dict
) -> None:
    parent = (
        await client.post("/api/v1/categories", headers=admin_headers, json={"name": "Parent"})
    ).json()
    child = await client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child", "parent_id": parent["id"]},
    )
    assert (
        await client.delete(f"/api/v1/categories/{parent['id']}", headers=admin_headers)
    ).status_code == 409
    # A category cannot become its own descendant
    loop = await client.patch(
        f"/api/v1/categories/{parent['id']}",
        headers=admin_headers,
        json={"parent_id": child.json()["id"]},
    )
    assert loop.status_code == 409
    tree = (await client.get("/api/v1/categories/tree", headers=admin_headers)).json()
    assert tree[0]["children"][0]["name"] == "Child"


async def test_search_and_sort_are_safe(
    client: AsyncClient, admin_headers: dict, product_id: int
) -> None:
    injection = await client.get(
        "/api/v1/products", headers=admin_headers, params={"q": "' OR 1=1 --"}
    )
    assert injection.status_code == 200
    assert injection.json()["total"] == 0
    found = await client.get("/api/v1/products", headers=admin_headers, params={"q": "cem"})
    assert found.json()["total"] == 1
    # A field outside the allow-list is refused; a long injection string fails validation
    for sort, expected in (("password_hash", 400), ("price; DROP TABLE products", 422)):
        response = await client.get(
            "/api/v1/products", headers=admin_headers, params={"sort": sort}
        )
        assert response.status_code == expected, sort
    assert (await client.get("/api/v1/products", headers=admin_headers)).json()["total"] == 1


async def test_delete_without_movements_removes_product(
    client: AsyncClient, admin_headers: dict, product_id: int
) -> None:
    response = await client.delete(f"/api/v1/products/{product_id}", headers=admin_headers)
    assert response.json()["result"] == "deleted"
    assert (
        await client.get(f"/api/v1/products/{product_id}", headers=admin_headers)
    ).status_code == 404


def _png(width: int = 2000, height: int = 1000) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (255, 138, 0)).save(buffer, "PNG")
    return buffer.getvalue()


async def test_image_upload(
    client: AsyncClient, admin_headers: dict, product_id: int, media_dir
) -> None:
    response = await client.post(
        f"/api/v1/products/{product_id}/images",
        headers=admin_headers,
        files=[
            ("files", ("a.png", _png(), "image/png")),
            ("files", ("b.png", _png(), "image/png")),
        ],
    )
    assert response.status_code == 201, response.text
    images = response.json()
    assert [image["is_main"] for image in images] == [True, False]
    stored = media_dir / images[0]["url"].removeprefix("/media/")
    with Image.open(stored) as saved:
        assert saved.format == "WEBP"
        assert max(saved.size) == 1600
    with Image.open(media_dir / images[0]["thumb_url"].removeprefix("/media/")) as thumb:
        assert max(thumb.size) == 400

    # Make the second image the main one, then delete it: the first becomes main again
    second = images[1]["id"]
    patched = await client.patch(
        f"/api/v1/products/{product_id}/images/{second}",
        headers=admin_headers,
        json={"is_main": True},
    )
    assert patched.json()["is_main"] is True
    deleted = await client.delete(
        f"/api/v1/products/{product_id}/images/{second}", headers=admin_headers
    )
    assert deleted.status_code == 204
    product = (await client.get(f"/api/v1/products/{product_id}", headers=admin_headers)).json()
    assert product["main_image"]["id"] == images[0]["id"]


async def test_fake_image_is_rejected(
    client: AsyncClient, admin_headers: dict, product_id: int
) -> None:
    for name, content in (
        ("shell.jpg", b"<?php system($_GET['c']); ?>"),
        ("x.jpg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'),
    ):
        response = await client.post(
            f"/api/v1/products/{product_id}/images",
            headers=admin_headers,
            files=[("files", (name, content, "image/jpeg"))],
        )
        assert response.status_code == 400, name
