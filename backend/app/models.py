from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    notebooks: Mapped[list["NotebookORM"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sections: Mapped[list["SectionORM"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SectionORM(Base):
    __tablename__ = "sections"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    owner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped[UserORM] = relationship(back_populates="sections")
    notebooks: Mapped[list["NotebookORM"]] = relationship(
        back_populates="section",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="ck_sections_position_non_negative",
        ),
        Index(
            "uq_sections_owner_id_lower_title",
            "owner_id",
            func.lower(title),
            unique=True,
        ),
        Index("ix_sections_owner_id_position", "owner_id", "position"),
    )


class NotebookORM(Base):
    __tablename__ = "notebooks"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_notebooks_version_positive"),
        CheckConstraint(
            "position >= 0",
            name="ck_notebooks_position_non_negative",
        ),
        Index(
            "ix_notebooks_owner_id_section_id_position",
            "owner_id",
            "section_id",
            "position",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    owner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    section_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        default="Лист 1",
        server_default="Лист 1",
        nullable=False,
    )
    document: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {"schemaVersion": 1, "blocks": []},
        server_default=text("""'{"schemaVersion": 1, "blocks": []}'::jsonb"""),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    owner: Mapped[UserORM] = relationship(back_populates="notebooks")
    section: Mapped[SectionORM | None] = relationship(back_populates="notebooks")
