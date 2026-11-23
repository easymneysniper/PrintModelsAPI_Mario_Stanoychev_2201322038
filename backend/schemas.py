from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SQLITE_MAX_INTEGER = 2**63 - 1
PositiveInteger = Annotated[int, Field(strict=True, gt=0, le=SQLITE_MAX_INTEGER)]


class NamedCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: NonEmptyText


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
    instructions: NonEmptyText
    print_time_minutes: PositiveInteger
    copies: PositiveInteger
    designer_id: PositiveInteger
    category_id: PositiveInteger | None = None


class PrintModelRead(PrintModelCreate):
    id: int
