from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SectionORM

class SectionsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db


    def add(self, *, owner_id: UUID, title: str, position: int = 0) -> SectionORM:
        section = SectionORM(owner_id=owner_id, title=title, position=position)
        self.db.add(section)
        return section

    def get_owned(
        self,
        *,
        section_id: UUID,
        owner_id: UUID,
        for_update: bool = False,
    ) -> SectionORM | None:
        statement = select(SectionORM).where(
            SectionORM.id == section_id,
            SectionORM.owner_id == owner_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def list_owned(self, owner_id: UUID) -> list[SectionORM]:
            statement = (
                select(SectionORM).where(SectionORM.owner_id == owner_id)
                .order_by(
                    SectionORM.position.asc(),
                    SectionORM.created_at.asc(),
                    SectionORM.id.asc(),
                )
            )
            return list(self.db.scalars(statement))

    def get_by_title(self, title: str, owner_id:UUID) -> SectionORM:
         return self.db.scalar(
              select(SectionORM)
                    .where(
                    SectionORM.owner_id == owner_id, 
                    func.lower(SectionORM.title) == title.lower())
                )
    

    def count_owned(self, owner_id: UUID) -> int:
        total = self.db.scalar(
        select(func.count(SectionORM.id)).where(SectionORM.owner_id == owner_id)
    )
        return int(total or 0)

    def delete(self, *, owner_id: UUID, section_id: UUID) -> SectionORM | None:
        section_for_delete = self.get_owned(section_id=section_id, owner_id=owner_id)
        if section_for_delete is None:
             return None
        self.db.delete(section_for_delete)
        return section_for_delete