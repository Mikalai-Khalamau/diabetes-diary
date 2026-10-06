from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest
import respx
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas


# ---- БД-уровень ----

def _user(db, email="i@example.com"):
    return crud.create_user(db, schemas.UserCreate(email=email, password="password123"))


def test_food_name_unique_per_user(db):
    # arrange
    u1, u2 = _user(db, "a@e.com"), _user(db, "b@e.com")
    crud.create_food(db, schemas.FoodCreate(name="Яблоко", carbs_per_100g=Decimal("9.8")), user_id=u1.id)
    # act: то же имя у другого — ок
    assert crud.create_food(db, schemas.FoodCreate(name="Яблоко", carbs_per_100g=Decimal("9.8")), user_id=u2.id).id
    # act / assert: дубликат у того же — IntegrityError
    with pytest.raises(IntegrityError):
        crud.create_food(db, schemas.FoodCreate(name="Яблоко", carbs_per_100g=Decimal("9.8")), user_id=u1.id)
    db.rollback()


def test_delete_user_cascades(db):
    # arrange
    u = _user(db)
    food = crud.create_food(db, schemas.FoodCreate(name="Т", carbs_per_100g=Decimal("10")), user_id=u.id)
    crud.create_glucose_event(db, schemas.GlucoseEventCreate(value=Decimal("5.5")), user_id=u.id)
    crud.create_meal_event(db, schemas.MealEventCreate(food_id=food.id, grams=Decimal("100")), user_id=u.id)
    # act
    db.delete(u); db.commit()
    # assert
    assert db.query(models.Food).filter(models.Food.user_id == u.id).count() == 0
    assert db.query(models.MealEvent).filter(models.MealEvent.user_id == u.id).count() == 0


def test_delete_food_used_guard(db):
    # arrange
    u = _user(db)
    food = crud.create_food(db, schemas.FoodCreate(name="Рис", carbs_per_100g=Decimal("28")), user_id=u.id)
    crud.create_meal_event(db, schemas.MealEventCreate(food_id=food.id, grams=Decimal("100")), user_id=u.id)
    # act / assert: guard в crud
    with pytest.raises(ValueError):
        crud.delete_food(db, food_id=food.id, user_id=u.id)
    meal = db.query(models.MealEvent).first()
    crud.delete_meal_event(db, event_id=meal.id, user_id=u.id)
    assert crud.delete_food(db, food_id=food.id, user_id=u.id) is True


@pytest.mark.parametrize("offset,in_today,in_yest", [(0, True, False), (-2, False, False)])
def test_recent_tz_window(db, offset, in_today, in_yest):
    # arrange
    from freezegun import freeze_time
    u = _user(db)
    with freeze_time("2026-10-06 15:00:00+03:00"):
        occ = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc) + timedelta(days=offset)
        crud.create_glucose_event(db, schemas.GlucoseEventCreate(value=Decimal("6.0"), occurred_at=occ), user_id=u.id)
        res = crud.get_recent_events(db, user_id=u.id, timezone_str="Europe/Moscow")
    # act
    tid = {e["id"] for e in res["today"]["events"]}; yid = {e["id"] for e in res["yesterday"]["events"]}
    eid = db.query(models.GlucoseEvent).first().id
    # assert
    assert (eid in tid) == in_today and (eid in yid) == in_yest


# ---- HTTP: auth ----

def test_register_login_me(client, make_user):
    # arrange / act
    email, h = make_user()
    # assert
    r = client.get("/api/auth/me/", headers=h)
    assert r.status_code == 200 and r.json()["email"] == email


def test_register_duplicate_409(client):
    # arrange
    client.post("/api/auth/register/", json={"email": "d@e.com", "password": "password123"})
    # act / assert
    assert client.post("/api/auth/register/", json={"email": "d@e.com", "password": "password123"}).status_code == 409


@pytest.mark.parametrize("payload,code", [
    ({"email": "x@e.com", "password": "wrongpass"}, 401),
    ({"email": "nope@e.com", "password": "password123"}, 401),
    ({"email": "bad-email", "password": "password123"}, 422),
])
def test_login_negative(client, payload, code):
    # arrange
    client.post("/api/auth/register/", json={"email": "x@e.com", "password": "password123"})
    # act / assert
    assert client.post("/api/auth/login/", json=payload).status_code == code


def test_no_token_401(client):
    # arrange / act / assert
    assert client.get("/api/foods/").status_code == 401
    assert client.get("/api/foods/", headers={"Authorization": "Bearer junk"}).status_code == 401


# ---- HTTP: foods ----

def _food(client, h, name="Тест", carbs="12.0"):
    return client.post("/api/foods/", headers=h, json={"name": name, "carbs_per_100g": carbs})


def test_default_catalog_on_register(client, make_user):
    # arrange / act: limit=1000, иначе дефолтный limit=100 маскирует число
    _, h = make_user()
    # assert
    assert len(client.get("/api/foods/?limit=1000", headers=h).json()) >= 100


def test_food_crud_cycle(client, make_user):
    # arrange
    _, h = make_user()
    # act
    fid = _food(client, h, "Уник", "33.0").json()["id"]
    assert client.get(f"/api/foods/{fid}", headers=h).status_code == 200
    assert float(client.patch(f"/api/foods/{fid}", headers=h, json={"carbs_per_100g": "40.0"}).json()["carbs_per_100g"]) == 40.0
    assert client.delete(f"/api/foods/{fid}", headers=h).status_code == 204
    # assert
    assert client.get(f"/api/foods/{fid}", headers=h).status_code == 404


