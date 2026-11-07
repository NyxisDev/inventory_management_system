"""Sign-in, refresh-token rotation, sign-out and password change."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.net import get_client_ip, get_user_agent
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import AuditAction, Employee, RefreshToken
from app.schemas.auth import ChangePasswordRequest, LoginRequest
from app.services.audit import log_action
from app.services.errors import BadRequestError, ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=15)

INVALID_CREDENTIALS = "Invalid username or password"
SESSION_EXPIRED = "Session expired, please sign in again"


@dataclass(frozen=True, slots=True)
class AuthResult:
    employee: Employee
    access_token: str
    expires_in: int
    refresh_token: str  # raw value, goes only into the httpOnly cookie


async def revoke_all_refresh_tokens(session: AsyncSession, employee_id: int) -> None:
    """Revoke every active refresh token of the employee (does not commit)."""
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.employee_id == employee_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def _issue_tokens(
    session: AsyncSession, employee: Employee, request: Request
) -> tuple[AuthResult, RefreshToken]:
    raw_refresh = generate_refresh_token()
    token_row = RefreshToken(
        employee_id=employee.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_EXPIRE_DAYS),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    session.add(token_row)
    await session.flush()
    access_token, expires_in = create_access_token(employee.id, employee.role.value)
    result = AuthResult(
        employee=employee,
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=raw_refresh,
    )
    return result, token_row


async def login(session: AsyncSession, data: LoginRequest, request: Request) -> AuthResult:
    now = datetime.now(UTC)
    employee = await session.scalar(
        select(Employee).where(Employee.username == data.username).with_for_update()
    )

    # Unknown user or temporarily locked account: verify against a dummy hash so the response
    # takes the same time, and return the same message (nothing reveals that the user exists).
    if employee is None or (employee.locked_until is not None and employee.locked_until > now):
        verify_password(data.password, DUMMY_PASSWORD_HASH)
        await log_action(
            session,
            employee=None,
            action=AuditAction.login_failed,
            entity_type="auth",
            new_data={"username": data.username},
            request=request,
        )
        await session.commit()
        raise UnauthorizedError(INVALID_CREDENTIALS)

    if not verify_password(data.password, employee.password_hash):
        employee.failed_login_attempts += 1
        if employee.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            employee.locked_until = now + LOCK_DURATION
            employee.failed_login_attempts = 0
            logger.warning("Employee id=%s locked after failed sign-in attempts", employee.id)
        await log_action(
            session,
            employee=None,
            action=AuditAction.login_failed,
            entity_type="auth",
            new_data={"username": data.username},
            request=request,
        )
        await session.commit()
        raise UnauthorizedError(INVALID_CREDENTIALS)

    # The password is correct from here on, so telling about deactivation reveals nothing new.
    if not employee.is_active:
        await session.rollback()
        raise ForbiddenError("Account is deactivated")

    employee.failed_login_attempts = 0
    employee.locked_until = None
    employee.last_login_at = now
    result, _ = await _issue_tokens(session, employee, request)
    await log_action(
        session,
        employee=employee,
        action=AuditAction.login,
        entity_type="auth",
        entity_id=employee.id,
        request=request,
    )
    await session.commit()
    return result


async def refresh(session: AsyncSession, raw_token: str | None, request: Request) -> AuthResult:
    """Exchange a refresh token for a new access token and a NEW refresh token (rotation)."""
    if not raw_token:
        raise UnauthorizedError(SESSION_EXPIRED)
    token_row = await session.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(raw_token))
        .with_for_update()
    )
    if token_row is None:
        raise UnauthorizedError(SESSION_EXPIRED)

    now = datetime.now(UTC)
    if token_row.revoked_at is not None:
        # An old, already rotated token came back: it was probably stolen.
        # End every session of this employee.
        await revoke_all_refresh_tokens(session, token_row.employee_id)
        await session.commit()
        logger.warning(
            "Refresh token reuse detected for employee id=%s, all sessions revoked",
            token_row.employee_id,
        )
        raise UnauthorizedError(SESSION_EXPIRED)
    if token_row.expires_at <= now:
        raise UnauthorizedError(SESSION_EXPIRED)

    employee = await session.get(Employee, token_row.employee_id)
    if employee is None or not employee.is_active:
        await revoke_all_refresh_tokens(session, token_row.employee_id)
        await session.commit()
        raise UnauthorizedError(SESSION_EXPIRED)

    result, new_row = await _issue_tokens(session, employee, request)
    token_row.revoked_at = now
    token_row.replaced_by = new_row.id
    await session.commit()
    return result


async def logout(session: AsyncSession, raw_token: str | None, request: Request) -> None:
    """Revoke the refresh token from the cookie. Works with an expired access token too."""
    if not raw_token:
        return
    token_row = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    )
    if token_row is None or token_row.revoked_at is not None:
        return
    token_row.revoked_at = datetime.now(UTC)
    employee = await session.get(Employee, token_row.employee_id)
    await log_action(
        session,
        employee=employee,
        action=AuditAction.logout,
        entity_type="auth",
        entity_id=token_row.employee_id,
        request=request,
    )
    await session.commit()


async def logout_all(session: AsyncSession, employee: Employee, request: Request) -> None:
    await revoke_all_refresh_tokens(session, employee.id)
    await log_action(
        session,
        employee=employee,
        action=AuditAction.logout,
        entity_type="auth",
        entity_id=employee.id,
        new_data={"all_sessions": True},
        request=request,
    )
    await session.commit()


async def change_password(
    session: AsyncSession, employee: Employee, data: ChangePasswordRequest, request: Request
) -> AuthResult:
    """Change the own password. All sessions end; the current one gets fresh tokens."""
    if not verify_password(data.old_password, employee.password_hash):
        raise BadRequestError("Current password is incorrect")
    if data.new_password == data.old_password:
        raise BadRequestError("New password must be different from the current one")

    employee.password_hash = hash_password(data.new_password)
    employee.password_changed_at = datetime.now(UTC)
    await revoke_all_refresh_tokens(session, employee.id)
    result, _ = await _issue_tokens(session, employee, request)
    await log_action(
        session,
        employee=employee,
        action=AuditAction.update,
        entity_type="employee",
        entity_id=employee.id,
        old_data={"password": "***"},
        new_data={"password": "***"},
        request=request,
    )
    await session.commit()
    return result
