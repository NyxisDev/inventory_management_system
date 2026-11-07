"""Employees: admin only, never returns password hashes, protects the last admin."""

from httpx import AsyncClient

from tests.conftest import login


async def test_staff_gets_403_on_employees(client: AsyncClient, staff_headers: dict) -> None:
    assert (await client.get("/api/v1/employees", headers=staff_headers)).status_code == 403
    response = await client.post(
        "/api/v1/employees",
        headers=staff_headers,
        json={
            "first_name": "A",
            "last_name": "B",
            "username": "evil",
            "password": "Password-123",
        },
    )
    assert response.status_code == 403


async def test_admin_creates_employee_without_leaking_hash(
    client: AsyncClient, admin_headers: dict
) -> None:
    payload = {
        "first_name": "John",
        "last_name": "Smith",
        "username": "John.Smith",
        "password": "Password-123",
        "role": "staff",
    }
    created = await client.post("/api/v1/employees", headers=admin_headers, json=payload)
    assert created.status_code == 201
    assert created.json()["username"] == "john.smith"
    duplicate = await client.post("/api/v1/employees", headers=admin_headers, json=payload)
    assert duplicate.status_code == 409

    listing = await client.get("/api/v1/employees?q=smith", headers=admin_headers)
    assert listing.json()["total"] == 1
    assert "password" not in listing.text
    await login(client, "john.smith", "Password-123")


async def test_weak_password_and_unknown_fields_rejected(
    client: AsyncClient, admin_headers: dict
) -> None:
    base = {"first_name": "A", "last_name": "B", "username": "abc"}
    weak = await client.post(
        "/api/v1/employees", headers=admin_headers, json={**base, "password": "onlyletters"}
    )
    assert weak.status_code == 422
    extra = await client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={**base, "password": "Password-123", "is_admin": True},
    )
    assert extra.status_code == 422


async def test_cannot_demote_self_or_last_admin(client: AsyncClient, admin_headers: dict) -> None:
    me = (await client.get("/api/v1/auth/me", headers=admin_headers)).json()
    response = await client.patch(
        f"/api/v1/employees/{me['id']}", headers=admin_headers, json={"is_active": False}
    )
    assert response.status_code == 409


async def test_deactivation_blocks_access(client: AsyncClient, admin_headers: dict) -> None:
    created = await client.post(
        "/api/v1/employees",
        headers=admin_headers,
        json={"first_name": "A", "last_name": "B", "username": "temp", "password": "Password-123"},
    )
    employee_id = created.json()["id"]
    temp_headers = await login(client, "temp", "Password-123")
    await client.patch(
        f"/api/v1/employees/{employee_id}", headers=admin_headers, json={"is_active": False}
    )
    assert (await client.get("/api/v1/auth/me", headers=temp_headers)).status_code == 403
