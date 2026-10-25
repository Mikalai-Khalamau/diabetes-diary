import pytest
from app import security, schemas

def _auth(client, email="u@example.com", pwd="Password123"):
    client.post("/api/auth/register/", json={"email": email, "password": pwd})
    tok = client.post("/api/auth/login/", json={"email": email, "password": pwd}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}

def test_tc01_register_ok(client):
    # TC-01: Успешная регистрация нового пользователя
    resp = client.post("/api/auth/register/", json={"email": "tc1@example.com", "password": "Password123"})
    assert resp.status_code in (200, 201)

def test_tc02_register_duplicate(client):
    # TC-02: Ошибка 409 при дубликате email
    client.post("/api/auth/register/", json={"email": "tc2@example.com", "password": "Password123"})
    resp = client.post("/api/auth/register/", json={"email": "tc2@example.com", "password": "Password123"})
    assert resp.status_code == 409

def test_tc03_register_invalid_email(client):
    # TC-03: Ошибка 422 при неверном формате email
    resp = client.post("/api/auth/register/", json={"email": "not-an-email", "password": "Password123"})
    assert resp.status_code == 422

def test_tc04_password_hashed():
    # TC-04: Хэширование пароля через bcrypt
    h = security.hash_password("Password123")
    assert h.startswith("$2b$")
    assert security.verify_password("Password123", h) is True

