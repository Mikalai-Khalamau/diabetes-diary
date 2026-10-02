from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


class FoodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Название продукта")
    carbs_per_100g: Decimal = Field(..., ge=0, le=100, description="Углеводы на 100 г продукта")


class FoodCreate(FoodBase):
    pass


class FoodUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Название продукта")
    carbs_per_100g: Optional[Decimal] = Field(None, ge=0, le=100, description="Углеводы на 100 г продукта")


class FoodRead(FoodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlucoseEventBase(BaseModel):
    value: Decimal = Field(..., gt=0, le=50, description="Значение сахара в ммоль/л")
    note: Optional[str] = Field(None, max_length=500, description="Комментарий")


class GlucoseEventCreate(GlucoseEventBase):
    occurred_at: Optional[datetime] = Field(None, description="Время события")


class GlucoseEventUpdate(BaseModel):
    occurred_at: Optional[datetime] = None
    value: Optional[Decimal] = Field(None, gt=0, le=50)
    note: Optional[str] = Field(None, max_length=500)


class GlucoseEventRead(GlucoseEventBase):
    id: int
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsulinEventBase(BaseModel):
    insulin_type: Literal["short", "long"] = Field(..., description="Тип инсулина")
    dose: Decimal = Field(..., gt=0, le=200, description="Доза инсулина в единицах")
    note: Optional[str] = Field(None, max_length=500, description="Комментарий")


class InsulinEventCreate(InsulinEventBase):
    occurred_at: Optional[datetime] = Field(None, description="Время события")


class InsulinEventUpdate(BaseModel):
    occurred_at: Optional[datetime] = None
    insulin_type: Optional[Literal["short", "long"]] = None
    dose: Optional[Decimal] = Field(None, gt=0, le=200)
    note: Optional[str] = Field(None, max_length=500)


class InsulinEventRead(InsulinEventBase):
    id: int
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealEventBase(BaseModel):
    food_id: int = Field(..., description="ID продукта")
    grams: Decimal = Field(..., gt=0, le=5000, description="Масса продукта в граммах")
    note: Optional[str] = Field(None, max_length=500, description="Комментарий")


class MealEventCreate(MealEventBase):
    occurred_at: Optional[datetime] = Field(None, description="Время события")


class MealEventUpdate(BaseModel):
    occurred_at: Optional[datetime] = None
    food_id: Optional[int] = None
    grams: Optional[Decimal] = Field(None, gt=0, le=5000)
    note: Optional[str] = Field(None, max_length=500)


class MealEventRead(BaseModel):
    id: int
    occurred_at: datetime
    food_id: int
    grams: Decimal
    carbs_grams: Decimal
    bread_units: Decimal
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventItem(BaseModel):
    event_type: Literal["glucose", "insulin", "meal"]
    id: int
    occurred_at: datetime

    value: Optional[Decimal] = None
    note: Optional[str] = None

    insulin_type: Optional[Literal["short", "long"]] = None
    dose: Optional[Decimal] = None

    food_id: Optional[int] = None
    grams: Optional[Decimal] = None
    carbs_grams: Optional[Decimal] = None
    bread_units: Optional[Decimal] = None


class DayEvents(BaseModel):
    date: str
    events: list[EventItem]


class RecentEventsResponse(BaseModel):
    timezone: str
    today: DayEvents
    yesterday: DayEvents


class GlucoseStats(BaseModel):
    count: int
    avg: Optional[Decimal] = None
    min: Optional[Decimal] = None
    max: Optional[Decimal] = None


class InsulinStats(BaseModel):
    count: int
    total_dose: Decimal
    short_count: int
    short_total_dose: Decimal
    long_count: int
    long_total_dose: Decimal


class MealStats(BaseModel):
    count: int
    total_carbs_grams: Decimal
    total_bread_units: Decimal


class DayStats(BaseModel):
    date: str
    glucose: GlucoseStats
    insulin: InsulinStats
    meal: MealStats


class RecentStatsResponse(BaseModel):
    timezone: str
    today: DayStats
    yesterday: DayStats