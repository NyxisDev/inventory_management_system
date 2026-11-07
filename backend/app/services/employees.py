"""Employees (admin only). Employees are never deleted, only deactivated."""

from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import AuditAction, Employee, EmployeeRole
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, PasswordReset
from app.services.audit import EMPLOYEE_FIELDS, log_action, snapshot
from app.services.auth import revoke_all_refresh_tokens
from app.services.errors import ConflictError, NotFoundError
from app.services.query import escape_like, paginate


async def list_employees(
    session: AsyncSession,
    *,
    q: str | None,
    role: EmployeeRole | None,
    is_active: bool | None,
    page: int,
    page_size: int,
) -> tuple[list[Employee], int]:
    stmt = select(Employee)
    if q:
        pattern = f"%{escape_like(q)}%"
        stmt = stmt.where(
            or_(
                Employee.first_name.ilike(pattern, escape="\\"),
                Employee.last_name.ilike(pattern, escape="\\"),
                Employee.username.ilike(pattern, escape="\\"),
            )
        )
    if role is not None:
        stmt = stmt.where(Employee.role == role)
    if is_active is not None:
        stmt = stmt.where(Employee.is_active == is_active)
    stmt = stmt.order_by(Employee.last_name, Employee.first_name, Employee.id)
    return await paginate(session, stmt, page, page_size)


async def get_employee(session: AsyncSession, employee_id: int) -> Employee:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")
    return employee


async def create_employee(
    session: AsyncSession, data: EmployeeCreate, actor: Employee, request: Request
) -> Employee:
    exists = await session.scalar(select(Employee.id).where(Employee.username == data.username))
    if exists is not None:
        raise ConflictError("Username already exists")
    employee = Employee(
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    session.add(employee)
    await session.flush()
    await log_action(
        session,
        employee=actor,
        action=AuditAction.create,
        entity_type="employee",
        entity_id=employee.id,
        new_data=snapshot(employee, EMPLOYEE_FIELDS),
        label=employee.full_name,
        request=request,
    )
    await session.commit()
    return employee


async def _other_active_admins(session: AsyncSession, employee_id: int) -> int:
    # Lock the admin rows so two parallel requests cannot remove the last two admins at once
    ids = (
        await session.scalars(
            select(Employee.id)
            .where(
                Employee.role == EmployeeRole.admin,
                Employee.is_active.is_(True),
                Employee.id != employee_id,
            )
            .with_for_update()
        )
    ).all()
    return len(ids)


async def update_employee(
    session: AsyncSession,
    employee_id: int,
    data: EmployeeUpdate,
    actor: Employee,
    request: Request,
) -> Employee:
    employee = await get_employee(session, employee_id)
    before = snapshot(employee, EMPLOYEE_FIELDS)
    changes = data.model_dump(exclude_unset=True)
    # Explicit null for non-nullable fields means "no change"
    changes = {key: value for key, value in changes.items() if value is not None}

    loses_admin = employee.role == EmployeeRole.admin and (
        changes.get("role", employee.role) != EmployeeRole.admin
        or changes.get("is_active", employee.is_active) is False
    )
    deactivates = employee.is_active and changes.get("is_active") is False

    if employee.id == actor.id and (loses_admin or deactivates):
        raise ConflictError("You cannot deactivate or demote yourself")
    if loses_admin and employee.is_active and await _other_active_admins(session, employee.id) == 0:
        raise ConflictError("Cannot deactivate or demote the last active admin")

    for key, value in changes.items():
        setattr(employee, key, value)
    if deactivates:
        await revoke_all_refresh_tokens(session, employee.id)

    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="employee",
        entity_id=employee.id,
        old_data=before,
        new_data=snapshot(employee, EMPLOYEE_FIELDS),
        label=employee.full_name,
        request=request,
    )
    await session.commit()
    return employee


async def reset_password(
    session: AsyncSession,
    employee_id: int,
    data: PasswordReset,
    actor: Employee,
    request: Request,
) -> Employee:
    employee = await get_employee(session, employee_id)
    employee.password_hash = hash_password(data.new_password)
    employee.password_changed_at = datetime.now(UTC)
    employee.failed_login_attempts = 0
    employee.locked_until = None
    await revoke_all_refresh_tokens(session, employee.id)
    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="employee",
        entity_id=employee.id,
        new_data={"password": "***"},
        label=employee.full_name,
        request=request,
    )
    await session.commit()
    return employee
