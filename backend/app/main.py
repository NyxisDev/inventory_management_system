"""FastAPI application."""

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db import engine
from app.services.errors import ServiceError

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app")

MEDIA_URL = "/media"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    yield
    await engine.dispose()


def _validation_message(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors()[:5]:
        location = ".".join(str(item) for item in error.get("loc", ()) if item != "body")
        message = str(error.get("msg", "Invalid value")).removeprefix("Value error, ")
        parts.append(f"{location}: {message}" if location else message)
    return "Invalid request. " + "; ".join(parts)


def create_app() -> FastAPI:
    settings.MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="Inventory Management API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
        swagger_ui_parameters={"persistAuthorization": False},
    )

    app.state.limiter = limiter

    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
            max_age=600,
        )

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        path = request.url.path
        if path.startswith(MEDIA_URL + "/"):
            # Uploaded files are images only; nothing in them may run in the browser
            response.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
        elif path.startswith("/api/") and not path.startswith("/api/v1/public/"):
            # Employee data must not be stored by browsers or proxies
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    # ---------- errors: always {"detail": "text in English"} ----------

    @app.exception_handler(ServiceError)
    async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": _validation_message(exc)})

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_: Request, __: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429, content={"detail": "Too many requests. Please try again later."}
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Details go to the server log only, never to the client
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(api_router, prefix="/api/v1")
    app.mount(MEDIA_URL, StaticFiles(directory=settings.MEDIA_DIR), name="media")
    return app


app = create_app()
