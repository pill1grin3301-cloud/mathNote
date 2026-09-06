import os
from uuid import uuid4

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


def register(username: str) -> tuple[dict, dict]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "strong-password"},
    )
    assert response.status_code == 201
    body = response.json()
    return body, auth_header(body["access_token"])


def math_document() -> dict:
    return {
        "schemaVersion": 1,
        "blocks": [
            {
                "id": "1c0ea81e-1280-4c03-89d5-78a11dc472cc",
                "type": "math",
                "content": "x^2+1",
            }
        ],
    }


def test_register_has_draft_notebook_and_no_sections() -> None:
    auth, headers = register("math_user")

    sections = client.get("/api/sections", headers=headers)
    assert sections.status_code == 200
    assert sections.json() == []

    notebooks = client.get("/api/notebooks", headers=headers)
    assert notebooks.status_code == 200
    assert len(notebooks.json()) == 1
    first = notebooks.json()[0]
    assert first["id"] == auth["initialNotebookId"]
    assert first["sectionId"] is None
    assert first["position"] == 0


def test_create_section_duplicate_name_is_conflict() -> None:
    _, headers = register("math_user")

    created = client.post("/api/sections", headers=headers, json={"title": "Алгебра"})
    assert created.status_code == 201
    assert created.json()["title"] == "Алгебра"
    assert created.json()["position"] == 0

    duplicate = client.post("/api/sections", headers=headers, json={"title": "алгебра"})
    assert duplicate.status_code == 409


