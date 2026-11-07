"""Query helpers: pagination, LIKE escaping, sort allow-lists."""

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.services.errors import BadRequestError


def escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input is matched literally (escape char: backslash)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def paginate[T](
    session: AsyncSession, stmt: Select[tuple[T]], page: int, page_size: int
) -> tuple[list[T], int]:
    total_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = await session.scalar(total_stmt) or 0
    rows = await session.scalars(stmt.limit(page_size).offset((page - 1) * page_size))
    return list(rows.unique().all()), total


def order_by_from_sort(
    sort: str, allowed: dict[str, ColumnElement[Any] | Any]
) -> list[ColumnElement[Any]]:
    """Turn "price" / "-price" into ORDER BY, accepting only fields from the allow-list."""
    descending = sort.startswith("-")
    field = sort[1:] if descending else sort
    column = allowed.get(field)
    if column is None:
        options = ", ".join(sorted(allowed))
        raise BadRequestError(f"Invalid sort field. Allowed: {options} (prefix with - to reverse)")
    return [column.desc().nulls_last() if descending else column.asc().nulls_last()]
