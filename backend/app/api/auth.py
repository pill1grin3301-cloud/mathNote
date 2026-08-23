from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.dependencies import AuthServiceDep
from app.models import UserORM
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.security import create_access_token, get_current_user
from app.services.auth import InvalidCredentialsError, UsernameAlreadyExistsError
from bot.main import notify_user_deleted, notify_user_registered

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthServiceDep,
) -> AuthResponse:
    try:
        user, notebook = auth_service.register(payload)
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from exc

    background_tasks.add_task(
        notify_user_registered,
        user.username,
        auth_service.users.count(),
    )
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=user,
        initial_notebook_id=notebook.id,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> AuthResponse:
    try:
        user = auth_service.authenticate(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    notebook = auth_service.notebooks.get_first_owned(user.id)
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=user,
        initial_notebook_id=notebook.id if notebook else None,
    )


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    auth_service: AuthServiceDep,
    background_tasks: BackgroundTasks,
) -> None:
    username = current_user.username
    auth_service.delete_user(current_user)
    background_tasks.add_task(
        notify_user_deleted,
        username,
        auth_service.users.count(),
    )
