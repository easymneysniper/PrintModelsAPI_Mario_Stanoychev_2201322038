from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import Base


Model = TypeVar("Model", bound=Base)


def _get_or_404(db: Session, model: type[Model], record_id: int) -> Model:
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found.")
    return record


def _commit(db: Session, conflict_message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, conflict_message) from None


def _save(db: Session, record: Model, conflict_message: str) -> Model:
    db.add(record)
    _commit(db, conflict_message)
    db.refresh(record)
    return record


def list_designers(db: Session) -> list[models.Designer]:
    return list(db.scalars(select(models.Designer).order_by(models.Designer.id)))


def get_designer(db: Session, designer_id: int) -> models.Designer:
    return _get_or_404(db, models.Designer, designer_id)


def create_designer(db: Session, data: schemas.DesignerCreate) -> models.Designer:
    designer = models.Designer(**data.model_dump())
    return _save(db, designer, "A designer with this email already exists.")


def update_designer(db: Session, designer_id: int, data: schemas.DesignerCreate) -> models.Designer:
    designer = get_designer(db, designer_id)
    designer.name = data.name
    designer.email = data.email
    return _save(db, designer, "A designer with this email already exists.")


def delete_designer(db: Session, designer_id: int) -> None:
    db.delete(get_designer(db, designer_id))
    _commit(db, "Designer has print models and cannot be deleted.")


def list_categories(db: Session) -> list[models.Category]:
    return list(db.scalars(select(models.Category).order_by(models.Category.id)))


def get_category(db: Session, category_id: int) -> models.Category:
    return _get_or_404(db, models.Category, category_id)


def create_category(db: Session, data: schemas.CategoryCreate) -> models.Category:
    category = models.Category(**data.model_dump())
    return _save(db, category, "A category with this name already exists.")


def update_category(db: Session, category_id: int, data: schemas.CategoryCreate) -> models.Category:
    category = get_category(db, category_id)
    category.name = data.name
    return _save(db, category, "A category with this name already exists.")


def delete_category(db: Session, category_id: int) -> None:
    db.delete(get_category(db, category_id))
    _commit(db, "Category cannot be deleted because related data changed.")


def list_materials(db: Session) -> list[models.Material]:
    return list(db.scalars(select(models.Material).order_by(models.Material.id)))


def get_material(db: Session, material_id: int) -> models.Material:
    return _get_or_404(db, models.Material, material_id)


def create_material(db: Session, data: schemas.MaterialCreate) -> models.Material:
    material = models.Material(**data.model_dump())
    return _save(db, material, "A material with this name already exists.")


def update_material(db: Session, material_id: int, data: schemas.MaterialCreate) -> models.Material:
    material = get_material(db, material_id)
    material.name = data.name
    return _save(db, material, "A material with this name already exists.")


def delete_material(db: Session, material_id: int) -> None:
    db.delete(get_material(db, material_id))
    _commit(db, "Material is used by a print model and cannot be deleted.")


def list_print_models(db: Session) -> list[models.PrintModel]:
    return list(db.scalars(select(models.PrintModel).order_by(models.PrintModel.id)))


def get_print_model(db: Session, print_model_id: int) -> models.PrintModel:
    return _get_or_404(db, models.PrintModel, print_model_id)


def _check_model_relations(db: Session, data: schemas.PrintModelCreate) -> None:
    get_designer(db, data.designer_id)
    if data.category_id is not None:
        get_category(db, data.category_id)


def create_print_model(db: Session, data: schemas.PrintModelCreate) -> models.PrintModel:
    _check_model_relations(db, data)
    model = models.PrintModel(**data.model_dump())
    return _save(db, model, "Model conflicts with an existing name or related resource.")


def update_print_model(db: Session, print_model_id: int, data: schemas.PrintModelCreate) -> models.PrintModel:
    model = get_print_model(db, print_model_id)
    _check_model_relations(db, data)
    for field, value in data.model_dump().items():
        setattr(model, field, value)
    return _save(db, model, "Model conflicts with an existing name or related resource.")


def delete_print_model(db: Session, print_model_id: int) -> None:
    db.delete(get_print_model(db, print_model_id))
    _commit(db, "Print model cannot be deleted because related data changed.")
