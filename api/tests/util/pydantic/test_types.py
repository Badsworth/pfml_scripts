from typing import Optional

import pytest
from pydantic import BaseModel

from massgov.pfml.util.pydantic.types import TaxIdFormattedStr, TaxIdUnformattedStr


class PydanticTypesTestModel(BaseModel):
    tax_id_formatted: Optional[TaxIdFormattedStr]
    tax_id_unformatted: Optional[TaxIdUnformattedStr]


def test_tax_id_formatted_str_with_formatted_str():
    tax_id = "000-43-2123"
    model = PydanticTypesTestModel(tax_id_formatted=tax_id)
    assert model.tax_id_formatted == tax_id


def test_tax_id_formatted_str_with_unformatted_str():
    tax_id = "000432123"
    model = PydanticTypesTestModel(tax_id_formatted=tax_id)
    assert model.tax_id_formatted == "000-43-2123"


def test_tax_id_formatted_str_with_invalid_str():
    tax_id = "0003432122"
    with pytest.raises(ValueError) as err:
        PydanticTypesTestModel(tax_id_formatted=tax_id)
    assert "does not match" in str(err.value)


def test_tax_id_formatted_str_with_invalid_type():
    tax_id = 999432123
    with pytest.raises(ValueError) as err:
        PydanticTypesTestModel(tax_id_formatted=tax_id)
    assert "is not a str" in str(err.value)


def test_tax_id_unformatted_str_with_formatted_str():
    tax_id = "000-43-2123"
    model = PydanticTypesTestModel(tax_id_unformatted=tax_id)
    assert model.tax_id_unformatted == "000432123"


def test_tax_id_unformatted_str_with_unformatted_str():
    tax_id = "000432123"
    model = PydanticTypesTestModel(tax_id_unformatted=tax_id)
    assert model.tax_id_unformatted == tax_id


def test_tax_id_unformatted_str_with_invalid_str():
    tax_id = "0003432122"
    with pytest.raises(ValueError) as err:
        PydanticTypesTestModel(tax_id_unformatted=tax_id)
    assert "does not match" in str(err.value)


def test_tax_id_unformatted_str_with_invalid_type():
    tax_id = 999432123
    with pytest.raises(ValueError) as err:
        PydanticTypesTestModel(tax_id_unformatted=tax_id)
    assert "is not a str" in str(err.value)
