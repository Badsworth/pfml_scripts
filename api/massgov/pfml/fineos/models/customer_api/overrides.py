# just to get the namespace
from enum import Enum
from typing import List, Optional

from pydantic import Field

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


# Optional properties
class EmailAddress(base.EmailAddress):
    id: Optional[int] = Field(  # type: ignore
        None, description="The id of the contact method (e.g. phone / mobile / emailAddress) ",
    )


# Optional properties
class PhoneNumber(base.PhoneNumber):
    id: Optional[int] = Field(  # type: ignore
        None, description="The id of the contact method (e.g. phone / mobile / emailAddress) ",
    )


# uses the above overrides
class ParticipantContactDetails(base.ParticipantContactDetails):
    phoneNumbers: Optional[List[PhoneNumber]] = Field(  # type: ignore
        None, description="Return list of phone numbers"
    )
    emailAddresses: Optional[List[EmailAddress]] = Field(  # type: ignore
        None, description="Return list of email addresses"
    )


# uses the above overrides
class ContactDetails(base.ContactDetails):
    phoneNumbers: Optional[List[PhoneNumber]] = Field(  # type: ignore
        None, description="An array of objects which contain customer phone number details."
    )
    emailAddresses: Optional[List[EmailAddress]] = Field(  # type: ignore
        None, description="Email Address of the customer.", max_items=100, min_items=0
    )
