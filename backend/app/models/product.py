from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_column, updated_at_column

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.employee import Employee
    from app.models.stock import Stock


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="products_price_check"),
        Index("ix_products_category", "category_id"),
        Index(
            "ix_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_sku_trgm",
            "sku",
            postgresql_using="gin",
            postgresql_ops={"sku": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Used in the site URL: /product/<slug>
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)  # sanitized HTML
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL")
    )
    # pcs, kg, m, m², m³, l, pack
    unit: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'pcs'"))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL")
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    category: Mapped[Category | None] = relationship(back_populates="products")
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        order_by="(ProductImage.is_main.desc(), ProductImage.sort_order, ProductImage.id)",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    stock: Mapped[list[Stock]] = relationship(
        back_populates="product", cascade="all, delete-orphan", passive_deletes=True
    )
    creator: Mapped[Employee | None] = relationship(foreign_keys=[created_by])
    updater: Mapped[Employee | None] = relationship(foreign_keys=[updated_by])


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        # At most one main image per product
        Index(
            "ux_product_images_main", "product_id", unique=True, postgresql_where=text("is_main")
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = created_at_column()

    product: Mapped[Product] = relationship(back_populates="images")
