# DOR Import

Initial wiring for DOR importer.

## Prerequisites

AWS CLI
AWS SAM CLI
Docker

## Mock files

Generate mock DOR export files

```
make generate
```

Generate with specific number of employers (employees = employer * 15)

```
make generate EMPLOYER_COUNT=2000
```

## Dependencies

Run to get latest PFML API module as a dependency (whenever API code changes)

```
make build-api import-api-module
```

For decrypting files, a GPG binary is also required. For now, this is required even for
local development where decryption is off by default.

```
make deps
```

## Local testing

DOR Importer requires all migrations to be run and the database to be up. From the the `/api` directory:

```
$ make db-upgrade
$ make run
```

For testing against S3 you will need to be logged in to the PFML AWS. See documentation around `login-aws` in `/api/README.md`

Build the function (whenever the importer code changes)

```
$ make build
```

Invoke the function

```
make invoke-local
```

Invoke the function after a full build including API

```
make build-invoke-local
```

Clean build artificats

```
make clean
```

## Release

Build and upload to S3

```
make upload-release
```

Get the S3 key

```
make get-key
```
