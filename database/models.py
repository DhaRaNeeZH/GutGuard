"""
GutGuard – Database Models
All SQLAlchemy ORM models for the application.

Design principles:
- Normalised schema with proper foreign keys and indexes.
- Meal items (MealItem) hold the per-food detail; Meal holds the session.
- Custom foods live in CustomFood; they never corrupt FoodCatalogue.
- Timestamps are always UTC.
- Soft-delete not used in v1; hard delete with cascade is acceptable.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Index, Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from backend.extensions import db
except ImportError:
    from extensions import db


# ─── Helpers ──────────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


# ─── Role & User ──────────────────────────────────────────────────────────────

class Role(db.Model):
    """User roles: 'student' or 'admin'."""
    __tablename__ = "roles"

    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    """Registered student or admin."""
    __tablename__ = "users"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    student_id:   Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True,
                                                        index=True, comment="College roll/ID number")
    email:        Mapped[str]           = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str]           = mapped_column(String(100), nullable=False)
    password_hash:Mapped[str]           = mapped_column(String(255), nullable=False)
    role_id:      Mapped[int]           = mapped_column(ForeignKey("roles.id"), nullable=False)
    is_active:    Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    created_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow,
                                                        onupdate=utcnow, nullable=False)

    # Relationships
    role:         Mapped["Role"]           = relationship("Role", back_populates="users")
    meals:        Mapped[list["Meal"]]     = relationship("Meal", back_populates="user",
                                                          cascade="all, delete-orphan")
    water_logs:   Mapped[list["WaterLog"]] = relationship("WaterLog", back_populates="user",
                                                           cascade="all, delete-orphan")
    goals:        Mapped[list["UserGoal"]] = relationship("UserGoal", back_populates="user",
                                                           cascade="all, delete-orphan")
    custom_foods: Mapped[list["CustomFood"]] = relationship("CustomFood", back_populates="submitted_by",
                                                             cascade="all, delete-orphan")

    # Flask-Login helpers
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role and self.role.name == "admin"

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ─── Food Catalogue ───────────────────────────────────────────────────────────

class FoodCategory(db.Model):
    """Broad food groupings (e.g. South Indian, Snacks, Beverages)."""
    __tablename__ = "food_categories"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:        Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order:  Mapped[int]           = mapped_column(Integer, default=0, nullable=False)

    foods: Mapped[list["FoodCatalogue"]] = relationship("FoodCatalogue", back_populates="category")

    def __repr__(self) -> str:
        return f"<FoodCategory {self.name}>"


class FoodCatalogue(db.Model):
    """
    Reference food items.
    Only verified or reviewed foods live here.
    Custom/unverified submissions go to CustomFood.
    """
    __tablename__ = "food_catalogue"
    __table_args__ = (
        Index("ix_food_name_lower", "name_normalized"),
    )

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:            Mapped[str]           = mapped_column(String(200), nullable=False, index=True)
    name_normalized: Mapped[str]           = mapped_column(String(200), nullable=False,
                                                           comment="Lowercase, stripped – used for search")
    category_id:     Mapped[Optional[int]] = mapped_column(ForeignKey("food_categories.id"), nullable=True)
    region:          Mapped[Optional[str]] = mapped_column(String(100), nullable=True,
                                                           comment="e.g. South Indian, North Indian, Pan-India")
    is_vegetarian:   Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_vegan:        Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Nutritional data (per 100 g/ml) – nullable; only populated when credible source exists
    calories_kcal:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein_g:       Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs_g:         Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat_g:           Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fibre_g:         Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sodium_mg:       Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Provenance
    data_source:     Mapped[Optional[str]] = mapped_column(String(200), nullable=True,
                                                           comment="Source of nutritional data")
    data_license:    Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_verified:     Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False,
                                                           comment="Reviewed by admin")
    status:          Mapped[str]            = mapped_column(
        Enum("active", "pending", "retired", name="food_status"),
        default="active", nullable=False
    )
    created_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=utcnow,
                                                            onupdate=utcnow)

    # Relationships
    category:  Mapped[Optional["FoodCategory"]] = relationship("FoodCategory", back_populates="foods")
    aliases:   Mapped[list["FoodAlias"]]        = relationship("FoodAlias", back_populates="food",
                                                                cascade="all, delete-orphan")
    meal_items:Mapped[list["MealItem"]]         = relationship("MealItem", back_populates="food")

    def __repr__(self) -> str:
        return f"<FoodCatalogue {self.name}>"


class FoodAlias(db.Model):
    """
    Alternate names / spellings for a catalogue food.
    e.g. 'Pongal' → 'Ven Pongal', 'Khichdi', 'Kichadi'
    """
    __tablename__ = "food_aliases"
    __table_args__ = (
        UniqueConstraint("alias_normalized", name="uq_alias_normalized"),
    )

    id:               Mapped[int] = mapped_column(Integer, primary_key=True)
    food_id:          Mapped[int] = mapped_column(ForeignKey("food_catalogue.id",
                                                              ondelete="CASCADE"), nullable=False)
    alias:            Mapped[str] = mapped_column(String(200), nullable=False)
    alias_normalized: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    food: Mapped["FoodCatalogue"] = relationship("FoodCatalogue", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<FoodAlias {self.alias} → {self.food_id}>"


# ─── Custom / Unclassified Foods ──────────────────────────────────────────────

class CustomFood(db.Model):
    """
    Foods submitted by students that are not yet in the catalogue.
    Admin can review and promote them to FoodCatalogue.
    These are clearly separated from reference data.
    """
    __tablename__ = "custom_foods"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True)
    submitted_by_id:   Mapped[int]           = mapped_column(ForeignKey("users.id",
                                                                         ondelete="CASCADE"), nullable=False)
    name:              Mapped[str]           = mapped_column(String(200), nullable=False)
    name_normalized:   Mapped[str]           = mapped_column(String(200), nullable=False, index=True)
    notes:             Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status:     Mapped[str]           = mapped_column(
        Enum("pending", "approved", "rejected", name="custom_food_status"),
        default="pending", nullable=False
    )
    catalogue_food_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("food_catalogue.id"), nullable=True,
        comment="Set when approved and mapped to catalogue"
    )
    submitted_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    submitted_by:   Mapped["User"]                    = relationship("User", back_populates="custom_foods")
    catalogue_food: Mapped[Optional["FoodCatalogue"]] = relationship("FoodCatalogue")
    meal_items:     Mapped[list["MealItem"]]          = relationship("MealItem",
                                                                     back_populates="custom_food")

    def __repr__(self) -> str:
        return f"<CustomFood {self.name} [{self.review_status}]>"


# ─── Meals ────────────────────────────────────────────────────────────────────

class Meal(db.Model):
    """
    A single eating session (breakfast / lunch / dinner / snack).
    Contains one or more MealItems.
    """
    __tablename__ = "meals"
    __table_args__ = (
        Index("ix_meal_user_date", "user_id", "meal_date"),
    )

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:     Mapped[int]           = mapped_column(ForeignKey("users.id",
                                                                   ondelete="CASCADE"), nullable=False)
    meal_type:   Mapped[str]           = mapped_column(
        Enum("breakfast", "lunch", "dinner", "snack", name="meal_type"),
        nullable=False
    )
    meal_date:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False,
                                                       comment="Local date-time when the meal was eaten")
    notes:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo:     Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False,
                                                       comment="True = synthetic demo record, never in real analysis")
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow,
                                                        onupdate=utcnow)

    user:  Mapped["User"]           = relationship("User", back_populates="meals")
    items: Mapped[list["MealItem"]] = relationship("MealItem", back_populates="meal",
                                                   cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Meal {self.meal_type} {self.meal_date.date()}>"


class MealItem(db.Model):
    """
    One food within a meal.
    References either a catalogue food or a custom food—never both simultaneously.
    """
    __tablename__ = "meal_items"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    meal_id:        Mapped[int]           = mapped_column(ForeignKey("meals.id",
                                                                      ondelete="CASCADE"), nullable=False)
    # Exactly one of these two FK columns must be non-null
    food_id:        Mapped[Optional[int]] = mapped_column(ForeignKey("food_catalogue.id"), nullable=True)
    custom_food_id: Mapped[Optional[int]] = mapped_column(ForeignKey("custom_foods.id"), nullable=True)

    quantity:    Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                          comment="Numeric quantity")
    unit:        Mapped[Optional[str]]   = mapped_column(String(50), nullable=True,
                                                          comment="e.g. g, ml, piece, cup, plate")
    notes:       Mapped[Optional[str]]   = mapped_column(String(300), nullable=True)

    meal:        Mapped["Meal"]                   = relationship("Meal", back_populates="items")
    food:        Mapped[Optional["FoodCatalogue"]] = relationship("FoodCatalogue",
                                                                   back_populates="meal_items")
    custom_food: Mapped[Optional["CustomFood"]]    = relationship("CustomFood",
                                                                   back_populates="meal_items")

    @property
    def food_name(self) -> str:
        """Return the display name regardless of food type."""
        if self.food:
            return self.food.name
        if self.custom_food:
            return f"{self.custom_food.name} (custom)"
        return "Unknown food"

    def __repr__(self) -> str:
        return f"<MealItem meal={self.meal_id} food={self.food_name}>"


# ─── Water Log ────────────────────────────────────────────────────────────────

class WaterLog(db.Model):
    """
    Separate water intake records.
    Tracked independently from meals; never treated as a food risk item.
    """
    __tablename__ = "water_logs"
    __table_args__ = (
        Index("ix_water_user_date", "user_id", "logged_at"),
    )

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:     Mapped[int]           = mapped_column(ForeignKey("users.id",
                                                                   ondelete="CASCADE"), nullable=False)
    quantity:    Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                          comment="Amount; null if unknown")
    unit:        Mapped[str]           = mapped_column(String(20), default="ml", nullable=False)
    logged_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    notes:       Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_demo:     Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="water_logs")

    def __repr__(self) -> str:
        return f"<WaterLog {self.quantity}{self.unit} @ {self.logged_at}>"


# ─── Personal Goals ───────────────────────────────────────────────────────────

class UserGoal(db.Model):
    """
    Optional, student-defined personal habit goals.
    Not medically prescribed; used only for personal tracking.
    """
    __tablename__ = "user_goals"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]           = mapped_column(ForeignKey("users.id",
                                                                  ondelete="CASCADE"), nullable=False)
    goal_key:   Mapped[str]           = mapped_column(String(100), nullable=False,
                                                       comment="Machine-readable key, e.g. 'log_breakfast_daily'")
    goal_label: Mapped[str]           = mapped_column(String(200), nullable=False,
                                                       comment="Human-readable label")
    target_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active:  Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="goals")

    __table_args__ = (
        UniqueConstraint("user_id", "goal_key", name="uq_user_goal"),
    )

    def __repr__(self) -> str:
        return f"<UserGoal {self.goal_key} for user {self.user_id}>"


# ─── Report Metadata ──────────────────────────────────────────────────────────

class ReportRecord(db.Model):
    """Tracks generated PDF reports so students can re-download them."""
    __tablename__ = "report_records"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:      Mapped[int]           = mapped_column(ForeignKey("users.id",
                                                                    ondelete="CASCADE"), nullable=False)
    filename:     Mapped[str]           = mapped_column(String(300), nullable=False)
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=utcnow)
    is_shared:    Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False,
                                                        comment="True only when user explicitly shares")

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<ReportRecord user={self.user_id} {self.filename}>"
