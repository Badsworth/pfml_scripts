from datetime import date
from typing import List, Optional

from massgov.pfml.api.models.applications.common import (
    Address,
    ApplicationLeaveDetails,
    DocumentCategory,
    DocumentType,
    EmploymentStatus,
    Occupation,
    PaymentPreferences,
)
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINStr, MassIdStr, TaxIdUnformattedStr


class ApplicationRequestBody(PydanticBaseModel):
    application_nickname: Optional[str]
    employee_ssn: Optional[TaxIdUnformattedStr]
    tax_identifier: Optional[TaxIdUnformattedStr]
    employer_fein: Optional[FEINStr]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    has_state_id: Optional[bool]
    mass_id: Optional[MassIdStr]
    occupation: Optional[Occupation]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[ApplicationLeaveDetails]
    payment_preferences: Optional[List[PaymentPreferences]]
    mailing_address: Optional[Address]
    residential_address: Optional[Address]


class DocumentRequestBody(PydanticBaseModel):
    document_category: DocumentCategory
    document_type: DocumentType
    name: Optional[str]
    description: str
