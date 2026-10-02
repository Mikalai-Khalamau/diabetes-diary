# Дневник диабетика

Веб-приложение для ведения дневника самоконтроля уровня сахара в крови, инъекций инсулина и учёта приёмов пищи.

# Возможности

- Измерение уровня сахара в крови
- Учёт инъекций инсулина (короткий и длинный)
- Учёт приёмов пищи с автоматическим расчётом углеводов и хлебных единиц (ХЕ)
- Статистика за сегодня и вчера
- Справочник продуктов с содержанием углеводов

# Стек технологий

# Бэкенд
- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- Alembic (миграции БД)
- PostgreSQL 16
- Pydantic (валидация)

# Фронтенд
- HTML5
- CSS3
- JavaScript 

# Требования

- Python 3.11 или выше
- Docker Desktop
- Git

# Установка и запуск

# 1. Клонировать репозиторий

git clone https://github.com/Mikalai-Khalamau/diabetes-diary.git
cd diabetes-diary

### 2. Создать виртуальное окружение

python -m venv .venv
.venv\Scripts\activate

После активации в начале строки терминала появится (.venv).

### 3. Установить зависимости

pip install -r requirements.txt

# 4. Запустить PostgreSQL через Docker

docker run --name diabetes-pg -e POSTGRES_USER=ПОЛЬЗОВАТЕЛЬ -e POSTGRES_PASSWORD=ПАРОЛЬ -e POSTGRES_DB=diary -p 5433:5432 -d postgres:16        

Проверить, что контейнер запущен:
docker ps

# 5. Создать файл конфигурации

Скопируйте .env.example в .env

# 6. Применить миграции базы данных

cd backend
alembic upgrade head

# 7. Заполнить базу тестовыми данными (опционально)

python -m scripts.seed

# 8. Запустить сервер

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 9. Открыть приложение

http://localhost:8000/


