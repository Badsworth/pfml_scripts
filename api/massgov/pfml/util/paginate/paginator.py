import math
from enum import Enum
from typing import Any, List

import flask
from sqlalchemy import func
from sqlalchemy.orm import Query
from werkzeug.exceptions import BadRequest

DEFAULT_PAGE_OFFSET = 1
DEFAULT_PAGE_SIZE = 25


class OrderDirection(str, Enum):
    asc = "ascending"
    desc = "descending"


class PaginationAPIContext:
    def __init__(
        self, entity: Any, request: flask.Request,
    ):
        page_size = request.args.get("page_size", default=DEFAULT_PAGE_SIZE, type=int)
        page_offset = request.args.get("page_offset", default=DEFAULT_PAGE_OFFSET, type=int)
        order_by = request.args.get("order_by", default="created_at", type=str).strip().lower()
        order_direction = request.args.get(
            "order_direction", default=OrderDirection.desc.value, type=str
        )

        order_key = getattr(entity, order_by, None)
        if order_key is None:
            raise BadRequest(f"Unsupported order_key '{order_key}'")

        if order_direction == OrderDirection.asc.value:
            order_key = order_key.asc()
        else:
            order_key = order_key.desc()

        self.page_size = page_size
        self.page_offset = page_offset
        self.order_by = order_by
        self.order_direction = order_direction
        self.order_key = order_key

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
    def __init__(
        self, query_set: Query, page_size: int = DEFAULT_PAGE_SIZE, page_offset: int = 1,
    ):
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
