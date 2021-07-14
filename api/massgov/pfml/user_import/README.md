# Bulk User Import

A tool to import Leave Admin users from one or more CSV files stored locally or in S3


## Running the tool

The Poetry pyproject.toml has been updated to include the command `bulk-user-import`; this expects one or more paths to CSV files such as `"/Users/me/Desktop/test.csv"`

For example:
```sh
poetry run bulk-user-import "/Users/me/Desktop/test.csv"
```
### Running via ECS Tasks

A new ECS task has been created to run this in AWS

How to run this in test:
1. Upload your source file to `s3://massgov-pfml-test-bulk-user-import/source.csv`
2. Tail the logs `saw watch --raw service/pfml-api-test/ecs-tasks | python3 massgov/pfml/util/logging/decodelog.py`
3. Launch the task locally with `./bin/run-ecs-task/run-task.sh test bulk-user-import firstname.lastname bulk-user-import "s3://massgov-pfml-test-bulk-user-import/source.csv"`
4. Reset the password for your user and you can log in: https://paidleave-test.mass.gov/forgot-password/


## Workflow Diagram for Task

![Workflow Diagram for Bulk Importer](https://lucid.app/publicSegments/view/752992e1-9008-4454-891f-2d5158965c9e/image.png)


## Configuring the database

`process_csv.py` uses massgov.pfml.db.config to retrieve a database config

This means that environment variables will configure the database connection, such as:
* DB_HOST
* DB_USER
* DB_PASSWORD
* DB_PORT

Additionally `process_csv.py` uses `massgov/pfml/fineos/factory.py` to consume FINEOS configuration; these values are required
* FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL
* FINEOS_CLIENT_GROUP_CLIENT_API_URL
* FINEOS_CLIENT_CUSTOMER_API_URL
* FINEOS_CLIENT_WSCOMPOSER_API_URL
* FINEOS_CLIENT_WSCOMPOSER_USER_ID
* FINEOS_CLIENT_OAUTH2_URL
* FINEOS_CLIENT_OAUTH2_CLIENT_ID
* FINEOS_CLIENT_OAUTH2_CLIENT_SECRET

Finally, this requires `COGNITO_IDENTITY_POOL_ID` to be set in order to create user accounts in Cognito's User Pool
* COGNITO_IDENTITY_POOL_ID

Note that in order to connect to S3 and to Cognito, the `ecs-task` or your local instance will need configuration that `boto3` will be able to find

(See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html for more info)

For a local execution, running `aws sso login` should suffice to provide you with access to Test

### IAM Permissions for ECS Task

In addition to our "normal" set of ECS task permissions - SSM access to read secrets, ECS access to pull images, CloudWatch access to write logs, etc, the following permissions are needed
* Access to Cognito resource (associated `COGNITO_IDENTITY_POOL_ID`)
  *  "cognito-idp:ListUsers"
  *  "cognito-idp:AdminCreateUser",
  *  "cognito-idp:AdminSetUserPassword"
* Access to S3 location to read files
  *  "s3:PutObject"
  *  "s3:GetObject"
  *  "s3:ListBucket"


## CSV Import Format

`process_csv.py` takes a list of `fein` and `email` stored in one or more CSV files; this is the expected format,
but the order is not important

| column            | default | required | description                                                     |
| :----:            | :-----: | :------: | :-------------------------------------------------------------- |
| fein              |  none   | yes      | the FEIN of the employer to generate codes for                  |
| email             |  none   | yes      | email of the user to register for; can be for an existing user  |



As the above indicates - the only _required_ fields are `fein`, and `email`; all other fields are optional


