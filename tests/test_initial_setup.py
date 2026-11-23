import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def database(tmp_path):
    from backend.database import make_engine

    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield engine
    engine.dispose()


def test_swagger_and_health():
    from backend.main import app

    async def check_endpoints():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            health = await client.get("/health")
            assert health.status_code == 200
            assert health.json() == {"status": "ok"}
            assert (await client.get("/docs")).status_code == 200
            specification = await client.get("/openapi.json")
            assert specification.status_code == 200
            assert specification.json()["info"]["title"] == "Print Models API"

    asyncio.run(check_endpoints())


def test_initial_migration_creates_tables_and_enables_foreign_keys(database):
    assert set(inspect(database).get_table_names()) == {
        "alembic_version", "designers", "categories", "materials",
        "print_models", "print_model_materials",
    }
    with database.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        assert connection.scalar(text("SELECT version_num FROM alembic_version"))


def test_name_uniqueness_ignores_case_and_surrounding_spaces(database):
    from backend.models import Category, Designer, Material, PrintModel

    with Session(database) as session:
        for entity in (Category, Material):
            session.add(entity(name="Кутия"))
            session.commit()
            session.add(entity(name="  КУТИЯ  "))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

        first = Designer(name="Иван", email="first@example.com")
        second = Designer(name="Иван", email="second@example.com")
        session.add_all([first, second])
        session.commit()
        first_id = first.id
        session.add_all([
            PrintModel(name="Кутия", instructions="Печат", print_time_minutes=60,
                       copies=2, designer_id=first_id),
            PrintModel(name="КУТИЯ", instructions="Печат", print_time_minutes=60,
                       copies=2, designer_id=second.id),
        ])
        session.commit()
        session.add(PrintModel(name=" кутия ", instructions="Печат", print_time_minutes=60,
                               copies=2, designer_id=first_id))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_email_is_unique(database):
    from backend.models import Designer

    with Session(database) as session:
        session.add(Designer(name="Иван", email="ivan@example.com"))
        session.commit()
        session.add(Designer(name="Петър", email=" IVAN@example.com "))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_deletion_preserves_models_and_materials(database):
    from backend.models import Category, Designer, Material, PrintModel, PrintModelMaterial

    with Session(database) as session:
        designer = Designer(name="Иван", email="ivan@example.com")
        category = Category(name="Играчки")
        material = Material(name="PLA")
        model = PrintModel(name="Куб", instructions="Печат", print_time_minutes=20,
                           copies=1, designer=designer, category=category)
        link = PrintModelMaterial(print_model=model, material=material, quantity=10, unit="g")
        session.add(link)
        session.commit()
        designer_id, material_id, model_id = designer.id, material.id, model.id

        # The database must reject deletion even if API checks are bypassed.
        for table, record_id in (("designers", designer_id), ("materials", material_id)):
            with pytest.raises(IntegrityError):
                session.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": record_id})
            session.rollback()

        session.delete(category)
        session.commit()
        session.expire_all()
        assert session.get(PrintModel, model_id).category_id is None

        session.delete(session.get(PrintModel, model_id))
        session.commit()
        assert session.get(Material, material_id) is not None
        assert session.get(Designer, designer_id) is not None
        assert session.scalars(select(PrintModelMaterial)).all() == []


def test_material_cannot_be_attached_twice(database):
    from backend.models import Designer, Material, PrintModel, PrintModelMaterial

    with Session(database) as session:
        model = PrintModel(name="Куб", instructions="Печат", print_time_minutes=20,
                           copies=1, designer=Designer(name="Иван", email="ivan@example.com"))
        material = Material(name="PLA")
        session.add(PrintModelMaterial(print_model=model, material=material, quantity=10, unit="g"))
        session.commit()
        model_id, material_id = model.id, material.id
        session.add(PrintModelMaterial(print_model_id=model_id, material_id=material_id,
                                       quantity=99, unit="m"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        original = session.get(PrintModelMaterial, (model_id, material_id))
        assert original.quantity == 10
        assert original.unit == "g"


@pytest.mark.parametrize("column,value", [("quantity", 0), ("quantity", -1), ("unit", "kg")])
def test_database_rejects_invalid_material_amounts(database, column, value):
    from backend.models import Designer, Material, PrintModel, PrintModelMaterial

    with Session(database) as session:
        model = PrintModel(name="Куб", instructions="Печат", print_time_minutes=20,
                           copies=1, designer=Designer(name="Иван", email="ivan@example.com"))
        material = Material(name="PLA")
        session.add(PrintModelMaterial(print_model=model, material=material, quantity=10, unit="g"))
        session.commit()
        with pytest.raises(IntegrityError):
            session.execute(text(f"UPDATE print_model_materials SET {column} = :value"), {"value": value})
        session.rollback()


@pytest.mark.parametrize("column,value", [
    ("print_time_minutes", 0), ("copies", 0), ("name", "  "), ("instructions", "  "),
])
def test_database_rejects_invalid_print_model_values(database, column, value):
    from backend.models import Designer, PrintModel

    with Session(database) as session:
        session.add(PrintModel(name="Куб", instructions="Печат", print_time_minutes=20,
                               copies=1, designer=Designer(name="Иван", email="ivan@example.com")))
        session.commit()
        with pytest.raises(IntegrityError):
            session.execute(text(f"UPDATE print_models SET {column} = :value"), {"value": value})
        session.rollback()
