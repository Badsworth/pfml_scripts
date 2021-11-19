from typing import Optional

import pytest
from pydantic import BaseModel, ValidationError

from massgov.pfml.db.models.factories import TaxIdentifierFactory
from massgov.pfml.types import TaxId


class PydanticTypesTestModel(BaseModel):
    tax_id: Optional[TaxId]


def test_masked_tax_id_formatted_str_with_str():
    tax_id = "000-43-2123"
    model = PydanticTypesTestModel(tax_id=tax_id)
    assert model.tax_id.to_masked_str() == "***-**-2123"


def test_masked_tax_id_formatted_str_with_tax_identifier(
    test_db_session, initialize_factories_session
):
    tax_id = TaxIdentifierFactory.create()
    model = PydanticTypesTestModel(tax_id=tax_id)
    assert model.tax_id.to_masked_str() == f"***-**-{tax_id.tax_identifier_last4}"


def test_tax_id_formatted_str_with_formatted_str():
    tax_id = "000-43-2123"
    model = PydanticTypesTestModel(tax_id=tax_id)
    assert model.tax_id.to_formatted_str() == "000-43-2123"


def test_tax_id_formatted_str_with_unformatted_str():
    tax_id = "000432123"
    model = PydanticTypesTestModel(tax_id=tax_id)
    assert model.tax_id.to_formatted_str() == "000-43-2123"


def test_tax_id_formatted_str_with_invalid_str():
    tax_id = "0003432122"
    with pytest.raises(ValueError) as err:
        PydanticTypesTestModel(tax_id=tax_id)
    assert "does not match" in str(err.value)


def test_tax_id_formatted_str_with_invalid_type():
    tax_id = 999432123
    with pytest.raises(ValidationError) as err:
        PydanticTypesTestModel(tax_id=tax_id)
    assert "string required" in str(err.value)


def test_tax_id_unformatted_str_with_formatted_str():
    tax_id = "000-43-2123"
    model = PydanticTypesTestModel(tax_id=tax_id)
    assert model.tax_id.to_unformatted_str() == "000432123"


def test_tax_id_unformatted_str_with_unformatted_str():
    tax_id = "000432123"
    model = PydanticTypesTestModel(tax_id=tax_id)
    assert model.tax_id.to_unformatted_str() == "000432123"


def test_tax_id_unformatted_str_with_invalid_str():
    tax_id = "0003432122"
    with pytest.raises(ValueError) as err:
        PydanticTypesTestModel(tax_id=tax_id)
    assert "does not match one of:" in str(err.value)


def test_tax_id_unformatted_str_with_invalid_type():
    tax_id = 999432123
    with pytest.raises(ValidationError) as err:
        PydanticTypesTestModel(tax_id=tax_id)
    assert "string required" in str(err.value)
