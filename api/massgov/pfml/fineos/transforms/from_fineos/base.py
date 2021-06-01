import abc
import re
from typing import Any, Dict, List, Optional, Type, Union, cast

from pydantic import BaseModel

from massgov.pfml.fineos.transforms.common import (
    DEFAULT_ENUM_REPLACEMENT_VALUE,
    FineosToApiEnumConverter,
)

DEFAULT_ENUM_VALUE_UNSELECTED = "Please Select"


class AbstractTransform(abc.ABC, metaclass=abc.ABCMeta):
    """ Base class that defines interface for transformations """

    @classmethod
    @abc.abstractmethod
    def from_fineos(cls, api_model: BaseModel) -> Any:
        """A method to transform a model into a FINEOS Model ."""
        pass


class TransformEformAttributes:

    PROP_MAP: Dict[str, Dict[str, Union[str, Type[FineosToApiEnumConverter]]]] = {}

    @classmethod
    def sanitize_attribute(cls, item_value: Any) -> Optional[Any]:
        # Removing white space
        if type(item_value) is str:
            item_value = item_value.strip()
        # Remove instances of "Please Select" - EMPLOYER-640
        if item_value == DEFAULT_ENUM_VALUE_UNSELECTED:
            item_value = DEFAULT_ENUM_REPLACEMENT_VALUE
        return item_value

    @classmethod
    def list_to_props(cls, attributes: List[Any]) -> List[Dict]:
        transformed: Dict[str, Dict] = {}
        attr_name: str = ""
        attr_number: str = ""
        regex = re.compile("([a-zA-Z]+)([0-9]*)")
        for attribute in attributes:
            matched = regex.match(attribute["name"])
            attr_name, attr_number = matched.groups() if matched else ("", "")
            if attr_name in cls.PROP_MAP:
                attr_type = cls.PROP_MAP[attr_name]["type"]
                transformed_name = cls.PROP_MAP[attr_name]["name"]
                attr_number = "0" if attr_number == "" else str(int(attr_number) - 1)

                if attr_number not in transformed:
                    transformed[attr_number] = {}

                if "embeddedProperty" in cls.PROP_MAP[attr_name]:
                    embeddedProperty = cls.PROP_MAP[attr_name]["embeddedProperty"]
                    transformed_value = attribute[attr_type][embeddedProperty]

                    if "enumOverride" in cls.PROP_MAP[attr_name]:
                        enum_override = cast(
                            FineosToApiEnumConverter, cls.PROP_MAP[attr_name]["enumOverride"]
                        )
                        transformed_value = enum_override.to_api_enum(transformed_value)
                else:
                    transformed_value = attribute[attr_type]

                transformed[attr_number][transformed_name] = cls.sanitize_attribute(
                    transformed_value
                )

        # Sort to preserve FINEOS ordering
        transformed_sorted = sorted(transformed.items())

        return list(map(lambda item_tuple: item_tuple[1], transformed_sorted))
