from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models import AuditAction


class AuditChange(BaseModel):
    field: str
    old: Any = None
    new: Any = None


class AuditRead(BaseModel):
    id: int
    created_at: datetime
    employee_id: int | None
    employee_name: str | None
    action: AuditAction
    entity_type: str
    entity_id: str | None
    changes: list[AuditChange]
    summary: str
    ip_address: str | None
    user_agent: str | None
