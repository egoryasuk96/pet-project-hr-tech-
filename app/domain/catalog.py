"""Live catalog / configuration: types, fields, dictionaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import FieldDataType
from app.domain.mixins import IntegerPrimaryKeyMixin
from app.domain.sa_types import field_data_type_enum

if TYPE_CHECKING:
    from app.domain.process import Process
    from app.domain.request import Request
    from app.domain.routing import ApprovalRoute


class Dictionary(IntegerPrimaryKeyMixin, Base):
    """Named catalog of selectable values (FR-ADMIN-06)."""

    __tablename__ = "dictionaries"

    name: Mapped[str] = mapped_column(String, nullable=False)

    items: Mapped[list[DictionaryItem]] = relationship(back_populates="dictionary")
    field_definitions: Mapped[list[RequestFieldDefinition]] = relationship(
        back_populates="dictionary"
    )


class DictionaryItem(IntegerPrimaryKeyMixin, Base):
    """Item of a dictionary; code unique per dictionary."""

    __tablename__ = "dictionary_items"
    __table_args__ = (
        UniqueConstraint("dictionary_id", "code", name="uq_dictionary_items_dictionary_code"),
    )

    dictionary_id: Mapped[int] = mapped_column(
        ForeignKey("dictionaries.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    dictionary: Mapped[Dictionary] = relationship(back_populates="items")


class RequestType(IntegerPrimaryKeyMixin, Base):
    """Live request type owned by a Process (FR-ADMIN-01)."""

    __tablename__ = "request_types"
    __table_args__ = (UniqueConstraint("code", name="uq_request_types_code"),)

    process_id: Mapped[int] = mapped_column(
        ForeignKey("processes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    process: Mapped[Process] = relationship(back_populates="request_types")
    field_definitions: Mapped[list[RequestFieldDefinition]] = relationship(
        back_populates="request_type"
    )
    approval_route: Mapped[ApprovalRoute | None] = relationship(
        back_populates="request_type",
        uselist=False,
    )
    requests: Mapped[list[Request]] = relationship(back_populates="request_type")


class RequestFieldDefinition(IntegerPrimaryKeyMixin, Base):
    """Live form field of a request type. code unique per type."""

    __tablename__ = "request_field_definitions"
    __table_args__ = (
        UniqueConstraint(
            "request_type_id",
            "code",
            name="uq_request_field_definitions_type_code",
        ),
        CheckConstraint(
            "dictionary_id IS NULL OR data_type = 'catalog'",
            name="ck_request_field_definitions_dictionary_catalog",
        ),
    )

    request_type_id: Mapped[int] = mapped_column(
        ForeignKey("request_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[FieldDataType] = mapped_column(field_data_type_enum, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    dictionary_id: Mapped[int | None] = mapped_column(
        ForeignKey("dictionaries.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    request_type: Mapped[RequestType] = relationship(back_populates="field_definitions")
    dictionary: Mapped[Dictionary | None] = relationship(back_populates="field_definitions")
