from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.dependencies import NotebookServiceDep
from app.models import UserORM
from app.schemas.notebook import (
    NotebookListItem,
    NotebookResponse,
    NotebookUpdateRequest,
    NotebookUpdateResponse,
)
from app.security import get_current_user
from app.services.notebooks import NotebookNotFoundError, NotebookVersionConflictError

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])
CurrentUser = Annotated[UserORM, Depends(get_current_user)]


@router.get("", response_model=list[NotebookListItem])
def list_notebooks(
    notebook_service: NotebookServiceDep,
    current_user: CurrentUser,
):
    return notebook_service.list_notebooks(current_user.id)


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
