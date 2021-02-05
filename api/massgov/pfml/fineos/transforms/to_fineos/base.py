import abc
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from massgov.pfml.fineos.models.group_client_api import EFormAttribute, ModelEnum


# TODO use EForm from group_client_api model here
class EFormBody(BaseModel):
    eformType: str = Field(
        None, description="Name of the EForm document type", min_length=0, max_length=200
    )
    eformId: Optional[int]
    eformAttributes: List[EFormAttribute] = Field(None, description="An array of EForm attributes.")


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

    ADDITIONAL_OBJECT: EFormAttribute

    @classmethod
    def to_attributes(cls, target: Any, suffix: Optional[str] = "") -> List[EFormAttribute]:
        transformed = []
        """For examples of ATTRIBUTE_MAP check fineos/transforms/to_fineos/eforms/employer.py
        keys come from front end, values are what fineos expects
        """
        for key in cls.ATTRIBUTE_MAP.keys():
            attribute_name = f"{cls.ATTRIBUTE_MAP[key]['name']}{suffix}"
            attribute_type = cls.ATTRIBUTE_MAP[key]["type"]
            attribute = EFormAttribute(name=attribute_name)
            attribute_value = getattr(target, key)
            if attribute_type == "enumValue":
                # enumValue types need to be coerced into a ModelEnum instance
                domain_name = cls.ATTRIBUTE_MAP[key]["domainName"]
                instance_value = attribute_value
                attribute_value = ModelEnum(domainName=domain_name, instanceValue=instance_value)
            elif isinstance(attribute_value, date):
                attribute_value = attribute_value.strftime("%Y-%m-%d")
            elif isinstance(attribute_value, Decimal):
                """Decimals get turned into float because
                fineos doesn't accept decimals
                """
                attribute_value = float(attribute_value)
            setattr(attribute, attribute_type, attribute_value)
            transformed.append(attribute)

        """Fineos will only display additional objects after we've selected
        yes to an additional objects selection, ex: 'Will the employee receive any other wage replacement?'
        if there's a suffix that means there's additional objects
        this will ensure we've selected yes for the additional object
        """
        if suffix:
            attribute = cls.ADDITIONAL_OBJECT
            attribute_name = f"{attribute.name}{suffix}"
            attribute_value = attribute.enumValue
            transformed.append(EFormAttribute(name=attribute_name, enumValue=attribute_value))
        return transformed

    @classmethod
    def list_to_attributes(
        cls, targets: List[Any], always_add_suffix: Optional[bool] = False
    ) -> List[EFormAttribute]:
        """Convert a list of objects to EFormAttributes
        always_add_suffix -- Optional boolean. If True then a suffix will always be added. If False a
        suffix will only be added for entries after targets[0]. Some eforms require an initial suffix and
        others require no initial suffix.
        """
        transformed = []
        for i, target in enumerate(targets):
            suffix = ""
            if i != 0 or always_add_suffix:
                suffix = str(i + 1)
            transformed.extend(cls.to_attributes(target=target, suffix=suffix))
        return transformed
