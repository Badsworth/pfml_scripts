# MFA Lockout Resolution
This is the ECS task / script for disabling Multi-Factor Authentication on a user's account. It is run when a user is locked out of their account due to their MFA setup.
A user must first call the contact center and request that their MFA be disabled before we run this script.
This script is idempotent - it can safely be run multiple times with the same input.

For more on the MFA Lockout Flow procedures, see: https://lwd.atlassian.net/wiki/spaces/CP/pages/2198995062/MFA+Lockout+Flow

## Important Note about PII!
This script logs metrics to New Relic, so it's important to make sure we don't expose any user PII! In particular, the call center agents may capture the user's full name as part of the PSD ticket. We don't need the user's name in order to run this script, and including it would cause it to be exposed.

For more information on the input parameters, and what information we should pass to them, see the [Optional Security Metrics](#optional-security-metrics) section.

## Running the Script
usage: mfa-lockout-resolution [-h] --email EMAIL --psd_number PSD_NUMBER --reason REASON --employee EMPLOYEE --verification_method VERIFICATION_METHOD [--dry_run DRY_RUN]

For info on how to run the script, use the `--help` flag.

### Sample Run
On local machine:
`cd pfml/api`
`make mfa-lockout-resolution args="--email=jesseshepherd+mfa-01@navapbc.com --psd_number=PSD-9876 --reason='They lost their phone' --employee='edith.finch@mass.gov' --verification_method='With Claim' --dry_run=true"`

In `test` environment:
`cd pfml`
`./bin/run-ecs-task/run-task.sh test mfa-lockout-resolution jesse.shepherd mfa-lockout-resolution --email=jesseshepherd+test-01@navapbc.com --psd_number=PSD-9876 --reason='They lost their phone' --employee='edith.finch@mass.gov' --verification_method='With Claim' --dry_run=true`

### Dry Run
By default, this script runs in "dry run" mode, and does not commit any changes to Amazon Cognito or the PFML db. To commit these changes, run the script with `--dry_run=false`

### Local Setup
(See: [Local Integration with AWS](/docs/api/local-integration-with-aws.md))

## Optional Security Metrics
We record optional usage metadata and report them to New Relic. We should make sure not to expose any user PII via this metadata!

These are "optional", but the script will complain if they are not included - we should explicitly specify "None Provided" if we're not able to provide this info.

### Reason
The user's reason for disabling MFA.

### Employee
The email address of the call center agent who created the PSD ticket. **(Important Note: We don't want to accidentally include the user's name here!)**

### Verification Method
The method used to verify the user's identity: "With Claim" or "Without Claim". If a user has called in _before submitting a claim_, the call center agent will include in the PSD ticket something like the following: "Claimant has not submitted their claim yet. No email exists in FINEOS and we are unable to verify the email address used." In this case, enter "Without Claim". Otherwise, enter "With Claim".

## Handling Errors
This script is idempotent - so when encountering an error, it is safe to re-run it!

If running in `prod`, and the script still fails after being re-run, escalate to an on-call engineer!

### AWS credentials issue
If you see an error with AWS credentials (like below), make sure you have credentials set up to run AWS commands on your local machine! Follow the instructions above in [Local Setup](#local-setup).

`"error configuring S3 Backend: error validating provider credentials: error calling sts:GetCallerIdentity: InvalidClientTokenId: The security token included in the request is invalid"`

### User not found
Make sure the user's email is provided, and spelled correctly!

### Errors updating Cognito
If running locally, make sure your AWS credentials are up-to-date, and are being supplied to the Docker container correctly.

### Errors updating SNS
A user's number can only be opted back into SNS once every 30 days - if any exceptions related to throttling are shown, there is no need to run the script again or escalate. 
