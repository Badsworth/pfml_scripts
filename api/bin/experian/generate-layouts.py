#!/usr/bin/env python3
import re

import massgov.pfml.experian.address_validate_soap.caller as soap_caller


def mk_valid_python_id(string):
    return re.sub(r"\W+|^(?=\d)", "_", string).rstrip("_")


experian_caller = soap_caller.LazyZeepApiCaller().get()

layouts = experian_caller.DoGetLayouts(Country="USA")["body"]["Layout"]  # type: ignore

layout_props = [
    f'    {mk_valid_python_id(layout["Name"])} = "{layout["Name"]}"' for layout in layouts
]
layout_prop_lines = "\n".join(layout_props)

print(
    f"""from enum import Enum


class Layout(Enum):
{layout_prop_lines}"""
)
