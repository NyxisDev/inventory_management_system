"""Public catalog: only published, non-archived products and only warehouses that are active and
shown on the site."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Product, Stock, Warehouse
from app.schemas.public import (
    PublicCategoryNode,
    PublicCategoryParent,
    PublicCategoryRef,
    PublicImage,
    PublicImageFull,
    PublicProductDetail,
    PublicProductItem,
    PublicStock,
    PublicWarehouse,
)
from app.services import media
from app.services.errors import NotFoundError
from app.services.query import escape_like, order_by_from_sort

ZERO = Decimal("0")

VISIBLE_PRODUCT = and_(Product.is_published.is_(True), Product.is_archived.is_(False))
VISIBLE_WAREHOUSE = and_(Warehouse.is_active.is_(True), Warehouse.show_on_site.is_(True))


def _visible_totals():
    return (
        select(Stock.product_id.label("product_id"), func.sum(Stock.quantity).label("total"))
        .join(Warehouse, Warehouse.id == Stock.warehouse_id)
        .where(VISIBLE_WAREHOUSE)
        .group_by(Stock.product_id)
        .subquery("visible_totals")
    )


async def _all_categories(session: AsyncSession) -> list[Category]:
    rows = await session.scalars(
        select(Category).order_by(Category.sort_order, Category.name, Category.id)
    )
    return list(rows.all())


def _descendant_ids(categories: list[Category], root_id: int) -> set[int]:
    children: dict[int | None, list[int]] = {}
    for category in categories:
        children.setdefault(category.parent_id, []).append(category.id)
    result: set[int] = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(children.get(current, []))
    return result


async def category_tree(session: AsyncSession) -> list[PublicCategoryNode]:
    """Only categories that contain published products (directly or in subcategories)."""
    categories = await _all_categories(session)
    direct = dict(
        (
            await session.execute(
                select(Product.category_id, func.count())
                .where(VISIBLE_PRODUCT, Product.category_id.is_not(None))
                .group_by(Product.category_id)
            )
        )
        .tuples()
        .all()
    )
    by_id = {category.id: category for category in categories}
    children: dict[int | None, list[Category]] = {}
    for category in categories:
        parent = category.parent_id if category.parent_id in by_id else None
        children.setdefault(parent, []).append(category)

    def build(parent_id: int | None, path: frozenset[int]) -> list[PublicCategoryNode]:
        nodes: list[PublicCategoryNode] = []
        for category in children.get(parent_id, []):
            if category.id in path:  # defensive: never loop on a broken tree
                continue
            sub = build(category.id, path | {category.id})
            count = direct.get(category.id, 0) + sum(node.product_count for node in sub)
            if count > 0:
                nodes.append(
                    PublicCategoryNode(
                        id=category.id,
                        name=category.name,
                        slug=category.slug,
                        product_count=count,
                        children=sub,
                    )
                )
        return nodes

    return build(None, frozenset())


def _category_ref(category: Category | None) -> PublicCategoryRef | None:
    if category is None:
        return None
    parent = category.parent
    return PublicCategoryRef(
        name=category.name,
        slug=category.slug,
        parent=PublicCategoryParent(name=parent.name, slug=parent.slug) if parent else None,
    )


def _item(product: Product, total: Decimal | None) -> PublicProductItem:
    main = product.images[0] if product.images else None  # ordered main-first
    return PublicProductItem(
        id=product.id,
        slug=product.slug,
        sku=product.sku,
        name=product.name,
        price=product.price,
        unit=product.unit,
        category=_category_ref(product.category),
        main_image=(
            PublicImage(
                url=media.file_url(main.file_path), thumb_url=media.thumb_url(main.file_path)
            )
            if main
            else None
        ),
        total_quantity=total or ZERO,
        created_at=product.created_at,
    )


_PRODUCT_OPTIONS = (
    selectinload(Product.images),
    selectinload(Product.category).selectinload(Category.parent),
)


@dataclass(frozen=True, slots=True)
class PublicFilters:
    q: str | None = None
    category_slug: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    in_stock: bool | None = None
    sort: str = "-created_at"


async def list_products(
    session: AsyncSession, filters: PublicFilters, page: int, page_size: int
) -> tuple[list[PublicProductItem], int]:
    totals = _visible_totals()
    stmt: Select[Any] = (
        select(Product, totals.c.total)
        .outerjoin(totals, totals.c.product_id == Product.id)
        .where(VISIBLE_PRODUCT)
    )
    if filters.q:
        pattern = f"%{escape_like(filters.q)}%"
        stmt = stmt.where(
            or_(Product.name.ilike(pattern, escape="\\"), Product.sku.ilike(pattern, escape="\\"))
        )
    if filters.category_slug:
        categories = await _all_categories(session)
        root = next((c for c in categories if c.slug == filters.category_slug), None)
        if root is None:
            raise NotFoundError("Category not found")
        stmt = stmt.where(Product.category_id.in_(_descendant_ids(categories, root.id)))
    if filters.price_min is not None:
        stmt = stmt.where(Product.price >= filters.price_min)
    if filters.price_max is not None:
        stmt = stmt.where(Product.price <= filters.price_max)
    if filters.in_stock:
        stmt = stmt.where(totals.c.total > 0)

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = order_by_from_sort(
        filters.sort,
        {"price": Product.price, "name": Product.name, "created_at": Product.created_at},
    )
    rows = (
        await session.execute(
            stmt.order_by(*order, Product.id.desc())
            .options(*_PRODUCT_OPTIONS)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()
    return [_item(row[0], row[1]) for row in rows], total


async def get_product(session: AsyncSession, slug: str) -> PublicProductDetail:
    product = await session.scalar(
        select(Product).where(Product.slug == slug, VISIBLE_PRODUCT).options(*_PRODUCT_OPTIONS)
    )
    if product is None:
        raise NotFoundError("Product not found")

    # Every warehouse shown on the site, also those with 0
    rows = (
        (
            await session.execute(
                select(Warehouse.name, Warehouse.address, func.coalesce(Stock.quantity, 0))
                .outerjoin(
                    Stock, and_(Stock.warehouse_id == Warehouse.id, Stock.product_id == product.id)
                )
                .where(VISIBLE_WAREHOUSE)
                .order_by(Warehouse.name)
            )
        )
        .tuples()
        .all()
    )
    stock = [
        PublicStock(warehouse_name=name, address=address, quantity=Decimal(quantity))
        for name, address, quantity in rows
    ]
    total = sum((row.quantity for row in stock), ZERO)
    item = _item(product, total)
    return PublicProductDetail(
        **item.model_dump(),
        description=product.description,
        images=[
            PublicImageFull(
                url=media.file_url(image.file_path),
                thumb_url=media.thumb_url(image.file_path),
                is_main=image.is_main,
            )
            for image in product.images
        ],
        stock=stock,
    )


async def list_warehouses(session: AsyncSession) -> list[PublicWarehouse]:
    rows = (
        (
            await session.execute(
                select(Warehouse.name, Warehouse.address)
                .where(VISIBLE_WAREHOUSE)
                .order_by(Warehouse.name)
            )
        )
        .tuples()
        .all()
    )
    return [PublicWarehouse(name=name, address=address) for name, address in rows]
