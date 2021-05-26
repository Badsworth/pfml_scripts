#!/usr/bin/env python3
import json
import os
import uuid

from jose import jwk
from jose.constants import ALGORITHMS

secret = os.urandom(256 // 8)
key = jwk.construct(secret, ALGORITHMS.HS256)

raw_key = key.to_dict()

full_key = {**raw_key, **{"kid": str(uuid.uuid4()), "use": "sig"}}

json.dump({"keys": [full_key]}, open("jwks.json", "w"), sort_keys=True, indent=4)
