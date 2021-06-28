#!/usr/bin/env python3
import json
import uuid

import rsa
from jose import jwk

(pubkey, privkey) = rsa.newkeys(1024)


pub_key = jwk.construct(pubkey.save_pkcs1(), "RS256")
raw_key1 = pub_key.to_dict()

pri_key = jwk.construct(privkey.save_pkcs1(), "RS256")
raw_key2 = pri_key.to_dict()

full_key1 = {**raw_key1, **{"kid": str(uuid.uuid4()), "use": "sig"}}
full_key2 = {**raw_key2, **{"kid": str(uuid.uuid4()), "use": "sig"}}


json.dump({"keys": [full_key1, full_key2]}, open("jwks.json", "w"), sort_keys=True, indent=4)
