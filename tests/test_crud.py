import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import PrintModelMaterial


RESOURCES = ("designers", "categories", "materials", "print-models")


def model_data(owner_id=1, **changes):
    return {
        "name": "Куб", "instructions": "Печат със слой 0.2 mm",
        "difficulty": "easy",
        "print_time_minutes": 20, "copies": 1, "designer_id": owner_id,
        "category_id": None, **changes,
    }


@pytest.fixture
def designer_id(api):
    response = api("POST", "/designers", json={"name": "Иван", "email": "ivan@example.com"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.parametrize("resource", RESOURCES)
def test_full_crud_cycle(api, resource):
    assert api("GET", f"/{resource}").json() == []
    data = {"name": "  Кутия  "}
    if resource == "designers":
        data["email"] = "  IVAN@example.com  "
    elif resource == "print-models":
        designer = api("POST", "/designers", json={"name": "Иван", "email": "ivan@example.com"})
        assert designer.status_code == 201
        data = model_data(designer.json()["id"], name="  Кутия  ")

    created = api("POST", f"/{resource}", json=data)
    assert created.status_code == 201, created.text
    saved = created.json()
    assert isinstance(saved["id"], int) and saved["id"] > 0
    assert saved["name"] == "Кутия"
    assert set(saved) == set(data) | {"id"}
    if resource == "designers":
        assert saved["email"] == "ivan@example.com"
    path = f"/{resource}/{saved['id']}"
    assert api("GET", path).json() == saved
    assert api("GET", f"/{resource}").json() == [saved]

    updated = api("PUT", path, json={**data, "name": "  Нова кутия  "})
    assert updated.status_code == 200, updated.text
    assert updated.json() == {**saved, "name": "Нова кутия"}
    assert api("GET", path).json() == updated.json()
    deleted = api("DELETE", path)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert api("GET", path).status_code == 404
    assert api("GET", f"/{resource}").json() == []


@pytest.mark.parametrize("resource", RESOURCES)
@pytest.mark.parametrize("method", ("GET", "PUT", "DELETE"))
def test_missing_record_returns_404(api, resource, method):
    data = {"name": "Кутия"}
    if resource == "designers":
        data["email"] = "ivan@example.com"
    elif resource == "print-models":
        data = model_data()
    kwargs = {"json": data} if method == "PUT" else {}
    response = api(method, f"/{resource}/999", **kwargs)
    assert response.status_code == 404
    assert set(response.json()) == {"message"}
    assert isinstance(response.json()["message"], str)


@pytest.mark.parametrize("resource", RESOURCES)
@pytest.mark.parametrize("record_id", (0, -1, "abc"))
def test_invalid_path_id_returns_422(api, resource, record_id):
    assert api("GET", f"/{resource}/{record_id}").status_code == 422


@pytest.mark.parametrize("resource", RESOURCES)
@pytest.mark.parametrize("name", ("", " \t\n ", None))
def test_invalid_names_return_422(api, resource, name):
    data = {"name": name}
    if resource == "designers":
        data["email"] = "ivan@example.com"
    elif resource == "print-models":
        data = model_data(name=name)
    assert api("POST", f"/{resource}", json=data).status_code == 422
    assert api("GET", f"/{resource}").json() == []


@pytest.mark.parametrize("email", ("invalid", "", "   ", None, 123))
def test_invalid_email_returns_422(api, email):
    assert api("POST", "/designers", json={"name": "Иван", "email": email}).status_code == 422


@pytest.mark.parametrize("changes", [
    {"instructions": " \t "}, {"instructions": None},
    {"print_time_minutes": 0}, {"print_time_minutes": -1},
    {"print_time_minutes": 1.5}, {"print_time_minutes": True}, {"print_time_minutes": "20"},
    {"copies": 0}, {"copies": -1}, {"copies": 1.5}, {"copies": True}, {"copies": "1"},
    {"designer_id": 0}, {"designer_id": None}, {"designer_id": True},
    {"category_id": 0}, {"category_id": True},
])
def test_invalid_print_model_fields_return_422(api, changes):
    assert api("POST", "/print-models", json=model_data(**changes)).status_code == 422


@pytest.mark.parametrize("resource", RESOURCES)
def test_unknown_and_missing_fields_are_rejected(api, resource):
    data = {"name": "Кутия"}
    if resource == "designers":
        data["email"] = "ivan@example.com"
    elif resource == "print-models":
        data = model_data()
    assert api("POST", f"/{resource}", json={**data, "name_key": "forged"}).status_code == 422
    assert api("POST", f"/{resource}", json={**data, "id": 100}).status_code == 422
    assert api("POST", f"/{resource}", json={}).status_code == 422


@pytest.mark.parametrize("resource", ("categories", "materials"))
def test_name_conflicts_on_create_and_update_preserve_records(api, resource):
    first = api("POST", f"/{resource}", json={"name": "Кутия"})
    assert first.status_code == 201
    duplicate = api("POST", f"/{resource}", json={"name": "  КУТИЯ  "})
    assert duplicate.status_code == 409
    second = api("POST", f"/{resource}", json={"name": "Друго"}).json()
    path = f"/{resource}/{second['id']}"
    assert api("PUT", path, json={"name": " кутия "}).status_code == 409
    assert api("GET", path).json() == second
    assert len(api("GET", f"/{resource}").json()) == 2
    assert api("PUT", path, json={"name": "Ново"}).status_code == 200
    assert api("POST", f"/{resource}", json={"name": " ДРУГО "}).status_code == 201


def test_unique_email_and_repeated_designer_names(api, designer_id):
    assert api("POST", "/designers", json={"name": "Петър", "email": " IVAN@example.com "}).status_code == 409
    second = api("POST", "/designers", json={"name": "Иван", "email": "second@example.com"})
    assert second.status_code == 201
    path = f"/designers/{second.json()['id']}"
    assert api("PUT", path, json={"name": "Нов", "email": "IVAN@example.com"}).status_code == 409
    assert api("GET", path).json() == second.json()


def test_model_names_are_unique_per_designer_on_create_and_update(api, designer_id):
    first = api("POST", "/print-models", json=model_data(designer_id))
    assert first.status_code == 201
    duplicate = api("POST", "/print-models", json=model_data(designer_id, name="  КУБ  "))
    assert duplicate.status_code == 409
    other = api("POST", "/designers", json={"name": "Иван", "email": "second@example.com"}).json()
    second = api("POST", "/print-models", json=model_data(other["id"]))
    assert second.status_code == 201
    path = f"/print-models/{second.json()['id']}"
    assert api("PUT", path, json=model_data(designer_id)).status_code == 409
    assert api("GET", path).json() == second.json()
    assert len(api("GET", "/print-models").json()) == 2


@pytest.mark.parametrize("changes", [{"designer_id": 999}, {"category_id": 999}])
def test_missing_related_records_return_404_on_create_and_update(api, designer_id, changes):
    model = api("POST", "/print-models", json=model_data(designer_id))
    assert model.status_code == 201
    assert api("POST", "/print-models", json=model_data(designer_id, **changes)).status_code == 404
    path = f"/print-models/{model.json()['id']}"
    assert api("PUT", path, json=model_data(designer_id, **changes)).status_code == 404
    assert api("GET", path).json() == model.json()


def test_optional_category_and_no_scaling_limit_on_stored_copies(api, designer_id):
    category = api("POST", "/categories", json={"name": "Играчки"}).json()
    data = model_data(designer_id, category_id=category["id"], copies=100)
    model = api("POST", "/print-models", json=data)
    assert model.status_code == 201
    assert model.json()["copies"] == 100
    path = f"/print-models/{model.json()['id']}"
    data.pop("category_id")
    updated = api("PUT", path, json=data)
    assert updated.status_code == 200
    assert updated.json()["category_id"] is None


def test_put_validates_full_body_and_preserves_record_on_error(api, designer_id):
    designer_path = f"/designers/{designer_id}"
    assert api("PUT", designer_path, json={"name": "Нов"}).status_code == 422
    assert api("PUT", designer_path, json={"name": "  ", "email": "invalid"}).status_code == 422
    assert api("GET", designer_path).json()["name"] == "Иван"
    model = api("POST", "/print-models", json=model_data(designer_id)).json()
    path = f"/print-models/{model['id']}"
    assert api("PUT", path, json=model_data(designer_id, copies=0)).status_code == 422
    assert api("GET", path).json() == model


def test_delete_rules_through_api(api, database, designer_id):
    category = api("POST", "/categories", json={"name": "Играчки"}).json()
    material = api("POST", "/materials", json={"name": "PLA"}).json()
    model = api("POST", "/print-models", json=model_data(designer_id, category_id=category["id"])).json()
    with Session(database) as session:
        session.add(PrintModelMaterial(print_model_id=model["id"], material_id=material["id"],
                                       quantity=10, unit="g"))
        session.commit()

    assert api("DELETE", f"/designers/{designer_id}").status_code == 409
    assert api("DELETE", f"/materials/{material['id']}").status_code == 409
    assert api("GET", f"/designers/{designer_id}").status_code == 200
    assert api("GET", f"/materials/{material['id']}").status_code == 200
    assert api("DELETE", f"/categories/{category['id']}").status_code == 204
    assert api("GET", f"/print-models/{model['id']}").json()["category_id"] is None
    assert api("DELETE", f"/print-models/{model['id']}").status_code == 204
    assert api("GET", f"/materials/{material['id']}").status_code == 200
    with Session(database) as session:
        assert session.scalars(select(PrintModelMaterial)).all() == []
    assert api("DELETE", f"/designers/{designer_id}").status_code == 204
    assert api("DELETE", f"/materials/{material['id']}").status_code == 204


def test_swagger_documents_all_crud_operations(api):
    paths = api("GET", "/openapi.json").json()["paths"]
    for resource in RESOURCES:
        assert {"get", "post"} <= paths[f"/{resource}"].keys()
        detail_path = next(path for path in paths if path.startswith(f"/{resource}/{{"))
        assert {"get", "put", "delete"} <= paths[detail_path].keys()


@pytest.mark.parametrize("resource", RESOURCES)
def test_path_id_above_database_integer_range_returns_422(api, resource):
    assert api("GET", f"/{resource}/{2**63}").status_code == 422
    assert api("GET", f"/{resource}/{2**63 - 1}").status_code == 404


@pytest.mark.parametrize("field", ("print_time_minutes", "copies", "designer_id", "category_id"))
def test_body_integer_overflow_is_rejected_without_changing_model(api, designer_id, field):
    original = api("POST", "/print-models", json=model_data(designer_id)).json()
    invalid = model_data(designer_id, **{field: 2**63})
    assert api("POST", "/print-models", json=invalid).status_code == 422
    path = f"/print-models/{original['id']}"
    assert api("PUT", path, json=invalid).status_code == 422
    assert api("GET", path).json() == original


def test_largest_database_integer_is_valid_for_time_and_copies(api, designer_id):
    data = model_data(designer_id, copies=2**63 - 1, print_time_minutes=2**63 - 1)
    response = api("POST", "/print-models", json=data)
    assert response.status_code == 201
    assert response.json()["copies"] == data["copies"]
    assert response.json()["print_time_minutes"] == data["print_time_minutes"]
