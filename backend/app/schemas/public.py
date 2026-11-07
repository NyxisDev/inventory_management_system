"""Public catalog API (no sign-in). Shapes follow docs/public-api.md.

Service fields are never exposed: created_by, updated_by, min_quantity, is_archived, employee ids.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import MoneyOut, QuantityOut


class PublicCategoryParent(BaseModel):
    name: str
    slug: str


class PublicCategoryRef(BaseModel):
    name: str
    slug: str
    parent: PublicCategoryParent | None


class PublicImage(BaseModel):
    url: str
    thumb_url: str


class PublicImageFull(PublicImage):
    is_main: bool


class PublicProductItem(BaseModel):
    id: int
    slug: str
    sku: str
    name: str
    price: MoneyOut
    unit: str
    category: PublicCategoryRef | None
    main_image: PublicImage | None
    total_quantity: QuantityOut
    created_at: datetime


class PublicStock(BaseModel):
    warehouse_name: str
    address: str | None
    quantity: QuantityOut


class PublicProductDetail(PublicProductItem):
    description: str | None
    images: list[PublicImageFull]
    stock: list[PublicStock]


class PublicCategoryNode(BaseModel):
    id: int
    name: str
    slug: str
    product_count: int
    children: list["PublicCategoryNode"] = Field(default_factory=list)


class PublicWarehouse(BaseModel):
    name: str
    address: str | None
