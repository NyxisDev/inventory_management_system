from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field, StringConstraints

from app.core.security import validate_password_strength
from app.models import EmployeeRole
from app.schemas.common import InputModel, OutputModel


def _lower(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Username = Annotated[
    str,
    BeforeValidator(_lower),
    StringConstraints(min_length=3, max_length=50, pattern=r"^[a-z0-9._-]+$"),
]
# Max length is checked in bytes by validate_password_strength (bcrypt limit: 72 bytes)
NewPassword = Annotated[str, Field(max_length=72), AfterValidator(validate_password_strength)]


class EmployeeCreate(InputModel):
    first_name: PersonName
    last_name: PersonName
    username: Username
    password: NewPassword
    role: EmployeeRole = EmployeeRole.staff


class EmployeeUpdate(InputModel):
    first_name: PersonName | None = None
    last_name: PersonName | None = None
    role: EmployeeRole | None = None
    is_active: bool | None = None


class PasswordReset(InputModel):
    new_password: NewPassword


class EmployeeBrief(OutputModel):
    id: int
    first_name: str
    last_name: str
    role: EmployeeRole


class EmployeeRead(OutputModel):
    """Never contains password_hash."""

    id: int
    first_name: str
    last_name: str
    username: str
    role: EmployeeRole
    is_active: bool
    locked_until: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
