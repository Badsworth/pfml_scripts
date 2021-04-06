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


class PydanticBaseSettings(pydantic.BaseSettings):
    class Config:
        env_file = env_file
