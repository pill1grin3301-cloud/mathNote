from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.dependencies import NotebookServiceDep
from app.models import UserORM
from app.schemas.notebook import (
    NotebookCreateRequest,
    NotebookListItem,
    NotebookPatchRequest,
    NotebookPatchResponse,
    NotebookResponse,
    NotebookUpdateRequest,
    NotebookUpdateResponse,
)
from app.security import get_current_user
from app.services.notebooks import (
    LastNotebookError,
    NotebookLimitExceededError,
    NotebookNotFoundError,
    NotebookVersionConflictError,
)
from app.services.sections import InvalidDataError

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])
CurrentUser = Annotated[UserORM, Depends(get_current_user)]


@router.get("", response_model=list[NotebookListItem])
def list_notebooks(
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
):
    return notebook_service.list_notebooks(current_user.id)


@router.post(
    "",
    response_model=NotebookResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notebook(
    payload: NotebookCreateRequest,
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
):
    try:
        return notebook_service.create_notebook(current_user.id, payload)
    except InvalidDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid notebook",
        ) from exc
    except NotebookLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Notebook limit reached",
        ) from exc
    except NotebookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        ) from exc


@router.get("/{notebook_id}", response_model=NotebookResponse)
def get_notebook(
    notebook_id: UUID,
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
):
    try:
        return notebook_service.get_notebook(
            notebook_id=notebook_id,
            owner_id=current_user.id,
        )
    except NotebookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        ) from exc


@router.put("/{notebook_id}", response_model=NotebookUpdateResponse)
def update_notebook(
    notebook_id: UUID,
    payload: NotebookUpdateRequest,
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
):
    try:
        return notebook_service.update_notebook(
            notebook_id=notebook_id,
            owner_id=current_user.id,
            payload=payload,
        )
    except NotebookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        ) from exc
    except NotebookVersionConflictError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Notebook version conflict",
                "currentVersion": exc.current_version,
            },
        )


@router.patch("/{notebook_id}", response_model=NotebookPatchResponse)
def patch_notebook(
    notebook_id: UUID,
    payload: NotebookPatchRequest,
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
):
    try:
        return notebook_service.patch_notebook(
            owner_id=current_user.id,
            notebook_id=notebook_id,
            payload=payload,
        )
    except NotebookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        ) from exc
    except InvalidDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid patch",
        ) from exc


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notebook(
    notebook_id: UUID,
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
) -> None:
    try:
        notebook_service.delete_notebook(
            owner_id=current_user.id,
            notebook_id=notebook_id,
        )
    except NotebookNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        ) from exc
    except LastNotebookError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete the last notebook",
        ) from exc
