from datetime import date
from enum import Enum
from typing import Optional, Union

from pydantic import Field, validator

from massgov.pfml.util.datetime import parse_date_YMD
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.strings import snake_to_camel


class RmvAcknowledgement(Enum):
    # Request did not pass validation. This could mean a required field is missing,
    # or the format of those fields are incorrect.
    REQUIRED_FIELDS_MISSING = "INVALIDINPUT_REQUIRED_FIELDS_MISSING"
    # 404 identity was not found in ATLAS, or did not have a verified SSN.
    CUSTOMER_NOT_FOUND = "INVALIDRESULTS_CUSTOMER_NOT_FOUND"
    # Multiple identities found in ATLAS for the given query.
    MULTIPLE_CUSTOMERS_FOUND = "INVALIDRESULTS_MULTIPLE_CUSTOMERS_FOUND"
    # Driver account or a license/permit not found.
    CREDENTIAL_NOT_FOUND = "INVALIDRESULTS_CREDENTIAL_NOT_FOUND"


class VendorLicenseInquiryRequest(PydanticBaseModel):
    first_name: str
    last_name: str
    date_of_birth: date = Field(..., alias="DOB")
    ssn_last_4: str = Field(..., alias="Last4SSN")
    license_id: Optional[str] = Field(None, alias="LicenseID")

    class Config:
        alias_generator = snake_to_camel
        allow_population_by_field_name = True


class RMVSex(str, Enum):
    M = "MALE"
    F = "FEMALE"
    X = "X"


class VendorLicenseInquiryResponse(PydanticBaseModel):
    customer_key: str
    license_id: str = Field(..., alias="LicenseID")
    license1_expiration_date: Optional[date]
    license2_expiration_date: Optional[date]
    cfl_sanctions: bool = Field(..., alias="CFLSanctions")
    cfl_sanctions_active: bool = Field(..., alias="CFLSanctionsActive")
    is_customer_inactive: bool = Field(..., alias="CustomerInActive")
    street1: str
    street2: Optional[str]
    city: str
    zip: str
    sex: Union[RMVSex, str, None]

    _parse_license1: classmethod = validator(
        "license1_expiration_date", pre=True, allow_reuse=True
    )(parse_date_YMD)
    _parse_license2: classmethod = validator(
        "license2_expiration_date", pre=True, allow_reuse=True
    )(parse_date_YMD)

    class Config:
        alias_generator = snake_to_camel
        allow_population_by_field_name = True
