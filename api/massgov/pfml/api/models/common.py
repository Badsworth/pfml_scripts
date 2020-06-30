from enum import Enum
from typing import Optional

import massgov.pfml.db.models.applications as db_application_models
from massgov.pfml.util.pydantic import PydanticBaseModel


class WarningsAndErrors(PydanticBaseModel):
    message: Optional[str]
    attribute: Optional[str]


class LookupEnum(Enum):
    @classmethod
    def get_lookup_model(cls):
        return getattr(db_application_models, cls.__name__)

    @classmethod
    def get_lookup_value_column_name(cls):
        return "".join([cls.get_lookup_model().__tablename__.replace("lk_", "", 1), "_description"])

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if isinstance(val, str):
            return cls(val)

        if not isinstance(val, cls.get_lookup_model()):
            raise TypeError(f"is not an instance of class {cls.get_lookup_model()}")

        # TODO: maybe more checking that we can actually retrieve the value?

        return cls(getattr(val, cls.get_lookup_value_column_name()))
