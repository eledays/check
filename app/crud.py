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


def create_project(
    name: str | None,
    short_name: str | None,
    description: str | None,
    goals: str | None,
    creator_id: int | None,
) -> Project:
    """
    Создает новый проект и сохраняет его в базе данных

    :param name: Название проекта
    :param short_name: Короткое имя проекта
    :param description: Описание проекта
    :param goals: Цели проекта
    :param creator_id: ID создателя проекта
    :return: Созданный проект
    """
    if name is None or short_name is None or creator_id is None:
        raise ValueError("Name, short_name, and creator_id are required to create a project.")

    project = Project()
    project.name = name
    project.short_name = short_name
    project.description = description
    project.goals = goals
    project.creator_id = creator_id
    
    db.session.add(project)
    db.session.commit()
    return project