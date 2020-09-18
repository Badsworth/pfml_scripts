from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Type, Union

import flask
from werkzeug.exceptions import BadRequest, HTTPException, NotFound, ServiceUnavailable

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


@dataclass
class Issue:
    type: str
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
    clean = {}
    for k, v in obj.items():
        if "data" == k:  # defer none exclusion of data payload to service layer
            clean[k] = v
        elif isinstance(v, dict):
            nested = exclude_none(v)
            if len(nested.keys()) > 0:
                clean[k] = nested
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
    status_code: Union[HTTPException, Type[BadRequest], Type[ServiceUnavailable], Type[NotFound]],
    message: str,
    errors: List[Issue],
    data: Union[None, Dict, List[Dict]] = None,
    warnings: Optional[List[Issue]] = None,
) -> Response:
    code = status_code.code if status_code.code is not None else 400
    return Response(status_code=code, message=message, errors=errors, data=data, warnings=warnings)