def test_food_name_conflicts(client, make_user):
    # arrange
    _, h = make_user()
    a = _food(client, h, "Альфа", "10.0").json()["id"]
    _food(client, h, "Бета", "10.0")
    # act / assert: создание дубля и переименование в занятое — 409
    assert _food(client, h, "Альфа", "20.0").status_code == 409
    assert client.patch(f"/api/foods/{a}", headers=h, json={"name": "Бета"}).status_code == 409


def test_food_delete_used_409(client, make_user):
    # arrange
    _, h = make_user()
    fid = _food(client, h, "Едимый", "20.0").json()["id"]
    client.post("/api/meal-events/", headers=h, json={"food_id": fid, "grams": "100"})
    # act / assert
    assert client.delete(f"/api/foods/{fid}", headers=h).status_code == 409


def test_food_isolation(client, make_user):
    # arrange
    _, h1 = make_user(); _, h2 = make_user()
    fid = _food(client, h1, "Личный", "10.0").json()["id"]
    # act / assert: второй не трогает чужое
    assert client.get(f"/api/foods/{fid}", headers=h2).status_code == 404
    assert client.delete(f"/api/foods/{fid}", headers=h2).status_code == 404
    assert "Личный" not in [f["name"] for f in client.get("/api/foods/?limit=1000", headers=h2).json()]


@pytest.mark.parametrize("carbs,code", [("101", 422), ("-1", 422), ("50", 201)])
def test_food_carbs_http_bounds(client, make_user, carbs, code):
    # arrange
    _, h = make_user()
    # act / assert
    assert _food(client, h, "Гр", carbs).status_code == code


def test_food_pagination(client, make_user):
    # arrange
    _, h = make_user()
    base = len(client.get("/api/foods/?limit=1000", headers=h).json())
    for i in range(3):
        _food(client, h, f"П{i}", "10.0")
    # act
    page = client.get("/api/foods/?skip=0&limit=2", headers=h).json()
    total = len(client.get("/api/foods/?limit=1000", headers=h).json())
    # assert
    assert len(page) == 2 and total == base + 3


# ---- HTTP: события ----

def _fid(client, h, name="Прод"):
    return client.post("/api/foods/", headers=h, json={"name": name, "carbs_per_100g": "20.0"}).json()["id"]


@pytest.mark.parametrize("path,payload,field", [
    ("/api/glucose-events/", {"value": "6.5"}, "value"),
    ("/api/insulin-events/", {"insulin_type": "short", "dose": "5"}, "dose"),
])
def test_event_crud_by_id(client, make_user, path, payload, field):
    # arrange
    _, h = make_user()
    # act
    eid = client.post(path, headers=h, json=payload).json()["id"]
    assert client.get(f"{path}{eid}", headers=h).status_code == 200
    patch = {"value": "7.0"} if "glucose" in path else {"dose": "6"}
    assert float(client.patch(f"{path}{eid}", headers=h, json=patch).json()[field]) == float(list(patch.values())[0])
    assert client.delete(f"{path}{eid}", headers=h).status_code == 204
    # assert
    assert client.get(f"{path}{eid}", headers=h).status_code == 404


def test_meal_calc_http(client, make_user):
    # arrange: продукт 20г/100г, ХЕ=12 -> 250г = 50г угл.; 50/12=4.166.., колонка Numeric(8,2) -> 4.17
    _, h = make_user()
    fid = _fid(client, h, "Овсянка20")
    # act
    b = client.post("/api/meal-events/", headers=h, json={"food_id": fid, "grams": "250"}).json()
    # assert
    assert float(b["carbs_grams"]) == pytest.approx(50.0, abs=1e-9)
    assert float(b["bread_units"]) == pytest.approx(4.17, abs=1e-9)


def test_meal_unknown_food_404(client, make_user):
    # arrange / act / assert
    _, h = make_user()
    assert client.post("/api/meal-events/", headers=h, json={"food_id": 999999, "grams": "100"}).status_code == 404


def test_meal_history_not_recomputed(client, make_user):
    # arrange
    _, h = make_user()
    fid = _fid(client, h, "История")
    meal = client.post("/api/meal-events/", headers=h, json={"food_id": fid, "grams": "100"}).json()
    old = float(meal["carbs_grams"])
    # act: правим углеводы продукта
    client.patch(f"/api/foods/{fid}", headers=h, json={"carbs_per_100g": "99.0"})
    # assert: старая запись не изменилась
    assert float(client.get(f"/api/meal-events/{meal['id']}", headers=h).json()["carbs_grams"]) == old


def test_recent_requires_auth(client):
    # arrange / act / assert
    assert client.get("/api/events/recent/").status_code == 401
    assert client.get("/api/stats/recent/").status_code == 401


# ---- HTTP-стаб внешнего сервиса (механизм + факт отсутствия outbound) ----

@respx.mock
def test_outbound_stub_works():
    # arrange
    route = respx.get("https://external.example/ping").mock(return_value=httpx.Response(200, json={"ok": True}))
    # act
    resp = httpx.get("https://external.example/ping")
    # assert
    assert resp.json() == {"ok": True} and route.called


def test_app_makes_no_outbound(client, make_user):
    # arrange: strict-стаб активен на весь цикл операций приложения
    with respx.mock(assert_all_called=False) as rx:
        _, h = make_user()
        # act
        client.post("/api/foods/", headers=h, json={"name": "X", "carbs_per_100g": "10.0"})
        client.post("/api/glucose-events/", headers=h, json={"value": "6.0"})
        client.get("/api/events/recent/", headers=h)
        # assert: ни одного исходящего HTTP-вызова (внешних интеграций в рантайме нет)
        assert rx.calls.call_count == 0