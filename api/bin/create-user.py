#!/usr/bin/env python3
import pprint

from massgov.pfml.db.models.factories import UserFactory

user = UserFactory.create()

pprint.pp({k: v for k, v in user.__dict__.items() if not k.startswith("_sa")})
