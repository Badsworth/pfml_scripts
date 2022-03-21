from typing import List

import pytest
from pydantic import BaseModel, ValidationError

from massgov.pfml.util.logging.pydantic import validation_error_log_attrs


class SimpleModelForTests(BaseModel):
    an_attribute: str


class SimpleMultipleModelForTests(BaseModel):
    attribute_1: str
    attribute_2: str


class ListModelForTests(BaseModel):
    a_list: List[str]


class NestedModelForTests(BaseModel):
    a_simple_model: SimpleModelForTests


def test_validation_error_log_attrs_simple():
    with pytest.raises(ValidationError) as exc_info:
        SimpleModelForTests()

    assert validation_error_log_attrs(exc_info.value) == {
        "an_attribute:field": "an_attribute",
        "an_attribute:first_loc": "an_attribute",
        "an_attribute:last_loc": "an_attribute",
        "an_attribute:loc_raw": "('an_attribute',)",
        "an_attribute:msg": "field required",
        "an_attribute:type": "value_error.missing",
        "validation_error_str": """1 validation error for SimpleModelForTests
an_attribute
  field required (type=value_error.missing)""",
    }


def test_validation_error_log_attrs_simple_multiple():
    with pytest.raises(ValidationError) as exc_info:
        SimpleMultipleModelForTests()

    assert validation_error_log_attrs(exc_info.value) == {
        "attribute_1:field": "attribute_1",
        "attribute_1:first_loc": "attribute_1",
        "attribute_1:last_loc": "attribute_1",
        "attribute_1:loc_raw": "('attribute_1',)",
        "attribute_1:msg": "field required",
        "attribute_1:type": "value_error.missing",
        "attribute_2:field": "attribute_2",
        "attribute_2:first_loc": "attribute_2",
        "attribute_2:last_loc": "attribute_2",
        "attribute_2:loc_raw": "('attribute_2',)",
        "attribute_2:msg": "field required",
        "attribute_2:type": "value_error.missing",
        "validation_error_str": """2 validation errors for SimpleMultipleModelForTests
attribute_1
  field required (type=value_error.missing)
attribute_2
  field required (type=value_error.missing)""",
    }


def test_validation_error_log_attrs_list():
    with pytest.raises(ValidationError) as exc_info:
        ListModelForTests.parse_obj({"a_list": ["foo", Exception("bar")]})

    assert validation_error_log_attrs(exc_info.value) == {
        "a_list.1:field": "a_list.1",
        "a_list.1:first_loc": "a_list",
        "a_list.1:last_loc": "1",
        "a_list.1:loc_raw": "('a_list', 1)",
        "a_list.1:msg": "str type expected",
        "a_list.1:type": "type_error.str",
        "validation_error_str": """1 validation error for ListModelForTests
a_list -> 1
  str type expected (type=type_error.str)""",
    }


def test_validation_error_log_attrs_nested():
    with pytest.raises(ValidationError) as exc_info:
        NestedModelForTests.parse_obj({"a_simple_model": {}})

    assert validation_error_log_attrs(exc_info.value) == {
        "a_simple_model.an_attribute:field": "a_simple_model.an_attribute",
        "a_simple_model.an_attribute:first_loc": "a_simple_model",
        "a_simple_model.an_attribute:last_loc": "an_attribute",
        "a_simple_model.an_attribute:loc_raw": "('a_simple_model', 'an_attribute')",
        "a_simple_model.an_attribute:msg": "field required",
        "a_simple_model.an_attribute:type": "value_error.missing",
        "validation_error_str": """1 validation error for NestedModelForTests
a_simple_model -> an_attribute
  field required (type=value_error.missing)""",
    }
