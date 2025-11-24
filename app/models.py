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


class ProjectPeriodicity(Enum):
    """Периодичность проекта в днях"""
    DAILY = 1
    TWO_DAYS = 2
    THREE_DAYS = 3
    WEEKLY = 7
    BIWEEKLY = 14
    MONTHLY = 30


class User(db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="creator", lazy=True)
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    
    # Reminder settings
    reminders_enabled: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    reminder_time: Mapped[str] = mapped_column(String(5), nullable=False, default="20:00")  # Format: "HH:MM"
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class Project(db.Model):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    goals: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)
    periodicity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)

    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", lazy=True, cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="project", lazy=True, cascade="all, delete-orphan")

    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    def get_last_activity_date(self) -> datetime.datetime:
        """Get the date of last activity on this project (last task completion or update)."""
        # Get the most recent task completion using SQL
        last_completed = db.session.query(db.func.max(Task.completed_at)).filter(
            Task.project_id == self.id,
            Task.completed_at.isnot(None)
        ).scalar()
        
        # Compare with project's updated_at
        if last_completed and last_completed > self.updated_at:
            return last_completed
        return self.updated_at
    
    def get_staleness_ratio(self, last_activity: Optional[datetime.datetime] = None) -> float:
        """
        Calculate how stale this project is based on periodicity_days.
        Returns a ratio: 0 = completely fresh, 1.0 = at the periodicity threshold, >1.0 = overdue
        
        Args:
            last_activity: Optional pre-calculated last activity date to avoid N+1 queries
        """
        if last_activity is None:
            last_activity = self.get_last_activity_date()
        now = datetime.datetime.now(datetime.timezone.utc)
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=datetime.timezone.utc)
        days_since_activity = (now - last_activity).days
        threshold = self.periodicity_days
        if threshold == 0:
            return float('inf')  # Avoid division by zero
        return days_since_activity / threshold


class Task(db.Model):
    __tablename__ = "task"
    __table_args__ = (
        db.Index('idx_task_project_id', 'project_id'),
        db.Index('idx_task_project_status', 'project_id', 'status'),
        db.Index('idx_task_completed_at', 'completed_at'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")

    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class Note(db.Model):
    __tablename__ = "note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(512), nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="notes")
