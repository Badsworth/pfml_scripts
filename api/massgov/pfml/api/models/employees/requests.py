from typing import Optional

from pydantic import root_validator, validator

from massgov.pfml.api.models.common import SearchEnvelope
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import TaxIdUnformattedStr


class EmployeeSearchTerms(PydanticBaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email_address: Optional[str]
    phone_number: Optional[str]
    tax_identifier: Optional[TaxIdUnformattedStr]
    fineos_customer_number: Optional[str]

    @validator("email_address")
    def check_email_content(cls, v):  # noqa: B902
        alphanumeric_count = 0
        for c in v:
            if c.isalnum():
                alphanumeric_count += 1

        if alphanumeric_count < 3:
            raise ValueError("must contain at least 3 alphanumeric characters")
        return v

    @validator("first_name", "last_name")
    def check_name_content(cls, v):  # noqa: B902
        if not (v.isalnum() and len(v) >= 3):
            raise ValueError(
                "Name fields must only contain alphanumeric characters and have at least 3 of them"
            )
        return v

    @root_validator(pre=True)
    def check_required_names(cls, values):  # noqa: B902
        first_name, last_name = values.get("first_name"), values.get("last_name")

        if type(first_name) == type(last_name):
            return values

        raise ValueError(
            "If either first_name or last_name are specified, the other must be as well"
        )


EmployeeSearchRequest = SearchEnvelope[EmployeeSearchTerms]
