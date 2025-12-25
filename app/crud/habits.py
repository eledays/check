from app import db

from app.models import Habit

from typing import List


def get_habits(user_id: int) -> List[Habit]:
    return Habit.query.filter_by(owner_id=user_id).all()
