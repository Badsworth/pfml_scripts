## include template file
include ../Makefile.template

## Build and release variables

API_DIR := $(realpath ../..)
API_DIST_DIR := $(API_DIR)/dist
LAMBDA_FUNCTION_NAME := DORImportFunction
LAMBDA_BUILD_BUCKET := massgov-pfml-api-lambda-builds
LAMBDA_BUILD_PREFIX := dor-import

## DOR specific targets and overrides

clean-deps: ## Clean binary dependencies	
	rm -rf dependencies/ +
	rm -f dependencies.zip +

clean: ## Include dependency clean to template target
clean: clean-deps

deps:  ## Build binary dependencies
	mkdir -p ./dependencies
	docker run --rm -v "$(PWD)"/dependencies:/lambda/opt lambci/yumda:2 yum install -y gnupg
	(cd dependencies && zip -yr ../dependencies.zip .)

build: ## Include extra binary dependcies to the template build
build: deps

get-release-deps-url: ## Get S3 URL for uploaded release's dependent layer(s) from SAM package output file
	@jq -r '.Resources.DependenciesLayer.Properties.ContentUri' $(RELEASE_INFO_FILE)

get-release-deps-key: ## Get just the S3 key (i.e., path without the bucket name) for uploaded release's dependent layer(s)
	@jq -r '.Resources.DependenciesLayer.Properties.ContentUri' $(RELEASE_INFO_FILE) | sed "s|s3://${LAMBDA_BUILD_BUCKET}/${LAMBDA_BUILD_PREFIX}/||"

## Mock DOR file generation

## Mock DOR file folder (use API folder as root context)
MOCK_OUTPUT_FOLDER := lambdas/dor/mock_output

EMPLOYER_COUNT := 100

generate:
	cd $(API_DIR); massgov/pfml/dor/mock/generate.py --folder $(MOCK_OUTPUT_FOLDER) --count $(EMPLOYER_COUNT)

clean-mock:
	rm -rf mock_output/*