# DOR Import

Initial wiring for DOR importer.

## Prerequisites

AWS CLI
AWS SAM CLI
Docker

# Dependencies

Run to get latest PFML API module as a dependency (whenever API code changes)

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
make local
```

## AWS Labmda (TODO - bring over from /massgov/pfml/data_integrations/dor/import)

<!-- Build and deploy
```
$ make publish
```

Invoke the function
```
make invoke
``` -->
