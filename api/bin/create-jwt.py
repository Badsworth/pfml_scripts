#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timedelta

from jose import jwt

jwks_path = sys.argv[1]
user_auth_id = sys.argv[2]

with open(jwks_path, "r") as fp:
    jwk = json.load(fp)["keys"][0]

claims = {"exp": datetime.now() + timedelta(days=1), "sub": user_auth_id}

print(jwt.encode(claims, jwk))
