import pytest


def create(api, path, data):
    response = api("POST", path, json=data)
    assert response.status_code == 201, response.text
    return response.json()


def model_data(designer_id, **changes):
    return {
        "name": "Куб", "instructions": "Печат със слой 0.2 mm",
        "difficulty": "easy",
        "print_time_minutes": 30, "copies": 4, "designer_id": designer_id,
        "category_id": None, **changes,
    }


@pytest.fixture
def model(api):
    designer = create(api, "/designers", {"name": "Иван", "email": "ivan@example.com"})
    return create(api, "/print-models", model_data(designer["id"]))


@pytest.fixture
def material(api):
    return create(api, "/materials", {"name": "PLA"})


def test_related_lists_distinguish_missing_and_empty_parents(api, model):
    assert api("GET", "/designers/999/print-models").status_code == 404
    assert api("GET", "/print-models/999/materials").status_code == 404
    materials = api("GET", f"/print-models/{model['id']}/materials")
    assert materials.status_code == 200 and materials.json() == []
    designer = create(api, "/designers", {"name": "Иван", "email": "second@example.com"})
    models = api("GET", f"/designers/{designer['id']}/print-models")
    assert models.status_code == 200 and models.json() == []


def test_designer_models_exclude_other_designers(api, model):
    designer = create(api, "/designers", {"name": "Иван", "email": "second@example.com"})
    other = create(api, "/print-models", model_data(designer["id"]))
    first = api("GET", f"/designers/{model['designer_id']}/print-models")
    second = api("GET", f"/designers/{designer['id']}/print-models")
    assert first.status_code == second.status_code == 200
    assert first.json() == [model]
    assert second.json() == [other]


@pytest.mark.parametrize("unit", ("g", "m", "ml"))
def test_attach_edit_and_remove_material(api, model, material, unit):
    collection = f"/print-models/{model['id']}/materials"
    path = f"{collection}/{material['id']}"
    created = api("POST", collection, json={"material_id": material["id"], "quantity": 12.5, "unit": unit})
    expected = {"material_id": material["id"], "quantity": 12.5, "unit": unit, "material": material}
    assert created.status_code == 201
    assert created.json() == expected
    assert api("GET", collection).json() == [expected]
    updated = api("PUT", path, json={"quantity": 20, "unit": "ml"})
    expected.update(quantity=20, unit="ml")
    assert updated.status_code == 200 and updated.json() == expected
    assert api("GET", collection).json() == [expected]
    assert api("DELETE", f"/materials/{material['id']}").status_code == 409
    removed = api("DELETE", path)
    assert removed.status_code == 204 and removed.content == b""
    assert api("GET", collection).json() == []
    assert api("GET", f"/materials/{material['id']}").json() == material
    assert api("GET", f"/print-models/{model['id']}").json() == model
    assert api("PUT", path, json={"quantity": 1, "unit": "g"}).status_code == 404
    assert api("DELETE", path).status_code == 404


def test_duplicate_attachment_does_not_change_amount(api, model, material):
    path = f"/print-models/{model['id']}/materials"
    original = create(api, path, {"material_id": material["id"], "quantity": 10, "unit": "g"})
    duplicate = api("POST", path, json={"material_id": material["id"], "quantity": 99, "unit": "m"})
    assert duplicate.status_code == 409
    assert api("GET", path).json() == [original]


def test_same_material_has_independent_quantities_for_each_model(api, model, material):
    other = create(api, "/print-models", model_data(model["designer_id"], name="Кутия"))
    first_path = f"/print-models/{model['id']}/materials"
    other_path = f"/print-models/{other['id']}/materials"
    create(api, first_path, {"material_id": material["id"], "quantity": 10, "unit": "g"})
    saved_other = create(api, other_path, {"material_id": material["id"], "quantity": 3, "unit": "m"})
    assert api("PUT", f"{first_path}/{material['id']}", json={"quantity": 25, "unit": "ml"}).status_code == 200
    assert api("GET", other_path).json() == [saved_other]
    assert api("DELETE", f"/print-models/{model['id']}").status_code == 204
    assert api("GET", other_path).json() == [saved_other]
    assert api("DELETE", f"/materials/{material['id']}").status_code == 409