def test_rename_section_to_own_title_is_allowed() -> None:
    _, headers = register("math_user")
    section_id = client.post(
        "/api/sections", headers=headers, json={"title": "Алгебра"}
    ).json()["id"]

    renamed = client.patch(
        f"/api/sections/{section_id}",
        headers=headers,
        json={"title": "алгебра"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "алгебра"


def test_empty_section_patch_is_rejected() -> None:
    _, headers = register("math_user")
    section_id = client.post(
        "/api/sections", headers=headers, json={"title": "Алгебра"}
    ).json()["id"]

    response = client.patch(
        f"/api/sections/{section_id}",
        headers=headers,
        json={},
    )
    assert response.status_code == 422


def test_create_notebook_with_foreign_section_is_hidden() -> None:
    _, first_headers = register("first_user")
    _, second_headers = register("second_user")
    section_id = client.post(
        "/api/sections", headers=first_headers, json={"title": "Алгебра"}
    ).json()["id"]

    response = client.post(
        "/api/notebooks",
        headers=second_headers,
        json={"title": "Кр 2", "sectionId": section_id},
    )
    assert response.status_code == 404


def test_notebook_can_move_between_section_and_drafts() -> None:
    auth, headers = register("math_user")
    algebra = client.post(
        "/api/sections", headers=headers, json={"title": "Алгебра"}
    ).json()
    matan = client.post(
        "/api/sections", headers=headers, json={"title": "Матан"}
    ).json()

    created = client.post(
        "/api/notebooks",
        headers=headers,
        json={"title": "Кр 2", "sectionId": algebra["id"]},
    )
    assert created.status_code == 201
    notebook_id = created.json()["id"]
    assert created.json()["sectionId"] == algebra["id"]
    assert created.json()["position"] == 0

    listed = client.get("/api/notebooks", headers=headers).json()
    assert len(listed) == 2
    by_id = {item["id"]: item for item in listed}
    assert by_id[notebook_id]["sectionId"] == algebra["id"]

    moved = client.patch(
        f"/api/notebooks/{notebook_id}",
        headers=headers,
        json={"sectionId": matan["id"]},
    )
    assert moved.status_code == 200
    assert moved.json()["sectionId"] == matan["id"]
    assert moved.json()["position"] == 0

    drafted = client.patch(
        f"/api/notebooks/{notebook_id}",
        headers=headers,
        json={"sectionId": None},
    )
    assert drafted.status_code == 200
    assert drafted.json()["sectionId"] is None


def test_put_document_does_not_clear_section() -> None:
    _, headers = register("math_user")
    section_id = client.post(
        "/api/sections", headers=headers, json={"title": "Алгебра"}
    ).json()["id"]
    notebook = client.post(
        "/api/notebooks",
        headers=headers,
        json={"title": "Кр 2", "sectionId": section_id},
    ).json()

    saved = client.put(
        f"/api/notebooks/{notebook['id']}",
        headers=headers,
        json={
            "title": "Кр 2",
            "document": math_document(),
            "baseVersion": 1,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["version"] == 2

    loaded = client.get(f"/api/notebooks/{notebook['id']}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["sectionId"] == section_id
    assert loaded.json()["position"] == 0


def test_delete_section_moves_notebooks_to_drafts() -> None:
    _, headers = register("math_user")
    section_id = client.post(
        "/api/sections", headers=headers, json={"title": "Алгебра"}
    ).json()["id"]
    notebook_id = client.post(
        "/api/notebooks",
        headers=headers,
        json={"title": "Кр 2", "sectionId": section_id},
    ).json()["id"]

    deleted = client.delete(f"/api/sections/{section_id}", headers=headers)
    assert deleted.status_code == 204

    loaded = client.get(f"/api/notebooks/{notebook_id}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["sectionId"] is None


def test_foreign_section_and_notebook_are_hidden() -> None:
    first, first_headers = register("first_user")
    _, second_headers = register("second_user")
    section_id = client.post(
        "/api/sections", headers=first_headers, json={"title": "Алгебра"}
    ).json()["id"]
    notebook_id = first["initialNotebookId"]
    missing = str(uuid4())

    assert (
        client.patch(
            f"/api/sections/{section_id}",
            headers=second_headers,
            json={"title": "Чужое"},
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/sections/{section_id}", headers=second_headers).status_code
        == 404
    )
    assert (
        client.get(f"/api/notebooks/{notebook_id}", headers=second_headers).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/notebooks/{notebook_id}",
            headers=second_headers,
            json={"title": "Чужое"},
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/notebooks/{notebook_id}", headers=second_headers).status_code
        == 404
    )
    assert (
        client.delete(f"/api/notebooks/{missing}", headers=second_headers).status_code
        == 404
    )


def test_cannot_delete_last_notebook() -> None:
    auth, headers = register("math_user")
    response = client.delete(
        f"/api/notebooks/{auth['initialNotebookId']}",
        headers=headers,
    )
    assert response.status_code == 409


def test_second_notebook_can_be_deleted() -> None:
    auth, headers = register("math_user")
    second = client.post(
        "/api/notebooks",
        headers=headers,
        json={"title": "Кр 2"},
    )
    assert second.status_code == 201

    listed = client.get("/api/notebooks", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    deleted = client.delete(f"/api/notebooks/{second.json()['id']}", headers=headers)
    assert deleted.status_code == 204
    remaining = client.get("/api/notebooks", headers=headers).json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == auth["initialNotebookId"]


def test_same_notebook_title_is_allowed() -> None:
    _, headers = register("math_user")
    first = client.post("/api/notebooks", headers=headers, json={"title": "Кр 2"})
    second = client.post("/api/notebooks", headers=headers, json={"title": "Кр 2"})
    assert first.status_code == 201
    assert second.status_code == 201


def test_section_limit_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.sections.MAX_SECTIONS_PER_USER", 1)
    _, headers = register("math_user")
    assert (
        client.post("/api/sections", headers=headers, json={"title": "Алгебра"}).status_code
        == 201
    )
    limited = client.post("/api/sections", headers=headers, json={"title": "Матан"})
    assert limited.status_code == 422


def test_notebook_limit_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.notebooks.MAX_NOTEBOOKS_PER_USER", 1)
    _, headers = register("math_user")
    limited = client.post("/api/notebooks", headers=headers, json={"title": "Кр 2"})
    assert limited.status_code == 422
