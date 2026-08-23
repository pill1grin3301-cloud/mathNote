from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies import get_auth_service
from app.main import app

client = TestClient(app)


def test_telegram_notification_runs_only_after_registration(monkeypatch) -> None:
    user = SimpleNamespace(
        id=uuid4(),
        username="new_user",
        created_at=datetime.now(UTC),
    )
    notebook = SimpleNamespace(id=uuid4())
    notifications: list[tuple[str, int]] = []

    class FakeAuthService:
        def __init__(self) -> None:
            self.notebooks = SimpleNamespace(get_first_owned=lambda _user_id: notebook)
            self.users = SimpleNamespace(count=lambda: 4)

        def register(self, _payload):
            return user, notebook

        def authenticate(self, _payload):
            return user

    app.dependency_overrides[get_auth_service] = FakeAuthService
    monkeypatch.setattr(
        "app.api.auth.notify_user_registered",
        lambda username, total: notifications.append((username, total)),
    )
    try:
        register_response = client.post(
            "/api/auth/register",
            json={"username": "new_user", "password": "strong-password"},
        )
        login_response = client.post(
            "/api/auth/login",
            json={"username": "new_user", "password": "strong-password"},
        )
    finally:
        app.dependency_overrides.clear()

    assert register_response.status_code == 201
    assert register_response.json()["initialNotebookId"] == str(notebook.id)
    assert login_response.status_code == 200
    assert notifications == [("new_user", 4)]


def test_delete_user_notifies_telegram(monkeypatch) -> None:
    deleted: list[object] = []
    notifications: list[tuple[str, int]] = []
    user = SimpleNamespace(
        id=uuid4(),
        username="gone_user",
        created_at=datetime.now(UTC),
    )

    class FakeAuthService:
        def __init__(self) -> None:
            self.users = SimpleNamespace(count=lambda: 3)

        def delete_user(self, current_user):
            deleted.append(current_user.username)

    from app.security import get_current_user

    app.dependency_overrides[get_auth_service] = FakeAuthService
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        "app.api.auth.notify_user_deleted",
        lambda username, total: notifications.append((username, total)),
    )
    try:
        response = client.delete("/api/auth/delete")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert deleted == ["gone_user"]
    assert notifications == [("gone_user", 3)]
