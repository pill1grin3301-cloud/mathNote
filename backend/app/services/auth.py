from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import NotebookORM, UserORM
from app.repositories.notebooks import NotebooksRepository
from app.repositories.users import UsersRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.security import hash_password, verify_password


class UsernameAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def default_notebook_document() -> dict:
    return {
        "schemaVersion": 1,
        "blocks": [
            {
                "id": str(uuid4()),
                "type": "heading",
                "content": "Решение",
            },
            {
                "id": str(uuid4()),
                "type": "math",
                "content": "",
            },
        ],
    }


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UsersRepository(db)
        self.notebooks = NotebooksRepository(db)

    def register(self, payload: RegisterRequest) -> tuple[UserORM, NotebookORM]:
        username = payload.username
        if self.users.get_by_username(username) is not None:
            raise UsernameAlreadyExistsError

        user = self.users.add(
            username=username,
            password_hash=hash_password(payload.password.get_secret_value()),
        )
        try:
            self.db.flush()
            notebook = self.notebooks.add(
                owner_id=user.id,
                title="Лист 1",
                document=default_notebook_document(),
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise UsernameAlreadyExistsError from exc
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(user)
        self.db.refresh(notebook)
        return user, notebook

    def authenticate(self, payload: LoginRequest) -> UserORM:
        user = self.users.get_by_username(payload.username)
        if user is None or not verify_password(
            payload.password.get_secret_value(),
            user.password_hash,
        ):
            raise InvalidCredentialsError
        return user

    def delete_user(self, current_user: UserORM) -> None:
        try:
            self.users.delete(current_user)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
