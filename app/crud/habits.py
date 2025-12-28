from app import db

from app.models import Habit

from typing import List
import logging


logger = logging.getLogger(__name__)


def get_habits(user_id: int) -> List[Habit]:
    return Habit.query.filter_by(owner_id=user_id).all()


def create_or_update_habit(habit_id: int, name: str, owner_id: int) -> Habit | None:
    habit: Habit | None = Habit.query.filter_by(id=habit_id).first()

    if not habit:
        habit = Habit()
        habit.name = name
        habit.owner_id = owner_id

        db.session.add(habit)
        db.session.commit()

        logger.info(f'{habit} created')
    else:
        habit.name = name
        db.session.commit()
        logger.info(f'{habit} updated')

    db.session.refresh(habit)

    return habit


def delete_habit(habit_id: int) -> None:
    habit: Habit | None = Habit.query.filter_by(id=habit_id).first()
    
    if not habit:
        return
    
    logger.info(f'{habit} deleted')
    db.session.delete(habit)