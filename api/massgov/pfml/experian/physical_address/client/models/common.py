from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

import massgov.pfml.util.strings as string_util


class ResponseError(BaseModel):
    type: Optional[str] = Field(
        None,
        description="A link to documentation that provides more details about the error you've encountered.",
    )
    title: Optional[str] = Field(None, description="The title of the error.")
    detail: Optional[str] = Field(None, description="A description of the error.")
    instance: Optional[str] = Field(None, description="The endpoint that returned the error.")

    class Config:
        # the keys in the error response can be capitalized, even though the
        # spec says they are lowercase, so generate capitalized aliases and
        # allow populating by both the field and alias to achieve some measure
        # of case-insensitivity
        alias_generator = string_util.capitalize
        allow_population_by_field_name = True


class Confidence(str, Enum):
    VERIFIED_MATCH = "Verified match"
    MULTIPLE_MATCHES = "Multiple matches"
    NO_MATCHES = "No matches"
    INSUFFICIENT_SEARCH_TERMS = "Insufficient search terms"
