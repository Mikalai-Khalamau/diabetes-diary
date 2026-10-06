import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app import crud, schemas, models

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test12345"

# Имена продуктов из базового справочника, на которых строим демо-события.
FOOD_OAT = "Каша овсяная"
FOOD_BUCKWHEAT = "Каша гречневая (из крупы ядрица)"
FOOD_RICE = "Каша рисовая"
FOOD_APPLE = "Яблоки"
FOOD_BANANA = "Банан"
FOOD_COTTAGE = "Творог 5%"
FOOD_MILK = "Молоко 2,5%"


def get_or_create_user(db: Session) -> models.User:
    user = crud.get_user_by_email(db, email=TEST_EMAIL)
    if user:
        print(f"  [skip] Пользователь '{TEST_EMAIL}' уже существует")
        return user
    user = crud.create_user(db, schemas.UserCreate(email=TEST_EMAIL, password=TEST_PASSWORD))
    print(f"  [ok] Создан пользователь: {user.email}")
    return user


def ensure_default_foods(db: Session, user_id: int) -> dict[str, models.Food]:
    foods = crud.create_default_foods(db, user_id=user_id)
    print(f"  [ok] Базовый справочник продуктов: {len(foods)} позиций")
    return foods


def create_events(db: Session, user_id: int, foods: dict[str, models.Food]) -> None:
    already_has_events = (
        db.query(models.GlucoseEvent).filter(models.GlucoseEvent.user_id == user_id).first()
        or db.query(models.InsulinEvent).filter(models.InsulinEvent.user_id == user_id).first()
        or db.query(models.MealEvent).filter(models.MealEvent.user_id == user_id).first()
    )
    if already_has_events:
        print("  [skip] У пользователя уже есть события — пропускаем сидинг событий")
        return

    now = datetime.now(timezone.utc)
    today_morning = now.replace(hour=8, minute=30, second=0, microsecond=0)
    today_lunch = now.replace(hour=13, minute=0, second=0, microsecond=0)
    today_evening = now.replace(hour=19, minute=30, second=0, microsecond=0)
    yesterday_morning = today_morning - timedelta(days=1)
    yesterday_lunch = today_lunch - timedelta(days=1)
    yesterday_evening = today_evening - timedelta(days=1)

    def fid(name: str) -> int:
        food = foods.get(name)
        if food is None:
            raise RuntimeError(f"Продукт '{name}' отсутствует в базовом справочнике")
        return food.id

    events_data = [
        {"type": "glucose", "occurred_at": yesterday_morning, "data": {"value": Decimal("5.8"), "note": "Натощак"}},
        {"type": "insulin", "occurred_at": yesterday_morning + timedelta(minutes=5), "data": {"insulin_type": "short", "dose": Decimal("4.0")}},
        {"type": "meal", "occurred_at": yesterday_morning + timedelta(minutes=10), "data": {"food_id": fid(FOOD_OAT), "grams": Decimal("250"), "note": "Завтрак"}},
        {"type": "glucose", "occurred_at": yesterday_lunch - timedelta(minutes=15), "data": {"value": Decimal("8.2")}},
        {"type": "insulin", "occurred_at": yesterday_lunch - timedelta(minutes=10), "data": {"insulin_type": "short", "dose": Decimal("6.0")}},
        {"type": "meal", "occurred_at": yesterday_lunch, "data": {"food_id": fid(FOOD_BUCKWHEAT), "grams": Decimal("200"), "note": "Обед"}},
        {"type": "insulin", "occurred_at": yesterday_evening, "data": {"insulin_type": "long", "dose": Decimal("10.0"), "note": "Базальный"}},
        {"type": "glucose", "occurred_at": today_morning, "data": {"value": Decimal("6.2"), "note": "Натощак"}},
        {"type": "insulin", "occurred_at": today_morning + timedelta(minutes=5), "data": {"insulin_type": "short", "dose": Decimal("4.5")}},
        {"type": "meal", "occurred_at": today_morning + timedelta(minutes=10), "data": {"food_id": fid(FOOD_APPLE), "grams": Decimal("150"), "note": "Завтрак"}},
        {"type": "glucose", "occurred_at": today_lunch - timedelta(minutes=15), "data": {"value": Decimal("7.5")}},
        {"type": "insulin", "occurred_at": today_lunch - timedelta(minutes=10), "data": {"insulin_type": "short", "dose": Decimal("5.0")}},
        {"type": "meal", "occurred_at": today_lunch, "data": {"food_id": fid(FOOD_RICE), "grams": Decimal("180"), "note": "Обед"}},
    ]

    for event_data in events_data:
        event_type = event_data["type"]
        occurred_at = event_data["occurred_at"]
        data = event_data["data"]

        if event_type == "glucose":
            crud.create_glucose_event(db, schemas.GlucoseEventCreate(occurred_at=occurred_at, **data), user_id=user_id)
            print(f"  [ok] Измерение сахара: {data['value']} ммоль/л ({occurred_at.strftime('%Y-%m-%d %H:%M')})")
        elif event_type == "insulin":
            crud.create_insulin_event(db, schemas.InsulinEventCreate(occurred_at=occurred_at, **data), user_id=user_id)
            print(f"  [ok] Инсулин {data['insulin_type']}: {data['dose']} ед ({occurred_at.strftime('%Y-%m-%d %H:%M')})")
        elif event_type == "meal":
            crud.create_meal_event(db, schemas.MealEventCreate(occurred_at=occurred_at, **data), user_id=user_id)
            print(f"  [ok] Приём пищи: {data['grams']} г ({occurred_at.strftime('%Y-%m-%d %H:%M')})")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("\nСоздание пользователя")
        user = get_or_create_user(db)

        print("\nБазовый справочник продуктов")
        foods = ensure_default_foods(db, user_id=user.id)

        print("\nСоздание событий")
        create_events(db, user_id=user.id, foods=foods)

        print("\nБаза данных заполнена тестовыми данными.")
        print(f"Тестовый вход: email={TEST_EMAIL} password={TEST_PASSWORD}")
    except Exception as e:
        db.rollback()
        print(f"\n[error] Ошибка при заполнении базы данных: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()