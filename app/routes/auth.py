from app import app, db
from app.crud.users import get_user_by_yandex_id

from flask import Blueprint, redirect, request, session, flash, url_for

from urllib.parse import urlencode
import requests
import secrets
from logging import Logger, getLogger

from app.models import User

bp = Blueprint("auth", __name__)
logger: Logger = getLogger(__name__)


@bp.route('/login')
def login():
    return redirect(url_for('auth.oauth_yandex'))


@bp.route("/oauth/yandex")
def oauth_yandex():
    # Генерация случайного state для защиты от CSRF атак
    state = secrets.token_hex(32)

    session["state"] = state

    params = {
        "response_type": "code",
        "client_id": app.config["YANDEX_CLIENT_ID"],
        "redirect_uri": app.config["YANDEX_REDIRECT_URI"],
        "scope": "login:info",
        "state": state
    }

    auth_url = "https://oauth.yandex.ru/authorize?" + urlencode(params)
    return redirect(auth_url)


@bp.route('/oauth/yandex/callback')
def oauth_callback():
    # Проверка state
    state: str | None = request.args.get('state')
    if state != session.get('state'):
        flash('Ошибка авторизации')
        logger.error('Auth state mismatch: %s %s', state, session.get('state'))
        return redirect(url_for('main.index'))
    
    # Удаление state из сессии
    session.pop('state')

    # Получение кода из запроса
    code: str | None = request.args.get('code')
    
    if code is None:
        flash('Ошибка авторизации')
        logger.error('Auth code not found')
        return redirect(url_for('main.index'))
    
    # Обмен кода на токен
    token_url = 'https://oauth.yandex.ru/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': app.config['YANDEX_CLIENT_ID'],
        'client_secret': app.config['YANDEX_CLIENT_SECRET']
    }
    
    response: requests.Response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        flash('Не удалось получить токен')
        return redirect(url_for('main.index'))
    
    token_info = response.json()
    access_token: str | None = token_info.get('access_token')

    if access_token is None:
        flash('Не удалось получить токен')
        return redirect(url_for('main.index'))
    
    # Получение информации о пользователе
    user_info_url = 'https://login.yandex.ru/info'
    headers = {'Authorization': f'OAuth {access_token}'}
    user_response = requests.get(user_info_url, headers=headers)
    
    if user_response.status_code != 200:
        flash('Не удалось получить информацию о пользователе')
        return redirect(url_for('main.index'))
    
    user_data = user_response.json()

    try:
        yandex_id: int = int(user_data['id'])
        login: str = user_data['login']
        client_id: str = user_data['client_id']
        first_name: str = user_data['first_name']
        last_name: str = user_data['last_name']
    except (KeyError, TypeError):
        flash('Не удалось получить информацию о пользователе')
        return redirect(url_for('main.index'))
    
    # Поиск или создание пользователя в базе
    user: User | None = get_user_by_yandex_id(yandex_id)
    if user is None:
        user = User()
        user.yandex_id = yandex_id
        user.login = login
        user.first_name = first_name
        user.last_name = last_name
        db.session.add(user)
        db.session.commit()

        logger.info('New user created: %s', user)
    else:
        user.login = login
        user.first_name = first_name
        user.last_name = last_name
        db.session.commit()

        logger.info('User updated: %s', user)

    session["user_id"] = user.id

    return redirect(url_for('main.index'))


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))