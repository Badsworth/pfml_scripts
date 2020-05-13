import json

with open("dor-import-lambda-s3-package.json") as f:
    data = json.load(f)

uri = data["Resources"]["DependenciesLayer"]["Properties"]["ContentUri"]
key_start_index = uri.rfind("/") + 1
s3_key = uri[key_start_index:]
print(s3_key)
