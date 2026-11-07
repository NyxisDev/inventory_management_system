"""Products: staff and admin."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentEmployee, SessionDep, get_current_employee
from app.schemas.common import Page, PageNumber, PageSize
from app.schemas.product import (
    ProductCreate,
    ProductDeleteResult,
    ProductListItem,
    ProductRead,
    ProductUpdate,
)
from app.services import products as service
from app.services.products import ProductFilters

router = APIRouter(
    prefix="/products", tags=["products"], dependencies=[Depends(get_current_employee)]
)


@router.get("")
async def list_products(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    category_id: int | None = None,
    warehouse_id: int | None = None,
    is_published: bool | None = None,
    is_archived: bool | None = False,
    low_stock: bool | None = None,
    sort: Annotated[str, Query(max_length=20, description="name, price, created_at, ...; -x")] = (
        "-created_at"
    ),
    page: PageNumber = 1,
    page_size: PageSize = 20,
) -> Page[ProductListItem]:
    filters = ProductFilters(
        q=q,
        category_id=category_id,
        warehouse_id=warehouse_id,
        is_published=is_published,
        is_archived=is_archived,
        low_stock=low_stock,
        sort=sort,
    )
    items, total = await service.list_products(session, filters, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}")
async def get_product(product_id: int, session: SessionDep) -> ProductRead:
    return await service.get_product(session, product_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request, data: ProductCreate, session: SessionDep, employee: CurrentEmployee
) -> ProductRead:
    return await service.create_product(session, data, employee, request)


@router.patch("/{product_id}")
async def update_product(
    request: Request,
    product_id: int,
    data: ProductUpdate,
    session: SessionDep,
    employee: CurrentEmployee,
) -> ProductRead:
    return await service.update_product(session, product_id, data, employee, request)


@router.delete("/{product_id}")
async def delete_product(
    request: Request, product_id: int, session: SessionDep, employee: CurrentEmployee
) -> ProductDeleteResult:
    outcome = await service.delete_product(session, product_id, employee, request)
    if outcome == "archived":
        return ProductDeleteResult(
            result="archived",
            detail="The product has stock movements, so it was archived instead of deleted",
        )
    return ProductDeleteResult(result="deleted", detail="Product deleted")
