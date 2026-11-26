import pytest
from sqlalchemy.orm import Session

from backend.exceptions import ConflictError, NotFound
from backend.schemas import CategoryCreate, DesignerCreate, MaterialCreate
from backend.services import CategoryService, DesignerService, MaterialService


@pytest.mark.parametrize("service", (DesignerService(), CategoryService(), MaterialService()))
def test_missing_record_raises_domain_error(database, service):
    with Session(database) as session:
        with pytest.raises(NotFound, match="not found"):
            service.get(999, session)


@pytest.mark.parametrize("service,data", (
    (DesignerService(), DesignerCreate(name="Designer", email="designer@example.com")),
    (CategoryService(), CategoryCreate(name="Tools")),
    (MaterialService(), MaterialCreate(name="PLA")),
))
def test_conflict_rolls_back_and_session_remains_usable(database, service, data):
    with Session(database) as session:
        original = service.create(data, session)
        record_id = original.id
        with pytest.raises(ConflictError):
            service.create(data, session)

        changed = data.model_copy(update={"name": "Changed"})
        updated = service.update(record_id, changed, session)
        assert updated.name == "Changed"
        assert [record.id for record in service.list(session)] == [record_id]
