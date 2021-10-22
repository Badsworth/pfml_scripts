from __future__ import annotations

from typing import Optional

import pydantic


class CreateOrUpdateLeaveAdmin(pydantic.BaseModel):
    fineos_web_id: str
    fineos_employer_id: int
    admin_full_name: str
    admin_area_code: Optional[str]
    admin_phone_number: Optional[str]
    admin_email: str


class PhoneNumber(pydantic.BaseModel):
    area_code: Optional[str] = pydantic.Field(None, alias="tns:contactAreaCode")
    extension_code: Optional[str] = pydantic.Field(None, alias="tns:contactExtensionCode")
    international_code: Optional[str] = pydantic.Field(None, alias="tns:contactInternationalCode")
    contact_number: Optional[str] = pydantic.Field(None, alias="tns:contactNumber")

    class Config:
        allow_population_by_field_name = True


class CreateOrUpdateLeaveAdminRequest(pydantic.BaseModel):
    xmlns_tns: str = pydantic.Field(
        "http://www.fineos.com/frontoffice/externaluserprovisioning/external", alias="@xmlns:tns"
    )
    xmlns_xsi: str = pydantic.Field("http://www.w3.org/2001/XMLSchema-instance", alias="@xmlns:xsi")
    xsi_schemaLocation: str = pydantic.Field(
        "http://www.fineos.com/frontoffice/externaluserprovisioning/external CreateOrUpdateEmployerViewpointUserRequest.xsd",
        alias="@xsi:schemaLocation",
    )
    party_reference: str = pydantic.Field(..., alias="tns:partyReference")
    user_id: str = pydantic.Field(..., alias="tns:userID")
    full_name: str = pydantic.Field(..., alias="tns:fullName")
    email: str = pydantic.Field(..., alias="tns:emailAddress")
    phone: Optional[PhoneNumber] = pydantic.Field(None, alias="tns:phone")
    user_role: str = pydantic.Field("AllPermissions", alias="tns:userRole")
    enabled: str = pydantic.Field("true", alias="tns:enabled")

    class Config:
        allow_population_by_field_name = True
