from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    database_engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(database_engine, "connect")
    def enable_foreign_keys(connection, connection_record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return database_engine


DATABASE_PATH = Path(__file__).resolve().parents[1] / "print_models.db"
engine = make_engine(f"sqlite:///{DATABASE_PATH.as_posix()}")
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
