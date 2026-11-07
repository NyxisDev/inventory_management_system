"""Products (staff and admin): list with filters, details, create, update, delete or archive."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy import Select, and_, exists, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.models import AuditAction, Category, Employee, Product, Stock, StockMovement, Warehouse
from app.schemas.product import (
    ImageRead,
    ProductCreate,
    ProductListItem,
    ProductRead,
    ProductUpdate,
    StockRow,
)
from app.services import media
from app.services.audit import log_action
from app.services.errors import ConflictError, NotFoundError
from app.services.query import escape_like, order_by_from_sort
from app.services.sanitize import clean_description
from app.services.slugs import unique_slug

SLUG_MAX_LENGTH = 255
ZERO = Decimal("0")


def is_low(quantity: Decimal, min_quantity: Decimal) -> bool:
    """min_quantity 0 means "not tracked"; otherwise low when at or below the minimum."""
    return min_quantity > 0 and quantity <= min_quantity


def _stock_totals():
    """Per product: total quantity over all warehouses and whether any active one is low."""
    low_condition = and_(
        Warehouse.is_active.is_(True),
        Stock.min_quantity > 0,
        Stock.quantity <= Stock.min_quantity,
    )
    return (
        select(
            Stock.product_id.label("product_id"),
            func.sum(Stock.quantity).label("total"),
            func.bool_or(low_condition).label("low"),
        )
        .join(Warehouse, Warehouse.id == Stock.warehouse_id)
        .group_by(Stock.product_id)
        .subquery("stock_totals")
    )


def image_read(image: Any) -> ImageRead:
    return ImageRead(
        id=image.id,
        url=media.file_url(image.file_path),
        thumb_url=media.thumb_url(image.file_path),
        is_main=image.is_main,
        sort_order=image.sort_order,
    )


def _list_item(product: Product, total: Decimal | None, low: bool | None) -> ProductListItem:
    main = product.images[0] if product.images else None  # relationship is ordered main-first
    return ProductListItem(
        id=product.id,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        unit=product.unit,
        price=product.price,
        is_published=product.is_published,
        is_archived=product.is_archived,
        main_image=image_read(main) if main else None,
        total_quantity=total or ZERO,
        is_low_stock=bool(low),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@dataclass(frozen=True, slots=True)
class ProductFilters:
    q: str | None = None
    category_id: int | None = None
    warehouse_id: int | None = None
    is_published: bool | None = None
    is_archived: bool | None = False
    low_stock: bool | None = None
    sort: str = "-created_at"


async def list_products(
    session: AsyncSession, filters: ProductFilters, page: int, page_size: int
) -> tuple[list[ProductListItem], int]:
    totals = _stock_totals()
    stmt: Select[Any] = select(
        Product, totals.c.total, func.coalesce(totals.c.low, false()).label("low")
    ).outerjoin(totals, totals.c.product_id == Product.id)

    if filters.q:
        pattern = f"%{escape_like(filters.q)}%"
        stmt = stmt.where(
            or_(Product.name.ilike(pattern, escape="\\"), Product.sku.ilike(pattern, escape="\\"))
        )
    if filters.category_id is not None:
        stmt = stmt.where(Product.category_id == filters.category_id)
    if filters.warehouse_id is not None:
        stmt = stmt.where(
            exists().where(
                Stock.product_id == Product.id, Stock.warehouse_id == filters.warehouse_id
            )
        )
    if filters.is_published is not None:
        stmt = stmt.where(Product.is_published == filters.is_published)
    if filters.is_archived is not None:
        stmt = stmt.where(Product.is_archived == filters.is_archived)
    if filters.low_stock is True:
        stmt = stmt.where(totals.c.low.is_(True))
    elif filters.low_stock is False:
        stmt = stmt.where(func.coalesce(totals.c.low, false()).is_(False))

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    order = order_by_from_sort(
        filters.sort,
        {
            "name": Product.name,
            "sku": Product.sku,
            "price": Product.price,
            "created_at": Product.created_at,
            "updated_at": Product.updated_at,
            "total_quantity": func.coalesce(totals.c.total, 0),
        },
    )
    stmt = (
        stmt.order_by(*order, Product.id.desc())
        .options(selectinload(Product.images), selectinload(Product.category))
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    rows = (await session.execute(stmt)).all()
    return [_list_item(row[0], row[1], row[2]) for row in rows], total


async def get_product_model(session: AsyncSession, product_id: int) -> Product:
    product = await session.scalar(
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.images), selectinload(Product.category))
    )
    if product is None:
        raise NotFoundError("Product not found")
    return product


async def get_product(session: AsyncSession, product_id: int) -> ProductRead:
    product = await get_product_model(session, product_id)

    # Every active warehouse (0 if there is no stock row yet) plus inactive ones that hold stock
    rows = (
        await session.execute(
            select(Warehouse, Stock)
            .outerjoin(
                Stock, and_(Stock.warehouse_id == Warehouse.id, Stock.product_id == product.id)
            )
            .where(or_(Warehouse.is_active.is_(True), Stock.product_id.is_not(None)))
            .order_by(Warehouse.name, Warehouse.id)
        )
    ).all()
    stock: list[StockRow] = []
    total = ZERO
    low = False
    for warehouse, row in rows:
        quantity = row.quantity if row else ZERO
        min_quantity = row.min_quantity if row else ZERO
        row_low = warehouse.is_active and is_low(quantity, min_quantity)
        total += quantity
        low = low or row_low
        stock.append(
            StockRow(
                warehouse_id=warehouse.id,
                warehouse_name=warehouse.name,
                warehouse_is_active=warehouse.is_active,
                quantity=quantity,
                min_quantity=min_quantity,
                is_low_stock=row_low,
            )
        )

    item = _list_item(product, total, low)
    return ProductRead(
        **item.model_dump(),
        description=product.description,
        created_by=product.created_by,
        updated_by=product.updated_by,
        images=[image_read(image) for image in product.images],
        stock=stock,
    )


async def _check_category(session: AsyncSession, category_id: int | None) -> None:
    if category_id is not None and await session.get(Category, category_id) is None:
        raise NotFoundError("Category not found")


async def _ensure_sku_free(session: AsyncSession, sku: str, exclude_id: int | None) -> None:
    stmt = select(Product.id).where(Product.sku == sku)
    if exclude_id is not None:
        stmt = stmt.where(Product.id != exclude_id)
    if await session.scalar(stmt) is not None:
        raise ConflictError("A product with this SKU already exists")


async def create_product(
    session: AsyncSession, data: ProductCreate, actor: Employee, request: Request
) -> ProductRead:
    await _ensure_sku_free(session, data.sku, None)
    await _check_category(session, data.category_id)
    product = Product(
        sku=data.sku,
        name=data.name,
        slug=await unique_slug(
            session, Product.slug, data.name, max_length=SLUG_MAX_LENGTH, fallback="product"
        ),
        description=clean_description(data.description),
        category_id=data.category_id,
        unit=data.unit,
        price=data.price,
        is_published=data.is_published,
        created_by=actor.id,
        updated_by=actor.id,
    )
    session.add(product)
    await session.flush()
    await log_action(
        session,
        employee=actor,
        action=AuditAction.create,
        entity_type="product",
        entity_id=product.id,
        request=request,
    )
    await session.commit()
    return await get_product(session, product.id)


async def update_product(
    session: AsyncSession,
    product_id: int,
    data: ProductUpdate,
    actor: Employee,
    request: Request,
) -> ProductRead:
    product = await get_product_model(session, product_id)
    fields = data.model_fields_set

    if data.sku is not None and data.sku != product.sku:
        await _ensure_sku_free(session, data.sku, product.id)
        product.sku = data.sku
    if data.name is not None and data.name != product.name:
        product.name = data.name
        product.slug = await unique_slug(
            session,
            Product.slug,
            data.name,
            max_length=SLUG_MAX_LENGTH,
            fallback="product",
            exclude_id=product.id,
            id_column=Product.id,
        )
    if "description" in fields:
        product.description = clean_description(data.description)
    if "category_id" in fields and data.category_id != product.category_id:
        await _check_category(session, data.category_id)
        product.category_id = data.category_id
    if data.unit is not None:
        product.unit = data.unit
    if data.price is not None:
        product.price = data.price
    if data.is_archived is not None:
        product.is_archived = data.is_archived
        if data.is_archived:
            product.is_published = False
    if data.is_published is not None:
        if data.is_published and product.is_archived:
            raise ConflictError("An archived product cannot be published")
        product.is_published = data.is_published

    product.updated_by = actor.id
    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="product",
        entity_id=product.id,
        request=request,
    )
    await session.commit()
    return await get_product(session, product.id)


async def delete_product(
    session: AsyncSession, product_id: int, actor: Employee, request: Request
) -> str:
    """Archive a product that has stock movements, delete it otherwise. Returns the outcome."""
    product = await get_product_model(session, product_id)
    has_movements = await session.scalar(
        select(exists().where(StockMovement.product_id == product.id))
    )
    if has_movements:
        product.is_archived = True
        product.is_published = False
        product.updated_by = actor.id
        await log_action(
            session,
            employee=actor,
            action=AuditAction.update,
            entity_type="product",
            entity_id=product.id,
            request=request,
        )
        await session.commit()
        return "archived"

    await log_action(
        session,
        employee=actor,
        action=AuditAction.delete,
        entity_type="product",
        entity_id=product.id,
        request=request,
    )
    await session.delete(product)
    await session.commit()
    await run_in_threadpool(media.delete_product_dir, product_id)
    return "deleted"
