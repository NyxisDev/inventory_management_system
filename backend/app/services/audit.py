"""Audit log: who did what, with the old and the new values.

log_action adds the record to the SAME session and transaction as the change and never commits,
so a failed action leaves no record. Passwords, hashes and tokens are always masked.
"""

import enum
import ipaddress
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.net import get_client_ip, get_user_agent
from app.models import AuditAction, AuditLog, Employee

MASK = "***"
SENSITIVE_MARKERS = ("password", "token", "secret", "hash")
# Not part of the changes: a human-readable name of the object for the summary
LABEL_KEY = "_label"

EMPLOYEE_FIELDS = ("id", "first_name", "last_name", "username", "role", "is_active")
CATEGORY_FIELDS = ("id", "name", "slug", "parent_id", "sort_order")
WAREHOUSE_FIELDS = ("id", "name", "address", "is_active", "show_on_site")
PRODUCT_FIELDS = (
    "id",
    "sku",
    "name",
    "slug",
    "description",
    "category_id",
    "unit",
    "price",
    "is_published",
    "is_archived",
)
IMAGE_FIELDS = ("id", "product_id", "file_path", "is_main", "sort_order")


def to_json(value: Any) -> Any:
    """Make a value JSONB-safe: Decimal, dates, UUID and enums become strings."""
    if isinstance(value, dict):
        return {str(key): to_json(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [to_json(item) for item in value]
    if isinstance(value, enum.Enum):
        return to_json(value.value)
    if isinstance(value, Decimal | uuid.UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def mask_sensitive(data: Any) -> Any:
    """Replace every value whose key looks like a password, hash or token with "***"."""
    if isinstance(data, dict):
        return {
            key: MASK
            if any(marker in str(key).lower() for marker in SENSITIVE_MARKERS)
            else mask_sensitive(value)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [mask_sensitive(item) for item in data]
    return data


def snapshot(obj: object, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(obj, field) for field in fields}


def _clean_ip(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


async def log_action(
    session: AsyncSession,
    *,
    employee: Employee | None,
    action: AuditAction,
    entity_type: str,
    entity_id: str | int | None = None,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
    request: Request | None = None,
    label: str | None = None,
) -> AuditLog | None:
    """Add an audit record to the current transaction (never commits).

    For "update" only the changed fields are kept; if nothing changed, no record is written.
    """
    old = mask_sensitive(to_json(old_data)) if old_data is not None else None
    new = mask_sensitive(to_json(new_data)) if new_data is not None else None

    if action == AuditAction.update and old is not None and new is not None:
        changed = [key for key in {**old, **new} if old.get(key) != new.get(key)]
        if not changed:
            return None
        old = {key: old.get(key) for key in changed}
        new = {key: new.get(key) for key in changed}

    if label:
        target = new if new is not None else old
        if target is None:
            new = target = {}
        target[LABEL_KEY] = label

    record = AuditLog(
        employee_id=employee.id if employee else None,
        employee_name=employee.full_name[:201] if employee else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        old_data=old,
        new_data=new,
        ip_address=_clean_ip(get_client_ip(request)) if request else None,
        user_agent=get_user_agent(request) if request else None,
    )
    session.add(record)
    return record
