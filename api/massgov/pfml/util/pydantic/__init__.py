#
# Project base classes that extend Pydantic base classes.
#

import os.path
from typing import Any, Dict

import pydantic
from typing_extensions import Protocol

import massgov

env_file = os.path.join(
    os.path.dirname(os.path.dirname(massgov.__file__)),
    "config",
    "%s.env" % os.getenv("ENVIRONMENT", "local"),
)


# Protocol that wraps the pydantic.BaseModel from_orm classmethod. This is required
# because mypy cannot resolve classmethod based protocols - (https://github.com/python/mypy/issues/10081).
# Allows us to generically implement serialization of  massgov models in paginated API responses
# See also: massgov.pfml.api.util.reponse.paginated_success_response
class Serializer(Protocol):
    def serialize(self, obj: Any) -> Dict[str, Any]:
        ...


class PydanticBaseModel(pydantic.BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        min_anystr_length = 1

    def serialize(self, obj: Any) -> Dict[str, Any]:
        return self.from_orm(obj).dict()


class PydanticBaseSettings(pydantic.BaseSettings):
    class Config:
        env_file = env_file
