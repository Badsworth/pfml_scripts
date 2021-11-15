from datetime import date
from typing import List, Optional

from pydantic import validator

from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.util.pydantic import PydanticBaseModel


class RecipientDetails(PydanticBaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    contact_id: Optional[str]
    email_address: str


class ClaimantInfo(PydanticBaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    customer_id: str


class NotificationRequest(PydanticBaseModel):
    absence_case_id: str
    document_type: Optional[str]
    fein: str
    organization_name: str
    trigger: str
    source: str
    recipient_type: str
    recipients: List[RecipientDetails]
    claimant_info: ClaimantInfo

    @validator("recipients")
    def validate_recipients(cls, v, values, **kwargs):  # noqa: B902
        """ Validate conditionally required recipient parameters """
        recipient_type = values["recipient_type"]

        error_list = []
        if recipient_type == "Claimant":
            expected_fields = ["first_name", "last_name", "email_address"]
        elif recipient_type == "Leave Administrator":
            expected_fields = ["full_name", "contact_id", "email_address"]

        for recipient in v:
            for expected_field in expected_fields:
                if not getattr(recipient, expected_field):
                    error_list.append(
                        ValidationErrorDetail(
                            message=f"{expected_field} is required when recipient type is {recipient_type}: {recipient}",
                            type=IssueType.required,
                            field=expected_field,
                        )
                    )
            # Don't duplicate the error message for every wrong recipient, just put it once
            if error_list:
                break

        if error_list:
            raise ValidationException(errors=error_list, message="Validation error", data={})
        return v
