"""Database setup for Campaign Optimizer."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for ORM models."""


settings = get_settings()

engine = create_engine(
    settings.database_url,
    future=True,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def init_db() -> None:
    """Create database tables if they do not exist."""

    # Import models so SQLAlchemy registers them before creating tables
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)