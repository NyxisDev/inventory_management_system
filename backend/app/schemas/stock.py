import uuid
from datetime import datetime
from typing import Annotated

from pydantic import StringConstraints, model_validator

from app.models import MovementType
from app.schemas.common import (
    InputModel,
    NonNegativeQuantity,
    OutputModel,
    PositiveQuantity,
    QuantityOut,
)

Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
RequiredComment = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class IncomeRequest(InputModel):
    product_id: int
    warehouse_id: int
    quantity: PositiveQuantity
    comment: Comment | None = None


class OutcomeRequest(IncomeRequest):
    pass


class AdjustmentRequest(InputModel):
    """Stock-taking: the counted quantity. The difference is written as the movement."""

    product_id: int
    warehouse_id: int
    new_quantity: NonNegativeQuantity
    comment: RequiredComment


class TransferRequest(InputModel):
    product_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: PositiveQuantity
    comment: Comment | None = None

    @model_validator(mode="after")
    def _different_warehouses(self) -> "TransferRequest":
        if self.from_warehouse_id == self.to_warehouse_id:
            raise ValueError("Source and destination warehouses must be different")
        return self


class MinQuantityRequest(InputModel):
    product_id: int
    warehouse_id: int
    min_quantity: NonNegativeQuantity


class StockRead(OutputModel):
    product_id: int
    product_sku: str
    product_name: str
    unit: str
    warehouse_id: int
    warehouse_name: str
    quantity: QuantityOut
    min_quantity: QuantityOut
    is_low_stock: bool
    updated_at: datetime


class MovementRead(OutputModel):
    id: int
    product_id: int
    product_sku: str
    product_name: str
    unit: str
    warehouse_id: int
    warehouse_name: str
    employee_id: int | None
    employee_name: str | None
    type: MovementType
    quantity_change: QuantityOut
    quantity_after: QuantityOut
    transfer_group: uuid.UUID | None
    comment: str | None
    created_at: datetime


class TransferResult(OutputModel):
    transfer_group: uuid.UUID
    transfer_out: MovementRead
    transfer_in: MovementRead
