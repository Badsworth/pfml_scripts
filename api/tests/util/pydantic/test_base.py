import uuid
from typing import Optional

import pydantic
import pytest
from sqlalchemy import Column, Integer, String

from massgov.pfml.db.models.base import Base
from massgov.pfml.util.pydantic import (
    PydanticBaseModel,
    PydanticBaseModelEmptyStrIsNone,
    PydanticBaseModelRemoveEmptyStrFields,
)


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

    assert model.__fields_set__ == {
        "required",
        "not_required",
        "not_required_alt",
        "not_required_num",
    }

    assert model.required == ""
    assert model.not_required is None
    assert model.not_required_alt is None
    assert model.not_required_num == 3


class RemoveEmptyStrFieldsTestModel(PydanticBaseModelRemoveEmptyStrFields):
    required: str
    not_required: Optional[str] = None
    not_required_alt: Optional[str] = "foo"
    not_required_num: Optional[int] = 1


def test_remove_empty_str_fields_empty_required_errors():
    with pytest.raises(pydantic.ValidationError) as exc_info:
        RemoveEmptyStrFieldsTestModel.parse_obj({"required": ""})

    assert exc_info.value.errors()[0]["type"] == "value_error.missing"
    assert exc_info.value.errors()[0]["loc"] == ("required",)
    assert exc_info.value.errors()[0]["msg"] == "field required"


@pytest.mark.parametrize(
    "model",
    [
        pytest.param(
            RemoveEmptyStrFieldsTestModel.parse_obj(
                {
                    "required": "bar",
                    "not_required": "",
                    "not_required_alt": "",
                    "not_required_num": 3,
                }
            ),
            id="parse_obj",
        ),
        pytest.param(
            RemoveEmptyStrFieldsTestModel(
                required="bar", not_required="", not_required_alt="", not_required_num=3
            ),
            id="direct_construction",
        ),
    ],
)
def test_remove_empty_str_fields_optional_fields_use_default(model):
    assert model.__fields_set__ == {"required", "not_required_num"}

    assert model.required == "bar"
    assert model.not_required is None
    assert model.not_required_alt == "foo"
    assert model.not_required_num == 3
