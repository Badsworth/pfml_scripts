from typing import Optional

import pytest

from massgov.pfml.util.pydantic import PydanticBaseModel


class Sample(PydanticBaseModel):
    first_name: str
    middle_name: Optional[str]


def test_reject_empty_string_value():
    with pytest.raises(ValueError):
        Sample(first_name="", middle_name="test")

    with pytest.raises(ValueError):
        Sample(first_name="test", middle_name="")

    with pytest.raises(ValueError):
        Sample(first_name="", middle_name="")
