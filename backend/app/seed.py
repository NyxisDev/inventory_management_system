"""Initial data: first admin, "Main warehouse" and two categories.

Run with: python -m app.seed
Safe to run more than once: existing rows are left untouched
(the admin password is never overwritten).
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, validate_password_strength
from app.db import SessionLocal, engine
from app.models import Category, Employee, EmployeeRole, Warehouse

MAIN_WAREHOUSE_NAME = "Main warehouse"
DEFAULT_CATEGORIES = [
    ("Building materials", "building-materials", 0),
    ("Tools", "tools", 1),
]


async def seed_admin(session: AsyncSession) -> None:
    username = settings.ADMIN_USERNAME.strip()
    if not username or len(username) > 50:
        raise SystemExit("ADMIN_USERNAME must be 1-50 characters")

    existing = await session.scalar(select(Employee).where(Employee.username == username))
    if existing is not None:
        print(f"Admin '{username}' already exists, skipped")
        return

    try:
        validate_password_strength(settings.ADMIN_PASSWORD)
    except ValueError as exc:
        raise SystemExit(f"ADMIN_PASSWORD is not valid: {exc}") from None

    session.add(
        Employee(
            first_name="System",
            last_name="Administrator",
            username=username,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=EmployeeRole.admin,
        )
    )
    print(f"Admin '{username}' created")


async def seed_warehouse(session: AsyncSession) -> None:
    existing = await session.scalar(select(Warehouse).where(Warehouse.name == MAIN_WAREHOUSE_NAME))
    if existing is not None:
        print(f"Warehouse '{MAIN_WAREHOUSE_NAME}' already exists, skipped")
        return
    session.add(Warehouse(name=MAIN_WAREHOUSE_NAME))
    print(f"Warehouse '{MAIN_WAREHOUSE_NAME}' created")


async def seed_categories(session: AsyncSession) -> None:
    for name, slug, sort_order in DEFAULT_CATEGORIES:
        existing = await session.scalar(select(Category).where(Category.slug == slug))
        if existing is not None:
            print(f"Category '{name}' already exists, skipped")
            continue
        session.add(Category(name=name, slug=slug, sort_order=sort_order))
        print(f"Category '{name}' created")


async def main() -> None:
    try:
        async with SessionLocal() as session, session.begin():
            await seed_admin(session)
            await seed_warehouse(session)
            await seed_categories(session)
    finally:
        await engine.dispose()
    print("Seed finished")


if __name__ == "__main__":
    asyncio.run(main())
