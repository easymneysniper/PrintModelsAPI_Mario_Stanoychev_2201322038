from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import make_engine
from backend.models import Designer, PrintModel


@pytest.fixture
def model_payload(api):
    designer = api("POST", "/designers", json={"name": "Иван", "email": "ivan@example.com"})
    assert designer.status_code == 201
    return {
        "name": "Куб", "instructions": "Печат със слой 0.2 mm",
        "print_time_minutes": 30, "copies": 4,
        "designer_id": designer.json()["id"], "category_id": None,
        "difficulty": "easy",
    }


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_create_read_and_edit_difficulty(api, model_payload, difficulty):
    payload = {**model_payload, "difficulty": difficulty}
    created = api("POST", "/print-models", json=payload)
    assert created.status_code == 201
    model = created.json()
    assert model["difficulty"] == difficulty
    path = f"/print-models/{model['id']}"
    assert api("GET", path).json() == model
    assert api("GET", "/print-models").json() == [model]
    assert api("GET", f"/designers/{model['designer_id']}/print-models").json() == [model]
    assert api("GET", f"{path}/scaled", params={"copies": 8}).json()["difficulty"] == difficulty
    changed = "medium" if difficulty == "hard" else "hard"
    updated = api("PUT", path, json={**payload, "difficulty": changed})
    assert updated.status_code == 200
    assert updated.json() == {**model, "difficulty": changed}
    assert api("GET", path).json() == updated.json()


@pytest.mark.parametrize("difficulty", ("", " ", "Easy", "medium ", "invalid", 1, True, None))
def test_invalid_difficulty_does_not_change_data(api, model_payload, difficulty):
    original = api("POST", "/print-models", json=model_payload)
    assert original.status_code == 201
    path = f"/print-models/{original.json()['id']}"
    invalid = {**model_payload, "difficulty": difficulty}
    assert api("POST", "/print-models", json=invalid).status_code == 422
    assert api("PUT", path, json=invalid).status_code == 422
    assert api("GET", path).json() == original.json()
    assert api("GET", "/print-models").json() == [original.json()]


def test_difficulty_is_required_for_create_and_update(api, model_payload):
    original = api("POST", "/print-models", json=model_payload)
    assert original.status_code == 201
    path = f"/print-models/{original.json()['id']}"
    model_payload.pop("difficulty")
    assert api("POST", "/print-models", json=model_payload).status_code == 422
    assert api("PUT", path, json=model_payload).status_code == 422
    assert api("GET", path).json() == original.json()


def test_swagger_documents_required_difficulty(api):
    schemas = api("GET", "/openapi.json").json()["components"]["schemas"]
    for name in ("PrintModelCreate", "PrintModelRead", "ScaledPrintModelRead"):
        schema = schemas[name]
        assert "difficulty" in schema["required"]
        assert schema["properties"]["difficulty"]["enum"] == ["easy", "medium", "hard"]


@pytest.mark.parametrize("difficulty", ("invalid", "Easy", "", None))
def test_database_rejects_invalid_difficulty(database, difficulty):
    with Session(database) as session:
        model = PrintModel(name="Куб", instructions="Печат", print_time_minutes=20,
                           copies=1, designer=Designer(name="Иван", email="ivan@example.com"))
        session.add(model)
        session.commit()
        model_id = model.id
        assert model.difficulty == "easy"
        with pytest.raises(IntegrityError):
            session.execute(text("UPDATE print_models SET difficulty = :value WHERE id = :id"),
                            {"value": difficulty, "id": model_id})
        session.rollback()
        assert session.get(PrintModel, model_id).difficulty == "easy"


def snapshot(connection):
    return {
        table: [dict(row) for row in connection.execute(text(f"SELECT * FROM {table} ORDER BY 1, 2")).mappings()]
        for table in ("designers", "categories", "materials", "print_models", "print_model_materials")
    }


def test_difficulty_migration_preserves_existing_records_and_relations(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0001_initial")
            assert "difficulty" not in {column["name"] for column in inspect(connection).get_columns("print_models")}
            connection.execute(text("INSERT INTO designers (id, name, email) VALUES (10, 'Иван', 'ivan@example.com')"))
            connection.execute(text("INSERT INTO categories (id, name, name_key) VALUES (20, 'Играчки', 'играчки')"))
            connection.execute(text("INSERT INTO materials (id, name, name_key) VALUES (30, 'PLA', 'pla')"))
            connection.execute(text(
                "INSERT INTO print_models (id, name, name_key, instructions, print_time_minutes, copies, designer_id, category_id) "
                "VALUES (40, 'Куб', 'куб', 'Печат', 30, 4, 10, 20), "
                "(41, 'Кутия', 'кутия', 'Още инструкции', 60, 2, 10, NULL)"
            ))
            connection.execute(text(
                "INSERT INTO print_model_materials (print_model_id, material_id, quantity, unit) "
                "VALUES (40, 30, 12.5, 'g'), (41, 30, 2, 'm')"
            ))
            before = snapshot(connection)

        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            columns = {column["name"]: column for column in inspect(connection).get_columns("print_models")}
            assert "difficulty" in columns
            assert columns["difficulty"]["nullable"] is False
            after = snapshot(connection)
            for model in after["print_models"]:
                assert model.pop("difficulty") == "easy"
            assert after == before
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002_add_difficulty"
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
            assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
            command.upgrade(config, "head")
            command.check(config)

        # Verify reversal only in this temporary database, preserving the original data.
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "0001_initial")
            assert snapshot(connection) == before
            assert "difficulty" not in {column["name"] for column in inspect(connection).get_columns("print_models")}

        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            after = snapshot(connection)
            for model in after["print_models"]:
                assert model.pop("difficulty") == "easy"
            assert after == before
    finally:
        engine.dispose()
