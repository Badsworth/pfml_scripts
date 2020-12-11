from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

import flask
from werkzeug.exceptions import BadRequest, Forbidden, HTTPException, NotFound, ServiceUnavailable

from massgov.pfml.api.validation.exceptions import ValidationErrorDetail


# == response data structures ==
@dataclass
class PagingMetaData:
    offset: int
    limit: int
    count: int
    total: int


@dataclass
class MetaData:
    resource: str
    method: str
    query: Optional[Dict[str, str]] = None
    paging: Optional[PagingMetaData] = None


# Partial list of types currently used manually
# This is not a comprehensive list of all IssueRules
class IssueRule(str, Enum):
    # At least one leave period should be present
    min_leave_periods = "min_leave_periods"
    # At least one reduced leave schedule day should have an amount of reduced time
    min_reduced_leave_minutes = "min_reduced_leave_minutes"
    # A rule only applied because a certain condition was met
    conditional = "conditional"
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


# Partial list of types currently used manually
# This is not a comprehensive list of all IssueTypes
class IssueType(str, Enum):
    # Data is present but shouldn't be
    conflicting = "conflicting"
    # Number or Date is greater than expected range
    maximum = "maximum"
    # Number or Date is less than the expected range
    minimum = "minimum"
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


@dataclass
class Issue:
    type: Union[IssueType, str, None] = None
    message: str = ""
    rule: Optional[Any] = None
    field: Optional[str] = None


@dataclass
class Response:
    status_code: int
    message: str = ""
    meta: Optional[MetaData] = None
    data: Union[None, Dict, List[Dict]] = None
    warnings: Optional[List[Issue]] = None
    errors: Optional[List[Issue]] = None

    def to_dict(self) -> Dict[str, Any]:
        return exclude_none(asdict(self))

    def to_api_response(self) -> flask.Response:
        # If other warnings are passed in, merge with warnings set from validators.py
        if flask.request.__dict__.get("warning_list", None) is not None:
            if self.warnings is None:
                self.warnings = flask.request.warning_list
            else:
                self.warnings = self.warnings + flask.request.warning_list

        if self.meta is None:
            self.meta = MetaData(resource=flask.request.path, method=flask.request.method)
        else:
            self.meta.resource = flask.request.path
            self.meta.method = flask.request.method

        return flask.make_response(flask.jsonify(self.to_dict()), self.status_code)


# == internal utilities ==


def exclude_none(obj):
    if not isinstance(obj, dict):
        return obj
    clean = {}
    for k, v in obj.items():
        if "data" == k:  # defer none exclusion of data payload to service layer
            clean[k] = v
        elif isinstance(v, dict):
            nested = exclude_none(v)
            if len(nested.keys()) > 0:
                clean[k] = nested
        elif isinstance(v, list):
            clean[k] = list(map(exclude_none, v))
        elif v is not None:
            clean[k] = v
    return clean


# == helper factory functions ==


def custom_issue(type: str, message: str, rule: str = "", field: str = "") -> Issue:
    return Issue(type=type, message=message, rule=rule, field=field)


def validation_issue(exception: ValidationErrorDetail) -> Issue:
    return Issue(
        type=exception.type, message=exception.message, rule=exception.rule, field=exception.field
    )


# == response utilties ==


def success_response(
    message: str,
    data: Union[None, Dict, List[Dict]] = None,
    warnings: Optional[List[Issue]] = None,
    status_code: int = 200,
) -> Response:
    return Response(status_code=status_code, message=message, data=data, warnings=warnings)


def error_response(
    status_code: Union[
        HTTPException, Type[BadRequest], Type[ServiceUnavailable], Type[NotFound], Type[Forbidden]
    ],
    message: str,
    errors: List[Issue],
    data: Union[None, Dict, List[Dict]] = None,
    warnings: Optional[List[Issue]] = None,
) -> Response:
    code = status_code.code if status_code.code is not None else 400
    return Response(status_code=code, message=message, errors=errors, data=data, warnings=warnings)
