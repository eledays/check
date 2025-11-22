from app import db

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, backref, Mapped, mapped_column
from enum import Enum
from typing import Optional

import datetime


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class User(db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="creator", lazy=True)


class Project(db.Model):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    goals: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)

    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", lazy=True, cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="project", lazy=True, cascade="all, delete-orphan")

    created_at = mapped_column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class Task(db.Model):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")

    created_at = mapped_column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class Note(db.Model):
    __tablename__ = "note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(512), nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="notes")
