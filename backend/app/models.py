from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    foods = relationship("Food", back_populates="user", cascade="all, delete-orphan")
    glucose_events = relationship("GlucoseEvent", back_populates="user", cascade="all, delete-orphan")
    insulin_events = relationship("InsulinEvent", back_populates="user", cascade="all, delete-orphan")
    meal_events = relationship("MealEvent", back_populates="user", cascade="all, delete-orphan")


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    carbs_per_100g = Column(Numeric(6, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="foods")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_food_user_name"),
        CheckConstraint("carbs_per_100g >= 0 AND carbs_per_100g <= 100", name="check_carbs_range"),
    )


class GlucoseEvent(Base):
    __tablename__ = "glucose_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True,
                         default=lambda: datetime.now(timezone.utc))
    value = Column(Numeric(4, 2), nullable=False)
    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="glucose_events")

    __table_args__ = (
        CheckConstraint("value > 0", name="check_glucose_value_positive"),
    )


class InsulinEvent(Base):
    __tablename__ = "insulin_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True,
                         default=lambda: datetime.now(timezone.utc))
    insulin_type = Column(String(10), nullable=False)
    dose = Column(Numeric(5, 2), nullable=False)
    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="insulin_events")

    __table_args__ = (
        CheckConstraint("insulin_type IN ('short', 'long')", name="check_insulin_type"),
        CheckConstraint("dose > 0", name="check_insulin_dose_positive"),
    )


class MealEvent(Base):
    __tablename__ = "meal_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True,
                         default=lambda: datetime.now(timezone.utc))

    food_id = Column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False)
    grams = Column(Numeric(7, 2), nullable=False)
    carbs_grams = Column(Numeric(8, 2), nullable=False)
    bread_units = Column(Numeric(8, 2), nullable=False)
    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="meal_events")
    food = relationship("Food")

    __table_args__ = (
        CheckConstraint("grams > 0", name="check_grams_positive"),
        CheckConstraint("carbs_grams >= 0", name="check_carbs_grams_positive"),
        CheckConstraint("bread_units >= 0", name="check_bread_units_positive"),
    )