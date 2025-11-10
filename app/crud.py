from app import db
from app.models import Project

from flask_sqlalchemy.query import Query


def get_user_projects(user_id: int) -> list[Project]:
    """
    Возвращает список всех проектов пользователя

    :param user_id: ID пользователя
    :return: Список проектов
    """
    query: Query = Project.query.filter_by(creator_id=user_id)
    return query.all()
