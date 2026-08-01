from fastapi.testclient import TestClient

from app.core.config import settings


def test_private_user_creation_is_not_exposed_outside_local(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": "pollo@listo.com",
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    assert settings.ENVIRONMENT == "test"
    assert r.status_code == 404
    assert r.json()["error"] == {
        "code": "not_found",
        "message": "Resource not found",
    }
