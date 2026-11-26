from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from backend import schemas
from backend.database import get_db
from backend.services import CategoryService, DesignerService, MaterialService, PrintModelService


router = APIRouter()
designer_service = DesignerService()
category_service = CategoryService()
material_service = MaterialService()
print_model_service = PrintModelService(designer_service, category_service, material_service)


@router.get("/designers", response_model=list[schemas.DesignerRead], tags=["Designers"])
def list_designers(db_session: Session = Depends(get_db)):
    return designer_service.list(db_session)


@router.post("/designers", response_model=schemas.DesignerRead, status_code=status.HTTP_201_CREATED, tags=["Designers"])
def create_designer(data: schemas.DesignerCreate, db_session: Session = Depends(get_db)):
    return designer_service.create(data, db_session)


@router.get("/designers/{designer_id}", response_model=schemas.DesignerRead, tags=["Designers"])
def get_designer(
    designer_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
):
    return designer_service.get(designer_id, db_session)


@router.put("/designers/{designer_id}", response_model=schemas.DesignerRead, tags=["Designers"])
def update_designer(
    data: schemas.DesignerCreate, designer_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return designer_service.update(designer_id, data, db_session)


@router.delete("/designers/{designer_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Designers"])
def delete_designer(
    designer_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
) -> Response:
    designer_service.delete(designer_id, db_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/categories", response_model=list[schemas.CategoryRead], tags=["Categories"])
def list_categories(db_session: Session = Depends(get_db)):
    return category_service.list(db_session)


@router.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(data: schemas.CategoryCreate, db_session: Session = Depends(get_db)):
    return category_service.create(data, db_session)


@router.get("/categories/{category_id}", response_model=schemas.CategoryRead, tags=["Categories"])
def get_category(
    category_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
):
    return category_service.get(category_id, db_session)


@router.put("/categories/{category_id}", response_model=schemas.CategoryRead, tags=["Categories"])
def update_category(
    data: schemas.CategoryCreate, category_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return category_service.update(category_id, data, db_session)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"])
def delete_category(
    category_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
) -> Response:
    category_service.delete(category_id, db_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/materials", response_model=list[schemas.MaterialRead], tags=["Materials"])
def list_materials(db_session: Session = Depends(get_db)):
    return material_service.list(db_session)


@router.post("/materials", response_model=schemas.MaterialRead, status_code=status.HTTP_201_CREATED, tags=["Materials"])
def create_material(data: schemas.MaterialCreate, db_session: Session = Depends(get_db)):
    return material_service.create(data, db_session)


@router.get("/materials/{material_id}", response_model=schemas.MaterialRead, tags=["Materials"])
def get_material(
    material_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
):
    return material_service.get(material_id, db_session)


@router.put("/materials/{material_id}", response_model=schemas.MaterialRead, tags=["Materials"])
def update_material(
    data: schemas.MaterialCreate, material_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return material_service.update(material_id, data, db_session)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Materials"])
def delete_material(
    material_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
) -> Response:
    material_service.delete(material_id, db_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/print-models", response_model=list[schemas.PrintModelRead], tags=["Print Models"])
def list_print_models(
    name: str | None = None,
    category_id: int | None = Query(default=None, gt=0, le=schemas.SQLITE_MAX_INTEGER),
    max_print_time: int | None = Query(default=None, gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return print_model_service.list(db_session, name, category_id, max_print_time)


@router.post("/print-models", response_model=schemas.PrintModelRead, status_code=status.HTTP_201_CREATED, tags=["Print Models"])
def create_print_model(data: schemas.PrintModelCreate, db_session: Session = Depends(get_db)):
    return print_model_service.create(data, db_session)


@router.get("/print-models/{print_model_id}", response_model=schemas.PrintModelRead, tags=["Print Models"])
def get_print_model(
    print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
):
    return print_model_service.get(print_model_id, db_session)


@router.put("/print-models/{print_model_id}", response_model=schemas.PrintModelRead, tags=["Print Models"])
def update_print_model(
    data: schemas.PrintModelCreate, print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return print_model_service.update(print_model_id, data, db_session)


@router.delete("/print-models/{print_model_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Print Models"])
def delete_print_model(
    print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
) -> Response:
    print_model_service.delete(print_model_id, db_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/designers/{designer_id}/print-models", response_model=list[schemas.PrintModelRead], tags=["Designers"])
def list_designer_models(
    designer_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
):
    return designer_service.list_models(designer_id, db_session)


@router.get("/print-models/{print_model_id}/materials", response_model=list[schemas.ModelMaterialRead], tags=["Model Materials"])
def list_model_materials(
    print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER), db_session: Session = Depends(get_db),
):
    return print_model_service.list_materials(print_model_id, db_session)


@router.post("/print-models/{print_model_id}/materials", response_model=schemas.ModelMaterialRead, status_code=status.HTTP_201_CREATED, tags=["Model Materials"])
def add_model_material(
    data: schemas.ModelMaterialCreate, print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return print_model_service.add_material(print_model_id, data, db_session)


@router.put("/print-models/{print_model_id}/materials/{material_id}", response_model=schemas.ModelMaterialRead, tags=["Model Materials"])
def update_model_material(
    data: schemas.MaterialAmount,
    print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    material_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
):
    return print_model_service.update_material(print_model_id, material_id, data, db_session)


@router.delete("/print-models/{print_model_id}/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Model Materials"])
def remove_model_material(
    print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    material_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    db_session: Session = Depends(get_db),
) -> Response:
    print_model_service.remove_material(print_model_id, material_id, db_session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/print-models/{print_model_id}/scaled", response_model=schemas.ScaledPrintModelRead, tags=["Print Models"])
def get_scaled_print_model(
    print_model_id: int = Path(gt=0, le=schemas.SQLITE_MAX_INTEGER),
    copies: int = Query(gt=0, le=schemas.MAX_SCALED_COPIES),
    db_session: Session = Depends(get_db),
):
    return print_model_service.get_scaled(print_model_id, copies, db_session)