@pytest.mark.parametrize("method", ("POST", "PUT", "DELETE"))
def test_missing_model_or_material_returns_404(api, model, material, method):
    for model_id, material_id in ((999, material["id"]), (model["id"], 999)):
        path = f"/print-models/{model_id}/materials"
        data = {"quantity": 10, "unit": "g"}
        if method == "POST":
            data["material_id"] = material_id
        else:
            path += f"/{material_id}"
        kwargs = {"json": data} if method != "DELETE" else {}
        assert api(method, path, **kwargs).status_code == 404


@pytest.mark.parametrize("changes", [
    {"quantity": 0}, {"quantity": -1}, {"quantity": True},
    {"quantity": "10"}, {"quantity": None}, {"unit": "kg"},
    {"unit": "G"}, {"unit": ""}, {"unit": None}, {"extra": 1},
])
def test_invalid_amounts_do_not_change_existing_link(api, model, material, changes):
    path = f"/print-models/{model['id']}/materials"
    saved = create(api, path, {"material_id": material["id"], "quantity": 10, "unit": "g"})
    amount = {"quantity": 20, "unit": "m", **changes}
    assert api("POST", path, json={"material_id": material["id"], **amount}).status_code == 422
    assert api("PUT", f"{path}/{material['id']}", json=amount).status_code == 422
    assert api("GET", path).json() == [saved]


@pytest.mark.parametrize("value", (0, True, "1", None, 2**63))
def test_invalid_material_id_is_rejected(api, model, value):
    path = f"/print-models/{model['id']}/materials"
    assert api("POST", path, json={"material_id": value, "quantity": 10, "unit": "g"}).status_code == 422


@pytest.mark.parametrize("body", ({}, {"quantity": 1}, {"unit": "g"}))
def test_material_amount_fields_are_required(api, model, material, body):
    path = f"/print-models/{model['id']}/materials"
    assert api("POST", path, json={"material_id": material["id"], **body}).status_code == 422
    assert api("PUT", f"{path}/{material['id']}", json=body).status_code == 422


@pytest.mark.parametrize("quantity", ("1e400", "-1e400", "NaN", "Infinity"))
def test_nonfinite_quantity_returns_422_without_changing_link(api, model, material, quantity):
    path = f"/print-models/{model['id']}/materials"
    saved = create(api, path, {"material_id": material["id"], "quantity": 10, "unit": "g"})
    headers = {"Content-Type": "application/json"}
    created = api("POST", path, content=f'{{"material_id": {material["id"]}, "quantity": {quantity}, "unit": "g"}}', headers=headers)
    updated = api("PUT", f"{path}/{material['id']}", content=f'{{"quantity": {quantity}, "unit": "g"}}', headers=headers)
    assert created.status_code == updated.status_code == 422
    assert api("GET", path).json() == [saved]


@pytest.fixture
def catalog(api):
    designer = create(api, "/designers", {"name": "Иван", "email": "ivan@example.com"})
    first_category = create(api, "/categories", {"name": "Играчки"})
    second_category = create(api, "/categories", {"name": "Инструменти"})
    specifications = [
        ("Куб малък", first_category["id"], 30),
        ("КУБ голям", first_category["id"], 60),
        ("Куб шаблон", second_category["id"], 30),
        ("Кутия", first_category["id"], 20),
        ("Без категория", None, 10),
        ("100%_модел/тест", None, 15),
    ]
    models = [create(api, "/print-models", model_data(
        designer["id"], name=name, category_id=category, print_time_minutes=minutes,
    )) for name, category, minutes in specifications]
    return first_category["id"], models


@pytest.mark.parametrize("parameters,expected_indices", [
    ({"name": "  кУб  "}, [0, 1, 2]),
    ({"category_id": "category"}, [0, 1, 3]),
    ({"max_print_time": 30}, [0, 2, 3, 4, 5]),
    ({"name": "куб", "category_id": "category"}, [0, 1]),
    ({"name": "куб", "max_print_time": 30}, [0, 2]),
    ({"category_id": "category", "max_print_time": 30}, [0, 3]),
    ({"name": "куб", "category_id": "category", "max_print_time": 30}, [0]),
    ({"category_id": 999}, []),
    ({"name": "няма"}, []),
    ({"max_print_time": 1}, []),
    ({"name": " \t "}, [0, 1, 2, 3, 4, 5]),
    ({"name": "%_"}, [5]),
    ({"name": "/тест"}, [5]),
    ({"name": "' OR 1=1 --"}, []),
])
def test_combined_database_filters(api, catalog, parameters, expected_indices):
    category_id, models = catalog
    parameters = {key: category_id if value == "category" else value for key, value in parameters.items()}
    response = api("GET", "/print-models", params=parameters)
    assert response.status_code == 200
    assert response.json() == [models[index] for index in expected_indices]


