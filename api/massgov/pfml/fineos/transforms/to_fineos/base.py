import abc
from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from massgov.pfml.fineos.models.group_client_api import EFormAttribute


class AbstractTransform(abc.ABC, metaclass=abc.ABCMeta):
    """ Base class that defines interface for transformations """

    @classmethod
    @abc.abstractmethod
    def to_fineos(cls, api_model: BaseModel) -> Any:
        """A method to transform a model into a FINEOS Model ."""
        pass


class TransformEformAttributes:

    ATTRIBUTE_MAP: Dict[str, Dict[str, str]] = {}
    """ Example map:
    {
        'pythonModelKey': {'name': 'EformAttribute.name', 'type': 'EformAttribute.type'}
    }
    """

    @classmethod
    def to_attributes(cls, target: Any, suffix: Optional[str] = "") -> List[EFormAttribute]:
        transformed = []
        for key in cls.ATTRIBUTE_MAP.keys():
            attribute_name = f"{cls.ATTRIBUTE_MAP[key]['name']}{suffix}"
            attribute_type = cls.ATTRIBUTE_MAP[key]["type"]
            attribute = EFormAttribute(name=attribute_name)
            attribute_value = getattr(target, key)
            if isinstance(attribute_value, date):
                attribute_value = attribute_value.strftime("%Y-%m-%d")
            setattr(attribute, attribute_type, attribute_value)
            transformed.append(attribute)
        return transformed

    @classmethod
    def list_to_attributes(cls, targets: List[Any]) -> List[EFormAttribute]:
        transformed = []
        for i, target in enumerate(targets):
            suffix = ""
            if i != 0:
                suffix = str(i + 1)
            transformed.extend(cls.to_attributes(target=target, suffix=suffix))
        return transformed
