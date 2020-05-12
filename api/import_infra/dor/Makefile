## Constants
API_FOLDER := ../..
DOR_IMPORT_LAMBDA_FOLDER := ../../massgov/pfml/data_integrations/dor/import
MOCK_GENERATOR := massgov/pfml/data_integrations/dor/mock/generate.py
MOCK_OUTPUT_FOLDER := import_infra/dor/mock_output

## Helpers

clean:
	rm -rf .aws-sam

# build massgov.pfml.api package
build-api:
	cd $(API_FOLDER); poetry build

# place the massgov.pfml.api package as a DOR import dependncy
import-api-module:
	cp $(API_FOLDER)/dist/massgov.pfml.api-0.1.0-py3-none-any.whl $(DOR_IMPORT_LAMBDA_FOLDER)/lambda/massgov.pfml.api-0.1.0-py3-none-any.whl

## Import Lambda

# build the DOR import lambda within a SAM container
build:
	sam build --template $(DOR_IMPORT_LAMBDA_FOLDER)/template.yaml --use-container

# invoke locally by passing environment variable file and test event

invoke-local:
	sam local invoke "ImportFunction" \
		--env-vars local.json \
		--log-file local-log.txt \
		--event test_event.json

build-invoke-local: build-api import-api-module build invoke-local

# build and publish lambda function to AWS
upload-release: import-api-module build
	sam package \
		--s3-bucket massgov-pfml-api-lambda-builds \
		--s3-prefix dor-import \
		--use-json \
		--output-template-file dor-import-lambda-s3-package.json

# get the S3 key of the most recently packaged release
get-key:
	python3 get-lambda-build.py

## Mock Generation

generate:
	cd $(API_FOLDER); $(MOCK_GENERATOR) --folder $(MOCK_OUTPUT_FOLDER)

generate-count:
	cd $(API_FOLDER); $(MOCK_GENERATOR) --folder $(MOCK_OUTPUT_FOLDER) --count $(EMP_COUNT)
