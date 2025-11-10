from app import db

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, backref
from enum import Enum

import datetime


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class User(db.Model):
    __tablename__ = "user"

    id: Column[int] = Column(Integer, primary_key=True)
    telegram_id: Column[int] = Column(BigInteger, unique=True, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="creator", lazy=True)


class Project(db.Model):
    __tablename__ = "project"

    id: Column[int] = Column(Integer, primary_key=True)
    name: Column[str] = Column(String(128), nullable=False)
    short_name: Column[str] = Column(String(16), nullable=False)
    description: Column[str] = Column(String(256), nullable=True)
    goals: Column[str] = Column(String(4096), nullable=True)

    creator_id: Column[int] = Column(Integer, ForeignKey("user.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", lazy=True)
    notes = relationship("Note", back_populates="project", lazy=True)

    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class Task(db.Model):
    __tablename__ = "task"

    id: Column[int] = Column(Integer, primary_key=True)
    title: Column[str] = Column(String(128), nullable=False)
    status: Column[TaskStatus] = Column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    project_id: Column[int] = Column(Integer, ForeignKey("project.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")

    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class Note(db.Model):
    __tablename__ = "note"

    id: Column[int] = Column(Integer, primary_key=True)
    content: Column[str] = Column(String(512), nullable=False)
    project_id: Column[int] = Column(Integer, ForeignKey("project.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="notes")
