from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import NotebookORM


class NotebooksRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        *,
        owner_id: UUID,
        title: str,
        section_id: UUID| None = None,
        position: int = 0,
        document: dict[str, Any],
    ) -> NotebookORM:
        notebook = NotebookORM(
            owner_id=owner_id,
            title=title,
            document=document,
            section_id=section_id,
            position=position
        )
        self.db.add(notebook)
        return notebook


    def get_owned(
        self,
        *,
        notebook_id: UUID,
        owner_id: UUID,
        for_update: bool = False,
    ) -> NotebookORM | None:
        statement = select(NotebookORM).where(
            NotebookORM.id == notebook_id,
            NotebookORM.owner_id == owner_id,
            NotebookORM.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)


    def count_owned(self, owner_id: UUID) -> int:
        total = self.db.scalar(
        select(func.count(NotebookORM.id)).where(NotebookORM.owner_id == owner_id, NotebookORM.deleted_at.is_(None))
    )
        return int(total or 0)


    def max_position(self, *, owner_id: UUID, section_id: UUID | None) -> int | None:
        statement = select(func.max(NotebookORM.position)).where(
            NotebookORM.owner_id == owner_id,
            NotebookORM.deleted_at.is_(None),
        )
        if section_id is None:
            statement = statement.where(NotebookORM.section_id.is_(None))
        else:
            statement = statement.where(NotebookORM.section_id == section_id)
        return self.db.scalar(statement)


    def list_owned(self, owner_id: UUID) -> list[NotebookORM]:
        statement = (
            select(NotebookORM)
            .where(
                NotebookORM.owner_id == owner_id,
                NotebookORM.deleted_at.is_(None),
            )
            .order_by(
                NotebookORM.section_id.asc().nulls_first(),
                NotebookORM.position.asc(),
                NotebookORM.created_at.asc(),
                NotebookORM.id.asc(),
            )
        )
        return list(self.db.scalars(statement))


    def get_first_owned(self, owner_id: UUID) -> NotebookORM | None:
        statement = (
            select(NotebookORM)
            .where(
                NotebookORM.owner_id == owner_id,
                NotebookORM.deleted_at.is_(None),
            )
            .order_by(NotebookORM.created_at.asc())
            .limit(1)
        )
        return self.db.scalar(statement)


    def get_by_title(self, owner_id: UUID, title: str) -> NotebookORM:
        return self.db.scalar(
                        select(NotebookORM)
                            .where(
                            NotebookORM.owner_id == owner_id, 
                            func.lower(NotebookORM.title) == title.lower())
                        )


    def delete(self, owner_id: UUID, notebook_id: UUID) -> NotebookORM | None:
        notebook_for_delete = self.get_owned(notebook_id=notebook_id, owner_id=owner_id)
        if notebook_for_delete is None:
                return None
        self.db.delete(notebook_for_delete)
        return notebook_for_delete
