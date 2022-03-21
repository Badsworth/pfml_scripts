from typing import Any, Dict

from pydantic import ValidationError

import massgov.pfml.util.collections.dict as dict_util


def validation_error_log_attrs(e: ValidationError) -> Dict[str, str]:
    errors_attrs = map(error_dict_log_attrs, e.errors())

    ret = {
        # this will generally be captured in the `exc_text` field if the
        # exception is logged with logger.exception(), but providing it here as
        # well just in case
        "validation_error_str": str(e),
    }
    for error_attrs in errors_attrs:
        # using `:` as separator for the log parts since `.` is used as the
        # separator for the construction of `field` in `error_dict_log_attrs`
        ret |= dict_util.flatten(error_attrs, key_prefix=error_attrs["field"], separator=":")

    return ret


def error_dict_log_attrs(error_dict: Dict[str, Any]) -> Dict[str, str]:
    return {
        "type": error_dict["type"],
        "msg": error_dict["msg"],
        "loc_raw": str(error_dict["loc"]),
        # custom fields
        "field": ".".join(str(loc) for loc in error_dict["loc"]),
        "first_loc": str(error_dict["loc"][0]),
        "last_loc": str(error_dict["loc"][-1]),
    }
