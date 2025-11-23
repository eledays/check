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
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


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
    
    created_at = mapped_column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class Project(db.Model):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    goals: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)
    periodicity: Mapped[ProjectPeriodicity] = mapped_column(
        SAEnum(ProjectPeriodicity), 
        nullable=False, 
        default=ProjectPeriodicity.WEEKLY
    )

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
    
    def get_staleness_ratio(self) -> float:
        """
        Calculate how stale this project is based on periodicity.
        Returns a ratio: 0 = completely fresh, 1.0 = at the periodicity threshold, >1.0 = overdue
        """
        last_activity = self.get_last_activity_date()
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Make last_activity timezone-aware if it isn't
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=datetime.timezone.utc)
        
        days_since_activity = (now - last_activity).days
        
        # Define threshold days for each periodicity
        periodicity_days = {
            ProjectPeriodicity.DAILY: 1,
            ProjectPeriodicity.WEEKLY: 7,
            ProjectPeriodicity.BIWEEKLY: 14,
            ProjectPeriodicity.MONTHLY: 30,
            ProjectPeriodicity.QUARTERLY: 90,
        }
        
        threshold = periodicity_days.get(self.periodicity, 7)
        
        # Return ratio (0 = fresh, 1.0 = at threshold, >1.0 = overdue)
        return days_since_activity / threshold


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
