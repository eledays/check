# check

## Инструкция по запуску

1. Клонируйте репозиторий

```bash
git clone https://github.com/eledays/check.git
cd check
```

2. Создайте виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Установите зависимости

```bash
pip install -r requirements.txt
```

4. Выполните миграцию

```bash
flask db upgrade
```

5. Настройте переменные окружения в файле `.env` по шаблону `.env.example`

6. Запустите приложение

```bash
python app.py
```