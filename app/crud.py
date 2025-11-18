from app import db
from app.models import Project, Task

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


def update_task(task_id: int, title: str) -> Task | None:
    """
    Обновляет название задачи

    :param task_id: ID задачи
    :param title: Новое название задачи
    :return: Обновленная задача или None, если задача не найдена
    """
    task: Task | None = Task.query.get(task_id)
    if task is None:
        return None
    
    task.title = title
    db.session.commit()
    return task


def delete_task(task_id: int) -> bool:
    """
    Удаляет задачу из базы данных

    :param task_id: ID задачи
    :return: True, если задача была удалена, False, если задача не найдена
    """
    task: Task | None = Task.query.get(task_id)
    if task is None:
        return False
    
    db.session.delete(task)
    db.session.commit()
    return True


def update_project(
    project_id: int,
    name: str | None = None,
    short_name: str | None = None,
    description: str | None = None,
    goals: str | None = None,
) -> Project | None:
    """
    Обновляет данные проекта

    :param project_id: ID проекта
    :param name: Новое название проекта
    :param short_name: Новое короткое имя проекта
    :param description: Новое описание проекта
    :param goals: Новые цели проекта
    :return: Обновленный проект или None, если проект не найден
    """
    project: Project | None = Project.query.get(project_id)
    if project is None:
        return None
    
    if name is not None:
        project.name = name
    if short_name is not None:
        project.short_name = short_name
    if description is not None:
        project.description = description
    if goals is not None:
        project.goals = goals
    
    db.session.commit()
    return project
