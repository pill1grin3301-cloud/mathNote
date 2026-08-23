from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"


class CredentialsRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=USERNAME_PATTERN,
    )
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class RegisterRequest(CredentialsRequest):
    pass


class LoginRequest(CredentialsRequest):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    created_at: datetime


class AuthResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse
    initial_notebook_id: UUID | None = Field(
        default=None,
        serialization_alias="initialNotebookId",
    )
