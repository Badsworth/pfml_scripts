# DOR Import

Initial wiring for DOR importer.

## Prerequisites

AWS CLI
AWS SAM CLI
Docker

## Local testing

Build the function
```
$ make build
```

Invoke the function
```
make local
```

## AWS Labmda

Build and deploy
```
$ make publish
```

Invoke the function
```
make invoke
```

## Using Lambda in AWS Console

- Log in to your AWS console and go to Lambda
- Search for the function name massgov-pfml-poc-lambda-process-dor
