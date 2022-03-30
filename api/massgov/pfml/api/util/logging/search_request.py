from typing import Any, Dict

from massgov.pfml.api.models.common import SearchEnvelope, SearchTermsT
from massgov.pfml.api.util.paginate.paginator import Page


def search_request_log_info(request: SearchEnvelope[SearchTermsT], page: Page) -> Dict[str, Any]:
    return search_envelope_log_info(request) | pagination_log_info_from_request(request, page)


def search_envelope_log_info(request: SearchEnvelope[SearchTermsT]) -> Dict[str, Any]:
    USER_PROVIDED_TERMS = request.terms.__fields_set__

    log_info = {
        "order.by": request.order.by,
        "order.direction": request.order.direction.value,
        "paging.offset": request.paging.offset,
        "paging.size": request.paging.size,
    }

    for key, value in request.terms.dict().items():
        if isinstance(value, str):
            log_info.update({f"terms.{key}_length": len(value)})
        log_info.update({f"terms.{key}_provided": (key in USER_PROVIDED_TERMS)})

    return log_info


def pagination_log_info_from_request(
    request: SearchEnvelope[SearchTermsT], page: Page
) -> Dict[str, Any]:
    response_keys = {
        "pagination.order_by": request.order.by,
        "pagination.order_direction": request.order.direction.value,
        "pagination.page_offset": request.paging.offset,
        "pagination.page_size": request.paging.size,
        "pagination.total_pages": page.total_pages,
        "pagination.total_records": page.total_records,
    }

    return response_keys
