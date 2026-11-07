"""Categories (staff and admin). Nested via parent_id."""

from fastapi import Request
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, Category, Employee, Product
from app.schemas.category import CategoryCreate, CategoryTreeNode, CategoryUpdate
from app.services.audit import CATEGORY_FIELDS, log_action, snapshot
from app.services.errors import ConflictError, NotFoundError
from app.services.slugs import unique_slug

SLUG_MAX_LENGTH = 150


async def list_categories(session: AsyncSession) -> list[Category]:
    rows = await session.scalars(
        select(Category).order_by(Category.sort_order, Category.name, Category.id)
    )
    return list(rows.all())


def build_tree(categories: list[Category]) -> list[CategoryTreeNode]:
    nodes = {
        category.id: CategoryTreeNode(
            id=category.id,
            name=category.name,
            slug=category.slug,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            children=[],
        )
        for category in categories
    }
    roots: list[CategoryTreeNode] = []
    for category in categories:  # already sorted, so children keep the order
        node = nodes[category.id]
        parent = nodes.get(category.parent_id) if category.parent_id is not None else None
        if parent is None:
            roots.append(node)
        else:
            parent.children.append(node)
    return roots


async def get_category(session: AsyncSession, category_id: int) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category not found")
    return category


async def _check_parent(session: AsyncSession, category_id: int | None, parent_id: int) -> None:
    """The parent must exist and must not be the category itself or one of its descendants."""
    parents = dict((await session.execute(select(Category.id, Category.parent_id))).tuples().all())
    if parent_id not in parents:
        raise NotFoundError("Parent category not found")
    current: int | None = parent_id
    seen: set[int] = set()
    while current is not None and current not in seen:
        if current == category_id:
            raise ConflictError("A category cannot be moved inside itself")
        seen.add(current)
        current = parents.get(current)


async def create_category(
    session: AsyncSession, data: CategoryCreate, actor: Employee, request: Request
) -> Category:
    if data.parent_id is not None:
        await _check_parent(session, None, data.parent_id)
    category = Category(
        name=data.name,
        slug=await unique_slug(
            session, Category.slug, data.name, max_length=SLUG_MAX_LENGTH, fallback="category"
        ),
        parent_id=data.parent_id,
        sort_order=data.sort_order,
    )
    session.add(category)
    await session.flush()
    await log_action(
        session,
        employee=actor,
        action=AuditAction.create,
        entity_type="category",
        entity_id=category.id,
        new_data=snapshot(category, CATEGORY_FIELDS),
        label=category.name,
        request=request,
    )
    await session.commit()
    return category


async def update_category(
    session: AsyncSession,
    category_id: int,
    data: CategoryUpdate,
    actor: Employee,
    request: Request,
) -> Category:
    category = await get_category(session, category_id)
    before = snapshot(category, CATEGORY_FIELDS)
    fields = data.model_fields_set

    if "parent_id" in fields and data.parent_id != category.parent_id:
        if data.parent_id is not None:
            await _check_parent(session, category.id, data.parent_id)
        category.parent_id = data.parent_id
    if data.name is not None and data.name != category.name:
        category.name = data.name
        category.slug = await unique_slug(
            session,
            Category.slug,
            data.name,
            max_length=SLUG_MAX_LENGTH,
            fallback="category",
            exclude_id=category.id,
            id_column=Category.id,
        )
    if data.sort_order is not None:
        category.sort_order = data.sort_order

    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="category",
        entity_id=category.id,
        old_data=before,
        new_data=snapshot(category, CATEGORY_FIELDS),
        label=category.name,
        request=request,
    )
    await session.commit()
    return category


async def delete_category(
    session: AsyncSession, category_id: int, actor: Employee, request: Request
) -> None:
    category = await get_category(session, category_id)
    has_products = await session.scalar(select(exists().where(Product.category_id == category.id)))
    if has_products:
        raise ConflictError("Category has products and cannot be deleted")
    has_children = await session.scalar(select(exists().where(Category.parent_id == category.id)))
    if has_children:
        raise ConflictError("Category has subcategories and cannot be deleted")

    await log_action(
        session,
        employee=actor,
        action=AuditAction.delete,
        entity_type="category",
        entity_id=category.id,
        old_data=snapshot(category, CATEGORY_FIELDS),
        label=category.name,
        request=request,
    )
    await session.delete(category)
    await session.commit()
