from enum import Enum
from typing import Dict, Sized, Union

from pydantic import BaseModel

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
    log_info: Dict[str, LogTypes] = {}

    # TODO: better name than "request_top_level"?
    log_info |= request_field_log_attrs(request, "request_top_level")

    for field_name, field_model in request:
        log_info |= request_field_log_attrs(field_model, field_name)

    # legacy fields and log size value (as ints aren't currently automatically
    # included in logs)
    log_info |= {
        "order.by": request.order.by,
        "order.direction": request.order.direction.value,
        "paging.offset": request.paging.offset,
        "paging.size": request.paging.size,
    }

    return log_info


# TODO: move to general API request logging util location?
def request_field_log_attrs(model: BaseModel, key: str) -> Dict[str, LogTypes]:
    provided_fields = model.__fields_set__

    log_info: Dict[str, LogTypes] = {
        f"{key}_fields_provided": ",".join(sorted(provided_fields)),
        f"{key}_fields_provided_length": len(provided_fields),
    }

    for sub_field_key, value in model:
        log_info.update({f"{key}.{sub_field_key}_provided": (sub_field_key in provided_fields)})

        # This is primarily for cases where a field might accept multiple types,
        # e.g., a single string vs a list.
        #
        # This kind of field might more commonly be normalized to a single type
        # in the model, which would make this less useful, but for the cases
        # where a field may want to support distinct types all the way through,
        # this could be useful.
        log_info.update({f"{key}.{sub_field_key}_type": str(type(value))})

        if isinstance(value, Sized):
            log_info.update({f"{key}.{sub_field_key}_length": len(value)})

        if isinstance(value, bool):
            log_info.update({f"{key}.{sub_field_key}_value": value})

        if isinstance(value, Enum):
            log_info.update({f"{key}.{sub_field_key}_value": value.value})
            log_info.update({f"{key}.{sub_field_key}_name": value.name})

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
