from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import UserORM


class UsersRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: UUID) -> UserORM | None:
        return self.db.get(UserORM, user_id)

    def get_by_username(self, username: str) -> UserORM | None:
        statement = select(UserORM).where(UserORM.username == username)
        return self.db.scalar(statement)

    def add(self, *, username: str, password_hash: str) -> UserORM:
        user = UserORM(username=username, password_hash=password_hash)
        self.db.add(user)
        return user

    def delete(self, user: UserORM) -> None:
        self.db.delete(user)

    def count(self) -> int:
        total = self.db.scalar(select(func.count(UserORM.id)))
        return int(total or 0)
