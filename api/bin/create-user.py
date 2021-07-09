#!/usr/bin/env python3
import pprint
import sys

import massgov.pfml.db
import massgov.pfml.db.models.employees as employee_models
from massgov.pfml.db.models.factories import UserFactory

massgov.pfml.db.init(sync_lookups=True)

roles = []

# Use the strings passed in to get the Role (eg. user -> USER, fineos -> FINEOS)
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        roles.append(employee_models.Role.__dict__[arg.upper()])

user = UserFactory.create(roles=roles, consented_to_data_sharing=True)

pprint.pp({k: v for k, v in user.__dict__.items() if not k.startswith("_sa")})
