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
    # Leave periods and previous leaves cannot overlap
    disallow_overlapping_leave_period_with_previous_leave = (
        "disallow_overlapping_leave_period_with_previous_leave"
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


class IssueType(str, Enum):
    """
    Potential values for the `type` field of a `ValidationErrorDetail`.
    Reuse of existing types when applicable is encouraged.
    """

    # Data is present but shouldn't be
    conflicting = "conflicting"
    # Eform versions should be consistent
    contains_v1_and_v2_eforms = "contains_v1_and_v2_eforms"
    # A matching record already exists
    duplicate = "duplicate"
    # A record already exists, preventing this data from being used again
    exists = "exists"
    # Number or Date is greater than expected range
    maximum = "maximum"
    # Number or Date is less than the expected range
    minimum = "minimum"
    # Data didn't conform to expected pattern
    # OpenAPI validation errors may have this `type`, so using the same term to be consistent.
    pattern = "pattern"
    # Data is insecure or compromised and cannot be used
    insecure = "insecure"
    # Generic issue indicating the data is wrong in some way. For example, it doesn't match our records.
    incorrect = "incorrect"
    # Generic issue indicating something about the data is invalid. This should
    # only be used when we're unable to provide anything more specific about the issue,
    # for instance when the issue could be a range of things that we're unable to specify.
    invalid = "invalid"
    # TODO (EMPLOYER-1642): Use more generic error
    invalid_phone_number = "invalid_phone_number"
    # Date range is invalid, eg a start date occurs after an end date
    invalid_date_range = "invalid_date_range"
    # TODO (EMPLOYER-1642): Use more generic error
    invalid_year_range = "invalid_year_range"
    # TODO (EMPLOYER-1642): Use more generic error
    invalid_previous_leave_start_date = "invalid_previous_leave_start_date"
    # TODO (EMPLOYER-1642): Use more generic error
    invalid_age = "invalid_age"
    # TODO (EMPLOYER-1642): Use more generic error
    future_birth_date = "future_birth_date"
    # Data is missing
    required = "required"
    object_not_found = "object_not_found"
    # TODO (EMPLOYER-1642): Use more generic error
    outstanding_information_request_required = "outstanding_information_request_required"
    # Masked field is not allowed
    invalid_masked_field = "invalid_masked_field"
    # File mime type is not a supported mime type
    file_type = "file_type"
    # Extension portion is required in the filename, but missing.
    file_name_extension = "file_name_extension"
    # Parsed mime type is different than what file extension indicates
    file_type_mismatch = "file_type_mismatch"
    # Generic error indicating the error originated from Fineos (FINEOSClientBadResponse)
    fineos_client = "fineos_client"
    # A claimant could not be created in FINEOS
    fineos_case_creation_issues = "fineos_case_creation_issues"
    # An unspecified error related to creating/completing the absence case in fineos
    fineos_case_error = "fineos_case_error"
    # Indicates that the requested FINEOS claim has been withdrawn and can no longer be accessed
    fineos_claim_withdrawn = "fineos_claim_withdrawn"
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
    # Leave admin user attempting to view data for an organization they don't have access to
    unauthorized_leave_admin = "unauthorized_leave_admin"
    # Generic error indicating the error originated from our own business logic.
    # This was added when we began enforcing that `type` is an `IssueType`. Avoid using
    # this moving forward.
    # TODO (EMPLOYER-1643): Remove this once the errors the reference it no longer use IssueRule
    pfml = ""


@dataclass
class ValidationErrorDetail:
    type: IssueType
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
