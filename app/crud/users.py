from app import db

from app.models import User


def get_user_by_yandex_id(yandex_id: int) -> User | None:
    return User.query.filter_by(yandex_id=yandex_id).first()
