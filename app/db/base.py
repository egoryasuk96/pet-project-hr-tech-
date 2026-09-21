"""SQLAlchemy declarative base for domain models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for ORM models. Tables are registered via app.domain imports."""
