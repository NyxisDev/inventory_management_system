"""Audit log: what is recorded, masking, read-only API and append-only table."""

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from tests.conftest import TEST_DATABASE_URL


async def _entries(client: AsyncClient, headers: dict, **params: str) -> list[dict]:
    response = await client.get("/api/v1/audit", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()["items"]


async def test_price_change_records_old_and_new(
    client: AsyncClient, admin_headers: dict, product_id: int
) -> None:
    response = await client.patch(
        f"/api/v1/products/{product_id}", headers=admin_headers, json={"price": 120}
    )
    assert response.status_code == 200
    entries = await _entries(client, admin_headers, entity_type="product", action="update")
    assert len(entries) == 1
    entry = entries[0]
    assert entry["changes"] == [{"field": "price", "old": "100.00", "new": "120.00"}]
    assert entry["employee_name"] == "Admin Tester"
    assert entry["summary"] == ("Admin Tester changed the price of «Cement M500»: 100.00 → 120.00")
    assert entry["ip_address"] == "127.0.0.1"

    # Saving the same value again changes nothing, so nothing is recorded
    await client.patch(f"/api/v1/products/{product_id}", headers=admin_headers, json={"price": 120})
    assert len(await _entries(client, admin_headers, entity_type="product", action="update")) == 1

    history = await client.get(f"/api/v1/audit/entity/product/{product_id}", headers=admin_headers)
    assert [item["action"] for item in history.json()["items"]] == ["update", "create"]


async def test_employee_create_never_logs_password(
    client: AsyncClient, admin_headers: dict
) -> None:
    created = await client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={
            "first_name": "John",
            "last_name": "Smith",
            "username": "jsmith",
            "password": "Password-123",
        },
    )
    employee_id = created.json()["id"]
    await client.post(
        f"/api/v1/employees/{employee_id}/reset-password",
        headers=admin_headers,
        json={"new_password": "Another-pass-456"},
    )
    export = await client.get("/api/v1/audit/export.csv", headers=admin_headers)
    listing = await client.get("/api/v1/audit", headers=admin_headers)
    for body in (export.text, listing.text):
        assert "Password-123" not in body
        assert "Another-pass-456" not in body
        assert "$2b$" not in body
    entries = await _entries(client, admin_headers, entity_type="employee")
    assert entries[0]["summary"] == "Admin Tester changed the password of «John Smith»"
    assert entries[1]["summary"] == "Admin Tester created employee «John Smith»"


async def test_failed_outcome_leaves_no_record(
    client: AsyncClient, admin_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, _ = warehouse_ids
    await client.post(
        "/api/v1/stock/income",
        headers=admin_headers,
        json={"product_id": product_id, "warehouse_id": main, "quantity": "5"},
    )
    failed = await client.post(
        "/api/v1/stock/outcome",
        headers=admin_headers,
        json={"product_id": product_id, "warehouse_id": main, "quantity": "50"},
    )
    assert failed.status_code == 409
    entries = await _entries(client, admin_headers, action="stock_change")
    assert len(entries) == 1
    assert entries[0]["entity_id"] == f"{product_id}:{main}"
    assert entries[0]["changes"] == [{"field": "quantity", "old": "0.000", "new": "5.000"}]
    assert "income +5.000" in entries[0]["summary"]


async def test_transfer_writes_two_records(
    client: AsyncClient, admin_headers: dict, warehouse_ids: tuple[int, int], product_id: int
) -> None:
    main, second = warehouse_ids
    await client.post(
        "/api/v1/stock/income",
        headers=admin_headers,
        json={"product_id": product_id, "warehouse_id": main, "quantity": "5"},
    )
    await client.post(
        "/api/v1/stock/transfer",
        headers=admin_headers,
        json={
            "product_id": product_id,
            "from_warehouse_id": main,
            "to_warehouse_id": second,
            "quantity": "2",
        },
    )
    entries = await _entries(client, admin_headers, action="stock_change")
    assert {entry["entity_id"] for entry in entries[:2]} == {
        f"{product_id}:{main}",
        f"{product_id}:{second}",
    }


async def test_logins_are_recorded(client: AsyncClient, admin_headers: dict) -> None:
    await client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong-1"})
    actions = [entry["action"] for entry in await _entries(client, admin_headers)]
    assert actions[:2] == ["login_failed", "login"]


async def test_staff_gets_403_on_audit(client: AsyncClient, staff_headers: dict) -> None:
    for path in ("/api/v1/audit", "/api/v1/audit/export.csv", "/api/v1/audit/entity/product/1"):
        assert (await client.get(path, headers=staff_headers)).status_code == 403


async def test_audit_api_is_read_only(client: AsyncClient, admin_headers: dict) -> None:
    for method in ("PUT", "PATCH", "DELETE"):
        response = await client.request(method, "/api/v1/audit", headers=admin_headers)
        assert response.status_code == 405


async def test_csv_export_format(client: AsyncClient, admin_headers: dict, product_id: int) -> None:
    await client.patch(
        f"/api/v1/products/{product_id}", headers=admin_headers, json={"name": "=HYPERLINK(1)"}
    )
    response = await client.get("/api/v1/audit/export.csv", headers=admin_headers)
    assert response.headers["content-type"].startswith("text/csv")
    raw = response.content
    assert raw.startswith("﻿".encode())
    header = raw.decode("utf-8-sig").splitlines()[0]
    assert header.split(";")[:3] == ["Date", "Employee", "Action"]
    # A value that looks like a formula is never at the start of a cell
    assert ";=HYPERLINK" not in raw.decode("utf-8-sig")


@pytest.fixture
async def app_user_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


async def test_audit_log_cannot_be_changed_in_the_database(
    client: AsyncClient, admin_headers: dict, owner_engine: AsyncEngine, app_user_engine
) -> None:
    # app_user (the API role) has no UPDATE / DELETE rights at all
    for statement in ("UPDATE audit_log SET entity_type = 'x'", "DELETE FROM audit_log"):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with app_user_engine.begin() as conn:
                await conn.execute(text(statement))
    # even the table owner is stopped by the trigger
    with pytest.raises(DBAPIError, match="append-only"):
        async with owner_engine.begin() as conn:
            await conn.execute(text("UPDATE audit_log SET entity_type = 'x'"))
