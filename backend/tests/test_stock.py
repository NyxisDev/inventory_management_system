"""Stock operations: income, outcome, transfer, stock-taking, concurrency."""

import asyncio

from httpx import AsyncClient


async def _income(client: AsyncClient, headers: dict, product: int, warehouse: int, qty: str):
    response = await client.post(
        "/api/v1/stock/income",
        headers=headers,
        json={"product_id": product, "warehouse_id": warehouse, "quantity": qty},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _quantity(client: AsyncClient, headers: dict, product: int, warehouse: int) -> str:
    rows = (
        await client.get(
            "/api/v1/stock",
            headers=headers,
            params={"product_id": product, "warehouse_id": warehouse},
        )
    ).json()
    return rows[0]["quantity"] if rows else "0.000"


async def test_outcome_larger_than_stock_returns_409(
    client: AsyncClient, staff_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, _ = warehouse_ids
    await _income(client, staff_headers, product_id, main, "10")
    response = await client.post(
        "/api/v1/stock/outcome",
        headers=staff_headers,
        json={"product_id": product_id, "warehouse_id": main, "quantity": "10.001"},
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Not enough stock in this warehouse"}
    assert await _quantity(client, staff_headers, product_id, main) == "10.000"
    movements = (await client.get("/api/v1/stock/movements", headers=staff_headers)).json()
    assert movements["total"] == 1  # only the income: the failed outcome left nothing


async def test_transfer_changes_both_warehouses(
    client: AsyncClient, staff_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, second = warehouse_ids
    await _income(client, staff_headers, product_id, main, "12.5")
    response = await client.post(
        "/api/v1/stock/transfer",
        headers=staff_headers,
        json={
            "product_id": product_id,
            "from_warehouse_id": main,
            "to_warehouse_id": second,
            "quantity": "2.25",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["transfer_out"]["quantity_change"] == "-2.250"
    assert body["transfer_in"]["quantity_change"] == "2.250"
    assert body["transfer_out"]["transfer_group"] == body["transfer_in"]["transfer_group"]
    assert await _quantity(client, staff_headers, product_id, main) == "10.250"
    assert await _quantity(client, staff_headers, product_id, second) == "2.250"

    same = await client.post(
        "/api/v1/stock/transfer",
        headers=staff_headers,
        json={
            "product_id": product_id,
            "from_warehouse_id": main,
            "to_warehouse_id": main,
            "quantity": "1",
        },
    )
    assert same.status_code == 422


async def test_adjustment_records_difference(
    client: AsyncClient, staff_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, _ = warehouse_ids
    await _income(client, staff_headers, product_id, main, "10")
    no_comment = await client.post(
        "/api/v1/stock/adjustment",
        headers=staff_headers,
        json={"product_id": product_id, "warehouse_id": main, "new_quantity": "7"},
    )
    assert no_comment.status_code == 422
    response = await client.post(
        "/api/v1/stock/adjustment",
        headers=staff_headers,
        json={
            "product_id": product_id,
            "warehouse_id": main,
            "new_quantity": "7",
            "comment": "Stock-taking",
        },
    )
    assert response.json()["quantity_change"] == "-3.000"
    assert response.json()["quantity_after"] == "7.000"


async def test_invalid_quantities_rejected(
    client: AsyncClient, staff_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, _ = warehouse_ids
    for quantity in ("0", "-5", "1.0001", "1e20"):
        response = await client.post(
            "/api/v1/stock/income",
            headers=staff_headers,
            json={"product_id": product_id, "warehouse_id": main, "quantity": quantity},
        )
        assert response.status_code == 422, quantity


async def test_archived_product_and_inactive_warehouse_return_409(
    client: AsyncClient,
    admin_headers: dict,
    warehouse_ids: tuple[int, int],
    product_id: int,
) -> None:
    main, second = warehouse_ids
    await _income(client, admin_headers, product_id, main, "1")
    archived = await client.delete(f"/api/v1/products/{product_id}", headers=admin_headers)
    assert archived.json()["result"] == "archived"
    response = await client.post(
        "/api/v1/stock/income",
        headers=admin_headers,
        json={"product_id": product_id, "warehouse_id": main, "quantity": "1"},
    )
    assert response.status_code == 409

    await client.patch(
        f"/api/v1/products/{product_id}", headers=admin_headers, json={"is_archived": False}
    )
    await client.patch(
        f"/api/v1/warehouses/{second}", headers=admin_headers, json={"is_active": False}
    )
    response = await client.post(
        "/api/v1/stock/income",
        headers=admin_headers,
        json={"product_id": product_id, "warehouse_id": second, "quantity": "1"},
    )
    assert response.status_code == 409


async def test_parallel_outcomes_never_go_negative(
    client: AsyncClient, staff_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, _ = warehouse_ids
    await _income(client, staff_headers, product_id, main, "5")

    async def take_three() -> int:
        response = await client.post(
            "/api/v1/stock/outcome",
            headers=staff_headers,
            json={"product_id": product_id, "warehouse_id": main, "quantity": "3"},
        )
        return response.status_code

    statuses = await asyncio.gather(*(take_three() for _ in range(4)))
    assert sorted(statuses) == [201, 409, 409, 409]
    assert await _quantity(client, staff_headers, product_id, main) == "2.000"


async def test_low_stock_filter(
    client: AsyncClient, staff_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, _ = warehouse_ids
    await _income(client, staff_headers, product_id, main, "3")
    low = await client.get("/api/v1/products?low_stock=true", headers=staff_headers)
    assert low.json()["total"] == 0  # min_quantity 0 means "not tracked"
    await client.patch(
        "/api/v1/stock/min-quantity",
        headers=staff_headers,
        json={"product_id": product_id, "warehouse_id": main, "min_quantity": "5"},
    )
    low = await client.get("/api/v1/products?low_stock=true", headers=staff_headers)
    assert low.json()["total"] == 1
    assert low.json()["items"][0]["is_low_stock"] is True
