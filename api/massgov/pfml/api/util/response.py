from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Type, Union

import flask
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    Forbidden,
    HTTPException,
    NotFound,
    ServiceUnavailable,
)

from massgov.pfml.api.validation.exceptions import PaymentRequired, ValidationErrorDetail
from massgov.pfml.util.paginate.paginator import Page, PaginationAPIContext
from massgov.pfml.util.pydantic import PydanticBaseModel


# == response data structures ==
@dataclass
class PagingMetaData:
    page_offset: int
    page_size: int
    total_records: int
    total_pages: int
    order_by: str
    order_direction: str


@dataclass
class MetaData:
    resource: str
    method: str
    query: Optional[Dict[str, str]] = None
    paging: Optional[PagingMetaData] = None


@dataclass
class Response:
    status_code: int
    message: str = ""
    meta: Optional[MetaData] = None
    data: Union[None, Dict, List[Dict]] = None
    warnings: Optional[List[ValidationErrorDetail]] = None
    errors: Optional[List[ValidationErrorDetail]] = None

    def to_dict(self) -> Dict[str, Any]:
        return exclude_none(asdict(self))

    def to_api_response(self) -> flask.Response:
        # If other warnings are passed in, merge with warnings set from validators.py
        request_warning_list = flask.request.__dict__.get("warning_list", None)
        if request_warning_list is not None:
            if self.warnings is None:
                self.warnings = request_warning_list
            else:
                self.warnings = self.warnings + request_warning_list

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


# == response utilities ==
def success_response(
    message: str,
    data: Union[None, Dict, List[Dict]] = None,
    warnings: Optional[List[ValidationErrorDetail]] = None,
    status_code: int = 200,
) -> Response:
    return Response(status_code=status_code, message=message, data=data, warnings=warnings)


def paginated_success_response(
    message: str,
    context: PaginationAPIContext,
    page: Page,
    model: Type[PydanticBaseModel],
    warnings: Optional[List[ValidationErrorDetail]] = None,
    status_code: int = 200,
) -> Response:
    paging_meta = PagingMetaData(
        total_records=page.total_records,
        total_pages=page.total_pages,
        page_offset=context.page_offset,
        page_size=context.page_size,
        order_by=context.order_by,
        order_direction=context.order_direction,
    )

    # resource and method values are injected in Metadata.to_api_response function
    meta = MetaData(paging=paging_meta, method="", resource="")
    data = [model.from_orm(value).dict() for value in page.values]  # type: ignore
    # Skip type checking on this line because of a pydantic-mypy bug:
    # https://github.com/samuelcolvin/pydantic/issues/2819

    return Response(
        status_code=status_code, message=message, data=data, warnings=warnings, meta=meta
    )


def error_response(
    status_code: Union[
        HTTPException,
        Type[HTTPException],
        Type[BadRequest],
        Type[PaymentRequired],
        Type[Conflict],
        Type[ServiceUnavailable],
        Type[NotFound],
        Type[Forbidden],
    ],
    message: str,
    errors: List[ValidationErrorDetail],
    data: Union[None, Dict, List[Dict]] = None,
    warnings: Optional[List[ValidationErrorDetail]] = None,
) -> Response:
    code = status_code.code if status_code.code is not None else 400
    return Response(status_code=code, message=message, errors=errors, data=data, warnings=warnings)
