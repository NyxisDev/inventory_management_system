from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from app.schemas.common import InputModel, MoneyIn, MoneyOut, OutputModel, QuantityOut

Unit = Literal["pcs", "kg", "m", "m²", "m³", "l", "pack"]
Sku = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]*$"
    ),
]
ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
# Raw HTML from the editor; sanitized with bleach before saving
Description = Annotated[str, Field(max_length=50_000)]


class ProductCreate(InputModel):
    sku: Sku
    name: ProductName
    description: Description | None = None
    category_id: int | None = None
    unit: Unit = "pcs"
    price: MoneyIn
    is_published: bool = False


class ProductUpdate(InputModel):
    """description / category_id: send null to clear."""

    sku: Sku | None = None
    name: ProductName | None = None
    description: Description | None = None
    category_id: int | None = None
    unit: Unit | None = None
    price: MoneyIn | None = None
    is_published: bool | None = None
    is_archived: bool | None = None


class ImageRead(OutputModel):
    id: int
    url: str
    thumb_url: str
    is_main: bool
    sort_order: int


class ImageUpdate(InputModel):
    # Only "make this the main image"; the previous main image is unset automatically
    is_main: Literal[True] | None = None
    sort_order: Annotated[int, Field(ge=0, le=1_000_000)] | None = None


class StockRow(OutputModel):
    warehouse_id: int
    warehouse_name: str
    warehouse_is_active: bool
    quantity: QuantityOut
    min_quantity: QuantityOut
    is_low_stock: bool


class ProductListItem(OutputModel):
    id: int
    sku: str
    name: str
    slug: str
    category_id: int | None
    category_name: str | None
    unit: str
    price: MoneyOut
    is_published: bool
    is_archived: bool
    main_image: ImageRead | None
    total_quantity: QuantityOut
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime


class ProductRead(ProductListItem):
    description: str | None
    created_by: int | None
    updated_by: int | None
    images: list[ImageRead]
    stock: list[StockRow]


class ProductDeleteResult(OutputModel):
    result: Literal["deleted", "archived"]
    detail: str
