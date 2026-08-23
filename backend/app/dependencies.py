from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.notebooks import NotebooksRepository
from app.repositories.users import UsersRepository
from app.services.auth import AuthService
from app.services.notebooks import NotebookService


def get_users_repository(db: Annotated[Session, Depends(get_db)]) -> UsersRepository:
    return UsersRepository(db)


def get_notebooks_repository(
    db: Annotated[Session, Depends(get_db)],
) -> NotebooksRepository:
    return NotebooksRepository(db)


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


def get_notebook_service(db: Annotated[Session, Depends(get_db)]) -> NotebookService:
    return NotebookService(db)


UsersRepositoryDep = Annotated[UsersRepository, Depends(get_users_repository)]
NotebooksRepositoryDep = Annotated[
    NotebooksRepository, Depends(get_notebooks_repository)
]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
NotebookServiceDep = Annotated[NotebookService, Depends(get_notebook_service)]
