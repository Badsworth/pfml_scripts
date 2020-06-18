#!/usr/bin/env python3
import json
import os
import uuid

from jose import jwk
from jose.constants import ALGORITHMS

secret = os.urandom(256 // 8)
key = jwk.construct(secret, ALGORITHMS.HS256)

raw_key = key.to_dict()
raw_key["k"] = raw_key["k"].decode("utf-8")

full_key = {**raw_key, **{"kid": str(uuid.uuid4()), "use": "sig"}}

print(json.dumps({"keys": [full_key]}, sort_keys=True, indent=4))
