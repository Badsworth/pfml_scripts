import abc
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# This should be replaced with the groupclient api EFormAttribute
# TODO: https://lwd.atlassian.net/browse/EMPLOYER-425
from massgov.pfml.fineos.models.customer_api import EFormAttribute


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
            setattr(attribute, attribute_type, getattr(target, key))
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
