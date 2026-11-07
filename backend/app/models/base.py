from datetime import datetime
from types import MappingProxyType

from sqlalchemy import DateTime, FetchedValue, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # Fetch server-generated values (id, created_at, trigger-updated updated_at) with RETURNING,
    # so no lazy load is needed in async code.
    __mapper_args__ = MappingProxyType({"eager_defaults": True})


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


def updated_at_column() -> Mapped[datetime]:
    # The value is set by the set_updated_at() trigger on every UPDATE.
    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=FetchedValue(),
    )
