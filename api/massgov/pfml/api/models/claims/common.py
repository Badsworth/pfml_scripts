from datetime import date
from typing import List, Optional

import pydantic


class EmployerBenefit(pydantic.BaseModel):
    """ Defines an employer benefit """

    benefit_amount_dollars: Optional[float]
    benefit_amount_frequency: Optional[str]
    benefit_start_date: date
    benefit_end_date: date
    benefit_type: Optional[str]


class PreviousLeave(pydantic.BaseModel):
    """ Defines a prior leave """

    leave_start_date: date
    leave_end_date: date
    leave_type: Optional[str]


class EmployerClaimReview(pydantic.BaseModel):
    """ Defines the Employer info request / response format """

    comment: Optional[str]
    employer_benefits: List[EmployerBenefit]
    employer_notification_date: Optional[date]
    intermittent_leave_duration: Optional[str]
    previous_leaves: List[PreviousLeave]
    hours_worked: Optional[int]
