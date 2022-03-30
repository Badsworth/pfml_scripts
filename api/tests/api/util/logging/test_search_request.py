from enum import Enum
from re import match

import pytest

from massgov.pfml.api.models.common import SearchEnvelope
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


DEFAULT_ORDER_AND_PAGING_ATTRS = {
    "order.by": "created_at",
    "order.direction": "descending",
    "paging.offset": 1,
    "paging.size": 25,
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
        pytest.param(SearchEnvelope(terms=EmptyTerms()), {}, id="no_provided_terms"),
        pytest.param(
            SearchEnvelope(terms=ExampleSearchTerms(an_enum=ExampleEnum.FOO)),
            {
                "terms.an_enum_provided": True,
                "terms.an_enum_type": "<enum 'ExampleEnum'>",
                "terms.an_enum_value": "foo",
                "terms.an_enum_name": "FOO",
                "terms.a_string_provided": False,
                "terms.a_string_type": "<class 'str'>",
                "terms.a_string_length": 3,
                "terms.a_list_provided": False,
                "terms.a_list_type": "<class 'list'>",
                "terms.a_list_length": 0,
                "terms.an_int_provided": False,
                "terms.an_int_type": "<class 'int'>",
                "terms.a_bool_provided": False,
                "terms.a_bool_type": "<class 'bool'>",
                "terms.a_bool_value": False,
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
