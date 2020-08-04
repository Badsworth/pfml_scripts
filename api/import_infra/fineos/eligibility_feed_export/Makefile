## Constants
API_FOLDER := ../../..
FINEOS_ELIGIBILITY_FEED_EXPORT_LAMBDA_FOLDER := ../../../massgov/pfml/fineos/eligibility_feed_export

## Helpers

clean:
	rm -rf .aws-sam +
	rm -f $(FINEOS_ELIGIBILITY_FEED_EXPORT_LAMBDA_FOLDER)/massgov.pfml.api-0.1.0-py3-none-any.whl +
	rm -rf dependencies/ +
	rm -f dependencies.zip +
	rm -f local-log.txt +
	rm -f response.json +

# build massgov.pfml.api package
build-api:
	cd $(API_FOLDER); poetry build

# place the massgov.pfml.api package as a dependncy
import-api-module:
	cp $(API_FOLDER)/dist/massgov.pfml.api-0.1.0-py3-none-any.whl $(FINEOS_ELIGIBILITY_FEED_EXPORT_LAMBDA_FOLDER)/massgov.pfml.api-0.1.0-py3-none-any.whl

deps:  ## Build binary dependencies
	mkdir -p ./dependencies
	docker run --rm -v "$(PWD)"/dependencies:/lambda/opt lambci/yumda:2 yum install -y gnupg
	(cd dependencies && zip -yr ../dependencies.zip .)

## Import Lambda

# build the export lambda within a SAM container
build:
	sam build --template template.yaml --use-container

# invoke locally by passing environment variable file and test event
invoke-local:
	sam local invoke "EligibilityExportFunction" \
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
		--s3-prefix fineos-eligibility-feed-export \
		--use-json \
		--output-template-file fineos-eligibility-feed-export-lambda-s3-package.json

# get the S3 key of the most recently packaged release
get-key:
	python3 get-lambda-build.py

# get the S3 key of the most recently packaged dependencies
get-deps-key:
	python3 get-lambda-dependencies.py
