# MFA Lockout Resolution
This is the ECS task / script for disabling Multi-Factor Authentication on a user's account. It is run when a user is locked out of their account due to their MFA setup.
A user must first call the contact center and request that their MFA be disabled before we run this script.
This script is idempotent - it can safely be run multiple times with the same input.

For more on the MFA Lockout Flow procedures, see: https://lwd.atlassian.net/wiki/spaces/CP/pages/2198995062/MFA+Lockout+Flow

## Sample Run
On local machine:
`cd pfml/api`
`make mfa-lockout-resolution args="--email jesseshepherd+mfa-01@navapbc.com --dry_run true"`

In `test` environment:
`cd pfml`
`./bin/run-ecs-task/run-task.sh test mfa-lockout-resolution jesse.shepherd mfa-lockout-resolution --email jesseshepherd+test-mfa-01@navapbc.com --dry_run true`

## Required Params
- email (str)       - The email associated with the user's PFML account.

## Optional Params
- dry_run (str)     - If enabled (set to "True"), the script will not make any changes to Amazon Cognito or the PFML db

## Local Setup
(See: [Local Integration with AWS](/docs/api/local-integration-with-aws.md))

## Handling Errors
This script is idempotent - so when encountering an error, it is safe to re-run it!

If running in `prod`, and the script still fails after being re-run, escalate to an on-call engineer!

### User not found
Make sure the user's email is provided, and spelled correctly!

### Errors updating Cognito
If running locally, make sure your AWS credentials are up-to-date, and are being supplied to the Docker container correctly.

### Errors updating SNS
A user's number can only be opted back into SNS once every 30 days - if any exceptions related to throttling are shown, there is no need to run the script again or escalate. 
