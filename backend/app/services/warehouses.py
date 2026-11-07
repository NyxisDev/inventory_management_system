"""Warehouses. Never deleted, only deactivated (is_active=false)."""

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, Employee, Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.services.audit import log_action
from app.services.errors import ConflictError, NotFoundError


async def list_warehouses(session: AsyncSession, *, is_active: bool | None) -> list[Warehouse]:
    stmt = select(Warehouse).order_by(Warehouse.name, Warehouse.id)
    if is_active is not None:
        stmt = stmt.where(Warehouse.is_active == is_active)
    return list((await session.scalars(stmt)).all())


async def get_warehouse(session: AsyncSession, warehouse_id: int) -> Warehouse:
    warehouse = await session.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise NotFoundError("Warehouse not found")
    return warehouse


async def _ensure_name_free(session: AsyncSession, name: str, exclude_id: int | None) -> None:
    stmt = select(Warehouse.id).where(Warehouse.name == name)
    if exclude_id is not None:
        stmt = stmt.where(Warehouse.id != exclude_id)
    if await session.scalar(stmt) is not None:
        raise ConflictError("A warehouse with this name already exists")


async def create_warehouse(
    session: AsyncSession, data: WarehouseCreate, actor: Employee, request: Request
) -> Warehouse:
    await _ensure_name_free(session, data.name, None)
    warehouse = Warehouse(
        name=data.name,
        address=data.address or None,
        is_active=data.is_active,
        show_on_site=data.show_on_site,
    )
    session.add(warehouse)
    await session.flush()
    await log_action(
        session,
        employee=actor,
        action=AuditAction.create,
        entity_type="warehouse",
        entity_id=warehouse.id,
        request=request,
    )
    await session.commit()
    return warehouse


async def update_warehouse(
    session: AsyncSession,
    warehouse_id: int,
    data: WarehouseUpdate,
    actor: Employee,
    request: Request,
) -> Warehouse:
    warehouse = await get_warehouse(session, warehouse_id)
    fields = data.model_fields_set
    if data.name is not None and data.name != warehouse.name:
        await _ensure_name_free(session, data.name, warehouse.id)
        warehouse.name = data.name
    if "address" in fields:
        warehouse.address = data.address or None
    if data.is_active is not None:
        warehouse.is_active = data.is_active
    if data.show_on_site is not None:
        warehouse.show_on_site = data.show_on_site

    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="warehouse",
        entity_id=warehouse.id,
        request=request,
    )
    await session.commit()
    return warehouse
