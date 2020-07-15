from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from massgov.pfml.api.models.applications.common import (
    ApplicationLeaveDetails,
    EmploymentStatus,
    Occupation,
    PaymentPreferences,
)
from massgov.pfml.api.models.common import WarningsAndErrors
from massgov.pfml.util.pydantic import PydanticBaseModel


class ApplicationRequestBody(PydanticBaseModel):
    application_nickname: Optional[str]
    employee_ssn: Optional[str]
    employer_fein: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    occupation: Optional[Occupation]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[ApplicationLeaveDetails]
    payment_preferences: Optional[List[PaymentPreferences]]


# TODO: this behavior should eventually be generalized, so request handlers just
# call X.parse_obj directly and any validation errors get turned into a proper
# error response automatically
def validate(
    request_body: Dict[str, Any]
) -> Tuple[Optional[ApplicationRequestBody], List[WarningsAndErrors]]:
    parsed = None
    errors = []

    try:
        parsed = ApplicationRequestBody.parse_obj(request_body)
    except ValidationError as e:
        errors = list(
            map(
                lambda x: WarningsAndErrors(attribute=".".join(x["loc"]), message=x["msg"]),
                e.errors(),
            )
        )

    return parsed, errors
