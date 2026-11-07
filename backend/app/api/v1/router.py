"""All /api/v1 routers."""

from fastapi import APIRouter

from app.api.v1.routers import (
    auth,
    categories,
    employees,
    images,
    products,
    public,
    stock,
    warehouses,
)

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(categories.router)
api_router.include_router(warehouses.router)
api_router.include_router(products.router)
api_router.include_router(images.router)
api_router.include_router(stock.router)
api_router.include_router(public.router)
