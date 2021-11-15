from typing import Optional

import pytest
from pydantic import BaseModel

from massgov.pfml.db.models.factories import TaxIdentifierFactory
from massgov.pfml.util.pydantic.types import (
    MaskedTaxIdFormattedStr,
    TaxIdFormattedStr,
    TaxIdUnformattedStr,
)


class PydanticTypesTestModel(BaseModel):
    masked_tax_id_formatted: Optional[MaskedTaxIdFormattedStr]
    tax_id_formatted: Optional[TaxIdFormattedStr]
    tax_id_unformatted: Optional[TaxIdUnformattedStr]


def test_masked_tax_id_formatted_str_with_str():
    tax_id = "000-43-2123"
    model = PydanticTypesTestModel(masked_tax_id_formatted=tax_id)
    assert model.masked_tax_id_formatted == "***-**-2123"


def test_masked_tax_id_formatted_str_with_tax_identifier(
    test_db_session, initialize_factories_session
):
    tax_id = TaxIdentifierFactory.create()
    model = PydanticTypesTestModel(masked_tax_id_formatted=tax_id)
    assert model.masked_tax_id_formatted == f"***-**-{tax_id.tax_identifier_last4}"


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
