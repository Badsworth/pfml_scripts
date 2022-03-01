import os
from typing import TYPE_CHECKING, Any, Optional

from xmlschema import ElementData, XMLSchema, XMLSchemaConverter
from xmlschema.aliases import BaseXsdType

if TYPE_CHECKING:
    from xmlschema.validators import XsdElement


def fineos_wscomposer_schema(xsd_filename: str) -> XMLSchema:
    return XMLSchema(
        source=os.path.join(os.path.dirname(__file__), xsd_filename), converter=FINEOSConverter,
    )


class FINEOSConverter(XMLSchemaConverter):
    def element_decode(
        self,
        data: ElementData,
        xsd_element: "XsdElement",
        xsd_type: Optional[BaseXsdType] = None,
        level: int = 0,
    ) -> Any:
        decoded_data = super().element_decode(data, xsd_element, xsd_type, level)

        if isinstance(decoded_data, dict) and decoded_data.get("@xsi:nil") == "true":
            return None

        return decoded_data
