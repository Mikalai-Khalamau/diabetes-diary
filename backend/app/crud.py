from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings


def create_food(db: Session, food: schemas.FoodCreate) -> models.Food:
    db_food = models.Food(name=food.name, carbs_per_100g=food.carbs_per_100g)
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food


def get_foods(db: Session, skip: int = 0, limit: int = 100) -> list[models.Food]:
    return db.query(models.Food).offset(skip).limit(limit).all()


def get_food(db: Session, food_id: int) -> models.Food | None:
    return db.query(models.Food).filter(models.Food.id == food_id).first()


def get_food_by_name(db: Session, name: str) -> models.Food | None:
    return db.query(models.Food).filter(models.Food.name == name).first()


def update_food(db: Session, food_id: int, food: schemas.FoodUpdate) -> models.Food | None:
    db_food = get_food(db, food_id)
    if not db_food:
        return None
    update_data = food.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_food, field, value)
    db.commit()
    db.refresh(db_food)
    return db_food


def delete_food(db: Session, food_id: int) -> bool:
    db_food = get_food(db, food_id)
    if not db_food:
        return False

    is_used = db.query(models.MealEvent).filter(models.MealEvent.food_id == food_id).first()
    if is_used:
        raise ValueError("Невозможно удалить продукт: он уже используется в записях о приемах пищи")

    db.delete(db_food)
    db.commit()
    return True


def create_glucose_event(db: Session, event: schemas.GlucoseEventCreate) -> models.GlucoseEvent:
    occurred_at = event.occurred_at or datetime.now(timezone.utc)
    db_event = models.GlucoseEvent(occurred_at=occurred_at, value=event.value, note=event.note)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_glucose_events(db: Session, skip: int = 0, limit: int = 100) -> list[models.GlucoseEvent]:
    return db.query(models.GlucoseEvent).offset(skip).limit(limit).all()


def get_glucose_event(db: Session, event_id: int) -> models.GlucoseEvent | None:
    return db.query(models.GlucoseEvent).filter(models.GlucoseEvent.id == event_id).first()


def update_glucose_event(db: Session, event_id: int, event: schemas.GlucoseEventUpdate) -> models.GlucoseEvent | None:
    db_event = get_glucose_event(db, event_id)
    if not db_event:
        return None
    update_data = event.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_glucose_event(db: Session, event_id: int) -> bool:
    db_event = get_glucose_event(db, event_id)
    if not db_event:
        return False
    db.delete(db_event)
    db.commit()
    return True


