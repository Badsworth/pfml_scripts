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
    else:
        # Some entries have an "allOf" property with a reference as well as properties, e.g. `AUTaxCodeDetails`
        continue

print(json.dumps(parsed))
