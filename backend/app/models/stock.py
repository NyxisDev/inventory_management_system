from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_column, updated_at_column
from app.models.enums import MovementType, movement_type_type

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.product import Product
    from app.models.warehouse import Warehouse


class Stock(Base):
    """Current quantity of a product in a warehouse. Changed only by stock operations."""

    __tablename__ = "stock"
    __table_args__ = (CheckConstraint("quantity >= 0", name="stock_quantity_check"),)

    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), primary_key=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, server_default=text("0")
    )
    # At or below this value the product is "low stock"
    min_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, server_default=text("0")
    )
    updated_at: Mapped[datetime] = updated_at_column()

    product: Mapped[Product] = relationship(back_populates="stock")
    warehouse: Mapped[Warehouse] = relationship(back_populates="stock")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_movements_product", "product_id", text("created_at DESC")),
        Index("ix_movements_warehouse", "warehouse_id", text("created_at DESC")),
        Index("ix_movements_employee", "employee_id", text("created_at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    employee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL")
    )
    type: Mapped[MovementType] = mapped_column(movement_type_type, nullable=False)
    # Positive = came in, negative = went out
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    # Links a transfer_out with its transfer_in
    transfer_group: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = created_at_column()

    product: Mapped[Product] = relationship()
    warehouse: Mapped[Warehouse] = relationship()
    employee: Mapped[Employee | None] = relationship()
