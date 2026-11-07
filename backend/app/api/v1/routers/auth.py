"""Sign-in, token refresh, sign-out, own profile and password change."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status

from app.api.deps import CurrentEmployee, SessionDep
from app.core.config import settings
from app.core.rate_limit import LOGIN_LIMIT, REFRESH_LIMIT, limiter
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.employee import EmployeeBrief, EmployeeRead
from app.services import auth as auth_service
from app.services.auth import AuthResult
from app.services.errors import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.REFRESH_EXPIRE_DAYS * 24 * 3600,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
    )


def _delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
    )


def _token_response(result: AuthResult, response: Response) -> TokenResponse:
    _set_refresh_cookie(response, result.refresh_token)
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        employee=EmployeeBrief.model_validate(result.employee),
    )


async def require_xhr_header(
    x_requested_with: Annotated[str | None, Header()] = None,
) -> None:
    """CSRF protection for cookie-based endpoints (in addition to SameSite=Strict)."""
    if x_requested_with != "XMLHttpRequest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing header X-Requested-With: XMLHttpRequest",
        )


RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE)]


@router.post("/login")
@limiter.limit(LOGIN_LIMIT)
async def login(
    request: Request, response: Response, data: LoginRequest, session: SessionDep
) -> TokenResponse:
    result = await auth_service.login(session, data, request)
    return _token_response(result, response)


@router.post("/refresh", dependencies=[Depends(require_xhr_header)])
@limiter.limit(REFRESH_LIMIT)
async def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: RefreshCookie = None,
) -> TokenResponse:
    try:
        result = await auth_service.refresh(session, refresh_token, request)
    except UnauthorizedError:
        # Clear the dead cookie, keep the 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_service.SESSION_EXPIRED,
            headers={"Set-Cookie": _expired_cookie_header()},
        ) from None
    return _token_response(result, response)


def _expired_cookie_header() -> str:
    probe = Response()
    _delete_refresh_cookie(probe)
    return probe.headers["set-cookie"]


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_xhr_header)],
)
async def logout(
    request: Request,
    response: Response,
    session: SessionDep,
    refresh_token: RefreshCookie = None,
) -> None:
    await auth_service.logout(session, refresh_token, request)
    _delete_refresh_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    request: Request, response: Response, session: SessionDep, employee: CurrentEmployee
) -> None:
    await auth_service.logout_all(session, employee, request)
    _delete_refresh_cookie(response)


@router.get("/me")
async def me(employee: CurrentEmployee) -> EmployeeRead:
    return EmployeeRead.model_validate(employee)


@router.post("/change-password")
async def change_password(
    request: Request,
    response: Response,
    data: ChangePasswordRequest,
    session: SessionDep,
    employee: CurrentEmployee,
) -> TokenResponse:
    result = await auth_service.change_password(session, employee, data, request)
    return _token_response(result, response)
