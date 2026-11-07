"""Shared schema pieces: base models, money and quantity types, pagination."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

MONEY_STEP = Decimal("0.01")
QUANTITY_STEP = Decimal("0.001")
# NUMERIC(12,2) and NUMERIC(14,3) limits
MONEY_MAX = Decimal("9999999999.99")
QUANTITY_MAX = Decimal("99999999999.999")


class InputModel(BaseModel):
    """Request body: unknown fields are rejected, strings are stripped."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _money_to_str(value: Decimal) -> str:
    return str(value.quantize(MONEY_STEP))


def _quantity_to_str(value: Decimal) -> str:
    return str(value.quantize(QUANTITY_STEP))


# Output types: always decimal strings with a fixed scale ("12.50", "9.150"), never floats.
MoneyOut = Annotated[Decimal, PlainSerializer(_money_to_str, return_type=str)]
QuantityOut = Annotated[Decimal, PlainSerializer(_quantity_to_str, return_type=str)]

# Input types
MoneyIn = Annotated[Decimal, Field(ge=0, le=MONEY_MAX, max_digits=12, decimal_places=2)]
PositiveQuantity = Annotated[Decimal, Field(gt=0, le=QUANTITY_MAX, max_digits=14, decimal_places=3)]
NonNegativeQuantity = Annotated[
    Decimal, Field(ge=0, le=QUANTITY_MAX, max_digits=14, decimal_places=3)
]

PageNumber = Annotated[int, Field(ge=1, le=100_000)]
PageSize = Annotated[int, Field(ge=1, le=100)]


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    detail: str
