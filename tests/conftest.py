import os

# Задаём env ДО импорта app: settings требует database_url и secret_key без дефолтов,
# и мы хотим целиться в тестовую БД (порт 5434), а не в прода-хост "db".
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://app:app@localhost:5434/diary_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_TIMEZONE", "Europe/Moscow")
os.environ.setdefault("CARBS_PER_BREAD_UNIT", "12")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app as fastapi_app

TEST_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_URL, poolclass=NullPool)  # NullPool — чтобы truncate не конфликтовал с соединениями
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


def _clean(engine):
    tables = ", ".join(Base.metadata.tables.keys())
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(engine):
    _clean(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(engine):
    _clean(engine)
    Session = sessionmaker(bind=engine)

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    fastapi_app.dependency_overrides[get_db] = override
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def make_user(client):
    n = {"i": 0}

    def _make():
        n["i"] += 1
        email = f"u{n['i']}@example.com"
        assert client.post("/api/auth/register/", json={"email": email, "password": "password123"}).status_code == 201
        tok = client.post("/api/auth/login/", json={"email": email, "password": "password123"}).json()["access_token"]
        return email, {"Authorization": f"Bearer {tok}"}

    return _make