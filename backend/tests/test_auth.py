"""Sign-in, lockout, refresh rotation and token checks."""

from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient

from app.core.config import settings
from app.models import EmployeeRole
from tests.conftest import DEFAULT_PASSWORD, EmployeeFactory, login

XHR = {"X-Requested-With": "XMLHttpRequest"}
INVALID = "Invalid username or password"


async def test_admin_login(client: AsyncClient, make_employee: EmployeeFactory) -> None:
    await make_employee("admin", EmployeeRole.admin)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "Admin", "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["employee"]["role"] == "admin"
    assert "password_hash" not in str(body)
    cookie = response.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "path=/api/v1/auth" in cookie

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.json()["username"] == "admin"


async def test_wrong_password_and_unknown_user_look_the_same(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("anna")
    wrong = await client.post("/api/v1/auth/login", json={"username": "anna", "password": "x"})
    unknown = await client.post("/api/v1/auth/login", json={"username": "nobody", "password": "x"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": INVALID}


async def test_lockout_after_five_failures(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("anna")
    for _ in range(5):
        response = await client.post(
            "/api/v1/auth/login", json={"username": "anna", "password": "wrong-pass-1"}
        )
        assert response.status_code == 401
    # Even the correct password is refused while the account is locked, with the same message
    response = await client.post(
        "/api/v1/auth/login", json={"username": "anna", "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": INVALID}


async def test_inactive_employee_gets_403(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("gone", is_active=False)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "gone", "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 403


async def test_refresh_rotates_and_reuse_revokes_everything(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("anna")
    await login(client, "anna")
    old_token = client.cookies.get("refresh_token")

    assert (await client.post("/api/v1/auth/refresh")).status_code == 403  # no CSRF header

    first = await client.post("/api/v1/auth/refresh", headers=XHR)
    assert first.status_code == 200
    new_token = client.cookies.get("refresh_token")
    assert new_token
    assert new_token != old_token

    # Replaying the old (rotated) token = theft: every session of the employee ends
    client.cookies.clear()
    replay = await client.post("/api/v1/auth/refresh", headers=_cookie(old_token))
    assert replay.status_code == 401
    after = await client.post("/api/v1/auth/refresh", headers=_cookie(new_token))
    assert after.status_code == 401


def _cookie(token: str | None) -> dict:
    return {**XHR, "Cookie": f"refresh_token={token}"}


async def test_logout_revokes_refresh_token(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("anna")
    await login(client, "anna")
    token = client.cookies.get("refresh_token")
    assert (await client.post("/api/v1/auth/logout", headers=XHR)).status_code == 204
    client.cookies.clear()
    assert (await client.post("/api/v1/auth/refresh", headers=_cookie(token))).status_code == 401


async def test_change_password_invalidates_old_tokens(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("anna")
    # Make the old token clearly older than the password change
    old_token, _ = _token(1, "staff", issued=datetime.now(UTC) - timedelta(minutes=1))
    old_headers = {"Authorization": f"Bearer {old_token}"}
    headers = await login(client, "anna")

    weak = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"old_password": DEFAULT_PASSWORD, "new_password": "short1"},
    )
    assert weak.status_code == 422

    response = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"old_password": DEFAULT_PASSWORD, "new_password": "Another-pass-456"},
    )
    assert response.status_code == 200
    new_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert (await client.get("/api/v1/auth/me", headers=new_headers)).status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=old_headers)).status_code == 401
    await login(client, "anna", "Another-pass-456")


def _token(
    employee_id: int,
    role: str,
    *,
    issued: datetime | None = None,
    lifetime: timedelta = timedelta(minutes=15),
    secret: str | None = None,
    algorithm: str = "HS256",
) -> tuple[str, dict]:
    issued = issued or datetime.now(UTC)
    payload = {
        "sub": str(employee_id),
        "role": role,
        "iat": int(issued.timestamp()),
        "exp": int((issued + lifetime).timestamp()),
    }
    return jwt.encode(payload, secret or settings.JWT_SECRET, algorithm=algorithm), payload


async def test_expired_forged_and_none_tokens_are_rejected(
    client: AsyncClient, make_employee: EmployeeFactory
) -> None:
    await make_employee("admin", EmployeeRole.admin)
    expired, _ = _token(
        1, "admin", issued=datetime.now(UTC) - timedelta(hours=1), lifetime=timedelta(minutes=15)
    )
    forged, _ = _token(1, "admin", secret="x" * 40)
    unsigned = jwt.encode({"sub": "1", "role": "admin", "iat": 1, "exp": 9999999999}, None, "none")
    for token in (expired, forged, unsigned, "garbage"):
        response = await client.get(
            "/api/v1/employees", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401, token
    assert (await client.get("/api/v1/employees")).status_code == 401
