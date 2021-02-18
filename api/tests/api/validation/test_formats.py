import pytest

from massgov.pfml.api.validation.formats import is_date, is_maskable_date


def test_is_date_with_non_str():
    assert is_date(123)


def test_is_date_with_date():
    assert is_date("2020-01-29")


def test_is_date_with_invalid_date():
    with pytest.raises(ValueError):
        is_date("2020-00-01")


def test_is_date_with_non_date():
    with pytest.raises(ValueError):
        is_date("hello")

    with pytest.raises(ValueError):
        is_date("****-01-29")


def test_is_maskable_date_with_non_str():
    assert is_maskable_date(123)


def test_is_maskable_date_with_date():
    assert is_maskable_date("2020-01-29")


def test_is_maskable_date_with_masked_date():
    assert is_maskable_date("****-01-29")


def test_is_maskable_date_with_invalid_date():
    with pytest.raises(ValueError):
        is_maskable_date("2020-00-01")


def test_is_maskable_date_with_non_date():
    with pytest.raises(ValueError):
        is_maskable_date("hello")


def test_is_maskable_date_with_masked_invalid_date():
    with pytest.raises(ValueError):
        is_maskable_date("****-00-29")


def test_is_maskable_date_with_masked_non_date():
    with pytest.raises(ValueError):
        is_maskable_date("****-ab-cd")
