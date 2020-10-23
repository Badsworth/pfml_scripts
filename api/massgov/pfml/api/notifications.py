import json
from datetime import date
from typing import List, Optional

import connexion
from pydantic import validator

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.datetime as datetime_util
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.db.models.applications import Notification
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
    document_type: str
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
                            type="missing_expected_field",
                            field=expected_field,
                        )
                    )
            # Don't duplicate the error message for every wrong recipient, just put it once
            if error_list:
                break

        if error_list:
            raise ValidationException(errors=error_list, message="Validation error", data={})
        return v


def notifications_post():
    # Bounce them out if they do not have access
    ensure(CREATE, Notification)

    body = connexion.request.json
    # Use the pydantic models for validation
    NotificationRequest.parse_obj(connexion.request.json)
    # Persist the notification to the DB
    with app.db_session() as db_session:
        notification = Notification()

        now = datetime_util.utcnow()
        notification.created_at = now
        notification.updated_at = now

        notification.request_json = json.dumps(body)  # type: ignore

        db_session.add(notification)

    return response_util.success_response(
        message="Successfully started notification process.", status_code=201, data={}
    ).to_api_response()
