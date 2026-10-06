def _reg(client, email):
    assert client.post("/api/auth/register/", json={"email": email, "password": "password123"}).status_code == 201
    tok = client.post("/api/auth/login/", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_register_bulk_active(client):
    # arrange / act (вход в Active пакетно)
    h = _reg(client, "s1@example.com")
    # assert
    assert len(client.get("/api/foods/?limit=1000", headers=h).json()) >= 100


def test_create_then_duplicate_rejected(client):
    # arrange
    h = _reg(client, "s2@example.com")
    # act / assert (create [имя свободно] -> Active; create [занято] -> отказ 409)
    assert client.post("/api/foods/", headers=h, json={"name": "У", "carbs_per_100g": "10.0"}).status_code == 201
    assert client.post("/api/foods/", headers=h, json={"name": "У", "carbs_per_100g": "20.0"}).status_code == 409


def test_update_conflict_then_ok(client):
    # arrange
    h = _reg(client, "s3@example.com")
    a = client.post("/api/foods/", headers=h, json={"name": "Альфа", "carbs_per_100g": "10.0"}).json()["id"]
    client.post("/api/foods/", headers=h, json={"name": "Бета", "carbs_per_100g": "10.0"})
    # act / assert (update [конфликт] -> 409, состояние Active сохранено; update [свободно] -> Active изменён)
    assert client.patch(f"/api/foods/{a}", headers=h, json={"name": "Бета"}).status_code == 409
    assert client.get(f"/api/foods/{a}", headers=h).json()["name"] == "Альфа"
    assert client.patch(f"/api/foods/{a}", headers=h, json={"name": "Гамма"}).status_code == 200


def test_delete_blocked_then_allowed(client):
    # arrange
    h = _reg(client, "s4@example.com")
    fid = client.post("/api/foods/", headers=h, json={"name": "Едимый", "carbs_per_100g": "20.0"}).json()["id"]
    meal = client.post("/api/meal-events/", headers=h, json={"food_id": fid, "grams": "100"}).json()
    # act / assert (delete [используется] -> 409, остаётся Active)
    assert client.delete(f"/api/foods/{fid}", headers=h).status_code == 409
    assert client.get(f"/api/foods/{fid}", headers=h).status_code == 200
    # act (снимаем связь -> delete [не используется] -> Deleted -> терминальное 404)
    assert client.delete(f"/api/meal-events/{meal['id']}", headers=h).status_code == 204
    assert client.delete(f"/api/foods/{fid}", headers=h).status_code == 204
    assert client.get(f"/api/foods/{fid}", headers=h).status_code == 404


def test_isolation_across_users(client):
    # arrange
    h1, h2 = _reg(client, "s5a@example.com"), _reg(client, "s5b@example.com")
    fid = client.post("/api/foods/", headers=h1, json={"name": "Мой", "carbs_per_100g": "10.0"}).json()["id"]
    # act / assert (чужой продукт недоступен: 404 до всякого перехода)
    assert client.get(f"/api/foods/{fid}", headers=h2).status_code == 404
    assert client.get(f"/api/foods/{fid}", headers=h1).status_code == 200