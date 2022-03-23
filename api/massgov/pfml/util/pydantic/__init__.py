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
    """Model that casts empty strings to None for Optional fields

    Fields that are not Optional/do not support None as a value will have the
    raw input (i.e., the empty string) passed along to be parsed by the field as
    usual.

    The fields will still be listed in `__fields_set__`.
    """

    @pydantic.validator("*", pre=True)
    def empty_str_to_none(cls, v, field):  # noqa: B902
        if field.allow_none and v == "":
            return None

        return v


class PydanticBaseModelRemoveEmptyStrFields(pydantic.BaseModel):
    """Model that removes empty fields from parsing

    Effectively the fields will be treated as though they were not provided in
    the first place.

    This means field default values will be used for Optional fields and
    required fields will error that the required field is missing.

    The removed fields will not be in `__fields_set__`.
    """

    @pydantic.root_validator(pre=True)
    def remove_empty(cls, values):  # noqa: B902
        for k in list(values):
            if values.get(k) == "":
                del values[k]

        return values


class PydanticBaseSettings(pydantic.BaseSettings):
    class Config:
        env_file = env_file
