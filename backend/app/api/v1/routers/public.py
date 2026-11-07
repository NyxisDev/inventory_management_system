"""Public catalog API: no sign-in, read only, cached for 60 seconds."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Path, Query, Request, Response
from pydantic import Field

from app.api.deps import SessionDep
from app.core.rate_limit import PUBLIC_LIMIT, limiter
from app.schemas.common import MONEY_MAX, Page, PageNumber, PageSize
from app.schemas.public import (
    PublicCategoryNode,
    PublicProductDetail,
    PublicProductItem,
    PublicWarehouse,
)
from app.services import public as service
from app.services.public import PublicFilters

router = APIRouter(prefix="/public", tags=["public"])

CACHE_CONTROL = "public, max-age=60"
Price = Annotated[Decimal, Field(ge=0, le=MONEY_MAX)]


@router.get("/categories")
@limiter.limit(PUBLIC_LIMIT)
async def categories(
    request: Request, response: Response, session: SessionDep
) -> list[PublicCategoryNode]:
    response.headers["Cache-Control"] = CACHE_CONTROL
    return await service.category_tree(session)


@router.get("/products")
@limiter.limit(PUBLIC_LIMIT)
async def products(
    request: Request,
    response: Response,
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    category_slug: Annotated[str | None, Query(max_length=150)] = None,
    price_min: Annotated[Price | None, Query()] = None,
    price_max: Annotated[Price | None, Query()] = None,
    in_stock: bool | None = None,
    sort: Annotated[str, Query(max_length=20, description="price, -price, name, -created_at")] = (
        "-created_at"
    ),
    page: PageNumber = 1,
    page_size: PageSize = 12,
) -> Page[PublicProductItem]:
    response.headers["Cache-Control"] = CACHE_CONTROL
    filters = PublicFilters(
        q=q,
        category_slug=category_slug,
        price_min=price_min,
        price_max=price_max,
        in_stock=in_stock,
        sort=sort,
    )
    items, total = await service.list_products(session, filters, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/products/{slug}")
@limiter.limit(PUBLIC_LIMIT)
async def product(
    request: Request,
    response: Response,
    session: SessionDep,
    slug: Annotated[str, Path(max_length=255)],
) -> PublicProductDetail:
    response.headers["Cache-Control"] = CACHE_CONTROL
    return await service.get_product(session, slug)


@router.get("/warehouses")
@limiter.limit(PUBLIC_LIMIT)
async def warehouses(
    request: Request, response: Response, session: SessionDep
) -> list[PublicWarehouse]:
    response.headers["Cache-Control"] = CACHE_CONTROL
    return await service.list_warehouses(session)
