import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from backend.database import get_db, make_engine
from backend.main import app


@pytest.fixture
def database(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def api(database):
    def override_get_db():
        with Session(database) as session:
            yield session

    def request(method, path, **kwargs):
        async def send():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield request
    finally:
        del app.dependency_overrides[get_db]
