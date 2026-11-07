from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_column
from app.models.enums import AuditAction, audit_action_type

if TYPE_CHECKING:
    from app.models.employee import Employee


class AuditLog(Base):
    """Append-only journal of employee actions (UPDATE / DELETE are blocked by a trigger)."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_employee", "employee_id", text("created_at DESC")),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_created", text("created_at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="SET NULL")
    )
    # "First Last" at the time of the action
    employee_name: Mapped[str | None] = mapped_column(String(201))
    action: Mapped[AuditAction] = mapped_column(audit_action_type, nullable=False)
    # product, employee, category, warehouse, stock, product_image, auth
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    old_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = created_at_column()

    employee: Mapped[Employee | None] = relationship()