@pytest.mark.parametrize("parameter", ("category_id", "max_print_time"))
@pytest.mark.parametrize("value", (0, -1, "abc", "1.5", 2**63))
def test_invalid_filters_return_422(api, parameter, value):
    assert api("GET", "/print-models", params={parameter: value}).status_code == 422


@pytest.mark.parametrize("copies", (1, 2, 4, 88))
def test_scaled_model_quantities_are_proportional_and_not_persisted(api, model, material, copies):
    other_material = create(api, "/materials", {"name": "Смола"})
    path = f"/print-models/{model['id']}"
    first = create(api, f"{path}/materials", {"material_id": material["id"], "quantity": 40, "unit": "g"})
    second = create(api, f"{path}/materials", {"material_id": other_material["id"], "quantity": 2.5, "unit": "ml"})
    response = api("GET", f"{path}/scaled", params={"copies": copies})
    assert response.status_code == 200
    scaled = response.json()
    assert {key: value for key, value in scaled.items() if key != "materials"} == {**model, "copies": copies}
    assert scaled["materials"] == [
        {**first, "quantity": pytest.approx(40 * copies / model["copies"])},
        {**second, "quantity": pytest.approx(2.5 * copies / model["copies"])},
    ]
    assert api("GET", path).json() == model
    assert api("GET", f"{path}/materials").json() == [first, second]


def test_scaled_model_handles_empty_and_missing_models(api, model):
    empty = api("GET", f"/print-models/{model['id']}/scaled", params={"copies": 88})
    assert empty.status_code == 200
    assert empty.json() == {**model, "copies": 88, "materials": []}
    assert api("GET", "/print-models/999/scaled", params={"copies": 1}).status_code == 404


@pytest.mark.parametrize("copies", (0, -1, 89, "abc", "1.5", 2**63))
def test_invalid_requested_copies_return_422(api, model, copies):
    path = f"/print-models/{model['id']}/scaled"
    assert api("GET", path, params={"copies": copies}).status_code == 422


def test_requested_copies_are_required(api, model):
    assert api("GET", f"/print-models/{model['id']}/scaled").status_code == 422


@pytest.mark.parametrize("quantity,base_copies,requested_copies", [
    (1e308, 1, 88), (5e-324, 2**63 - 1, 1),
])
def test_unrepresentable_scaled_quantity_returns_422_and_preserves_data(
    api, model, material, quantity, base_copies, requested_copies,
):
    path = f"/print-models/{model['id']}"
    assert api("PUT", path, json=model_data(model["designer_id"], copies=base_copies)).status_code == 200
    saved = create(api, f"{path}/materials", {"material_id": material["id"], "quantity": quantity, "unit": "g"})
    assert api("GET", f"{path}/scaled", params={"copies": requested_copies}).status_code == 422
    assert api("GET", f"{path}/materials").json() == [saved]


def test_scaling_does_not_overflow_an_intermediate_product(api, model, material):
    path = f"/print-models/{model['id']}"
    assert api("PUT", path, json=model_data(model["designer_id"], copies=88)).status_code == 200
    create(api, f"{path}/materials", {"material_id": material["id"], "quantity": 1e308, "unit": "g"})
    response = api("GET", f"{path}/scaled", params={"copies": 88})
    assert response.status_code == 200
    assert response.json()["materials"][0]["quantity"] == 1e308


def test_openapi_documents_relationships_filters_and_scaling(api):
    paths = api("GET", "/openapi.json").json()["paths"]
    assert "get" in paths["/designers/{designer_id}/print-models"]
    assert {"get", "post"} <= paths["/print-models/{print_model_id}/materials"].keys()
    assert {"put", "delete"} <= paths["/print-models/{print_model_id}/materials/{material_id}"].keys()
    assert "get" in paths["/print-models/{print_model_id}/scaled"]
    query_names = {parameter["name"] for parameter in paths["/print-models"]["get"]["parameters"]}
    assert {"name", "category_id", "max_print_time"} <= query_names
