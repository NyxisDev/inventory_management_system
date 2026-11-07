from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints

from app.schemas.common import InputModel, OutputModel

CategoryName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
]
SortOrder = Annotated[int, Field(ge=0, le=1_000_000)]


class CategoryCreate(InputModel):
    name: CategoryName
    parent_id: int | None = None
    sort_order: SortOrder = 0


class CategoryUpdate(InputModel):
    """parent_id: send null to move the category to the top level."""

    name: CategoryName | None = None
    parent_id: int | None = None
    sort_order: SortOrder | None = None


class CategoryRead(OutputModel):
    id: int
    name: str
    slug: str
    parent_id: int | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class CategoryTreeNode(OutputModel):
    id: int
    name: str
    slug: str
    parent_id: int | None
    sort_order: int
    children: list["CategoryTreeNode"] = Field(default_factory=list)
