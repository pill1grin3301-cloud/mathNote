from uuid import UUID

from sqlalchemy.orm import Session

from app.models import NotebookORM
from app.repositories.notebooks import NotebooksRepository
from app.schemas.notebook import NotebookUpdateRequest


class NotebookNotFoundError(Exception):
    pass


class NotebookVersionConflictError(Exception):
    def __init__(self, current_version: int):
        self.current_version = current_version
        super().__init__("Notebook version conflict")


class NotebookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notebooks = NotebooksRepository(db)

    def list_notebooks(self, owner_id: UUID) -> list[NotebookORM]:
        return self.notebooks.list_owned(owner_id)

    def get_notebook(self, *, notebook_id: UUID, owner_id: UUID) -> NotebookORM:
        notebook = self.notebooks.get_owned(
            notebook_id=notebook_id,
            owner_id=owner_id,
        )
        if notebook is None:
            raise NotebookNotFoundError
        return notebook

    def update_notebook(
        self,
        *,
        notebook_id: UUID,
        owner_id: UUID,
        payload: NotebookUpdateRequest,
    ) -> NotebookORM:
        notebook = self.notebooks.get_owned(
            notebook_id=notebook_id,
            owner_id=owner_id,
            for_update=True,
        )
        if notebook is None:
            self.db.rollback()
            raise NotebookNotFoundError
        if notebook.version != payload.base_version:
            current_version = notebook.version
            self.db.rollback()
            raise NotebookVersionConflictError(current_version)

        notebook.title = payload.title
        notebook.document = payload.document.model_dump(
            by_alias=True,
            mode="json",
        )
        notebook.version += 1
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(notebook)
        return notebook
