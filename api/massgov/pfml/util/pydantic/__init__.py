#
# Project base classes that extend Pydantic base classes.
#

import os.path

import pydantic

import massgov

env_file = os.path.join(
    os.path.dirname(os.path.dirname(massgov.__file__)),
    "config",
    "%s.env" % os.getenv("ENVIRONMENT", "local"),
)


class PydanticBaseModel(pydantic.BaseModel):
    class Config:
        orm_mode = True


class PydanticBaseModelEmptyStrIsNone(pydantic.BaseModel):
    @pydantic.validator("*", pre=True)
    def empty_str_to_none(cls, v):  # noqa: B902
        if v == "":
            return None
        return v


class PydanticBaseSettings(pydantic.BaseSettings):
    class Config:
        env_file = env_file
