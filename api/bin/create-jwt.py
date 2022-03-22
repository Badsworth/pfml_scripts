#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timedelta

from jose import jwt
from jose.constants import ALGORITHMS

jwks_path = sys.argv[1]
user_auth_id = sys.argv[2]

with open(jwks_path, "r") as fp:
    jwk_private = json.load(fp)["keys"][1]

claims = {"exp": datetime.now() + timedelta(days=1), "sub": user_auth_id}

print(jwt.encode(claims, jwk_private, algorithm=ALGORITHMS.RS256))
