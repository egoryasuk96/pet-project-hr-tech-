"""Organizational structure: Company → Department → Employee (ADR-ORG-01)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.mixins import IntegerPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domain.identity import User


class Company(IntegerPrimaryKeyMixin, Base):
    """Demo tenant root. One company in MVP (not multi-tenant)."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    departments: Mapped[list[Department]] = relationship(back_populates="company")


class Department(IntegerPrimaryKeyMixin, Base):
    """Department within a company."""

    __tablename__ = "departments"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    company: Mapped[Company] = relationship(back_populates="departments")
    employees: Mapped[list[Employee]] = relationship(back_populates="department")


class Employee(IntegerPrimaryKeyMixin, Base):
    """HR person record. manager_employee_id is data only — not auto-routing."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_number", name="uq_employees_employee_number"),
    )

    employee_number: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String, nullable=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    manager_employee_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    position: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    department: Mapped[Department] = relationship(back_populates="employees")
    manager: Mapped[Employee | None] = relationship(
        remote_side="Employee.id",
        foreign_keys=[manager_employee_id],
        back_populates="direct_reports",
    )
    direct_reports: Mapped[list[Employee]] = relationship(
        back_populates="manager",
        foreign_keys=[manager_employee_id],
    )
    user: Mapped[User | None] = relationship(
        back_populates="employee",
        uselist=False,
    )
