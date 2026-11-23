from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.database import Base


class Designer(Base):
    __tablename__ = "designers"
    __table_args__ = (
        UniqueConstraint("email", name="uq_designers_email"),
        CheckConstraint("length(trim(name)) > 0", name="ck_designers_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    print_models: Mapped[list[PrintModel]] = relationship(
        back_populates="designer", passive_deletes="all"
    )

    @validates("email")
    def normalize_email(self, key: str, value: str) -> str:
        return value.strip().casefold()


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("name_key", name="uq_categories_name_key"),
        CheckConstraint("length(trim(name)) > 0", name="ck_categories_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    name_key: Mapped[str] = mapped_column(String)
    print_models: Mapped[list[PrintModel]] = relationship(
        back_populates="category", passive_deletes="all"
    )

    @validates("name")
    def normalize_name(self, key: str, value: str) -> str:
        self.name_key = value.strip().casefold()
        return value.strip()


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (
        UniqueConstraint("name_key", name="uq_materials_name_key"),
        CheckConstraint("length(trim(name)) > 0", name="ck_materials_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    name_key: Mapped[str] = mapped_column(String)
    print_model_materials: Mapped[list[PrintModelMaterial]] = relationship(
        back_populates="material", passive_deletes="all"
    )

    @validates("name")
    def normalize_name(self, key: str, value: str) -> str:
        self.name_key = value.strip().casefold()
        return value.strip()


class PrintModel(Base):
    __tablename__ = "print_models"
    __table_args__ = (
        UniqueConstraint("designer_id", "name_key", name="uq_print_models_designer_name"),
        CheckConstraint("length(trim(name)) > 0", name="ck_print_models_name"),
        CheckConstraint("length(trim(instructions)) > 0", name="ck_print_models_instructions"),
        CheckConstraint("print_time_minutes > 0", name="ck_print_models_print_time"),
        CheckConstraint("copies > 0", name="ck_print_models_copies"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    name_key: Mapped[str] = mapped_column(String)
    instructions: Mapped[str] = mapped_column(Text)
    print_time_minutes: Mapped[int]
    copies: Mapped[int]
    designer_id: Mapped[int] = mapped_column(
        ForeignKey("designers.id", ondelete="RESTRICT"), index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    designer: Mapped[Designer] = relationship(back_populates="print_models")
    category: Mapped[Category | None] = relationship(back_populates="print_models")
    materials: Mapped[list[PrintModelMaterial]] = relationship(
        back_populates="print_model", cascade="all, delete-orphan", passive_deletes=True
    )

    @validates("name")
    def normalize_name(self, key: str, value: str) -> str:
        self.name_key = value.strip().casefold()
        return value.strip()


class PrintModelMaterial(Base):
    __tablename__ = "print_model_materials"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_print_model_materials_quantity"),
        CheckConstraint("unit IN ('g', 'm', 'ml')", name="ck_print_model_materials_unit"),
    )

    print_model_id: Mapped[int] = mapped_column(
        ForeignKey("print_models.id", ondelete="CASCADE"), primary_key=True
    )
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="RESTRICT"), primary_key=True
    )
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    print_model: Mapped[PrintModel] = relationship(back_populates="materials")
    material: Mapped[Material] = relationship(back_populates="print_model_materials")
