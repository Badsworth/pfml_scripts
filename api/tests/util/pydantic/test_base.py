import uuid

from sqlalchemy import Column, Integer

from massgov.pfml.db.models.base import Base
from massgov.pfml.util.pydantic import PydanticBaseModel


class PydanticTestModel(Base):
    __tablename__ = f"lk_pydantic_test_{uuid.uuid4()}"
    id = Column(Integer, primary_key=True, autoincrement=True)
    secret = Column(Integer)


class ModelForTest(PydanticBaseModel):
    id: int


def test_orm_mode():
    model = PydanticTestModel(id=123, secret=456)
    res = ModelForTest.from_orm(model)
    assert res.id == model.id
    assert res.dict().get("secret") is None
