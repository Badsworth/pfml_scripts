# Lambda Infrastructure

We use a parameterized Makefile to provide shared build, local testing and release commands around lambda functions.

## Prerequisites

Install the following prerequisites on your machine:
- Tooling to build main API project (e.g., poetry)
- AWS CLI
- AWS SAM CLI
- Docker
- jq

## Commands

`make` commands should be run from the specific lambda folder (i.e. `dor/` or `fineos/eligibility_export_feed`)

Build the function (whenever the importer code changes)

```
$ make build
```

Invoke the function locally

```
make invoke-local
```

Invoke the function after a full build including API

```
make build-invoke-local
```

Build and upload to lambda to S3

```
make release
```

Get the S3 key for the lambda build

```
make get-release-key
```

Clean build artifacts

```
make clean
```

View available commands

```
make help
```

## Setting up a new Lambda

Create a new folder and copy files from one of the existing lambdas. Update these files for your specific lambda:

`Makefile`:
* `Makefiles` should include the `Makefile.template` file in this folder
* `fineos/eligibility_export_feed` has the basic pattern and all you need to do is set the variables in the `Makefile` correctly
* Default pattern is empty event payload. Specify an event json payload for local testing by setting the `LOCAL_INVOKE_EVENT_JSON` variable in the lambda makefile (see `fineos/conginto_post_confirmation` as reference)
* `dor` has a binary dependencies layer to support gpg encryption. Use this as a template for lambdas with a binary dependency use case.
* lambda specific commands (see DOR `make generate`) should be added to the lambda specific Makefile and document with a README

`requirements.txt`: link to the PFML API source code. Also include any other python dependencies specific to your lambda code (if any).

`handler.py`: handler code (Usually just point to the handler code in the PFML API source). We prefer having code as part of the API source for code reuse and testability.

`template.yaml`: lambda template file - define source directory, point to handler and define expected environment variables.

`env.json`: environment variables to be supplied to the local lambda invoke. Environment variables for AWS environments are specified in terraform (see below).

## Local Testing

Lambdas that need database access will need a live database running.

```
$ make db-upgrade
$ make run
```

For lambdas that require AWS resources (i.e S3) you will need to be logged in to the PFML AWS. See documentation around `login-aws` in `/api/README.md`

## Infrastructure

Infrastructure for lambdas is described in various Terraform files.

Variables needed for lambda build (S3 keys, ARN):
* `infra/api/environments/{env}/` - `terraform plan` input variables (see `dor_lambda_artifact_s3_key.tf` as reference)
* `infra/api/template/variables.tf` - variables for the lambda function definition
* `infra/api/environments/{env}/main.tf` - pass in variables as argument to environment specific modules
* Environment generators - replicate input variable and arguments from above in `bin/bootstrap-env/api/main.tf` and `bin/boostrap-env/api/`

Lambda function definition:
* `infra/api/template/lambda.tf` - lambda functions definition and environment variables.
* `infra/api/template/iam.tf` - lambda role/policy
* `infra/api/template/security_groups.tf` - RDS access security groups

Lambda build buckets:
* `infra/pfml-aws/s3.tf` - S3 lambda build bucket. Specific lambdas are built into specific folders (prefixes). Build is performed by CD workflow in `.github/workflows/api-deploy.yml`

### Setting up a new lambda infrastructure
* Add any new input and argument variables and pass to top level environment modules as arguments
* Add your lambda definition `infra/api/template/lambda.tf` (see existing lambda definitions as reference)


## CI / CD

Lambdas are built and deployed as part of the our CD workflow using Github Actions.

* `.github/workflows/api-deploy.yml` - Duplicate code for one of the existing lambdas (see `dor-import-build` as reference)

### Setting up a new lambda CI/CD

* add a new lambda job (see `dor-import-build` as reference)
* add the job name under `api-db-migrate-up`
* add the job under `api-release`, specify input variables to the terraform plan



