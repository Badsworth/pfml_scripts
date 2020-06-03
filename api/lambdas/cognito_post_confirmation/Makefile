LAMBDA_NAME := cognito_post_confirmation

API_DIR := $(realpath ../..)
API_DIST_DIR := $(API_DIR)/dist

LAMBDA_BUILD_BUCKET := massgov-pfml-api-lambda-builds

RELEASE_INFO_FILE := lambda-s3-package.json

build: ## Build Lambda
build: build-src-wheel build-sam

build-sam: ## Build Lambda package via SAM
	sam build --use-container

build-src-wheel: ## Build Python package of source code
	cd $(API_DIR); poetry build --format wheel
	mkdir -p ./dist
	cp -r $(API_DIST_DIR)/* ./dist/

clean: ## Remove intermediate, cache, or build artifacts
	rm -rf dist
	rm -rf .aws-sam

invoke-local: event := test_event.json
invoke-local: env_vars := env.json
invoke-local: ## Run Lambda locally with $event, defaulting to ./test_event.json
	sam local invoke \
		--docker-network api_main \
		--env-vars $(env_vars) \
		--event $(event)

release: ## Build and upload Lambda
release: build release-publish

release-publish: ## Upload lambda
	sam package \
		--s3-bucket $(LAMBDA_BUILD_BUCKET) \
		--s3-prefix $(LAMBDA_NAME) \
		--use-json \
		--output-template-file $(RELEASE_INFO_FILE)

get-release-location: ## Get S3 URL for uploaded release from SAM package output file
	@jq -r '.Resources[].Properties.CodeUri' $(RELEASE_INFO_FILE)

get-release-key: ## Get just the S3 key (i.e., path without the bucket name) for uploaded release
	@jq -r '.Resources[].Properties.CodeUri' $(RELEASE_INFO_FILE) | sed "s|s3://${LAMBDA_BUILD_BUCKET}/||"
