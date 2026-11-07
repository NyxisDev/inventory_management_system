"""Reading the audit log: filters, the ready-made "changes" table, English summaries, CSV export."""

import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog
from app.schemas.audit import AuditChange, AuditRead
from app.services.audit import LABEL_KEY
from app.services.query import escape_like

CSV_MAX_ROWS = 50_000
SUMMARY_VALUE_MAX = 60
ENTITY_NAMES = {
    "product": "product",
    "employee": "employee",
    "category": "category",
    "warehouse": "warehouse",
    "product_image": "photo",
    "stock": "stock",
    "auth": "session",
}
# Cells starting with these characters could run as formulas in Excel / LibreOffice
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


@dataclass(frozen=True, slots=True)
class AuditFilters:
    employee_id: int | None = None
    action: AuditAction | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    date_from: datetime | date | None = None
    date_to: datetime | date | None = None
    q: str | None = None


def _day_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _apply_filters(stmt: Select[tuple[AuditLog]], filters: AuditFilters) -> Select[tuple[AuditLog]]:
    if filters.employee_id is not None:
        stmt = stmt.where(AuditLog.employee_id == filters.employee_id)
    if filters.action is not None:
        stmt = stmt.where(AuditLog.action == filters.action)
    if filters.entity_type:
        stmt = stmt.where(AuditLog.entity_type == filters.entity_type)
    if filters.entity_id:
        stmt = stmt.where(AuditLog.entity_id == filters.entity_id)
    if filters.date_from is not None:
        start = filters.date_from
        if not isinstance(start, datetime):
            start = _day_start(start)
        stmt = stmt.where(AuditLog.created_at >= start)
    if filters.date_to is not None:
        if isinstance(filters.date_to, datetime):
            stmt = stmt.where(AuditLog.created_at <= filters.date_to)
        else:
            stmt = stmt.where(AuditLog.created_at < _day_start(filters.date_to + timedelta(days=1)))
    if filters.q:
        stmt = stmt.where(AuditLog.employee_name.ilike(f"%{escape_like(filters.q)}%", escape="\\"))
    return stmt


def _visible(data: dict[str, Any] | None) -> dict[str, Any]:
    return {key: value for key, value in (data or {}).items() if key != LABEL_KEY}


def build_changes(record: AuditLog) -> list[AuditChange]:
    old = _visible(record.old_data)
    new = _visible(record.new_data)
    if record.action == AuditAction.stock_change:
        return [AuditChange(field="quantity", old=old.get("quantity"), new=new.get("quantity"))]
    keys = list(dict.fromkeys([*old, *new]))
    return [AuditChange(field=key, old=old.get(key), new=new.get(key)) for key in keys]


def _short(value: Any) -> str:
    text = "empty" if value is None or value == "" else str(value)
    return text if len(text) <= SUMMARY_VALUE_MAX else text[: SUMMARY_VALUE_MAX - 1] + "…"


def _label(record: AuditLog) -> str:
    for data in (record.new_data, record.old_data):
        if data and data.get(LABEL_KEY):
            return str(data[LABEL_KEY])
    entity = ENTITY_NAMES.get(record.entity_type, record.entity_type)
    return f"{entity} #{record.entity_id}" if record.entity_id else entity


def build_summary(record: AuditLog) -> str:
    who = record.employee_name or "Someone"
    entity = ENTITY_NAMES.get(record.entity_type, record.entity_type)
    label = _label(record)
    new = _visible(record.new_data)
    old = _visible(record.old_data)

    match record.action:
        case AuditAction.login:
            return f"{who} signed in"
        case AuditAction.login_failed:
            return f"Failed sign-in attempt for «{new.get('username', '?')}»"
        case AuditAction.logout:
            suffix = " on all devices" if new.get("all_sessions") else ""
            return f"{who} signed out{suffix}"
        case AuditAction.create:
            return f"{who} created {entity} «{label}»"
        case AuditAction.delete:
            return f"{who} deleted {entity} «{label}»"
        case AuditAction.stock_change:
            kind = str(new.get("type", "change")).replace("_", " ")
            return (
                f"{who} recorded {kind} {new.get('change', '')} for «{label}»: "
                f"{_short(old.get('quantity'))} → {_short(new.get('quantity'))}"
            )
        case _:  # update
            if "password" in new:
                return f"{who} changed the password of «{label}»"
            fields = list(dict.fromkeys([*old, *new]))
            if len(fields) == 1:
                field = fields[0]
                return (
                    f"{who} changed the {field.replace('_', ' ')} of «{label}»: "
                    f"{_short(old.get(field))} → {_short(new.get(field))}"
                )
            names = ", ".join(field.replace("_", " ") for field in fields)
            return f"{who} updated {entity} «{label}»: {names}"


def to_read(record: AuditLog) -> AuditRead:
    return AuditRead(
        id=record.id,
        created_at=record.created_at,
        employee_id=record.employee_id,
        employee_name=record.employee_name,
        action=record.action,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        changes=build_changes(record),
        summary=build_summary(record),
        ip_address=str(record.ip_address) if record.ip_address is not None else None,
        user_agent=record.user_agent,
    )


async def list_entries(
    session: AsyncSession, filters: AuditFilters, page: int, page_size: int
) -> tuple[list[AuditRead], int]:
    base = _apply_filters(select(AuditLog), filters)
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = await session.scalars(
        base.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return [to_read(record) for record in rows.all()], total


def _csv_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(CSV_FORMULA_PREFIXES):
        text = "'" + text  # shown as text, never evaluated
    return text


async def export_csv(session: AsyncSession, filters: AuditFilters) -> str:
    """UTF-8 with BOM (Excel opens Cyrillic correctly), ";" as the delimiter."""
    rows = await session.scalars(
        _apply_filters(select(AuditLog), filters)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(CSV_MAX_ROWS)
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(
        [
            "Date",
            "Employee",
            "Action",
            "Object type",
            "Object ID",
            "Summary",
            "Changes",
            "IP address",
            "User agent",
        ]
    )
    for record in rows.all():
        entry = to_read(record)
        changes = "; ".join(f"{c.field}: {_short(c.old)} → {_short(c.new)}" for c in entry.changes)
        writer.writerow(
            [
                _csv_cell(entry.created_at.isoformat()),
                _csv_cell(entry.employee_name),
                _csv_cell(entry.action.value),
                _csv_cell(entry.entity_type),
                _csv_cell(entry.entity_id),
                _csv_cell(entry.summary),
                _csv_cell(changes),
                _csv_cell(entry.ip_address),
                _csv_cell(entry.user_agent),
            ]
        )
    return "﻿" + buffer.getvalue()
