from enum import Enum
from re import match
from typing import Optional

import pytest

from massgov.pfml.api.models.common import OrderData, SearchEnvelope
from massgov.pfml.api.util.logging.search_request import (
    pagination_log_info_from_request,
    search_envelope_log_info,
    search_request_log_info,
)
from massgov.pfml.api.util.paginate.paginator import Page
from massgov.pfml.util.pydantic import PydanticBaseModel


class ExampleEnum(Enum):
    FOO = "foo"


class EmptyTerms(PydanticBaseModel):
    pass


class ExampleSearchTerms(PydanticBaseModel):
    an_enum: ExampleEnum = ExampleEnum.FOO
    a_string: str = "bar"
    a_list: list[str] = []
    an_int: int = 42
    a_bool: bool = False
    an_optional: Optional[str] = None


DEFAULT_ORDER_AND_PAGING_ATTRS = {
    "order_fields:provided": "",
    "order_fields:provided:length": 0,
    "order.by": "created_at",
    "order.by:provided": False,
    "order.by:length": 10,
    "order.by:type": "<class 'str'>",
    "order.direction": "descending",
    "order.direction:provided": False,
    "order.direction:length": 10,
    "order.direction:type": "<enum 'OrderDirection'>",
    "order.direction:value": "descending",
    "order.direction:name": "desc",
    "paging_fields:provided": "",
    "paging_fields:provided:length": 0,
    "paging.offset": 1,
    "paging.offset:provided": False,
    "paging.offset:type": "<class 'int'>",
    "paging.size": 25,
    "paging.size:provided": False,
    "paging.size:type": "<class 'int'>",
}


def test_search_request_log_info(mocker):
    mock_page = mocker.Mock(spec=Page)
    type(mock_page).total_records = mocker.PropertyMock(return_value=3)
    type(mock_page).total_pages = mocker.PropertyMock(return_value=2)

    request = SearchEnvelope(terms=ExampleSearchTerms())

    log_info = search_request_log_info(request, mock_page)
    log_keys = log_info.keys()

    pagination_keys = list(filter(lambda k: match(r"^pagination\.", k), log_keys))
    terms_keys = list(filter(lambda k: match(r"^terms\.", k), log_keys))

    assert len(pagination_keys) > 0
    assert len(terms_keys) > 0


@pytest.mark.parametrize(
    "search_request,expected",
    [
        pytest.param(
            SearchEnvelope(terms=EmptyTerms()),
            {
                "request_top_level_fields:provided": "terms",
                "request_top_level_fields:provided:length": 1,
                "request_top_level.terms:provided": True,
                "request_top_level.terms:type": "<class 'tests.api.util.logging.test_search_request.EmptyTerms'>",
                "request_top_level.order:provided": False,
                "request_top_level.order:type": "<class 'massgov.pfml.api.models.common.OrderData'>",
                "request_top_level.paging:provided": False,
                "request_top_level.paging:type": "<class 'massgov.pfml.api.models.common.PagingData'>",
                "terms_fields:provided": "",
                "terms_fields:provided:length": 0,
            },
            id="no_provided_terms",
        ),
        pytest.param(
            SearchEnvelope(terms=EmptyTerms(), order=OrderData(by="foo")),
            {
                "request_top_level_fields:provided": "order,terms",
                "request_top_level_fields:provided:length": 2,
                "request_top_level.terms:provided": True,
                "request_top_level.terms:type": "<class 'tests.api.util.logging.test_search_request.EmptyTerms'>",
                "request_top_level.order:provided": True,
                "request_top_level.order:type": "<class 'massgov.pfml.api.models.common.OrderData'>",
                "request_top_level.paging:provided": False,
                "request_top_level.paging:type": "<class 'massgov.pfml.api.models.common.PagingData'>",
                "terms_fields:provided": "",
                "terms_fields:provided:length": 0,
                "order_fields:provided": "by",
                "order_fields:provided:length": 1,
                "order.by": "foo",
                "order.by:provided": True,
                "order.by:length": 3,
            },
            id="order_provided",
        ),
        pytest.param(
            SearchEnvelope(terms=ExampleSearchTerms(an_enum=ExampleEnum.FOO)),
            {
                "request_top_level_fields:provided": "terms",
                "request_top_level_fields:provided:length": 1,
                "request_top_level.terms:provided": True,
                "request_top_level.terms:type": "<class 'tests.api.util.logging.test_search_request.ExampleSearchTerms'>",
                "request_top_level.order:provided": False,
                "request_top_level.order:type": "<class 'massgov.pfml.api.models.common.OrderData'>",
                "request_top_level.paging:provided": False,
                "request_top_level.paging:type": "<class 'massgov.pfml.api.models.common.PagingData'>",
                "terms_fields:provided": "an_enum",
                "terms_fields:provided:length": 1,
                "terms.an_enum:provided": True,
                "terms.an_enum:type": "<enum 'ExampleEnum'>",
                "terms.an_enum:value": "foo",
                "terms.an_enum:name": "FOO",
                "terms.a_string:provided": False,
                "terms.a_string:type": "<class 'str'>",
                "terms.a_string:length": 3,
                "terms.a_list:provided": False,
                "terms.a_list:type": "<class 'list'>",
                "terms.a_list:length": 0,
                "terms.an_int:provided": False,
                "terms.an_int:type": "<class 'int'>",
                "terms.a_bool:provided": False,
                "terms.a_bool:type": "<class 'bool'>",
                "terms.a_bool:value": False,
                "terms.an_optional:provided": False,
                "terms.an_optional:type": "<class 'NoneType'>",
            },
            id="terms",
        ),
    ],
)
def test_search_envelope_log_info(search_request, expected):
    log_attrs = search_envelope_log_info(search_request)

    assert log_attrs == (DEFAULT_ORDER_AND_PAGING_ATTRS | expected)


def test_pagination_log_info_from_request(mocker):
    mock_page = mocker.Mock(spec=Page)
    type(mock_page).total_records = mocker.PropertyMock(return_value=3)
    type(mock_page).total_pages = mocker.PropertyMock(return_value=2)

    empty_request = SearchEnvelope(terms=EmptyTerms())

    assert pagination_log_info_from_request(empty_request, mock_page) == {
        "pagination.order_by": "created_at",
        "pagination.order_direction": "descending",
        "pagination.page_offset": 1,
        "pagination.page_size": 25,
        "pagination.total_pages": 2,
        "pagination.total_records": 3,
    }
