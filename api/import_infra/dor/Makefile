## Constants
API_FOLDER := ../..
DOR_IMPORT_LAMBDA_FOLDER := ../../massgov/pfml/dor/importer
MOCK_GENERATOR := massgov/pfml/dor/mock/generate.py
MOCK_OUTPUT_FOLDER := import_infra/dor/mock_output

## Helpers

clean:
	rm -rf .aws-sam +
	rm -f $(DOR_IMPORT_LAMBDA_FOLDER)/massgov.pfml.api-0.1.0-py3-none-any.whl +
	rm -rf dependencies/ +
	rm -f dependencies.zip +
	rm -f local-log.txt +
	rm -f response.json +

# build massgov.pfml.api package
build-api:
	cd $(API_FOLDER); poetry build

# place the massgov.pfml.api package as a DOR import dependncy
import-api-module:
	cp $(API_FOLDER)/dist/massgov.pfml.api-0.1.0-py3-none-any.whl $(DOR_IMPORT_LAMBDA_FOLDER)/massgov.pfml.api-0.1.0-py3-none-any.whl

deps:  ## Build binary dependencies
	mkdir -p ./dependencies
	docker run --rm -v "$(PWD)"/dependencies:/lambda/opt lambci/yumda:2 yum install -y gnupg
	(cd dependencies && zip -yr ../dependencies.zip .)

## Import Lambda

# build the DOR import lambda within a SAM container
build:
	sam build --template template.yaml --use-container

# invoke locally by passing environment variable file and test event
invoke-local:
	sam local invoke "ImportFunction" \
		--env-vars local.json \
		--log-file local-log.txt \
		--event test_event.json

# full build before local invoke
build-invoke-local: build-api import-api-module deps build invoke-local

# build and publish lambda function to AWS
#
upload-release: import-api-module deps build
	sam package \
		--s3-bucket massgov-pfml-api-lambda-builds \
		--s3-prefix dor-import \
		--use-json \
		--output-template-file dor-import-lambda-s3-package.json

# get the S3 key of the most recently packaged release
get-key:
	python3 get-lambda-build.py

# get the S3 key of the most recently packaged dependencies
get-deps-key:
	python3 get-lambda-dependencies.py

## Mock Generation

generate:
	cd $(API_FOLDER); $(MOCK_GENERATOR) --folder $(MOCK_OUTPUT_FOLDER)

generate-count:
	cd $(API_FOLDER); $(MOCK_GENERATOR) --folder $(MOCK_OUTPUT_FOLDER) --count $(EMP_COUNT)
