from datetime import date
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from massgov.pfml.fineos.models.group_client_api import EFormAttribute, ModelEnum


class EFormBody:
    def __init__(self, eformType, eformAttributes):
        self.eformType: str = eformType
        self.eformAttributes: List[dict] = eformAttributes

    def get_attribute(self, name: str) -> Optional[dict]:
        return next((a for a in self.eformAttributes if a["name"] == name), None)


class EFormAttributeBuilder:
    """Base class for eForm attribute builders. Subclasses can define mappings for converting
    arbitrary objects into EFormAttributes, including any logic required for generating suffixes
    and adding static EFormAttribute values to every entry.
    """

    ATTRIBUTE_MAP: Dict[str, Dict[str, Any]] = {}
    """ Example map:
    {
        'pythonModelKey': {'name': 'EFormAttribute.name', 'type': 'EFormAttribute.type'}
    }
    """

    def __init__(self, target):
        self.target = target

    def get_suffix(self, definition: dict, count: int, suffix: str) -> str:
        suffix_override = definition.get("suffixOverride")
        return suffix_override(count) if suffix_override else suffix

    def to_attribute(self, value: Any, definition: dict, count: int, suffix: str) -> EFormAttribute:
        attribute_suffix = self.get_suffix(definition, count, suffix)
        attribute_name = f"{definition['name']}{attribute_suffix}"
        attribute_type = definition["type"]

        if attribute_type == "enumValue" and value is not None:
            # enumValue types need to be coerced into a ModelEnum instance
            domain_name = definition["domainName"]

            enum_override = definition.get("enumOverride")
            if enum_override:
                value = enum_override[value.name]

            value = ModelEnum(domainName=domain_name, instanceValue=value)

        attribute = EFormAttribute(name=attribute_name)
        setattr(attribute, attribute_type, value)
        return attribute

    def to_attributes(self, count: int, suffix: str) -> List[EFormAttribute]:
        attributes = []
        """For examples of ATTRIBUTE_MAP check fineos/transforms/to_fineos/eforms/employer.py
        keys come from front end, values are what fineos expects
        """
        for key, definition in self.ATTRIBUTE_MAP.items():
            value = getattr(self.target, key)
            attribute = self.to_attribute(value, definition, count, suffix)
            attributes.append(attribute)

        return attributes


class EFormBuilder:
    """Base class for eForm builder classes. Subclasses define logic for combining various pieces of data into
    a EFormBody for sending to FINEOS.
    """

    @classmethod
    def to_eform_attributes(
        cls, targets: Iterable[EFormAttributeBuilder], always_add_suffix: Optional[bool] = False
    ) -> List[EFormAttribute]:
        """Convert a list of EFormAttributeBuilders into EFormAttributes and apply suffixes to the names
        as appropriate so they can be used to create an eform.
        always_add_suffix -- Optional boolean. If True then a suffix will always be added. If False a
        suffix will only be added for entries after targets[0]. Some eforms require an initial suffix and
        others require no initial suffix.
        """
        attributes = []
        targets = list(iter(targets))
        for i, target in enumerate(targets):
            suffix = ""
            if i != 0 or always_add_suffix:
                suffix = str(i + 1)
            attributes.extend(target.to_attributes(i, suffix))
        return attributes

    @classmethod
    def serialize_eform_attributes(cls, attributes: List[EFormAttribute]) -> List[Dict[str, Any]]:
        """Convert EFormAttributes to a list of dictionaries which are ready to be serialized to JSON"""
        serialized = []

        for eformAttribute in attributes:
            cleanedEformAttribute: Dict[str, Any] = {}
            for key, value in dict(eformAttribute).items():
                if value is not None and isinstance(value, ModelEnum):
                    cleanedEformAttribute[key] = dict(value)
                elif isinstance(value, date):
                    # format dates for fineos
                    cleanedEformAttribute[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    """Decimals get turned into float because
                    fineos doesn't accept decimals
                    """
                    cleanedEformAttribute[key] = float(value)
                elif value is not None:
                    cleanedEformAttribute[key] = value
            if len(cleanedEformAttribute) > 1:
                serialized.append(cleanedEformAttribute)

        return serialized

    @classmethod
    def to_serialized_attributes(
        cls, targets: Iterable[EFormAttributeBuilder], always_add_suffix: Optional[bool] = False
    ) -> List[dict]:
        """Convert a list of EFormAttributeBuilders into a dictionary of attributes ready to be serialized to a
        JSON payload.
        """
        attributes = cls.to_eform_attributes(targets, always_add_suffix)
        return cls.serialize_eform_attributes(attributes)
