# just to get the namespace
from datetime import date
from enum import Enum
from typing import List, Optional, TypeVar

from pydantic import BaseModel, Field

from . import spec as base


# deprecated `AdditionalInformation` renamed to ReflexiveQuestions
class AdditionalInformation(base.ReflexiveQuestions):
    pass


# deprecated `Attribute` renamed to ReflexiveQuestionType
class Attribute(base.ReflexiveQuestionType):
    pass


# custom Enum
class AbsencePeriodStatus(Enum):
    KNOWN = "known"
    ESTIMATED = "estimated"


class EmailAddressV20(BaseModel):
    """API payload for FINEOS 20.2"""

    classExtensionInformation: Optional[List[base.ExtensionAttribute]] = Field(
        None,
        description="An array of the extensionAttribute objects which contain email Address extension information.",
    )
    emailAddress: Optional[str] = Field(
        None, description="Customers email address.", max_length=120, min_length=0
    )
    id: Optional[int] = Field(
        None,
        description="The id of the contact method (e.g. phone / mobile / emailAddress) ",
        ge=0.0,
    )
    preferred: Optional[bool] = Field(
        None, description="Specify if it is the first person to try to contact when it is required."
    )


class EmailAddressV21(base.EmailAddress):
    """API payload for FINEOS 21.3

    The notable difference from the v20 version is the `emailAddressType` field
    is required.
    """

    pass


EmailAddressT = TypeVar("EmailAddressT", EmailAddressV21, EmailAddressV20)


# uses the above overrides
class ContactDetails(base.ContactDetails):
    emailAddresses: Optional[List[EmailAddressT]] = Field(  # type: ignore
        None, description="Email Address of the customer.", max_items=100, min_items=0
    )


class AbsenceCaseSummary(base.AbsenceCaseSummary):
    # The FINEOS API spec indicates these should be date-times (e.g.,
    # YYYY-MM-DDTHH:MM), but FINEOS only returns a date (YYYY-MM-DD)
    startDate: Optional[date] = Field(  # type: ignore
        None, description="ISO 8601 date time format", example="1999-12-31T23:59:59Z"
    )
    endDate: Optional[date] = Field(  # type: ignore
        None, description="ISO 8601 date time format", example="1999-12-31T23:59:59Z"
    )
    createdDate: Optional[date] = Field(  # type: ignore
        None, description="ISO 8601 date time format", example="1999-12-31T23:59:59Z"
    )


class NotificationAbsenceCaseSummary(base.NotificationAbsenceCaseSummary):
    # The FINEOS API spec indicates these should be date-times (e.g.,
    # YYYY-MM-DDTHH:MM), but FINEOS only returns a date (YYYY-MM-DD)
    startDate: Optional[date] = Field(  # type: ignore
        None, description="ISO 8601 date time format", example="1999-12-31T23:59:59Z"
    )
    endDate: Optional[date] = Field(  # type: ignore
        None, description="ISO 8601 date time format", example="1999-12-31T23:59:59Z"
    )
    createdDate: Optional[date] = Field(  # type: ignore
        None, description="ISO 8601 date time format", example="1999-12-31T23:59:59Z"
    )


class NotificationCaseSummary(base.NotificationCaseSummary):
    absences: Optional[List[NotificationAbsenceCaseSummary]] = Field(  # type: ignore
        None, description="The child absence cases under this notification case."
    )


# Support placeholder alternative name
# TODO (PORTAL-1671): update code to use correct FINEOS model name
class ChangeRequestReason(base.ReasonRequest):
    pass


# Support placeholder alternative name
# TODO (PORTAL-1671): update code to use correct FINEOS model name
class LeavePeriodChangeRequest(base.CreateLeavePeriodsChangeRequestCommand):
    pass
