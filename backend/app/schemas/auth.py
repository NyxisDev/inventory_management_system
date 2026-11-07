from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from app.schemas.common import InputModel, OutputModel
from app.schemas.employee import EmployeeBrief, NewPassword


def _lower(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


class LoginRequest(InputModel):
    # No format rules here: any wrong value simply fails as "Invalid username or password"
    username: Annotated[str, BeforeValidator(_lower), Field(min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=1, max_length=128)]


class TokenResponse(OutputModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - OAuth token type, not a secret
    expires_in: int  # seconds
    employee: EmployeeBrief


class ChangePasswordRequest(InputModel):
    old_password: Annotated[str, Field(min_length=1, max_length=128)]
    new_password: NewPassword
