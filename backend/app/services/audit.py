"""Audit log. Placeholder until part 3 fills in log_action.

Every service already calls log_action at the right place, in the same session and transaction as
the change. Part 3 implements the body (old/new data, masking, IP, user agent).
"""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, Employee


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
) -> None:
    """Add an audit record to the current transaction (never commits). Implemented in part 3."""
    return
