from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    position: int
    created_at: datetime = Field(serialization_alias="createdAt")


class SectionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class SectionPatchRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    position: int | None = Field(default=None, ge=0)