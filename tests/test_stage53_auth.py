"""Stage 5.3 auth, /me, and request-type catalog tests."""

from __future__ import annotations

from tests.conftest import TEST_PASSWORD, ApiDataset, auth_header


def test_login_success(client, dataset: ApiDataset) -> None:
    response = client.post(
        "/auth/login",
        json={"login": dataset.employee_a_login, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["login"] == dataset.employee_a_login
    assert "employee" in body["user"]["roles"]
    assert "password_hash" not in body["user"]


def test_login_wrong_password(client, dataset: ApiDataset) -> None:
    response = client.post(
        "/auth/login",
        json={"login": dataset.employee_a_login, "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_INVALID_CREDENTIALS"


def test_login_unknown_user(client, dataset: ApiDataset) -> None:
    response = client.post(
        "/auth/login",
        json={"login": "unknown.user", "password": TEST_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_INVALID_CREDENTIALS"


def test_protected_without_token(client, dataset: ApiDataset) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_UNAUTHORIZED"


def test_protected_with_invalid_token(client, dataset: ApiDataset) -> None:
    response = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_UNAUTHORIZED"


def test_me_returns_current_user(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    response = client.get("/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["login"] == dataset.employee_a_login
    assert body["roles"] == ["employee"]


def test_me_does_not_expose_password_hash(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    response = client.get("/me", headers=headers)
    assert response.status_code == 200
    assert "password_hash" not in response.json()
    assert "password" not in response.json()


def test_list_active_request_types(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    response = client.get("/request-types", headers=headers)
    assert response.status_code == 200
    body = response.json()
    names = {item["name"] for item in body}
    assert "Отпуск" in names
    assert "Справка" in names
    assert "Inactive" not in names
    assert all("fields" not in item for item in body)


def test_request_type_schema_contains_definitions(client, dataset: ApiDataset) -> None:
    headers = auth_header(client, dataset.employee_a_login)
    response = client.get(f"/request-types/{dataset.vacation_type_id}/schema", headers=headers)
    assert response.status_code == 200
    body = response.json()
    codes = [field["code"] for field in body["fields"]]
    assert codes == ["date_from", "date_to", "comment"]
    assert body["fields"][0]["data_type"] == "date"
    assert body["fields"][0]["required"] is True

    catalog_schema = client.get(
        f"/request-types/{dataset.certificate_type_id}/schema",
        headers=headers,
    )
    assert catalog_schema.status_code == 200
    catalog_field = catalog_schema.json()["fields"][0]
    assert catalog_field["data_type"] == "catalog"
    assert catalog_field["dictionary"] is not None
    item_ids = {item["id"] for item in catalog_field["dictionary"]["items"]}
    assert str(dataset.catalog_item_id) in item_ids
