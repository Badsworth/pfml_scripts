# build for local invoke
build:
	sam build --use-container

# invoke lambda function locally
local:
	sam local invoke "ImportFunction" -e test_event.json

# build and deploy function on AWS lambda
publish:
	sam build --use-container
	sam package --s3-bucket nava-pfml-lambda-poc-import --use-json --output-template-file lambda-s3-package.json
	aws lambda update-function-code \
    --function-name=massgov-pfml-poc-lambda-process-dor \
    --s3-bucket=nava-pfml-lambda-poc-import \
    --s3-key=$(shell python3 get-lambda-build.py) \
    --publish

# invoke lambda function
invoke:
	base64 -i test_event.json -o test_event_b.json
	aws lambda invoke \
		--function-name=massgov-pfml-poc-lambda-process-dor \
		response.json \
		--payload file://test_event_b.json \
		--log-type Tail \
		--query LogResult \
		--output text | base64 -D

clean:
	rm -rf .aws-sam
