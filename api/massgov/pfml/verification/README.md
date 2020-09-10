# Verification Code Generator

A tool to create database `VerificationCode` records configured and driven by an input CSV file

Generates a CSV document containing the fein, `VerificationCode.verification_code`, uses, expiration_date, email

## Running the tool

The Makefile has been updated to include the command `generate-verification-codes`; this expects the params `input=a/path/to/a/file.csv` and `output=a/path/to/output.csv`

For example:
```sh
make generate-verification-codes input=massgov/pfml/verification/test.csv output=massgov/pfml/verification/output.csv
```
### Running via ECS Tasks

A new ECS task has been created to run this in AWS

How to run this in test:
1. Upload your source file to `s3://massgov-pfml-test-verification-codes/source.csv`
2. Launch the task locally with `../../../../bin/run-ecs-task/run-task.sh test test-ad-hoc-verification firstname.lastname`
3. Retrieve your output file from `s3://massgov-pfml-test-verification-codes/output.csv`

Note that this will create verification codes in the database for the appropriate environment

## Configuring the database

`generate_verification_codes.py` uses massgov.pfml.db.config to retrieve a database config

This means that environment variables will configure the database connection, such as:
* DB_HOST
* DB_USER
* DB_PASSWORD
* DB_PORT

## Using CSV inputs to control the behavior of the tool

`generate_verification_codes.py` has a number of "reasonable defaults" for many values that can be overridden in CSV columns.

These defaults should apply in the case of both missing columns or missing values.

| column      | default | required | description                                                |
| :----:      | :-----: | :------: | :--------------------------------------------------------- |
| fein        |  none   | yes      | the FEIN of the employer to generate codes for             |
| code_length | 6       | no       | Number of characters for the code                          |
| uses        | 1       | no       | Number of uses to store for this VerificationCode record   |
| quantity    | 1       | no       | Number of codes to generate for this FEIN                  |
| valid_for   | 90      | no       | Number of days from (today) the verification code is valid |
| email       |  none   | no       | If present, will appear in the output CSV on the same row  |

As the above indicates - the only _required_ field is `fein`; all other fields are optional


