#!/usr/bin/env python3
# Generate database schema diagram

import codecs

import pydot
import sadisplay

from massgov.pfml.db.models import applications, employees, payments, verifications

schema_modules = [
    (applications, "applications"),
    (employees, "employees"),
    (payments, "payments"),
    (verifications, "verifications"),
]

for module, file_name in schema_modules:
    description = sadisplay.describe(
        [getattr(module, attr) for attr in dir(module)],
        show_methods=True,
        show_properties=True,
        show_indexes=True,
    )

    with codecs.open(f"{file_name}.dot", "w", encoding="utf8") as f:
        dot_file = f.write(sadisplay.dot(description))

    (graph,) = pydot.graph_from_dot_file(f"{file_name}.dot")
    graph.write_png(f"{file_name}.png")
