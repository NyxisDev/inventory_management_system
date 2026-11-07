"""Stock operations: income, outcome, stock-taking, transfer, minimum quantity, history.

Each operation is one transaction. The stock row is locked with SELECT ... FOR UPDATE (and created
with 0 first if missing), so parallel operations on the same product and warehouse run one after
another and the quantity can never go below zero.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from fastapi import Request
from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import (
    AuditAction,
    Employee,
    MovementType,
    Product,
    Stock,
    StockMovement,
    Warehouse,
)
from app.schemas.common import QUANTITY_MAX
from app.schemas.stock import (
    AdjustmentRequest,
    IncomeRequest,
    MinQuantityRequest,
    MovementRead,
    OutcomeRequest,
    StockRead,
    TransferRequest,
    TransferResult,
)
from app.services.audit import log_action
from app.services.errors import ConflictError, NotFoundError
from app.services.products import is_low

NOT_ENOUGH_STOCK = "Not enough stock in this warehouse"


async def _get_active_product(session: AsyncSession, product_id: int) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise NotFoundError("Product not found")
    if product.is_archived:
        raise ConflictError("Operations with an archived product are not allowed")
    return product


async def _get_active_warehouse(session: AsyncSession, warehouse_id: int) -> Warehouse:
    warehouse = await session.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise NotFoundError("Warehouse not found")
    if not warehouse.is_active:
        raise ConflictError("Operations with an inactive warehouse are not allowed")
    return warehouse


async def _lock_stock(session: AsyncSession, product_id: int, warehouse_id: int) -> Stock:
    """Create the stock row with 0 if missing, then lock it until the transaction ends."""
    await session.execute(
        insert(Stock)
        .values(product_id=product_id, warehouse_id=warehouse_id)
        .on_conflict_do_nothing(index_elements=["product_id", "warehouse_id"])
    )
    stock = await session.scalar(
        select(Stock)
        .where(Stock.product_id == product_id, Stock.warehouse_id == warehouse_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if stock is None:  # pragma: no cover - the row was inserted above
        raise ConflictError("Stock row could not be locked")
    return stock


def _movement_read(
    movement: StockMovement, product: Product, warehouse: Warehouse, employee: Employee | None
) -> MovementRead:
    return MovementRead(
        id=movement.id,
        product_id=product.id,
        product_sku=product.sku,
        product_name=product.name,
        unit=product.unit,
        warehouse_id=warehouse.id,
        warehouse_name=warehouse.name,
        employee_id=employee.id if employee else None,
        employee_name=employee.full_name if employee else None,
        type=movement.type,
        quantity_change=movement.quantity_change,
        quantity_after=movement.quantity_after,
        transfer_group=movement.transfer_group,
        comment=movement.comment,
        created_at=movement.created_at,
    )


async def _apply(
    session: AsyncSession,
    *,
    stock: Stock,
    change: Decimal,
    movement_type: MovementType,
    actor: Employee,
    comment: str | None,
    request: Request,
    transfer_group: uuid.UUID | None = None,
) -> StockMovement:
    """Change the locked stock row, write the movement and the audit record (no commit)."""
    before = stock.quantity
    after = before + change
    if after < 0:
        raise ConflictError(NOT_ENOUGH_STOCK)
    if after > QUANTITY_MAX:
        raise ConflictError("Resulting quantity is too large")
    stock.quantity = after
    movement = StockMovement(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        employee_id=actor.id,
        type=movement_type,
        quantity_change=change,
        quantity_after=after,
        transfer_group=transfer_group,
        comment=comment or None,
    )
    session.add(movement)
    await session.flush()
    await log_action(
        session,
        employee=actor,
        action=AuditAction.stock_change,
        entity_type="stock",
        entity_id=f"{stock.product_id}:{stock.warehouse_id}",
        old_data={"quantity": before},
        new_data={"quantity": after, "type": movement_type.value, "movement_id": movement.id},
        request=request,
    )
    return movement


async def income(
    session: AsyncSession, data: IncomeRequest, actor: Employee, request: Request
) -> MovementRead:
    product = await _get_active_product(session, data.product_id)
    warehouse = await _get_active_warehouse(session, data.warehouse_id)
    stock = await _lock_stock(session, product.id, warehouse.id)
    movement = await _apply(
        session,
        stock=stock,
        change=data.quantity,
        movement_type=MovementType.income,
        actor=actor,
        comment=data.comment,
        request=request,
    )
    await session.commit()
    return _movement_read(movement, product, warehouse, actor)


async def outcome(
    session: AsyncSession, data: OutcomeRequest, actor: Employee, request: Request
) -> MovementRead:
    product = await _get_active_product(session, data.product_id)
    warehouse = await _get_active_warehouse(session, data.warehouse_id)
    stock = await _lock_stock(session, product.id, warehouse.id)
    movement = await _apply(
        session,
        stock=stock,
        change=-data.quantity,
        movement_type=MovementType.outcome,
        actor=actor,
        comment=data.comment,
        request=request,
    )
    await session.commit()
    return _movement_read(movement, product, warehouse, actor)


async def adjustment(
    session: AsyncSession, data: AdjustmentRequest, actor: Employee, request: Request
) -> MovementRead:
    product = await _get_active_product(session, data.product_id)
    warehouse = await _get_active_warehouse(session, data.warehouse_id)
    stock = await _lock_stock(session, product.id, warehouse.id)
    # The difference is recorded (it can be 0: the count confirmed the stock)
    movement = await _apply(
        session,
        stock=stock,
        change=data.new_quantity - stock.quantity,
        movement_type=MovementType.adjustment,
        actor=actor,
        comment=data.comment,
        request=request,
    )
    await session.commit()
    return _movement_read(movement, product, warehouse, actor)


async def transfer(
    session: AsyncSession, data: TransferRequest, actor: Employee, request: Request
) -> TransferResult:
    product = await _get_active_product(session, data.product_id)
    source = await _get_active_warehouse(session, data.from_warehouse_id)
    target = await _get_active_warehouse(session, data.to_warehouse_id)

    # Lock both rows in a fixed order (by warehouse id) so two opposite transfers cannot deadlock
    locked: dict[int, Stock] = {}
    for warehouse_id in sorted((source.id, target.id)):
        locked[warehouse_id] = await _lock_stock(session, product.id, warehouse_id)

    group = uuid.uuid4()
    out_movement = await _apply(
        session,
        stock=locked[source.id],
        change=-data.quantity,
        movement_type=MovementType.transfer_out,
        actor=actor,
        comment=data.comment,
        request=request,
        transfer_group=group,
    )
    in_movement = await _apply(
        session,
        stock=locked[target.id],
        change=data.quantity,
        movement_type=MovementType.transfer_in,
        actor=actor,
        comment=data.comment,
        request=request,
        transfer_group=group,
    )
    await session.commit()
    return TransferResult(
        transfer_group=group,
        transfer_out=_movement_read(out_movement, product, source, actor),
        transfer_in=_movement_read(in_movement, product, target, actor),
    )


async def set_min_quantity(
    session: AsyncSession, data: MinQuantityRequest, actor: Employee, request: Request
) -> StockRead:
    product = await session.get(Product, data.product_id)
    if product is None:
        raise NotFoundError("Product not found")
    warehouse = await session.get(Warehouse, data.warehouse_id)
    if warehouse is None:
        raise NotFoundError("Warehouse not found")
    stock = await _lock_stock(session, product.id, warehouse.id)
    old_value = stock.min_quantity
    stock.min_quantity = data.min_quantity
    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="stock",
        entity_id=f"{product.id}:{warehouse.id}",
        old_data={"min_quantity": old_value},
        new_data={"min_quantity": data.min_quantity},
        request=request,
    )
    await session.commit()
    await session.refresh(stock)
    return _stock_read(stock, product, warehouse)


def _stock_read(stock: Stock, product: Product, warehouse: Warehouse) -> StockRead:
    return StockRead(
        product_id=product.id,
        product_sku=product.sku,
        product_name=product.name,
        unit=product.unit,
        warehouse_id=warehouse.id,
        warehouse_name=warehouse.name,
        quantity=stock.quantity,
        min_quantity=stock.min_quantity,
        is_low_stock=warehouse.is_active and is_low(stock.quantity, stock.min_quantity),
        updated_at=stock.updated_at,
    )


async def list_stock(
    session: AsyncSession, *, product_id: int | None, warehouse_id: int | None
) -> list[StockRead]:
    stmt = (
        select(Stock, Product, Warehouse)
        .join(Product, Product.id == Stock.product_id)
        .join(Warehouse, Warehouse.id == Stock.warehouse_id)
        .order_by(Product.name, Warehouse.name)
    )
    if product_id is not None:
        stmt = stmt.where(Stock.product_id == product_id)
    if warehouse_id is not None:
        stmt = stmt.where(Stock.warehouse_id == warehouse_id)
    rows = (await session.execute(stmt.limit(1000))).tuples().all()
    return [_stock_read(stock, product, warehouse) for stock, product, warehouse in rows]


@dataclass(frozen=True, slots=True)
class MovementFilters:
    product_id: int | None = None
    warehouse_id: int | None = None
    employee_id: int | None = None
    type: MovementType | None = None
    date_from: datetime | date | None = None
    date_to: datetime | date | None = None


def _start(value: datetime | date) -> datetime:
    """A datetime as is; a plain date means the start of that day in UTC."""
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min, tzinfo=UTC)


def _apply_movement_filters(
    stmt: Select[tuple[StockMovement]], filters: MovementFilters
) -> Select[tuple[StockMovement]]:
    if filters.product_id is not None:
        stmt = stmt.where(StockMovement.product_id == filters.product_id)
    if filters.warehouse_id is not None:
        stmt = stmt.where(StockMovement.warehouse_id == filters.warehouse_id)
    if filters.employee_id is not None:
        stmt = stmt.where(StockMovement.employee_id == filters.employee_id)
    if filters.type is not None:
        stmt = stmt.where(StockMovement.type == filters.type)
    if filters.date_from is not None:
        stmt = stmt.where(StockMovement.created_at >= _start(filters.date_from))
    if filters.date_to is not None:
        if isinstance(filters.date_to, datetime):
            stmt = stmt.where(StockMovement.created_at <= filters.date_to)
        else:  # a whole day: up to the start of the next day
            stmt = stmt.where(
                StockMovement.created_at < _start(filters.date_to + timedelta(days=1))
            )
    return stmt


async def list_movements(
    session: AsyncSession, filters: MovementFilters, page: int, page_size: int
) -> tuple[list[MovementRead], int]:
    base = _apply_movement_filters(select(StockMovement), filters)
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.scalars(
        base.options(
            joinedload(StockMovement.product),
            joinedload(StockMovement.warehouse),
            joinedload(StockMovement.employee),
        )
        .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = [
        _movement_read(movement, movement.product, movement.warehouse, movement.employee)
        for movement in rows.all()
    ]
    return items, total
