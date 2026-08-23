import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.notebook import NotebookDocument


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
