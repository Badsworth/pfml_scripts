#!/usr/bin/env python3
# Generate database schema diagram

import codecs
import sadisplay

import subprocess
from massgov.pfml.db.models import applications, employees, payments, verifications


schema_modules = [
    (applications, "applications"),
    (employees, "employees"),
    (payments, "payments"),
    (verifications, "verifications")
]

for module, file_name in schema_modules:
    description = sadisplay.describe(
    [getattr(module, attr) for attr in dir(module)],
    show_methods=True,
    show_properties=True,
    show_indexes=True,
    )

    with codecs.open(f'{file_name}.dot', 'w', encoding='utf8') as f:
        dot_file = f.write(sadisplay.dot(description))
        print(dot_file)
    
    # TODO:
    # use python library
    # https://graphviz.org/resources/#python
    process = subprocess.Popen(f"dot -Tpng {file_name}.dot > {file_name}.png", shell=True, stdout=subprocess.PIPE)
    process.wait()
