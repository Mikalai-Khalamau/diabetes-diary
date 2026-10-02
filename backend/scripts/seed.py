import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app import crud, schemas, models


def create_foods(db: Session) -> dict[str, models.Food]:
    foods_data = [
        {"name": "Яблоко", "carbs_per_100g": Decimal("12.0")},
        {"name": "Банан", "carbs_per_100g": Decimal("23.0")},
        {"name": "Гречка варёная", "carbs_per_100g": Decimal("33.0")},
        {"name": "Рис варёный", "carbs_per_100g": Decimal("28.0")},
        {"name": "Хлеб белый", "carbs_per_100g": Decimal("49.0")},
        {"name": "Молоко 2.5%", "carbs_per_100g": Decimal("4.8")},
        {"name": "Овсяная каша на воде", "carbs_per_100g": Decimal("18.0")},
        {"name": "Творог 5%", "carbs_per_100g": Decimal("3.3")},
    ]

    created_foods = {}

    for food_data in foods_data:
        existing = crud.get_food_by_name(db, food_data["name"])
        if existing:
            print(f"  [skip] Продукт '{food_data['name']}' уже существует")
            created_foods[food_data["name"]] = existing
            continue

        food = crud.create_food(db, schemas.FoodCreate(**food_data))
        created_foods[food.name] = food
        print(f"  [ok] Создан продукт: {food.name} ({food.carbs_per_100g} г углеводов на 100 г)")

    return created_foods


def create_events(db: Session, foods: dict[str, models.Food]) -> None:
    now = datetime.now(timezone.utc)

    today_morning = now.replace(hour=8, minute=30, second=0, microsecond=0)
    today_lunch = now.replace(hour=13, minute=0, second=0, microsecond=0)
    today_evening = now.replace(hour=19, minute=30, second=0, microsecond=0)

    yesterday_morning = today_morning - timedelta(days=1)
    yesterday_lunch = today_lunch - timedelta(days=1)
    yesterday_evening = today_evening - timedelta(days=1)

    events_data = [
        {
            "type": "glucose",
            "occurred_at": yesterday_morning,
            "data": {"value": Decimal("5.8"), "note": "Натощак"},
        },
        {
            "type": "insulin",
            "occurred_at": yesterday_morning + timedelta(minutes=5),
            "data": {"insulin_type": "short", "dose": Decimal("4.0")},
        },
        {
            "type": "meal",
            "occurred_at": yesterday_morning + timedelta(minutes=10),
            "data": {
                "food_id": foods["Овсяная каша на воде"].id,
                "grams": Decimal("250"),
                "note": "Завтрак",
            },
        },
        {
            "type": "glucose",
            "occurred_at": yesterday_lunch - timedelta(minutes=15),
            "data": {"value": Decimal("8.2")},
        },
        {
            "type": "insulin",
            "occurred_at": yesterday_lunch - timedelta(minutes=10),
            "data": {"insulin_type": "short", "dose": Decimal("6.0")},
        },
        {
            "type": "meal",
            "occurred_at": yesterday_lunch,
            "data": {
                "food_id": foods["Гречка варёная"].id,
                "grams": Decimal("200"),
                "note": "Обед",
            },
        },
        {
            "type": "insulin",
            "occurred_at": yesterday_evening,
            "data": {"insulin_type": "long", "dose": Decimal("10.0"), "note": "Базальный"},
        },
        {
            "type": "glucose",
            "occurred_at": today_morning,
            "data": {"value": Decimal("6.2"), "note": "Натощак"},
        },
        {
            "type": "insulin",
            "occurred_at": today_morning + timedelta(minutes=5),
            "data": {"insulin_type": "short", "dose": Decimal("4.5")},
        },
        {
            "type": "meal",
            "occurred_at": today_morning + timedelta(minutes=10),
            "data": {
                "food_id": foods["Яблоко"].id,
                "grams": Decimal("150"),
                "note": "Завтрак",
            },
        },
        {
            "type": "glucose",
            "occurred_at": today_lunch - timedelta(minutes=15),
            "data": {"value": Decimal("7.5")},
        },
        {
            "type": "insulin",
            "occurred_at": today_lunch - timedelta(minutes=10),
            "data": {"insulin_type": "short", "dose": Decimal("5.0")},
        },
        {
            "type": "meal",
            "occurred_at": today_lunch,
            "data": {
                "food_id": foods["Рис варёный"].id,
                "grams": Decimal("180"),
                "note": "Обед",
            },
        },
    ]

    for event_data in events_data:
        event_type = event_data["type"]
        occurred_at = event_data["occurred_at"]
        data = event_data["data"]

        if event_type == "glucose":
            crud.create_glucose_event(db, schemas.GlucoseEventCreate(occurred_at=occurred_at, **data))
            print(f"  [ok] Измерение сахара: {data['value']} ммоль/л ({occurred_at.strftime('%Y-%m-%d %H:%M')})")

        elif event_type == "insulin":
            crud.create_insulin_event(db, schemas.InsulinEventCreate(occurred_at=occurred_at, **data))
            print(f"  [ok] Инсулин {data['insulin_type']}: {data['dose']} ед ({occurred_at.strftime('%Y-%m-%d %H:%M')})")

        elif event_type == "meal":
            crud.create_meal_event(db, schemas.MealEventCreate(occurred_at=occurred_at, **data))
            print(f"  [ok] Приём пищи: {data['grams']} г ({occurred_at.strftime('%Y-%m-%d %H:%M')})")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("\nСоздание продуктов")
        foods = create_foods(db)

        print("\nСоздание событий")
        create_events(db, foods)

        print("\nБаза данных заполнена тестовыми данными.")

    except Exception as e:
        db.rollback()
        print(f"\n[error] Ошибка при заполнении базы данных: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()