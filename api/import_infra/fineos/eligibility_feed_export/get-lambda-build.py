import json

with open("fineos-eligibility-feed-export-lambda-s3-package.json") as f:
    data = json.load(f)

uri = data["Resources"]["EligibilityExportFunction"]["Properties"]["CodeUri"]
key_start_index = uri.rfind("/") + 1
s3_key = uri[key_start_index:]
print(s3_key)
