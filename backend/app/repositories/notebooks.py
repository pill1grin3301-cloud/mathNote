from typing import Any
from uuid import UUID

from sqlalchemy import select
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
        document: dict[str, Any],
    ) -> NotebookORM:
        notebook = NotebookORM(
            owner_id=owner_id,
            title=title,
            document=document,
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

    def list_owned(self, owner_id: UUID) -> list[NotebookORM]:
        statement = (
            select(NotebookORM)
            .where(
                NotebookORM.owner_id == owner_id,
                NotebookORM.deleted_at.is_(None),
            )
            .order_by(NotebookORM.updated_at.desc())
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
