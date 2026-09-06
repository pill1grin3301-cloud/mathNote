import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.notebook import (
    NotebookCreateRequest,
    NotebookDocument,
    NotebookPatchRequest,
)
from app.schemas.section import SectionCreateRequest, SectionPatchRequest


def test_username_is_normalized() -> None:
    payload = RegisterRequest(
        username="  Math_User  ",
        password="strong-password",
    )

    assert payload.username == "math_user"


@pytest.mark.parametrize("username", ["ab", "has-dash", "кириллица"])
def test_invalid_username_is_rejected(username: str) -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(username=username, password="strong-password")


def test_notebook_document_accepts_frontend_shape() -> None:
    document = NotebookDocument.model_validate(
        {
            "schemaVersion": 1,
            "blocks": [],
        }
    )

    assert document.model_dump(by_alias=True) == {
        "schemaVersion": 1,
        "blocks": [],
    }


def test_section_create_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        SectionCreateRequest(title="")


def test_section_patch_tracks_unset_fields() -> None:
    payload = SectionPatchRequest.model_validate({"position": 2})
    assert payload.model_dump(exclude_unset=True) == {"position": 2}


def test_notebook_create_accepts_section_id_alias() -> None:
    payload = NotebookCreateRequest.model_validate(
        {"title": "Кр 2", "sectionId": "1c0ea81e-1280-4c03-89d5-78a11dc472cc"}
    )
    assert payload.title == "Кр 2"
    assert str(payload.section_id) == "1c0ea81e-1280-4c03-89d5-78a11dc472cc"


def test_notebook_patch_null_section_id_is_set() -> None:
    payload = NotebookPatchRequest.model_validate({"sectionId": None})
    data = payload.model_dump(exclude_unset=True)
    assert "section_id" in data
    assert data["section_id"] is None


def test_notebook_patch_omitted_section_id_is_unset() -> None:
    payload = NotebookPatchRequest.model_validate({"title": "Кр 2"})
    assert "section_id" not in payload.model_dump(exclude_unset=True)
