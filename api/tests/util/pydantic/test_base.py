import uuid
from typing import Optional

from sqlalchemy import Column, Integer, String

from massgov.pfml.db.models.base import Base
from massgov.pfml.util.pydantic import PydanticBaseModel, PydanticBaseModelEmptyStrIsNone


class PydanticTestModel(Base):
    __tablename__ = f"lk_pydantic_test_{uuid.uuid4()}"
    id = Column(Integer, primary_key=True, autoincrement=True)
    secret = Column(Integer)
    foo = Column(String)


class ModelForTest(PydanticBaseModel):
    id: int


def test_orm_mode():
    model = PydanticTestModel(id=123, secret=456)
    res = ModelForTest.from_orm(model)
    assert res.id == model.id
    assert res.dict().get("secret") is None


def test_copy(test_db_session):
    original = PydanticTestModel(secret=10, foo="bar")
    test_db_session.add(original)
    test_db_session.flush()
    assert original.id is not None
    copy = original.copy(foo="test")
    assert copy.secret == 10
    assert copy.foo == "test"
    assert copy.id is None


class EmptyStrIsNoneTestModel(PydanticBaseModelEmptyStrIsNone):
    required: str
    not_required: Optional[str] = None
    not_required_alt: Optional[str] = "foo"
    not_required_num: Optional[int] = 1


def test_empty_str_is_none():
    model = EmptyStrIsNoneTestModel(
        required="", not_required="", not_required_alt="", not_required_num=3
    )

    assert model.required == ""
    assert model.not_required is None
    assert model.not_required_alt is None
    assert model.not_required_num == 3
