# Cognito Post Confirmation hook Lambda

This directory holds the packaging parts for handling the Cognito Post
Confirmation Lambda.

The actual functionality of the Lambda lives in the
`massgov.pfml.cognito_post_confirmation_lambda` module.

The infrastructure code to create/deploy the Lambda lives in
`/infra/api/templates/lambda.tf`.

The Lambda is connected to Cognito in `/infra/portal/template/cognito.tf`.

## Build dependencies

- Tooling to build main API project (e.g., poetry)
- AWS SAM CLI
- jq

## Build

```sh
make build
```

Building the Lambda is a little strange, since the code actually lives
elsewhere. The setup is:
 - `./requirements.txt` points to `./dist` as a spot for pip to look for
   dependencies, which the only dependency is the `massgov` module
 - Build a wheel for the `massgov` module
 - Copy it to `./dist`
 - SAM builds and installs all of the `massgov` modules dependencies in a Docker
   container matching the Lambda hosting environment
 - Output of the SAM build is in `./.aws-sam/build/CognitoPostConfirmation`,
   this is the directory that will get zipped and uploaded when doing a release

`make build` handles all of that.

## Running locally

After building the Lambda, can run it locally with:

```sh
make invoke-local
```

which will spin up the Lambda locally and call it with event `./test_event.json`.

You can override the event used with the `event` argument, like:

```sh
make invoke-local event=./my_other_event.json
```

## Release

To upload a new release, run:

```sh
make release
```

Note a "release" is just a ZIP uploaded to a location in S3.

This will create a `lambda-s3-package.json` file, which holds the result of the
release, `make get-release-key` uses this file to print the release key when
it's needed.

## Deploy

To actually deploy the Lambda, grab the release key with `make get-release-key`,
then in `/infra/api/environments/<env>`, run:

```sh
# in /infra/api/environments/<env>
terraform apply -var cognito_post_confirmation_lambda_artifact_s3_key='<release key>'
```

Note the Cognito Terraform in the Portal config does not need applied, it always
uses the latest deploy of the Lambda.
