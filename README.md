# Дневник диабетика

Веб-приложение (клиент–сервер) для ведения дневника самоконтроля уровня сахара в крови, инъекций инсулина и учёта приёмов пищи.

## Целевые пользователи

- **Пациент с сахарным диабетом** — основной пользователь: регистрируется, вносит измерения сахара, инъекции инсулина и приёмы пищи, ведёт свой справочник продуктов, смотрит ленту и статистику.

## Возможности

- Измерение уровня сахара в крови
- Учёт инъекций инсулина (короткий и длинный)
- Учёт приёмов пищи с автоматическим расчётом углеводов и хлебных единиц (ХЕ)
- Статистика за сегодня и вчера
- Справочник продуктов с содержанием углеводов

## Стек технологий

**Бэкенд**
- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- Alembic (миграции БД)
- PostgreSQL 16
- Pydantic (валидация)
- bcrypt, PyJWT (аутентификация)

**Фронтенд**
- HTML5, CSS3, Vanilla JavaScript

**Инфраструктура**
- Docker / Docker Compose

## Архитектура

Единый бэкенд на FastAPI раздаёт REST API (`/api/*`) и статику фронтенда; фронтенд общается с бэкендом по HTTP/JSON; персистентность — PostgreSQL через SQLAlchemy. Авторизация stateless (JWT).

```mermaid
flowchart LR
  B[Браузер / frontend] -->|HTTP JSON| API[FastAPI backend/app]
  API --> R[api/* роутеры]
  R -.-> SEC[security / deps: JWT]
  R --> C[crud.py бизнес-логика]
  C --> M[models.py ORM]
  M -->|psycopg2| DB[(PostgreSQL)]
  API -.-> FS[.env / frontend статика]
```

## Модули и зоны ответственности

| Модуль | Ответственность |
|---|---|
| `backend/app/main.py` | сборка FastAPI, CORS, раздача фронтенда, `/healthz` |
| `backend/app/config.py` | настройки из переменных окружения (`.env`) |
| `backend/app/database.py` | `engine` / `SessionLocal` / `Base` / `get_db` |
| `backend/app/models.py` | ORM-модели таблиц |
| `backend/app/schemas.py` | Pydantic-контракты и валидация |
| `backend/app/crud.py` | бизнес-логика, доступ к данным, guard-правила, агрегаты |
| `backend/app/security.py` | хэширование паролей (bcrypt) и JWT |
| `backend/app/deps.py` | `get_current_user` (авторизация по токену) |
| `backend/app/default_foods.py` | базовый справочник продуктов |
| `backend/app/api/*` | HTTP-эндпоинты (`auth`, `foods`, события, `recent`) |
| `backend/run.py` | точка входа запуска (порт из `.env`) |
| `backend/scripts/seed.py` | инициализация схемы и демо-данных |
| `backend/check_db.py` | диагностика подключения к БД |
| `frontend/*` | клиент (HTML / CSS / JS) |
| `Dockerfile`, `docker-compose.yml` | контейнеризация и оркестрация `app` + `db` |
| `requirements.txt` | единый файл зависимостей |

## Точки интеграции

- **СУБД PostgreSQL** — через SQLAlchemy / `psycopg2`, строка подключения из `DATABASE_URL`.
- **Файловая система** — чтение `.env`, раздача каталога `frontend/` статикой, конфиг `alembic.ini`.
- **Входящий HTTP/REST** — JSON-эндпоинты `/api/*`, CORS, авторизация `Authorization: Bearer`, документация `/docs`, проверка живости `/healthz`.
- **Внешние исходящие сервисы** — отсутствуют в текущей версии.

## Требования

- Docker Desktop (для запуска через контейнеры или для PostgreSQL)
- Либо: Python 3.11+ и локально установленная PostgreSQL 16 (для запуска без Docker)
- Git

---

## Способ запуска 1. Запуск через Docker Compose (рекомендуется)

Весь стек (приложение + база данных) поднимается одной командой.

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Mikalai-Khalamau/diabetes-diary.git
cd diabetes-diary
```

### 2. Создать файл конфигурации

Скопируйте `.env.example` в `.env`:

```bash
copy .env.example .env      # Windows
cp .env.example .env        # Linux / macOS
```

Для Docker-запуска убедитесь, что в `.env` адрес БД указывает на сервис `db`:

```
DATABASE_URL=postgresql+psycopg2://app:app@db:5432/diary
```

### 3. Поднять стек

```bash
docker compose up --build
```

Команда соберёт образ приложения, запустит PostgreSQL, дождётся готовности БД,
автоматически инициализирует схему и тестовые данные (`scripts/seed`) и запустит
сервер.

### 4. Открыть приложение

- Веб-интерфейс: http://localhost:8000/
- Swagger API: http://localhost:8000/docs
- Health-check: http://localhost:8000/healthz

### Полезные команды

```bash
docker compose logs -f app     # логи приложения
docker compose stop            # остановить (данные БД сохранятся)
docker compose down            # удалить контейнеры (данные БД сохранятся)
docker compose down -v         # удалить контейнеры и данные БД (чистый старт)
```

---

## Способ 2. Запуск без Docker (локально)

Приложение запускается локально через Python; PostgreSQL при этом можно
поднять в Docker (или использовать локально установленную БД).

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Mikalai-Khalamau/diabetes-diary.git
cd diabetes-diary
```

### 2. Создать и активировать виртуальное окружение

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустить PostgreSQL

Вариант А — через Docker (проще всего):

```bash
docker run --name diabetes-pg ^
  -e POSTGRES_USER=app ^
  -e POSTGRES_PASSWORD=app ^
  -e POSTGRES_DB=diary ^
  -p 5433:5432 ^
  -d postgres:16
```

Проверить запуск: `docker ps`.

Вариант Б — локально установленная PostgreSQL: создайте БД `diary` и
пользователя, параметры подключите в `.env`.

### 5. Создать файл конфигурации

Скопируйте `.env.example` в `.env` и укажите адрес БД. Для Docker-варианта А
(порт 5433 на хосте):

```
DATABASE_URL=postgresql+psycopg2://app:app@localhost:5433/diary
APP_PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:8000
CARBS_PER_BREAD_UNIT=12
APP_TIMEZONE=Europe/Moscow
```

### 6. Инициализировать схему и тестовые данные

```bash
cd backend
python -m scripts.seed
```

Скрипт создаёт таблицы (через SQLAlchemy metadata) и наполняет базу
тестовыми продуктами и событиями. Повторный запуск идемпотентен для продуктов.

### 7. Запустить сервер

```bash
python run.py
```

Порт берётся из переменной `APP_PORT` в `.env` — менять команду запуска не нужно.

### 8. Открыть приложение

http://localhost:8000/


### 9. Запуск тестов

```bash
python -m venv .venv        
.venv\Scripts\activate 
pip install -r requirements-dev.txt  
docker compose -f docker-compose.test.yml up -d  
docker compose -f docker-compose.test.yml ps      
pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-report=html  
```