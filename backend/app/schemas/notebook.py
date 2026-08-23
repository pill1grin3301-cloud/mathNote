from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotebookBlock(BaseModel):
    id: UUID
    type: Literal["heading", "text", "math", "draw"]
    content: str = Field(max_length=5_000_000)


class NotebookDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal[1] = Field(
        default=1,
        alias="schemaVersion",
    )
    blocks: list[NotebookBlock] = Field(default_factory=list, max_length=1_000)


class NotebookUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=1, max_length=255)
    document: NotebookDocument
    base_version: int = Field(alias="baseVersion", ge=1)


class NotebookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    document: NotebookDocument
    version: int
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class NotebookListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    version: int
    updated_at: datetime = Field(serialization_alias="updatedAt")


class NotebookUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    version: int
    updated_at: datetime = Field(serialization_alias="updatedAt")


class VersionConflictResponse(BaseModel):
    detail: Literal["Notebook version conflict"] = "Notebook version conflict"
    current_version: int = Field(serialization_alias="currentVersion")
