"""Database engine and session management for PyPlanner."""

from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./recipe_manager.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """Create all tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session.

    Usage:
        with get_session() as session:
            session.add(obj)
            session.commit()
    """
    with Session(engine) as session:
        yield session
