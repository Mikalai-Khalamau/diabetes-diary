from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from freezegun import freeze_time
from pydantic import ValidationError

from app import crud, deps, security, schemas
from app.database import get_db
from app.default_foods import DEFAULT_FOODS


# ---- security ----

@pytest.mark.parametrize("pwd", ["password123", "Пароль123", "a" * 128])
def test_password_hash_then_verify_ok(pwd):
    # arrange
    h = security.hash_password(pwd)
    # act
    ok = security.verify_password(pwd, h)
    # assert
    assert ok and h != pwd


def test_password_verify_wrong_returns_false():
    # arrange
    h = security.hash_password("password123")
    # act / assert
    assert security.verify_password("wrong", h) is False
    assert security.verify_password("password1234", h) is False


def test_password_hash_is_salted():
    # arrange / act
    h1, h2 = security.hash_password("password123"), security.hash_password("password123")
    # assert
    assert h1 != h2 and security.verify_password("password123", h1)


def test_verify_corrupted_hash_no_raise():
    # arrange / act / assert
    assert security.verify_password("x", "not-a-bcrypt") is False


def test_token_roundtrip():
    # arrange / act
    tok = security.create_access_token(subject="u@example.com")
    payload = security.decode_access_token(tok)
    # assert
    assert payload["sub"] == "u@example.com"


@freeze_time("2026-10-06 12:00:00")
def test_expired_token_rejected():
    # arrange
    tok = security.create_access_token("u@example.com", expires_delta=timedelta(seconds=1))
    # act / assert
    with freeze_time("2026-10-06 12:00:30"):
        with pytest.raises(HTTPException) as e:
            security.decode_access_token(tok)
        assert e.value.status_code == 401


@pytest.mark.parametrize("bad", ["", "garbage", "a.b.c.d"])
def test_garbage_token_rejected(bad):
    # arrange / act / assert
    with pytest.raises(HTTPException) as e:
        security.decode_access_token(bad)
    assert e.value.status_code == 401


# ---- schemas (валидация границ) ----

@pytest.mark.parametrize("email", ["user@example.com", "a.b@sub.io"])
def test_email_valid(email):
    # arrange / act / assert
    assert schemas.UserCreate(email=email, password="password123").email == email


@pytest.mark.parametrize("email", ["", "no-at", "a@.bad"])
def test_email_invalid(email):
    # arrange / act / assert
    with pytest.raises(ValidationError):
        schemas.UserCreate(email=email, password="password123")


def test_password_length_bounds():
    # arrange / act / assert
    with pytest.raises(ValidationError):
        schemas.UserCreate(email="u@e.com", password="short")  # < 8
    assert schemas.UserCreate(email="u@e.com", password="a" * 8).password


@pytest.mark.parametrize("carbs,ok", [("0", True), ("100", True), ("100.1", False), ("-1", False)])
def test_food_carbs_bounds(carbs, ok):
    # arrange / act / assert
    if ok:
        schemas.FoodCreate(name="X", carbs_per_100g=Decimal(carbs))
    else:
        with pytest.raises(ValidationError):
            schemas.FoodCreate(name="X", carbs_per_100g=Decimal(carbs))


@pytest.mark.parametrize("name", ["", "x" * 201])
def test_food_name_invalid(name):
    # arrange / act / assert
    with pytest.raises(ValidationError):
        schemas.FoodCreate(name=name, carbs_per_100g=Decimal("10"))


@pytest.mark.parametrize("val,ok", [("0.1", True), ("50", True), ("0", False), ("50.1", False)])
def test_glucose_value_bounds(val, ok):
    # arrange / act / assert
    if ok:
        schemas.GlucoseEventCreate(value=Decimal(val))
    else:
        with pytest.raises(ValidationError):
            schemas.GlucoseEventCreate(value=Decimal(val))


@pytest.mark.parametrize("itype,dose,ok", [("short", "10", True), ("long", "200", True), ("ultra", "10", False), ("short", "0", False)])
def test_insulin_bounds(itype, dose, ok):
    # arrange / act / assert
    if ok:
        schemas.InsulinEventCreate(insulin_type=itype, dose=Decimal(dose))
    else:
        with pytest.raises(ValidationError):
            schemas.InsulinEventCreate(insulin_type=itype, dose=Decimal(dose))


