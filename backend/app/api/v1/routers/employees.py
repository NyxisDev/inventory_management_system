"""Employees: admin only. No DELETE: employees are deactivated instead."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentAdmin, SessionDep, require_admin
from app.models import EmployeeRole
from app.schemas.common import Page, PageNumber, PageSize
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate, PasswordReset
from app.services import employees as service

router = APIRouter(prefix="/employees", tags=["employees"], dependencies=[Depends(require_admin)])


@router.get("")
async def list_employees(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    role: EmployeeRole | None = None,
    is_active: bool | None = None,
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[EmployeeRead]:
    items, total = await service.list_employees(
        session, q=q, role=role, is_active=is_active, page=page, page_size=page_size
    )
    return Page(
        items=[EmployeeRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{employee_id}")
async def get_employee(employee_id: int, session: SessionDep) -> EmployeeRead:
    return EmployeeRead.model_validate(await service.get_employee(session, employee_id))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_employee(
    request: Request, data: EmployeeCreate, session: SessionDep, admin: CurrentAdmin
) -> EmployeeRead:
    employee = await service.create_employee(session, data, admin, request)
    return EmployeeRead.model_validate(employee)


@router.patch("/{employee_id}")
async def update_employee(
    request: Request,
    employee_id: int,
    data: EmployeeUpdate,
    session: SessionDep,
    admin: CurrentAdmin,
) -> EmployeeRead:
    employee = await service.update_employee(session, employee_id, data, admin, request)
    return EmployeeRead.model_validate(employee)


@router.post("/{employee_id}/reset-password")
async def reset_password(
    request: Request,
    employee_id: int,
    data: PasswordReset,
    session: SessionDep,
    admin: CurrentAdmin,
) -> EmployeeRead:
    employee = await service.reset_password(session, employee_id, data, admin, request)
    return EmployeeRead.model_validate(employee)
