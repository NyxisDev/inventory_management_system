from datetime import datetime
from typing import Annotated

from pydantic import StringConstraints

from app.schemas.common import InputModel, OutputModel

WarehouseName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
]
Address = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class WarehouseCreate(InputModel):
    name: WarehouseName
    address: Address | None = None
    is_active: bool = True
    show_on_site: bool = True


class WarehouseUpdate(InputModel):
    """address: send null to clear it."""

    name: WarehouseName | None = None
    address: Address | None = None
    is_active: bool | None = None
    show_on_site: bool | None = None


class WarehouseRead(OutputModel):
    id: int
    name: str
    address: str | None
    is_active: bool
    show_on_site: bool
    created_at: datetime
    updated_at: datetime
