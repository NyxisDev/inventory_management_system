"""Unique slugs from names (Cyrillic is transliterated by python-slugify)."""

from typing import Any

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.services.query import escape_like


async def unique_slug(
    session: AsyncSession,
    column: InstrumentedAttribute[Any],
    name: str,
    *,
    max_length: int,
    fallback: str,
    exclude_id: int | None = None,
    id_column: InstrumentedAttribute[Any] | None = None,
) -> str:
    """slugify(name), then "-2", "-3", ... if the slug is already taken."""
    base = slugify(name, max_length=max_length - 6, word_boundary=True) or fallback
    stmt = select(column).where(column.like(f"{escape_like(base)}%", escape="\\"))
    if exclude_id is not None and id_column is not None:
        stmt = stmt.where(id_column != exclude_id)
    taken = set((await session.scalars(stmt)).all())
    if base not in taken:
        return base
    number = 2
    while f"{base}-{number}" in taken:
        number += 1
    return f"{base}-{number}"
