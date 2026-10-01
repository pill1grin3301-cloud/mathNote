from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotebookBlock(BaseModel):
    id: UUID
    type: Literal["heading", "text", "math", "draw"]
    content: str = Field(max_length=5_000_000)

class NotebookCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=1, max_length=255)
    section_id: UUID | None = Field(default=None, alias="sectionId")

class NotebookImage(BaseModel):
    src: str = Field(min_length=16, max_length=1_500_000)
    w: int = Field(ge=1, le=8_000)
    h: int = Field(ge=1, le=8_000)

    @field_validator("src")
    @classmethod
    def src_is_data_image(cls, value: str) -> str:
        if not value.startswith("data:image/") or ";base64," not in value:
            raise ValueError("image src must be a data URL")
        return value


class NotebookDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal[1] = Field(
        default=1,
        alias="schemaVersion",
    )
    blocks: list[NotebookBlock] = Field(default_factory=list, max_length=1_000)
    images: dict[str, NotebookImage] = Field(default_factory=dict, max_length=80)

    @field_validator("images")
    @classmethod
    def image_ids_are_short(
        cls, value: dict[str, NotebookImage]
    ) -> dict[str, NotebookImage]:
        for key in value:
            if not key.isalnum() or not 4 <= len(key) <= 32:
                raise ValueError("invalid image id")
        return value


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
    section_id: UUID | None = Field(default=None, serialization_alias="sectionId")
    position: int = 0
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class NotebookListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    version: int
    section_id: UUID | None = Field(default=None, serialization_alias="sectionId")
    position: int = 0
    updated_at: datetime = Field(serialization_alias="updatedAt")


class NotebookUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    version: int
    updated_at: datetime = Field(serialization_alias="updatedAt")


class VersionConflictResponse(BaseModel):
    detail: Literal["Notebook version conflict"] = "Notebook version conflict"
    current_version: int = Field(serialization_alias="currentVersion")


class NotebookPatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    section_id: UUID | None = Field(default=None, alias="sectionId")
    position: int | None = Field(default=None, ge=0)


class NotebookPatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    section_id: UUID | None = Field(default=None, serialization_alias="sectionId")
    position: int