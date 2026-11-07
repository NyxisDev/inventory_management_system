"""Stock operations and history: staff and admin."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import AwareDatetime

from app.api.deps import CurrentEmployee, SessionDep, get_current_employee
from app.models import MovementType
from app.schemas.common import Page, PageNumber, PageSize
from app.schemas.stock import (
    AdjustmentRequest,
    IncomeRequest,
    MinQuantityRequest,
    MovementRead,
    OutcomeRequest,
    StockRead,
    TransferRequest,
    TransferResult,
)
from app.services import stock as service
from app.services.stock import MovementFilters

router = APIRouter(prefix="/stock", tags=["stock"], dependencies=[Depends(get_current_employee)])

DateFilter = Annotated[
    AwareDatetime | date | None,
    Query(description="A date (whole day, UTC) or a date-time with a time zone"),
]


@router.get("")
async def list_stock(
    session: SessionDep, product_id: int | None = None, warehouse_id: int | None = None
) -> list[StockRead]:
    return await service.list_stock(session, product_id=product_id, warehouse_id=warehouse_id)


@router.post("/income", status_code=status.HTTP_201_CREATED)
async def income(
    request: Request, data: IncomeRequest, session: SessionDep, employee: CurrentEmployee
) -> MovementRead:
    return await service.income(session, data, employee, request)


@router.post("/outcome", status_code=status.HTTP_201_CREATED)
async def outcome(
    request: Request, data: OutcomeRequest, session: SessionDep, employee: CurrentEmployee
) -> MovementRead:
    return await service.outcome(session, data, employee, request)


@router.post("/adjustment", status_code=status.HTTP_201_CREATED)
async def adjustment(
    request: Request, data: AdjustmentRequest, session: SessionDep, employee: CurrentEmployee
) -> MovementRead:
    return await service.adjustment(session, data, employee, request)


@router.post("/transfer", status_code=status.HTTP_201_CREATED)
async def transfer(
    request: Request, data: TransferRequest, session: SessionDep, employee: CurrentEmployee
) -> TransferResult:
    return await service.transfer(session, data, employee, request)


@router.patch("/min-quantity")
async def set_min_quantity(
    request: Request, data: MinQuantityRequest, session: SessionDep, employee: CurrentEmployee
) -> StockRead:
    return await service.set_min_quantity(session, data, employee, request)


@router.get("/movements")
async def list_movements(
    session: SessionDep,
    product_id: int | None = None,
    warehouse_id: int | None = None,
    employee_id: int | None = None,
    type: MovementType | None = None,
    date_from: DateFilter = None,
    date_to: DateFilter = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[MovementRead]:
    filters = MovementFilters(
        product_id=product_id,
        warehouse_id=warehouse_id,
        employee_id=employee_id,
        type=type,
        date_from=date_from,
        date_to=date_to,
    )
    items, total = await service.list_movements(session, filters, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)
