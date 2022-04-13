#!/usr/bin/env python3
import json
import sys

with open(sys.argv[1], "r") as f:
    parsed = json.loads(f.read())

schemas = parsed["components"]["schemas"]

for _schema_name, schema_desc in schemas.items():
    if "properties" in schema_desc:
        for _prop_name, prop_desc in schema_desc["properties"].items():
            if "format" in prop_desc:
                if prop_desc["format"] == "string":
                    prop_desc.pop("format", None)
                elif prop_desc["format"] == "money":
                    prop_desc["format"] = "decimal"
                    prop_desc.pop("maxLength", None)
                    prop_desc.pop("minLength", None)

            if "type" in prop_desc:
                # Seemingly when FINEOS uses `additionalProperties: { type:
                # object }` they don't usually mean the values will be objects,
                # but intend them to be any type.
                #
                # Since `additionalProperties: true` is the default setting and
                # by default does not constrain the type of the values, just
                # drop the declaration if it only says `{ type: object }`.
                if prop_desc["type"] == "object" and (
                    prop_desc.get("additionalProperties", None) == {"type": "object"}
                ):
                    prop_desc.pop("additionalProperties")

                if prop_desc["type"] == "string" and (prop_desc.get("maximum", None) is not None):
                    max_length = prop_desc.pop("maximum")
                    prop_desc["maxLength"] = max_length
    else:
        # Some entries have an "allOf" property with a reference as well as properties, e.g. `AUTaxCodeDetails`
        continue

print(json.dumps(parsed))
