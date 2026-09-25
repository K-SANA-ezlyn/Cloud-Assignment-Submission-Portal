"""
User model — students and teachers of the portal.

Cloud concept: this table lives in SQLite locally and in Supabase Postgres
in cloud mode. Identical code, different provider.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


def _uuid() -> str:
    """Globally-unique primary key (safe to expose in URLs and object paths)."""
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    """Server-side UTC timestamp — never trust client clocks."""
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Nullable: in Supabase-Auth mode the password lives with the auth provider.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False), default=UserRole.STUDENT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def public_dict(self) -> dict:
        """Safe representation — NEVER include password_hash."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
