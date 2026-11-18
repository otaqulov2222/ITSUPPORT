from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.db.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.org import Branch
    from app.db.models.rbac import UserRole


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list[UserRole]] = relationship(back_populates="user", cascade="all, delete-orphan")
    employee_profile: Mapped[Employee | None] = relationship(back_populates="user", uselist=False)


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("branch_id", "employee_code", name="uq_employees_branch_code"),
    )

    branch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, unique=True
    )
    employee_code: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    position: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role_code: Mapped[str] = mapped_column(String(64), default="PHARMACIST", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    branch: Mapped[Branch] = relationship(back_populates="employees")
    user: Mapped[User | None] = relationship(back_populates="employee_profile")
