This python script is a wrapper around the `mfa-lockout-resolution` ECS Task for disabling a claimants MFA in Cognito.

This wrapper allows for multiple ecs task invocations to be started from a single command

Beware of PII! ECS Task output will be in the AWS CloudWatch logs. Do not run commands that will potentially reveal PII in the output.

## Requirements

* [terraform](https://www.terraform.io)
* [jq](https://stedolan.github.io/jq)
* [AWS Command Line Interface](https://aws.amazon.com/cli)
* [EOTSS/PFML AWS Account](../../docs/infra/1-first-time-setup.md#Configure-AWS)


## Usage

* [Authenticate with AWS](../../docs/infra/1-first-time-setup.md#Configure-AWS)
2. Initialize terraform for the environment you want to run the ECS task in

```sh
cd infra/ecs-tasks/environments/test
terraform init
```

3. Populate the claimants.json file with claimant information from the PSD tickets you will be working

```{
        "email": "EMAIL",
        "psd_number": "PSD_NUMBER",
        "reason": "REASON",
        "employee": "EMPLOYEE",
        "verification_method": "VERIFICATION_NUMBER"
    }
```
* `EMAIL` is the email address of the claimant needing MFA disabled
* `PSD_NUMBER` is the PSD ticket id, example; `PSD-1234`
* `REASON` is the reason for MFA to be disabled provided in the PSD ticket
* `EMPLOYEE` is the email address in the reporter field of the PSD ticket, usually the Savilinx agent
* `VERIFICATION_METHOD` is the method used to verify the claimant to allow for MFA to be disabled, `With Claim` or `Without Claim`

4. Run the `batch_mfa_disable.py` python script with poetry:

```sh
poetry run python3 batch_mfa_disable.py --environment=test --dryrun=true --user=jay.reed
```

Notes:

* `<environment>`: a PFML environment, such as `test`, `stage`, `prod`, etc
* `<dryrun>`: whether or not to perform a dryrun (logs only) run of the script or to actually disable MFA for all claimants in claimants.json
* `<user>` is your `<firstname>.<lastname>`. This is shown in the AWS CloudWatch logs as the person running the ECS Task

## Viewing logs

The logs for your ECS task will be sent to Cloudwatch Logs and New Relic. See [Viewing ECS Task Logs](../../docs/infra/4-viewing-ecs-task-logs.md).