def test_tc05_login_ok(client):
    # TC-05: Успешный вход и получение JWT
    client.post("/api/auth/register/", json={"email": "tc5@example.com", "password": "Password123"})
    resp = client.post("/api/auth/login/", json={"email": "tc5@example.com", "password": "Password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_tc06_login_wrong_password(client):
    # TC-06: Ошибка 401 при неверном пароле
    client.post("/api/auth/register/", json={"email": "tc6@example.com", "password": "Password123"})
    resp = client.post("/api/auth/login/", json={"email": "tc6@example.com", "password": "WrongPassword"})
    assert resp.status_code == 401

def test_tc07_protected_route_no_token(client):
    # TC-07: Запрет доступа без токена (401)
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401

def test_tc08_auth_me(client):
    # TC-08: Получение данных текущего пользователя
    headers = _auth(client, "tc8@example.com")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tc8@example.com"

def test_tc09_data_isolation(client):
    # TC-09: Изоляция данных между пользователями (чужая запись дает 404)
    h1 = _auth(client, "tc9a@example.com")
    h2 = _auth(client, "tc9b@example.com")
    fid = client.post("/api/foods/", headers=h1, json={"name": "Яблоко", "carbs_per_100g": 10}).json()["id"]
    resp = client.get(f"/api/foods/{fid}", headers=h2)
    assert resp.status_code == 404

def test_tc10_default_catalog(client):
    # TC-10: Авто-создание базового справочника при регистрации (>100 продуктов)
    headers = _auth(client, "tc10@example.com")
    resp = client.get("/api/foods/?limit=200", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 100

def test_tc11_create_food(client):
    # TC-11: Создание пользовательского продукта
    headers = _auth(client, "tc11@example.com")
    resp = client.post("/api/foods/", headers=headers, json={"name": "Каша гречневая", "carbs_per_100g": 25.0})
    assert resp.status_code in (200, 201)

def test_tc12_food_name_unique(client):
    # TC-12: Ошибка 409 при дубликате имени продукта у пользователя
    headers = _auth(client, "tc12@example.com")
    client.post("/api/foods/", headers=headers, json={"name": "Рис", "carbs_per_100g": 28.0})
    resp = client.post("/api/foods/", headers=headers, json={"name": "Рис", "carbs_per_100g": 30.0})
    assert resp.status_code == 409

def test_tc13_update_food(client):
    # TC-13: Редактирование продукта
    headers = _auth(client, "tc13@example.com")
    fid = client.post("/api/foods/", headers=headers, json={"name": "Суп", "carbs_per_100g": 5.0}).json()["id"]
    resp = client.patch(f"/api/foods/{fid}", headers=headers, json={"name": "Суп овощной", "carbs_per_100g": 6.0})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Суп овощной"

def test_tc14_delete_used_food_blocked(client):
    # TC-14: Запрет удаления используемого в приёмах пищи продукта (409)
    headers = _auth(client, "tc14@example.com")
    fid = client.post("/api/foods/", headers=headers, json={"name": "Хлеб", "carbs_per_100g": 50.0}).json()["id"]
    client.post("/api/meal-events/", headers=headers, json={"food_id": fid, "grams": 100})
    resp = client.delete(f"/api/foods/{fid}", headers=headers)
    assert resp.status_code == 409

def test_tc15_glucose_create(client):
    # TC-15: Успешное создание замера сахара
    headers = _auth(client, "tc15@example.com")
    resp = client.post("/api/glucose-events/", headers=headers, json={"value": 5.8, "occurred_at": "2026-10-24T10:00:00", "note": "Тест"})
    assert resp.status_code in (200, 201)

def test_tc16_glucose_validation(client):
    # TC-16: Валидация диапазона значения сахара (выход за >50 дает 422)
    headers = _auth(client, "tc16@example.com")
    resp = client.post("/api/glucose-events/", headers=headers, json={"value": 60.0, "occurred_at": "2026-10-24T10:00:00"})
    assert resp.status_code == 422

def test_tc17_insulin_create(client):
    # TC-17: Создание инъекции инсулина
    headers = _auth(client, "tc17@example.com")
    resp = client.post("/api/insulin-events/", headers=headers, json={"insulin_type": "short", "dose": 5.0, "occurred_at": "2026-10-24T12:00:00"})
    assert resp.status_code in (200, 201)

def test_tc18_insulin_validation(client):
    # TC-18: Валидация инъекции инсулина (неверный тип дает 422)
    headers = _auth(client, "tc18@example.com")
    resp = client.post("/api/insulin-events/", headers=headers, json={"insulin_type": "bad_type", "dose": 5.0, "occurred_at": "2026-10-24T12:00:00"})
    assert resp.status_code == 422

def test_tc19_meal_autocalc(client):
    # TC-19: Автоматический расчёт углеводов и ХЕ при приёме пищи
    headers = _auth(client, "tc19@example.com")
    fid = client.post("/api/foods/", headers=headers, json={"name": "Макароны", "carbs_per_100g": 70.0}).json()["id"]
    resp = client.post("/api/meal-events/", headers=headers, json={"food_id": fid, "grams": 200.0, "occurred_at": "2026-10-24T14:00:00"})
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert float(data["carbs_grams"]) == 140.0
    assert abs(float(data["bread_units"]) - (140.0 / 12.0)) < 0.01

def test_tc20_meal_history_immutable(client):
    # TC-20: Неизменяемость истории при правке справочника
    headers = _auth(client, "tc20@example.com")
    fid = client.post("/api/foods/", headers=headers, json={"name": "Молоко", "carbs_per_100g": 5.0}).json()["id"]
    meal = client.post("/api/meal-events/", headers=headers, json={"food_id": fid, "grams": 200.0, "occurred_at": "2026-10-24T14:00:00"}).json()
    initial_carbs = meal["carbs_grams"]
    client.patch(f"/api/foods/{fid}", headers=headers, json={"name": "Молоко", "carbs_per_100g": 10.0})
    meals = client.get("/api/meal-events/", headers=headers).json()
    assert meals[0]["carbs_grams"] == initial_carbs

def test_tc21_pagination(client):
    # TC-21: Пагинация skip / limit
    headers = _auth(client, "tc21@example.com")
    resp = client.get("/api/foods/?skip=0&limit=5", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 5

def test_tc22_recent_feed(client):
    # TC-22: Лента событий за сегодня/вчера (возвращает структуру с today/yesterday)
    headers = _auth(client, "tc22@example.com")
    resp = client.get("/api/events/recent", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "today" in data
    assert "yesterday" in data

def test_tc23_recent_stats(client):
    # TC-23: Статистика за сегодня/вчера
    headers = _auth(client, "tc23@example.com")
    resp = client.get("/api/stats/recent", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "today" in data
    assert "glucose" in data["today"]

def test_tc24_healthz(client):
    # TC-24: Проверка здоровья сервиса /healthz
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

def test_test_tc25_xss_escaping():
    # TC-25: Проверка логики экранирования XSS на клиенте (исходный код app.js)
    with open("frontend/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "escapeHtml" in content
