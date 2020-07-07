from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import flask
from werkzeug.exceptions import HTTPException


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


@dataclass
class Issue:
    type: str
    message: str = ""
    field: Optional[str] = None
    extra: Optional[dict] = None


@dataclass
class DataPayload:
    item: Optional[dict] = None
    items: Optional[List[dict]] = None


@dataclass
class Response:
    status_code: int
    message: str = ""
    meta: Optional[MetaData] = None
    data: Optional[DataPayload] = None
    warning: Optional[List[Issue]] = None
    error: Optional[List[Issue]] = None

    # ignore None values on nested objects other than data
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}

    def to_api_response(self) -> flask.Response:
        if self.meta is None:
            self.meta = MetaData(resource=flask.request.path, method=flask.request.method)
        else:
            self.meta.resource = flask.request.path
            self.meta.method = flask.request.method

        return flask.make_response(flask.jsonify(self.to_dict()), self.status_code)


# == issue types ==
@dataclass
class KnownIssue:
    type: str
    message: str
    extra_properties: Optional[List[str]] = None


class WarningIssue(Enum):
    MISSING_FIELD = KnownIssue("required", "Missing Field")


class ErrorIssue(Enum):
    MISSING_FIELD = KnownIssue("required", "Missing Field")
    MULTIPLE_OF = KnownIssue("multipleOf", "Value must be multiple of an integer", ["multiple_of"])


# == helper factory functions ==


def custom_issue(type, message) -> Issue:
    return Issue(type=type, message=message)


def field_issue(
    issueType: Union[WarningIssue, ErrorIssue], field_name: str, extra: Optional[dict] = None
) -> Issue:

    issue: KnownIssue = issueType.value

    if issue.extra_properties:
        # validate there is an extra field
        if extra is None:
            raise ValueError(
                "Expected extra object with properties: {}".format(issue.extra_properties)
            )

        # validate the fields match
        issue.extra_properties.sort()
        keys = list(extra.keys())
        keys.sort()
        if keys != issue.extra_properties:
            raise ValueError(
                "Extra object properties do not match - expected: {}, got: {}".format(
                    issue.extra_properties, keys
                )
            )

    return Issue(type=issue.type, message=issue.message, field=field_name, extra=extra)


def single_data_payload(object: dict) -> DataPayload:
    return DataPayload(item=object)


def multiple_data_payload(list: List[dict]) -> DataPayload:
    return DataPayload(items=list)


# == response utilties ==


def success_response(
    message: str, data: DataPayload = None, warning: Optional[List[Issue]] = None,
):
    # meta = MetaData(resource=resource, method=method)
    # meta=None
    return Response(status_code=200, message=message, data=data, warning=warning)


def error_response(
    status_code: HTTPException,
    message: str,
    error: List[Issue],
    data: Optional[DataPayload] = None,
    warning: Optional[List[Issue]] = None,
):
    return Response(
        status_code=status_code.code, message=message, error=error, data=data, warning=warning
    )
