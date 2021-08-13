#
# Exceptions to be used to extract relevant validation exception values
#

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union

from werkzeug.exceptions import HTTPException


class PaymentRequired(HTTPException):
    code = 402
    description = "Payment required"


class ContainsV1AndV2Eforms(HTTPException):
    status_code = HTTPException
    description = "Claim contains both V1 and V2 eforms."


# Partial list of types currently used manually
# This is not a comprehensive list of all IssueRules
class IssueRule(str, Enum):
    # At least one leave period should be present
    min_leave_periods = "min_leave_periods"
    # At least one reduced leave schedule day should have an amount of reduced time
    min_reduced_leave_minutes = "min_reduced_leave_minutes"
    # A rule only applied because a certain condition was met
    conditional = "conditional"
    # Caring leave applications can't start before July
    disallow_caring_leave_before_july = "disallow_caring_leave_before_july"
    # Intermittent leave must be on its own application
    disallow_hybrid_intermittent_leave = "disallow_hybrid_intermittent_leave"
    # Can't submit when earliest leave period is more than 60 days in the future
    disallow_submit_over_60_days_before_start_date = (
        "disallow_submit_over_60_days_before_start_date"
    )
    # Leave Period dates can't overlap
    disallow_overlapping_leave_periods = "disallow_overlapping_leave_periods"
    # Range between earliest leave period start date and the latest leave period end date can’t be 12 months or longer
    disallow_12mo_leave_period = "disallow_12mo_leave_period"
    # Range between continuous leave period start date and end date can’t be 12 months or longer
    disallow_12mo_continuous_leave_period = "disallow_12mo_continuous_leave_period"
    # Range between intermittent leave period start date and end date can’t be 12 months or longer
    disallow_12mo_intermittent_leave_period = "disallow_12mo_intermittent_leave_period"
    # Range between reduced leave period start date and end date can’t be 12 months or longer
    disallow_12mo_reduced_leave_period = "disallow_12mo_reduced_leave_period"
    # If a claimant is awaiting approval for other incomes they can't also submit other incomes
    disallow_has_other_incomes_when_awaiting_approval = (
        "disallow_has_other_incomes_when_awaiting_approval"
    )
    # Employer must be notified when employment status is Employed
    require_employer_notified = "require_employer_notified"
    # Partially masked field does not match existing value
    disallow_mismatched_masked_field = "disallow_mismatched_masked_field"
    # Fully masked field present when system contains no data
    disallow_fully_masked_no_existing = "disallow_fully_masked_no_existing"
    # Disallow suspicious attempts for potential fraud cases.
    # Intentionally vague to avoid leaking this is for fraud prevention
    disallow_attempts = "disallow_attempts"
    # Employee must have wages from the Employer
    require_employee = "require_employee"


# Partial list of types currently used manually
# This is not a comprehensive list of all IssueTypes
class IssueType(str, Enum):
    # Data is present but shouldn't be
    conflicting = "conflicting"
    # A matching record already exists
    duplicate = "duplicate"
    # A record already exists, preventing this data from being used again
    exists = "exists"
    # Number or Date is greater than expected range
    maximum = "maximum"
    # Number or Date is less than the expected range
    minimum = "minimum"
    # Data is insecure or compromised and cannot be used
    insecure = "insecure"
    # Generic issue indicating something about the data is invalid. This should
    # only be used when we're unable to provide anything more specific about the issue,
    # for instance when the issue could be a range of things that we're unable to specify.
    invalid = "invalid"
    # Date range is invalid, eg a start date occurs after an end date
    invalid_date_range = "invalid_date_range"
    # Data is missing
    required = "required"
    # Masked field is not allowed
    invalid_masked_field = "invalid_masked_field"
    # A claimant could not be created in FINEOS
    fineos_case_creation_issues = "fineos_case_creation_issues"
    # An unspecified error related to creating/completing the absence case in fineos
    fineos_case_error = "fineos_case_error"
    # If duration of intermittent leave is in hours, hours must be less than a day (24)
    intermittent_duration_hours_maximum = "intermittent_duration_hours_maximum"
    # Total days in an intermittent interval cannot exceed total days in the leave period
    # e.g. You cannot have a leave interval of every 6 months if the start and end
    # date of the leave period is only 2 months
    intermittent_interval_maximum = "intermittent_interval_maximum"
    # Total days absent cannot exceed total days in the interval
    # e.g. You can not request 5 days off 2 times in a week as that would
    # exceed the 7 days in a week
    days_absent_per_intermittent_interval_maximum = "days_absent_per_intermittent_interval_maximum"
    # Employer record must exist in the API
    require_employer = "require_employer"
    # Employer record must exist in the API and FINEOS
    require_contributing_employer = "require_contributing_employer"
    # Data failed a checksum test e.g. Routing number
    checksum = "checksum"
    # Employer can't be verified because there's nothing to verify against
    employer_requires_verification_data = "employer_requires_verification_data"


@dataclass
class ValidationErrorDetail:
    type: Union[IssueType, str]
    message: str = ""
    rule: Optional[Union[IssueRule, str]] = None
    field: Optional[str] = None


class ValidationException(Exception):
    __slots__ = ["errors", "message", "data"]

    def __init__(
        self,
        errors: List[ValidationErrorDetail],
        message: str = "Invalid request",
        data: Optional[Union[dict, List[dict]]] = None,
    ):
        self.errors = errors
        self.message = message
        self.data = data or {}
