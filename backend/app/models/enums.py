import enum

from sqlalchemy.dialects.postgresql import ENUM


class EmployeeRole(enum.StrEnum):
    admin = "admin"
    staff = "staff"


class MovementType(enum.StrEnum):
    income = "income"
    outcome = "outcome"
    adjustment = "adjustment"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"


class AuditAction(enum.StrEnum):
    create = "create"
    update = "update"
    delete = "delete"
    login = "login"
    login_failed = "login_failed"
    logout = "logout"
    stock_change = "stock_change"


def _values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


# The PostgreSQL types themselves are created by the Alembic migration.
employee_role_type = ENUM(
    EmployeeRole, name="employee_role", values_callable=_values, create_type=False
)
movement_type_type = ENUM(
    MovementType, name="movement_type", values_callable=_values, create_type=False
)
audit_action_type = ENUM(
    AuditAction, name="audit_action", values_callable=_values, create_type=False
)
