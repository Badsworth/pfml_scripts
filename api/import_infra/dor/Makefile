DOR_IMPORT_LAMBDA_FOLDER := ../../massgov/pfml/data_integrations/dor/import

clean:
	rm -rf .aws-sam

# grab the latest pfml api code
deps:
	cd ../..; poetry build
	cp ../../dist/massgov.pfml.api-0.1.0-py3-none-any.whl $(DOR_IMPORT_LAMBDA_FOLDER)/lambda/massgov.pfml.api-0.1.0-py3-none-any.whl

# build the lambda within a SAM container
build:
	sam build --template $(DOR_IMPORT_LAMBDA_FOLDER)/template.yaml --use-container

# invoke locally by passing environment variable file and test event
local:
	sam local invoke "ImportFunction" \
		--env-vars local.json \
		--log-file local-log.txt \
		--event test_event.json

# build and publish lambda function to AWS
package:
	sam package \
		--s3-bucket massgov-pfml-test-lambda-builds \
		--s3-prefix dor-import \
		--use-json \
		--output-template-file dor-import-lambda-s3-package.json

get-key:
	python3 get-lambda-build.py

deploy:
	aws lambda update-function-code \
	  --function-name=massgov-pfml-poc-lambda-process-dor \
	  --s3-bucket=massgov-pfml-test-lambda-builds \
		--s3-prefix
	  --s3-key=$(shell python3 get-lambda-build.py) \
	  --publish