@pytest.mark.parametrize("grams,ok", [("0.1", True), ("5000", True), ("0", False), ("5000.1", False)])
def test_meal_grams_bounds(grams, ok):
    # arrange / act / assert
    if ok:
        schemas.MealEventCreate(food_id=1, grams=Decimal(grams))
    else:
        with pytest.raises(ValidationError):
            schemas.MealEventCreate(food_id=1, grams=Decimal(grams))


# ---- deps (моки зависимостей) ----
# ВАЖНО: deps делает `from app.security import decode_access_token`, поэтому патчим имя в deps, а не в security.

def test_current_user_no_credentials_401():
    # arrange / act / assert
    with pytest.raises(HTTPException) as e:
        deps.get_current_user(credentials=None, db=SimpleNamespace())
    assert e.value.status_code == 401


def test_current_user_loads_user(monkeypatch):
    # arrange
    fake = SimpleNamespace(id=1, email="u@example.com")
    monkeypatch.setattr(deps, "decode_access_token", lambda t: {"sub": fake.email})
    monkeypatch.setattr(deps.crud, "get_user_by_email", lambda db, email: fake)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
    # act
    user = deps.get_current_user(credentials=creds, db=SimpleNamespace())
    # assert
    assert user is fake


def test_current_user_unknown_email_401(monkeypatch):
    # arrange
    monkeypatch.setattr(deps, "decode_access_token", lambda t: {"sub": "ghost@e.com"})
    monkeypatch.setattr(deps.crud, "get_user_by_email", lambda db, email: None)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
    # act / assert
    with pytest.raises(HTTPException) as e:
        deps.get_current_user(credentials=creds, db=SimpleNamespace())
    assert e.value.status_code == 401


def test_get_db_yields_and_closes(monkeypatch):
    # arrange: закрываем генератор get_db без реальной БД
    fake = MagicMock()
    monkeypatch.setattr("app.database.SessionLocal", lambda: fake)
    gen = get_db()
    # act
    got = next(gen)
    try:
        next(gen)
    except StopIteration:
        pass
    # assert
    assert got is fake
    fake.close.assert_called_once()


# ---- расчёт ХЕ через мок crud (замена зависимостей) ----

def _food(carbs):
    f = MagicMock()
    f.carbs_per_100g = Decimal(carbs)
    return f


@pytest.mark.parametrize("grams,carbs,exp_c,exp_bu", [
    ("100", "12.0", "12.00", "1.00"),
    ("250", "18.0", "45.00", "3.75"),
    ("100", "0.0", "0.00", "0.00"),
])
def test_meal_calc(monkeypatch, grams, carbs, exp_c, exp_bu):
    # arrange
    monkeypatch.setattr(crud, "get_food", lambda db, fid, uid: _food(carbs))
    monkeypatch.setattr(crud.settings, "carbs_per_bread_unit", 12.0)
    db = MagicMock()
    ev = schemas.MealEventCreate(food_id=7, grams=Decimal(grams))
    # act
    res = crud.create_meal_event(db=db, event=ev, user_id=1)
    # assert
    assert Decimal(res.carbs_grams) == Decimal(exp_c)
    assert Decimal(res.bread_units) == Decimal(exp_bu)
    db.add.assert_called_once()


def test_meal_calc_missing_food(monkeypatch):
    # arrange
    monkeypatch.setattr(crud, "get_food", lambda db, fid, uid: None)
    db = MagicMock()
    # act / assert
    with pytest.raises(ValueError):
        crud.create_meal_event(db=db, event=schemas.MealEventCreate(food_id=9, grams=Decimal("100")), user_id=1)
    db.add.assert_not_called()


# ---- базовый справочник ----

def test_default_foods_sane():
    # arrange / act
    names = [n for n, _ in DEFAULT_FOODS]
    # assert
    assert len(names) >= 100
    assert len(names) == len(set(names))
    for _, c in DEFAULT_FOODS:
        assert Decimal("0") <= c <= Decimal("100")