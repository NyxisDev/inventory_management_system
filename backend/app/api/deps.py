"""FastAPI dependencies: database session, current employee, admin check."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, decode_access_token
from app.db import get_session
from app.models import Employee, EmployeeRole

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False, description="Access token from POST /api/v1/auth/login")


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_employee(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Employee:
    """Valid access token of an existing, active employee.

    The role used for permission checks is read from the database, not from the token, so a
    demoted admin loses access immediately.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        data = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise _unauthorized("Invalid or expired token") from None

    employee = await session.get(Employee, data.employee_id)
    if employee is None:
        raise _unauthorized("Invalid or expired token")
    # Tokens issued before the last password change are no longer valid
    if data.issued_at < int(employee.password_changed_at.timestamp()):
        raise _unauthorized("Invalid or expired token")
    if not employee.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return employee


CurrentEmployee = Annotated[Employee, Depends(get_current_employee)]


async def require_admin(employee: CurrentEmployee) -> Employee:
    if employee.role != EmployeeRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return employee


CurrentAdmin = Annotated[Employee, Depends(require_admin)]
