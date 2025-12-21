from core import db
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, ForeignKey


class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships - используем relationship вместо mapped_column
    habits: Mapped[list['Habit']] = relationship(back_populates='owner')


class Habit(db.Model):
    __tablename__ = 'habits'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships - используем relationship вместо mapped_column
    owner: Mapped['User'] = relationship(back_populates='habits')