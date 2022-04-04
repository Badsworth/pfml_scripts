from enum import Enum
from typing import Dict, Sized, Union

from massgov.pfml.api.models.common import SearchEnvelope, SearchTermsT
from massgov.pfml.api.util.paginate.paginator import Page

LogTypes = Union[str, int, bool]


def search_request_log_info(
    request: SearchEnvelope[SearchTermsT], page: Page
) -> Dict[str, LogTypes]:
    return search_envelope_log_info(request) | pagination_log_info_from_request(request, page)


def search_envelope_log_info(
    request: SearchEnvelope[SearchTermsT],
) -> Dict[str, LogTypes]:
    USER_PROVIDED_TERMS = request.terms.__fields_set__

    log_info: Dict[str, LogTypes] = {
        # top level fields info
        "request_top_level_fields_provided": ",".join(request.__fields_set__),
        "request_top_level_fields_provided_length": len(request.__fields_set__),
        # order fields info
        "order_fields_provided": ",".join(request.order.__fields_set__),
        "order_fields_provided_length": len(request.order.__fields_set__),
        "order.by": request.order.by,
        "order.direction": request.order.direction.value,
        # paging fields info
        "paging_fields_provided": ",".join(request.paging.__fields_set__),
        "paging_fields_provided_length": len(request.paging.__fields_set__),
        "paging.offset": request.paging.offset,
        "paging.size": request.paging.size,
        # high-level terms fields info
        "terms_fields_provided": ",".join(USER_PROVIDED_TERMS),
        "terms_fields_provided_length": len(USER_PROVIDED_TERMS),
    }

    for key, value in request.terms.dict().items():
        log_info.update({f"terms.{key}_provided": (key in USER_PROVIDED_TERMS)})
        # This is primarily for cases where a term might accept multiple types,
        # e.g., a single string vs a list.
        #
        # This kind of field might more commonly be normalized to a single type
        # in the Terms model, which would make this less useful, but for the
        # cases where a term may want to support distinct types all the way
        # through, this could be useful.
        log_info.update({f"terms.{key}_type": str(type(value))})

        if isinstance(value, Sized):
            log_info.update({f"terms.{key}_length": len(value)})

        if isinstance(value, bool):
            log_info.update({f"terms.{key}_value": value})

        if isinstance(value, Enum):
            log_info.update({f"terms.{key}_value": value.value})
            log_info.update({f"terms.{key}_name": value.name})

    return log_info


def pagination_log_info_from_request(
    request: SearchEnvelope[SearchTermsT], page: Page
) -> Dict[str, LogTypes]:
    response_keys: Dict[str, LogTypes] = {
        "pagination.order_by": request.order.by,
        "pagination.order_direction": request.order.direction.value,
        "pagination.page_offset": request.paging.offset,
        "pagination.page_size": request.paging.size,
        "pagination.total_pages": page.total_pages,
        "pagination.total_records": page.total_records,
    }

    return response_keys
