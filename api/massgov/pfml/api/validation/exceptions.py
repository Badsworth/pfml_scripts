#
# Exceptions to be used to extract relevant connexion validation exception values
#

from dataclasses import dataclass
from typing import Any, List, Optional, Union

from werkzeug.exceptions import HTTPException


class PaymentRequired(HTTPException):
    code = 402
    description = "Payment required"


@dataclass
class ValidationErrorDetail:
    type: str
    message: str = ""
    rule: Optional[Any] = None
    field: Optional[str] = None


class ValidationException(Exception):
    __slots__ = ["errors", "message", "data"]

    def __init__(
        self, errors: List[ValidationErrorDetail], message: str, data: Union[dict, List[dict]]
    ):
        self.errors = errors
        self.message = message
        self.data = data
