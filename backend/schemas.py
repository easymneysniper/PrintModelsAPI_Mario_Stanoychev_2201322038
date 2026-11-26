from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


SQLITE_MAX_INTEGER = 2**63 - 1
MAX_SCALED_COPIES = 50 + 38


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class MaterialUnit(str, Enum):
    g = "g"
    m = "m"
    ml = "ml"


class NamedCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str = Field(min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class DesignerCreate(NamedCreate):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold() if isinstance(value, str) else value


class DesignerRead(DesignerCreate):
    id: int


class CategoryCreate(NamedCreate):
    pass


class CategoryRead(CategoryCreate):
    id: int


class MaterialCreate(NamedCreate):
    pass


class MaterialRead(MaterialCreate):
    id: int


class PrintModelCreate(NamedCreate):
    instructions: str = Field(min_length=1)
    difficulty: Difficulty
    print_time_minutes: int = Field(strict=True, gt=0, le=SQLITE_MAX_INTEGER)
    copies: int = Field(strict=True, gt=0, le=SQLITE_MAX_INTEGER)
    designer_id: int = Field(strict=True, gt=0, le=SQLITE_MAX_INTEGER)
    category_id: int | None = Field(default=None, strict=True, gt=0, le=SQLITE_MAX_INTEGER)

    @field_validator("instructions", mode="before")
    @classmethod
    def strip_instructions(cls, value):
        return value.strip() if isinstance(value, str) else value


class PrintModelRead(PrintModelCreate):
    id: int


class MaterialAmount(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    quantity: float = Field(strict=True, gt=0, allow_inf_nan=False)
    unit: MaterialUnit


class ModelMaterialCreate(MaterialAmount):
    material_id: int = Field(strict=True, gt=0, le=SQLITE_MAX_INTEGER)


class ModelMaterialRead(ModelMaterialCreate):
    material: MaterialRead


class ScaledPrintModelRead(PrintModelRead):
    materials: list[ModelMaterialRead]
