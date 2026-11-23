from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from backend import crud, schemas
from backend.database import get_db


router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
ResourceId = Annotated[int, Path(gt=0, le=schemas.SQLITE_MAX_INTEGER)]


@router.get("/designers", response_model=list[schemas.DesignerRead], tags=["Designers"])
def list_designers(db: DbSession):
    return crud.list_designers(db)


@router.post("/designers", response_model=schemas.DesignerRead, status_code=status.HTTP_201_CREATED, tags=["Designers"])
def create_designer(data: schemas.DesignerCreate, db: DbSession):
    return crud.create_designer(db, data)


@router.get("/designers/{designer_id}", response_model=schemas.DesignerRead, tags=["Designers"])
def get_designer(designer_id: ResourceId, db: DbSession):
    return crud.get_designer(db, designer_id)


@router.put("/designers/{designer_id}", response_model=schemas.DesignerRead, tags=["Designers"])
def update_designer(designer_id: ResourceId, data: schemas.DesignerCreate, db: DbSession):
    return crud.update_designer(db, designer_id, data)


@router.delete("/designers/{designer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Designers"])
def delete_designer(designer_id: ResourceId, db: DbSession) -> Response:
    crud.delete_designer(db, designer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/categories", response_model=list[schemas.CategoryRead], tags=["Categories"])
def list_categories(db: DbSession):
    return crud.list_categories(db)


@router.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(data: schemas.CategoryCreate, db: DbSession):
    return crud.create_category(db, data)


@router.get("/categories/{category_id}", response_model=schemas.CategoryRead, tags=["Categories"])
def get_category(category_id: ResourceId, db: DbSession):
    return crud.get_category(db, category_id)


@router.put("/categories/{category_id}", response_model=schemas.CategoryRead, tags=["Categories"])
def update_category(category_id: ResourceId, data: schemas.CategoryCreate, db: DbSession):
    return crud.update_category(db, category_id, data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"])
def delete_category(category_id: ResourceId, db: DbSession) -> Response:
    crud.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/materials", response_model=list[schemas.MaterialRead], tags=["Materials"])
def list_materials(db: DbSession):
    return crud.list_materials(db)


@router.post("/materials", response_model=schemas.MaterialRead, status_code=status.HTTP_201_CREATED, tags=["Materials"])
def create_material(data: schemas.MaterialCreate, db: DbSession):
    return crud.create_material(db, data)


@router.get("/materials/{material_id}", response_model=schemas.MaterialRead, tags=["Materials"])
def get_material(material_id: ResourceId, db: DbSession):
    return crud.get_material(db, material_id)


@router.put("/materials/{material_id}", response_model=schemas.MaterialRead, tags=["Materials"])
def update_material(material_id: ResourceId, data: schemas.MaterialCreate, db: DbSession):
    return crud.update_material(db, material_id, data)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Materials"])
def delete_material(material_id: ResourceId, db: DbSession) -> Response:
    crud.delete_material(db, material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/print-models", response_model=list[schemas.PrintModelRead], tags=["Print Models"])
def list_print_models(db: DbSession):
    return crud.list_print_models(db)


@router.post("/print-models", response_model=schemas.PrintModelRead, status_code=status.HTTP_201_CREATED, tags=["Print Models"])
def create_print_model(data: schemas.PrintModelCreate, db: DbSession):
    return crud.create_print_model(db, data)


@router.get("/print-models/{print_model_id}", response_model=schemas.PrintModelRead, tags=["Print Models"])
def get_print_model(print_model_id: ResourceId, db: DbSession):
    return crud.get_print_model(db, print_model_id)


@router.put("/print-models/{print_model_id}", response_model=schemas.PrintModelRead, tags=["Print Models"])
def update_print_model(print_model_id: ResourceId, data: schemas.PrintModelCreate, db: DbSession):
    return crud.update_print_model(db, print_model_id, data)


@router.delete("/print-models/{print_model_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Print Models"])
def delete_print_model(print_model_id: ResourceId, db: DbSession) -> Response:
    crud.delete_print_model(db, print_model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
