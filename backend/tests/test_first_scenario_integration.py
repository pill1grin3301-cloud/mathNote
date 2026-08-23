import os

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is required for PostgreSQL integration tests",
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_registration_initial_notebook_save_and_conflict() -> None:
    registration = client.post(
        "/api/auth/register",
        json={"username": "math_user", "password": "strong-password"},
    )
    assert registration.status_code == 201

    auth = registration.json()
    notebook_id = auth["initialNotebookId"]
    headers = auth_header(auth["access_token"])

    loaded = client.get(f"/api/notebooks/{notebook_id}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["title"] == "Лист 1"
    assert loaded.json()["version"] == 1

    document = {
        "schemaVersion": 1,
        "blocks": [
            {
                "id": "1c0ea81e-1280-4c03-89d5-78a11dc472cc",
                "type": "math",
                "content": "x^2+1",
            }
        ],
    }
    saved = client.put(
        f"/api/notebooks/{notebook_id}",
        headers=headers,
        json={
            "title": "Алгебра",
            "document": document,
            "baseVersion": 1,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["version"] == 2

    conflict = client.put(
        f"/api/notebooks/{notebook_id}",
        headers=headers,
        json={
            "title": "Устаревшая версия",
            "document": document,
            "baseVersion": 1,
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["currentVersion"] == 2

    duplicate = client.post(
        "/api/auth/register",
        json={"username": "MATH_USER", "password": "another-password"},
    )
    assert duplicate.status_code == 409


def test_user_cannot_open_another_users_notebook() -> None:
    first = client.post(
        "/api/auth/register",
        json={"username": "first_user", "password": "strong-password"},
    ).json()
    second = client.post(
        "/api/auth/register",
        json={"username": "second_user", "password": "strong-password"},
    ).json()

    response = client.get(
        f"/api/notebooks/{first['initialNotebookId']}",
        headers=auth_header(second["access_token"]),
    )

    assert response.status_code == 404
