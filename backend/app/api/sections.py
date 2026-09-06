from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import SectionServiceDep
from app.models import UserORM
from app.schemas.section import (
    SectionCreateRequest,
    SectionPatchRequest,
    SectionResponse,
)
from app.security import get_current_user
from app.services.sections import (
    InvalidDataError,
    SectionLimitExceededError,
    SectionNameAlreadyExistError,
    SectionNotFoundError,
)

router = APIRouter(prefix="/api/sections", tags=["sections"])
CurrentUser = Annotated[UserORM, Depends(get_current_user)]


@router.get("", response_model=list[SectionResponse])
def list_sections(
    section_service: SectionServiceDep,
    current_user: CurrentUser,
):
    return section_service.get_all_sections(current_user.id)


@router.post(
    "",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_section(
    payload: SectionCreateRequest,
    section_service: SectionServiceDep,
    current_user: CurrentUser,
):
    try:
        return section_service.create_section(payload, current_user.id)
    except SectionLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Section limit reached",
        ) from exc
    except SectionNameAlreadyExistError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section name already exists",
        ) from exc


@router.patch("/{section_id}", response_model=SectionResponse)
def patch_section(
    section_id: UUID,
    payload: SectionPatchRequest,
    section_service: SectionServiceDep,
    current_user: CurrentUser,
):
    try:
        return section_service.update(
            owner_id=current_user.id,
            section_id=section_id,
            payload=payload,
        )
    except SectionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        ) from exc
    except InvalidDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid patch",
        ) from exc
    except SectionNameAlreadyExistError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section name already exists",
        ) from exc


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: UUID,
    section_service: SectionServiceDep,
    current_user: CurrentUser,
) -> None:
    try:
        section_service.delete_section(
            owner_id=current_user.id,
            section_id=section_id,
        )
    except SectionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        ) from exc
