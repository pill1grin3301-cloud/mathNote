from uuid import UUID

from sqlalchemy.orm import Session

from app.models import NotebookORM
from app.repositories.notebooks import NotebooksRepository
from app.schemas.notebook import NotebookCreateRequest, NotebookPatchRequest, NotebookUpdateRequest
from app.services.auth import default_notebook_document
from app.repositories.sections import SectionsRepository
from app.services.sections import InvalidDataError


class NotebookNotFoundError(Exception):
    pass

class LastNotebookError(Exception):
    pass

class NotebookLimitExceededError(Exception):
    pass


MAX_NOTEBOOKS_PER_USER = 100

class NotebookVersionConflictError(Exception):
    def __init__(self, current_version: int):
        self.current_version = current_version
        super().__init__("Notebook version conflict")


class NotebookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notebooks = NotebooksRepository(db)
        self.sections = SectionsRepository(db)

    def create_notebook(self, owner_id: UUID, payload: NotebookCreateRequest) -> NotebookORM:
        title = payload.title.strip()
        if not title:
            raise InvalidDataError()
        section_id = payload.section_id
        if self.notebooks.count_owned(owner_id) >= MAX_NOTEBOOKS_PER_USER:
            raise NotebookLimitExceededError()
        if section_id is not None and not self.sections.get_owned(owner_id=owner_id, section_id=section_id):
            raise NotebookNotFoundError()
        current_max = self.notebooks.max_position(owner_id=owner_id, section_id=section_id)
        position = 0 if current_max is None else current_max + 1
        
        new_notebook = self.notebooks.add(
            owner_id=owner_id,
            section_id=section_id, 
            title=payload.title.strip(), 
            position=position, 
            document=default_notebook_document()
        )
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(new_notebook)
        return new_notebook



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

    def patch_notebook(self, owner_id: UUID, notebook_id: UUID, payload: NotebookPatchRequest) -> NotebookORM:
        note_for_patch = self.notebooks.get_owned(notebook_id=notebook_id, owner_id=owner_id)
        if not note_for_patch:
            raise NotebookNotFoundError()
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise InvalidDataError()
        if "title" in data:
            title = data["title"].strip()
            if not title:
                raise InvalidDataError()
            note_for_patch.title = title
        if "section_id" in data:
            new_section_id = data["section_id"]
            if new_section_id is None:
                note_for_patch.section_id = None
            else:
                section = self.sections.get_owned(
                    section_id=new_section_id,
                    owner_id=owner_id,
                )
                if section is None:
                    raise NotebookNotFoundError()
                note_for_patch.section_id = new_section_id
            if "position" not in data:
                current_max = self.notebooks.max_position(
                    owner_id=owner_id,
                    section_id=new_section_id,
                )
                note_for_patch.position = (
                    0 if current_max is None else current_max + 1
                )

        if "position" in data:
            note_for_patch.position = data["position"]

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(note_for_patch)
        return note_for_patch


    def delete_notebook(self, owner_id: UUID, notebook_id: UUID):
        note_for_delete = self.notebooks.get_owned(notebook_id=notebook_id, owner_id=owner_id)
        if not note_for_delete: 
            raise NotebookNotFoundError()

        if self.notebooks.count_owned(owner_id=owner_id) <= 1:
            raise LastNotebookError()
        
        self.notebooks.delete(owner_id=owner_id, notebook_id=notebook_id)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        