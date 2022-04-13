import math
from typing import Any, List, Union

import flask
from sqlalchemy import func
from sqlalchemy.orm import Query
from werkzeug.exceptions import BadRequest

from massgov.pfml.api.models.common import OrderData, OrderDirection, PagingData, SearchEnvelope
from massgov.pfml.db.models.base import Base

DEFAULT_PAGE_OFFSET = 1
DEFAULT_PAGE_SIZE = 25


class PaginationAPIContext:
    def __init__(self, entity: Any, request: Union[flask.Request, SearchEnvelope]):
        pagination_params = make_pagination_params(request)

        self.page_size = pagination_params.paging.size
        self.page_offset = pagination_params.paging.offset
        self.order_by = pagination_params.order.by
        self.order_direction = pagination_params.order.direction.value

        valid_order_keys = entity.__dict__.keys() - set(Base.__dict__.keys()).union(
            {"__tablename__"}
        )

        if self.order_by not in valid_order_keys:
            raise BadRequest(f"Unsupported order by '{self.order_by}'")

        self.order_key = getattr(entity, self.order_by)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class Page:
    def __init__(self, values: List[Any], paginator: "Paginator", offset: int):
        self.values = values
        self.paginator = paginator
        self.offset = offset

    @property
    def size(self) -> int:
        return self.paginator.page_size

    @property
    def total_records(self) -> int:
        return self.paginator.total_records

    @property
    def total_pages(self) -> int:
        return self.paginator.total_pages


class Paginator:
    def __init__(self, query_set: Query, page_size: int = DEFAULT_PAGE_SIZE, page_offset: int = 1):
        self.query_set = query_set

        if page_size <= 0:
            page_size = DEFAULT_PAGE_SIZE  # set default page_size value to prevent divide by zero
        self.page_size = page_size

        self._total_records = -1

        if not page_offset or page_offset < 1:
            page_offset = DEFAULT_PAGE_SIZE
        self.page_offset = page_offset

    def __iter__(self):
        return self

    def __next__(self):
        page = self.page_at(self.page_offset)
        if len(page.values) == 0:
            raise StopIteration

        self.page_offset += 1
        return page

    def page_at(self, page_offset: int) -> Page:
        if page_offset < 1 or page_offset > self.total_pages:
            page_values = []
        else:
            offset = self.page_size * (page_offset - 1)
            page_values = self.query_set.offset(offset).limit(self.page_size).all()

        return Page(page_values, self, page_offset)

    @property
    def total_records(self) -> int:
        if self._total_records >= 0:
            return self._total_records

        total_records_query = self.query_set.order_by(None).statement.with_only_columns(
            [func.count()]
        )
        self._total_records = self.query_set.session.execute(total_records_query).scalar()
        return self._total_records

    @property
    def total_pages(self) -> int:
        return int(math.ceil(self.total_records / self.page_size))


def page_for_api_context(context: PaginationAPIContext, query: Query) -> Page:
    paginator = Paginator(query, page_size=context.page_size)
    return paginator.page_at(page_offset=context.page_offset)


def make_pagination_params(request: Union[flask.Request, SearchEnvelope]) -> SearchEnvelope:
    if isinstance(request, SearchEnvelope):
        return request

    page_data = {}

    if page_size := request.args.get("page_size", default=None, type=int):
        page_data["size"] = page_size

    if page_offset := request.args.get("page_offset", default=None, type=int):
        page_data["offset"] = page_offset

    order_data = {}

    if order_by := request.args.get("order_by", default=None, type=str):
        order_data["by"] = order_by

    if order_direction := request.args.get("order_direction", default=None, type=str):
        order_data["direction"] = OrderDirection(order_direction)

    return SearchEnvelope[None](  # type: ignore
        terms=None, order=OrderData(**order_data), paging=PagingData(**page_data)
    )
