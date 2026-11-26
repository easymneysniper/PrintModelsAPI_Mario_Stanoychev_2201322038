from __future__ import annotations

from math import isfinite
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend import models, schemas
from backend.database import Base
from backend.exceptions import ConflictError, InvalidInput, NotFound


Model = TypeVar("Model", bound=Base)


def _get_or_404(db: Session, model: type[Model], record_id: int) -> Model:
    record = db.get(model, record_id)
    if record is None:
        raise NotFound(f"{model.__name__} not found.")
    return record


def _commit(db: Session, conflict_message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(conflict_message) from None


def _save(db: Session, record: Model, conflict_message: str) -> Model:
    db.add(record)
    _commit(db, conflict_message)
    db.refresh(record)
    return record


class DesignerService:
    def list(self, db_session: Session) -> list[models.Designer]:
        return list(db_session.scalars(select(models.Designer).order_by(models.Designer.id)))

    def get(self, designer_id: int, db_session: Session) -> models.Designer:
        return _get_or_404(db_session, models.Designer, designer_id)

    def create(self, data: schemas.DesignerCreate, db_session: Session) -> models.Designer:
        designer = models.Designer(**data.model_dump())
        return _save(db_session, designer, "A designer with this email already exists.")

    def update(self, designer_id: int, data: schemas.DesignerCreate, db_session: Session) -> models.Designer:
        designer = self.get(designer_id, db_session)
        designer.name = data.name
        designer.email = data.email
        return _save(db_session, designer, "A designer with this email already exists.")

    def delete(self, designer_id: int, db_session: Session) -> None:
        db_session.delete(self.get(designer_id, db_session))
        _commit(db_session, "Designer has print models and cannot be deleted.")

    def list_models(self, designer_id: int, db_session: Session) -> list[models.PrintModel]:
        self.get(designer_id, db_session)
        statement = select(models.PrintModel).where(models.PrintModel.designer_id == designer_id)
        return list(db_session.scalars(statement.order_by(models.PrintModel.id)))


class CategoryService:
    def list(self, db_session: Session) -> list[models.Category]:
        return list(db_session.scalars(select(models.Category).order_by(models.Category.id)))

    def get(self, category_id: int, db_session: Session) -> models.Category:
        return _get_or_404(db_session, models.Category, category_id)

    def create(self, data: schemas.CategoryCreate, db_session: Session) -> models.Category:
        category = models.Category(**data.model_dump())
        return _save(db_session, category, "A category with this name already exists.")

    def update(self, category_id: int, data: schemas.CategoryCreate, db_session: Session) -> models.Category:
        category = self.get(category_id, db_session)
        category.name = data.name
        return _save(db_session, category, "A category with this name already exists.")

    def delete(self, category_id: int, db_session: Session) -> None:
        db_session.delete(self.get(category_id, db_session))
        _commit(db_session, "Category cannot be deleted because related data changed.")


class MaterialService:
    def list(self, db_session: Session) -> list[models.Material]:
        return list(db_session.scalars(select(models.Material).order_by(models.Material.id)))

    def get(self, material_id: int, db_session: Session) -> models.Material:
        return _get_or_404(db_session, models.Material, material_id)

    def create(self, data: schemas.MaterialCreate, db_session: Session) -> models.Material:
        material = models.Material(**data.model_dump())
        return _save(db_session, material, "A material with this name already exists.")

    def update(self, material_id: int, data: schemas.MaterialCreate, db_session: Session) -> models.Material:
        material = self.get(material_id, db_session)
        material.name = data.name
        return _save(db_session, material, "A material with this name already exists.")

    def delete(self, material_id: int, db_session: Session) -> None:
        db_session.delete(self.get(material_id, db_session))
        _commit(db_session, "Material is used by a print model and cannot be deleted.")


class PrintModelService:
    def __init__(self, designers: DesignerService, categories: CategoryService, materials: MaterialService):
        self.designers = designers
        self.categories = categories
        self.materials = materials

    def list(
        self, db_session: Session, name: str | None = None,
        category_id: int | None = None, max_print_time: int | None = None,
    ) -> list[models.PrintModel]:
        statement = select(models.PrintModel)
        if name is not None:
            statement = statement.where(models.PrintModel.name_key.contains(name.strip().casefold(), autoescape=True))
        if category_id is not None:
            statement = statement.where(models.PrintModel.category_id == category_id)
        if max_print_time is not None:
            statement = statement.where(models.PrintModel.print_time_minutes <= max_print_time)
        return list(db_session.scalars(statement.order_by(models.PrintModel.id)))

    def get(self, print_model_id: int, db_session: Session) -> models.PrintModel:
        return _get_or_404(db_session, models.PrintModel, print_model_id)

    def _check_relations(self, data: schemas.PrintModelCreate, db_session: Session) -> None:
        self.designers.get(data.designer_id, db_session)
        if data.category_id is not None:
            self.categories.get(data.category_id, db_session)

    def create(self, data: schemas.PrintModelCreate, db_session: Session) -> models.PrintModel:
        self._check_relations(data, db_session)
        model = models.PrintModel(**data.model_dump())
        return _save(db_session, model, "Model conflicts with an existing name or related resource.")

    def update(self, print_model_id: int, data: schemas.PrintModelCreate, db_session: Session) -> models.PrintModel:
        model = self.get(print_model_id, db_session)
        self._check_relations(data, db_session)
        for field, value in data.model_dump().items():
            setattr(model, field, value)
        return _save(db_session, model, "Model conflicts with an existing name or related resource.")

    def delete(self, print_model_id: int, db_session: Session) -> None:
        db_session.delete(self.get(print_model_id, db_session))
        _commit(db_session, "Print model cannot be deleted because related data changed.")

    def list_materials(self, print_model_id: int, db_session: Session) -> list[models.PrintModelMaterial]:
        self.get(print_model_id, db_session)
        statement = (
            select(models.PrintModelMaterial)
            .where(models.PrintModelMaterial.print_model_id == print_model_id)
            .options(joinedload(models.PrintModelMaterial.material))
            .order_by(models.PrintModelMaterial.material_id)
        )
        return list(db_session.scalars(statement))

    def add_material(
        self, print_model_id: int, data: schemas.ModelMaterialCreate, db_session: Session,
    ) -> models.PrintModelMaterial:
        self.get(print_model_id, db_session)
        self.materials.get(data.material_id, db_session)
        link = models.PrintModelMaterial(print_model_id=print_model_id, **data.model_dump())
        return _save(db_session, link, "Material is already attached to this print model.")

    def _get_material(self, print_model_id: int, material_id: int, db_session: Session) -> models.PrintModelMaterial:
        self.get(print_model_id, db_session)
        link = db_session.get(models.PrintModelMaterial, (print_model_id, material_id))
        if link is None:
            raise NotFound("Material is not attached to this print model.")
        return link

    def update_material(
        self, print_model_id: int, material_id: int, data: schemas.MaterialAmount, db_session: Session,
    ) -> models.PrintModelMaterial:
        link = self._get_material(print_model_id, material_id, db_session)
        link.quantity = data.quantity
        link.unit = data.unit
        return _save(db_session, link, "Material association conflicts with related data.")

    def remove_material(self, print_model_id: int, material_id: int, db_session: Session) -> None:
        db_session.delete(self._get_material(print_model_id, material_id, db_session))
        _commit(db_session, "Material association cannot be removed because related data changed.")

    def get_scaled(self, print_model_id: int, copies: int, db_session: Session) -> schemas.ScaledPrintModelRead:
        model = self.get(print_model_id, db_session)
        ratio = copies / model.copies
        materials = [
            schemas.ModelMaterialRead.model_validate(link)
            for link in self.list_materials(print_model_id, db_session)
        ]
        for material in materials:
            material.quantity *= ratio
            if not isfinite(material.quantity) or material.quantity <= 0:
                raise InvalidInput("Scaled quantity is outside the supported numeric range.")
        data = schemas.PrintModelRead.model_validate(model).model_dump()
        data["copies"] = copies
        return schemas.ScaledPrintModelRead(**data, materials=materials)