def create_insulin_event(db: Session, event: schemas.InsulinEventCreate) -> models.InsulinEvent:
    occurred_at = event.occurred_at or datetime.now(timezone.utc)
    db_event = models.InsulinEvent(
        occurred_at=occurred_at,
        insulin_type=event.insulin_type,
        dose=event.dose,
        note=event.note,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_insulin_events(db: Session, skip: int = 0, limit: int = 100) -> list[models.InsulinEvent]:
    return db.query(models.InsulinEvent).offset(skip).limit(limit).all()


def get_insulin_event(db: Session, event_id: int) -> models.InsulinEvent | None:
    return db.query(models.InsulinEvent).filter(models.InsulinEvent.id == event_id).first()


def update_insulin_event(db: Session, event_id: int, event: schemas.InsulinEventUpdate) -> models.InsulinEvent | None:
    db_event = get_insulin_event(db, event_id)
    if not db_event:
        return None
    update_data = event.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_insulin_event(db: Session, event_id: int) -> bool:
    db_event = get_insulin_event(db, event_id)
    if not db_event:
        return False
    db.delete(db_event)
    db.commit()
    return True


def create_meal_event(db: Session, event: schemas.MealEventCreate) -> models.MealEvent:
    food = get_food(db, event.food_id)
    if not food:
        raise ValueError(f"Продукт с ID {event.food_id} не найден")

    carbs_grams = (event.grams / Decimal("100")) * food.carbs_per_100g
    bread_units = carbs_grams / Decimal(str(settings.carbs_per_bread_unit))

    occurred_at = event.occurred_at or datetime.now(timezone.utc)

    db_event = models.MealEvent(
        occurred_at=occurred_at,
        food_id=event.food_id,
        grams=event.grams,
        carbs_grams=carbs_grams,
        bread_units=bread_units,
        note=event.note,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_meal_events(db: Session, skip: int = 0, limit: int = 100) -> list[models.MealEvent]:
    return db.query(models.MealEvent).offset(skip).limit(limit).all()


def get_meal_event(db: Session, event_id: int) -> models.MealEvent | None:
    return db.query(models.MealEvent).filter(models.MealEvent.id == event_id).first()


def update_meal_event(db: Session, event_id: int, event: schemas.MealEventUpdate) -> models.MealEvent | None:
    db_event = get_meal_event(db, event_id)
    if not db_event:
        return None

    update_data = event.model_dump(exclude_unset=True)

    if "food_id" in update_data or "grams" in update_data:
        food_id = update_data.get("food_id", db_event.food_id)
        grams = update_data.get("grams", db_event.grams)

        food = get_food(db, food_id)
        if not food:
            raise ValueError(f"Продукт с ID {food_id} не найден")

        carbs_grams = (grams / Decimal("100")) * food.carbs_per_100g
        bread_units = carbs_grams / Decimal(str(settings.carbs_per_bread_unit))

        update_data["carbs_grams"] = carbs_grams
        update_data["bread_units"] = bread_units

    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


def delete_meal_event(db: Session, event_id: int) -> bool:
    db_event = get_meal_event(db, event_id)
    if not db_event:
        return False
    db.delete(db_event)
    db.commit()
    return True


def _day_boundaries(timezone_str: str):
    """Возвращает границы (вчера 00:00, сегодня 00:00, завтра 00:00) в целевом TZ."""
    tz = ZoneInfo(timezone_str)
    now = datetime.now(tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    yesterday_start = today_start - timedelta(days=1)
    return yesterday_start, today_start, today_end


def get_recent_events(db: Session, timezone_str: str) -> dict:
    yesterday_start, today_start, today_end = _day_boundaries(timezone_str)

    # PostgreSQL (колонка TIMESTAMPTZ) корректно сравнивает aware-datetime из разных TZ
    glucose_events = db.query(models.GlucoseEvent).filter(
        models.GlucoseEvent.occurred_at >= yesterday_start,
        models.GlucoseEvent.occurred_at < today_end,
    ).all()

    insulin_events = db.query(models.InsulinEvent).filter(
        models.InsulinEvent.occurred_at >= yesterday_start,
        models.InsulinEvent.occurred_at < today_end,
    ).all()

    meal_events = db.query(models.MealEvent).filter(
        models.MealEvent.occurred_at >= yesterday_start,
        models.MealEvent.occurred_at < today_end,
    ).all()

    all_events = []

    for event in glucose_events:
        all_events.append({
            "event_type": "glucose",
            "id": event.id,
            "occurred_at": event.occurred_at,
            "value": event.value,
            "note": event.note,
        })

    for event in insulin_events:
        all_events.append({
            "event_type": "insulin",
            "id": event.id,
            "occurred_at": event.occurred_at,
            "insulin_type": event.insulin_type,
            "dose": event.dose,
            "note": event.note,
        })

    for event in meal_events:
        all_events.append({
            "event_type": "meal",
            "id": event.id,
            "occurred_at": event.occurred_at,
            "food_id": event.food_id,
            "grams": event.grams,
            "carbs_grams": event.carbs_grams,
            "bread_units": event.bread_units,
            "note": event.note,
        })

    all_events.sort(key=lambda x: x["occurred_at"], reverse=True)

    today_events = [e for e in all_events if e["occurred_at"] >= today_start]
    yesterday_events = [e for e in all_events if e["occurred_at"] < today_start]

    return {
        "timezone": timezone_str,
        "today": {"date": today_start.strftime("%Y-%m-%d"), "events": today_events},
        "yesterday": {"date": yesterday_start.strftime("%Y-%m-%d"), "events": yesterday_events},
    }


def get_recent_stats(db: Session, timezone_str: str) -> dict:
    yesterday_start, today_start, today_end = _day_boundaries(timezone_str)

    def calculate_day_stats(start, end):
        glucose_stats = db.query(
            func.count(models.GlucoseEvent.id).label("count"),
            func.avg(models.GlucoseEvent.value).label("avg"),
            func.min(models.GlucoseEvent.value).label("min"),
            func.max(models.GlucoseEvent.value).label("max"),
        ).filter(
            models.GlucoseEvent.occurred_at >= start,
            models.GlucoseEvent.occurred_at < end,
        ).first()

        insulin_total = db.query(
            func.count(models.InsulinEvent.id).label("count"),
            func.coalesce(func.sum(models.InsulinEvent.dose), 0).label("total_dose"),
        ).filter(
            models.InsulinEvent.occurred_at >= start,
            models.InsulinEvent.occurred_at < end,
        ).first()

        insulin_short = db.query(
            func.count(models.InsulinEvent.id).label("count"),
            func.coalesce(func.sum(models.InsulinEvent.dose), 0).label("total_dose"),
        ).filter(
            models.InsulinEvent.occurred_at >= start,
            models.InsulinEvent.occurred_at < end,
            models.InsulinEvent.insulin_type == "short",
        ).first()

        insulin_long = db.query(
            func.count(models.InsulinEvent.id).label("count"),
            func.coalesce(func.sum(models.InsulinEvent.dose), 0).label("total_dose"),
        ).filter(
            models.InsulinEvent.occurred_at >= start,
            models.InsulinEvent.occurred_at < end,
            models.InsulinEvent.insulin_type == "long",
        ).first()

        meal_stats = db.query(
            func.count(models.MealEvent.id).label("count"),
            func.coalesce(func.sum(models.MealEvent.carbs_grams), 0).label("total_carbs"),
            func.coalesce(func.sum(models.MealEvent.bread_units), 0).label("total_bu"),
        ).filter(
            models.MealEvent.occurred_at >= start,
            models.MealEvent.occurred_at < end,
        ).first()

        return {
            "date": start.strftime("%Y-%m-%d"),
            "glucose": {
                "count": glucose_stats.count or 0,
                "avg": float(glucose_stats.avg) if glucose_stats.avg is not None else None,
                "min": float(glucose_stats.min) if glucose_stats.min is not None else None,
                "max": float(glucose_stats.max) if glucose_stats.max is not None else None,
            },
            "insulin": {
                "count": insulin_total.count or 0,
                "total_dose": float(insulin_total.total_dose),
                "short_count": insulin_short.count or 0,
                "short_total_dose": float(insulin_short.total_dose),
                "long_count": insulin_long.count or 0,
                "long_total_dose": float(insulin_long.total_dose),
            },
            "meal": {
                "count": meal_stats.count or 0,
                "total_carbs_grams": float(meal_stats.total_carbs),
                "total_bread_units": float(meal_stats.total_bu),
            },
        }

    return {
        "timezone": timezone_str,
        "today": calculate_day_stats(today_start, today_end),
        "yesterday": calculate_day_stats(yesterday_start, today_start),
    }