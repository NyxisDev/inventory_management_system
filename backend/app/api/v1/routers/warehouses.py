"""Warehouses: list for staff and admin; create and edit for admin only. No DELETE."""

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import CurrentAdmin, SessionDep, get_current_employee
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services import warehouses as service

router = APIRouter(
    prefix="/warehouses", tags=["warehouses"], dependencies=[Depends(get_current_employee)]
)


@router.get("")
async def list_warehouses(
    session: SessionDep, is_active: bool | None = None
) -> list[WarehouseRead]:
    items = await service.list_warehouses(session, is_active=is_active)
    return [WarehouseRead.model_validate(item) for item in items]


@router.get("/{warehouse_id}")
async def get_warehouse(warehouse_id: int, session: SessionDep) -> WarehouseRead:
    return WarehouseRead.model_validate(await service.get_warehouse(session, warehouse_id))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    request: Request, data: WarehouseCreate, session: SessionDep, admin: CurrentAdmin
) -> WarehouseRead:
    warehouse = await service.create_warehouse(session, data, admin, request)
    return WarehouseRead.model_validate(warehouse)


@router.patch("/{warehouse_id}")
async def update_warehouse(
    request: Request,
    warehouse_id: int,
    data: WarehouseUpdate,
    session: SessionDep,
    admin: CurrentAdmin,
) -> WarehouseRead:
    warehouse = await service.update_warehouse(session, warehouse_id, data, admin, request)
    return WarehouseRead.model_validate(warehouse)
