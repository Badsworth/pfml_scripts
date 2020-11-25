import xml.dom.minidom as minidom
from typing import Any, Callable, Dict, Optional


class Constants:
    COMPTROLLER_UNIT_CODE = "8770"
    COMPTROLLER_DEPT_CODE = "EOL"


def validate_input(
    key: str,
    doc_data: Dict[str, Any],
    required: bool,
    max_length: int,
    truncate: bool,
    func: Optional[Callable[[Any], str]] = None,
) -> None:
    # This will need to be adjusted to use getattr once doc_data is a db model
    value = doc_data.get(key)

    if required and not value:
        raise Exception(f"Value for {key} is required to generate document.")
    elif not required and not value:
        return None

    if func is not None:
        value_str = func(value)
    else:
        value_str = str(value)  # Everything else should be safe to convert to string

    if len(value_str) > max_length:
        if truncate:
            return value_str[:max_length]
        # Don't add the value itself, these can include SSNs and other PII
        raise Exception(f"Value for {key} is longer than allowed length of {max_length}.")

    # TODO - when switching this to use DB models, add the model ID to the errors
    return value_str


def add_attributes(element: minidom.Element, attributes: Dict[str, str]) -> None:
    for k, v in attributes.items():
        element.setAttribute(k, v)


def add_cdata_elements(
    parent: minidom.Element, document: minidom.Document, elements: Dict[str, Any]
) -> None:
    for key, val in elements.items():
        elem = document.createElement(key)
        add_attributes(elem, {"Attribute": "Y"})
        parent.appendChild(elem)

        if val is None:
            cdata = document.createCDATASection("null")
        else:
            # Anything in the CDATA tag is passed directly and markup ignored
            cdata = document.createCDATASection(str(val))
        elem.appendChild(cdata)
