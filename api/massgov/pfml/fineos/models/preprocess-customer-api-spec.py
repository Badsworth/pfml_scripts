#!/usr/bin/env python3
import sys

import oyaml as yaml

with open(sys.argv[1], "r") as f:
    parsed = yaml.safe_load(f)

schemas = parsed["components"]["schemas"]

for _schema_name, schema_desc in schemas.items():
    for _prop_name, prop_desc in schema_desc["properties"].items():
        if "format" in prop_desc:
            if prop_desc["format"] == "string":
                prop_desc.pop("format", None)

            elif prop_desc["format"] == "date-time":
                prop_desc["format"] = "date"

            elif prop_desc["format"] == "money":
                prop_desc["format"] = "decimal"
                prop_desc.pop("maxLength", None)
                prop_desc.pop("minLength", None)

print(yaml.dump(parsed))
