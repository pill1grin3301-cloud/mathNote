from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.sections import SectionsRepository
from app.schemas.section import SectionCreateRequest, SectionPatchRequest
from app.models import SectionORM

class SectionNameAlreadyExistError(Exception):
    pass

class SectionNotFoundError(Exception):
    pass

class InvalidDataError(Exception):
    pass

class SectionLimitExceededError(Exception):
    pass


MAX_SECTIONS_PER_USER = 30


class SectionService:
    def __init__(self, db: Session):
        self.db = db
        self.sections = SectionsRepository(db)


    def create_section(self, section_create_data: SectionCreateRequest, owner_id: UUID) -> SectionORM:
        teor_max = self.sections.list_owned(owner_id=owner_id)
        if not teor_max:
            teor_max = 0
        else: teor_max = teor_max[-1].position + 1
        if self.sections.count_owned(owner_id) >= MAX_SECTIONS_PER_USER:
            raise SectionLimitExceededError()
        if self.sections.get_by_title(title=section_create_data.title.strip(), owner_id=owner_id):
            raise SectionNameAlreadyExistError()
        new_section = self.sections.add(owner_id=owner_id, title=section_create_data.title.strip(), position=teor_max)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise SectionNameAlreadyExistError from None
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(new_section)
        return new_section


    def get_all_sections(self, owner_id: UUID) -> list[SectionORM]:
        return self.sections.list_owned(owner_id=owner_id)


    def update(self, owner_id: UUID, section_id: UUID,  payload: SectionPatchRequest) -> SectionORM:

        section_for_update = self.sections.get_owned(section_id=section_id, owner_id=owner_id, for_update=True)
        if not section_for_update:
            raise SectionNotFoundError()

        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise InvalidDataError()
        
        if "title" in data:
            title = data["title"].strip()
            found = self.sections.get_by_title(title=title, owner_id=owner_id)
            if found is not None and found.id != section_id:
                raise SectionNameAlreadyExistError()
            section_for_update.title = title

        if "position" in data:
            section_for_update.position = data["position"]

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise SectionNameAlreadyExistError from None
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(section_for_update)
        return section_for_update


    def delete_section(self, owner_id: UUID, section_id: UUID)-> SectionORM | None:
        section_for_delete = self.sections.get_owned(section_id=section_id, owner_id=owner_id)
        if not section_for_delete:
            raise SectionNotFoundError()
        self.sections.delete(owner_id=owner_id, section_id=section_id)
        self.db.commit()
        return section_for_delete