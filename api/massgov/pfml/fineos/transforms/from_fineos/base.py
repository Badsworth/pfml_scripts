import abc
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

DEFAULT_ENUM_VALUE_UNSELECTED = "Please Select"
DEFAULT_ENUM_REPLACEMENT_VALUE = "Unknown"


class AbstractTransform(abc.ABC, metaclass=abc.ABCMeta):
    """ Base class that defines interface for transformations """

    @classmethod
    @abc.abstractmethod
    def from_fineos(cls, api_model: BaseModel) -> Any:
        """A method to transform a model into a FINEOS Model ."""
        pass


class TransformEformAttributes:

    PROP_MAP: Dict[str, Dict[str, str]] = {}

    @classmethod
    def sanitize_attribute(cls, item_value: Any) -> Optional[Any]:
        # Remove instances of "Please Select" - EMPLOYER-640
        return (
            DEFAULT_ENUM_REPLACEMENT_VALUE
            if item_value == DEFAULT_ENUM_VALUE_UNSELECTED
            else item_value
        )

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
                else:
                    transformed_value = attribute[attr_type]

                transformed[attr_number][transformed_name] = cls.sanitize_attribute(
                    transformed_value
                )

        # Sort to preserve FINEOS ordering
        transformed_sorted = sorted(transformed.items())

        return list(map(lambda item_tuple: item_tuple[1], transformed_sorted))
