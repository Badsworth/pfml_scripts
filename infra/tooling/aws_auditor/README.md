# AWS Auditor

This module audits AWS resources using a Lambda Function that writes
to a DynamoDB Table daily

## How to deploy

To deploy an auditor you will need to create a Python Lambda Function in the `infra/tooling/aws_auditor/lambda_functions/<resource_name>/` directory, with the name `<resource_name>.py`.
This will create the following

- An EventBridge Rule that triggers the Lambda Function once a day
- A Lambda Function named `massgov_pfml_<resource_name>`
- A DynamoDB Table named `massgov_pfml_<resource_name>`

Add `<resource_name>` as a key in the `infra/tooling/auditors.json` file with the actions required for the Auditor Lambda Function as an array of strings.

For example - This grants the massgov_pfml_audit_lambda function permissions
to Audit Lambda Functions in the account

```
{
    "lambda": {
        "actions": ["lambda:ListFunctions"]
    }
}
```
