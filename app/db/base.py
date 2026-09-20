"""SQLAlchemy declarative base for future models (none in Stage 5.1)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for ORM models. Models are intentionally not defined yet."""
