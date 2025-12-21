# check — трекер привычек

## Описание

Простой Телеграм бот с Mini App для отслеживания привычек.

## Установка и запуск

1. Склонируйте репозиторий

    ```
    git clone https://github.com/eledays/check.git
    ```

2. Установите зависимости

    ```
    pip install -r requirements.txt
    ```

3. Создайте файл .env и заполните его данными

    ```
    DATABASE_URL=your_database_url
    ```

4. Выполните миграции

    ```
    alembic upgrade head
    ```

5. Запустите приложение

    ```
    python main.py
    ```
