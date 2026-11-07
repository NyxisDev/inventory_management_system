"""Test setup: a separate database (<name>_test), migrated once per run and emptied before
every test. The app runs as app_user like in production; cleanup runs as app_owner.

The test database is created automatically if POSTGRES_USER / POSTGRES_PASSWORD (the container
superuser from the root .env) are available. Override the URLs with TEST_DATABASE_URL and
TEST_MIGRATIONS_DATABASE_URL if needed.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path

import asyncpg
import pytest
from alembic.config import Config
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from app.core.config import BACKEND_DIR, ROOT_DIR, settings
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.db import get_session
from app.main import app
from app.models import Employee, EmployeeRole

TABLES = (
    "audit_log, stock_movements, stock, product_images, products, "
    "refresh_tokens, categories, warehouses, employees"
)
DEFAULT_PASSWORD = "Secret-pass-123"


def _env(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    for env_file in (BACKEND_DIR / ".env", ROOT_DIR / ".env"):
        value = dotenv_values(env_file).get(name) if env_file.exists() else None
        if value:
            return value
    return None


def _test_url(env_name: str, base: str) -> str:
    explicit = _env(env_name)
    if explicit:
        return explicit
    url = make_url(base)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


TEST_DATABASE_URL = _test_url("TEST_DATABASE_URL", settings.DATABASE_URL)
TEST_MIGRATIONS_URL = _test_url("TEST_MIGRATIONS_DATABASE_URL", settings.MIGRATIONS_DATABASE_URL)


def _plain(url: str, database: str | None = None) -> str:
    """asyncpg DSN from a SQLAlchemy URL."""
    parsed = make_url(url).set(drivername="postgresql")
    if database is not None:
        parsed = parsed.set(database=database)
    return parsed.render_as_string(hide_password=False)


async def _ensure_test_database() -> None:
    target = make_url(TEST_MIGRATIONS_URL)
    try:
        conn = await asyncpg.connect(_plain(TEST_MIGRATIONS_URL))
        await conn.close()
        return
    except asyncpg.InvalidCatalogNameError:
        pass

    superuser = _env("POSTGRES_USER")
    password = _env("POSTGRES_PASSWORD")
    if not superuser or not password:
        pytest.exit(
            f"Test database {target.database!r} does not exist and POSTGRES_USER / "
            "POSTGRES_PASSWORD are not set to create it",
            returncode=2,
        )
    admin_url = target.set(username=superuser, password=password)
    admin = await asyncpg.connect(_plain(admin_url.render_as_string(False), "postgres"))
    try:
        await admin.execute(f'CREATE DATABASE "{target.database}" OWNER app_owner')
    finally:
        await admin.close()

    db = await asyncpg.connect(_plain(admin_url.render_as_string(False)))
    try:
        for statement in (
            f'REVOKE ALL ON DATABASE "{target.database}" FROM PUBLIC',
            f'GRANT CONNECT ON DATABASE "{target.database}" TO app_owner, app_user',
            "CREATE EXTENSION IF NOT EXISTS pg_trgm",
            "REVOKE ALL ON SCHEMA public FROM PUBLIC",
            "ALTER SCHEMA public OWNER TO app_owner",
            "GRANT USAGE ON SCHEMA public TO app_user",
            "ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user",
            "ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public "
            "GRANT USAGE, SELECT ON SEQUENCES TO app_user",
        ):
            await db.execute(statement)
    finally:
        await db.close()


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    """Create (if needed) and migrate the test database from scratch once per run."""
    asyncio.run(_ensure_test_database())
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.attributes["database_url"] = TEST_MIGRATIONS_URL
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def media_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings, "MEDIA_DIR", tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def no_rate_limit() -> None:
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    owner = create_async_engine(TEST_MIGRATIONS_URL, poolclass=NullPool)
    async with owner.begin() as conn:
        await conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    await owner.dispose()

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def _override() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    yield factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
async def owner_engine():
    engine = create_async_engine(TEST_MIGRATIONS_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    # https so the Secure refresh cookie is sent back like in a browser
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as http:
        yield http


EmployeeFactory = Callable[..., Awaitable[Employee]]


@pytest.fixture
def make_employee(session_factory: async_sessionmaker[AsyncSession]) -> EmployeeFactory:
    async def _make(
        username: str,
        role: EmployeeRole = EmployeeRole.staff,
        password: str = DEFAULT_PASSWORD,
        is_active: bool = True,
    ) -> Employee:
        async with session_factory() as session:
            employee = Employee(
                first_name=username.capitalize(),
                last_name="Tester",
                username=username,
                password_hash=hash_password(password),
                role=role,
                is_active=is_active,
            )
            session.add(employee)
            await session.commit()
            return employee

    return _make


async def login(client: AsyncClient, username: str, password: str = DEFAULT_PASSWORD) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, make_employee: EmployeeFactory) -> dict:
    await make_employee("admin", EmployeeRole.admin)
    return await login(client, "admin")


@pytest.fixture
async def staff_headers(client: AsyncClient, make_employee: EmployeeFactory) -> dict:
    await make_employee("staff", EmployeeRole.staff)
    return await login(client, "staff")


@pytest.fixture
async def warehouse_ids(client: AsyncClient, admin_headers: dict) -> tuple[int, int]:
    ids = []
    for name in ("Main warehouse", "Second warehouse"):
        response = await client.post(
            "/api/v1/warehouses", headers=admin_headers, json={"name": name, "address": "Street 1"}
        )
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    return ids[0], ids[1]


@pytest.fixture
async def product_id(client: AsyncClient, admin_headers: dict) -> int:
    response = await client.post(
        "/api/v1/products",
        headers=admin_headers,
        json={"sku": "CEM-500", "name": "Cement M500", "price": "100.00", "unit": "pcs"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
