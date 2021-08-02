import pytest

from massgov.pfml.types import TaxId


def test_tax_id_with_formatted_str():
    tax_id = TaxId("000-43-2123")

    assert tax_id.to_formatted_str() == "000-43-2123"
    assert tax_id.to_unformatted_str() == "000432123"


def test_tax_id_with_unformatted_str():
    tax_id = TaxId("000432123")

    assert tax_id.to_formatted_str() == "000-43-2123"
    assert tax_id.to_unformatted_str() == "000432123"


# def test_tax_id_with_invalid_str():
#     with pytest.raises(ValueError) as err:
#         TaxId("00043212")
#     assert "does not match" in str(err.value)


def test_tax_id_with_invalid_type():
    tax_id = 999432123
    with pytest.raises(TypeError) as err:
        TaxId(tax_id)
    assert "expected string" in str(err.value)


def test_tax_id_equality():
    assert TaxId("000-43-2123") == TaxId("000-43-2123")


def test_tax_id_inequality():
    assert TaxId("000-43-2123") != TaxId("000-43-2122")


def test_tax_id_equality_invalid():
    with pytest.raises(AssertionError):
        assert TaxId("000-43-2123") == "000-43-2123"
