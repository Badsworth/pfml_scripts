# Infrastructure

This directory houses the configuration needed for maintaining PFML infrastructure.
We use [Terraform](https://terraform.io) to manage our infra in a modular, concise, and reusable fashion.

- [Local Setup](#local-setup)
- [Runbook](#runbook)
- [Directory Structure](#directory-structure)
- [tfstate files](#tfstate-files)
- [Troubleshooting](#troubleshooting)

## Local Setup

These steps are required before running terraform or test commands locally on your machine.

<b>1. Configure AWS</b>

Since we manage AWS resources using Terraform, AWS credentials are needed to run terraform commands. Access to the AWS CLI is federated by AWS SSO, backed by Azure AD.

Visit [https://coma.awsapps.com/start](https://coma.awsapps.com/start) and log in with your Azure AD credentials. The UI will provide CLI credentials via `export` commands that you can paste into your terminal.

<b>2. Install Terraform</b>

Refer to the root-level [README](../README.md) for instructions on installing terraform.

<b>3. Optionally install NPM dependencies</b>

To locally run tests for JS lambdas, you'll also need to run the following with `infra/` as the working directory:

```
npm install
```

</p>
</details>

## Runbook

To view pending changes to infrastructure within an environment directory (i.e. `/test`, `/stage`):

```
$ terraform init
$ terraform plan
```

To apply changes to infrastructure:

```
$ terraform apply
```

### Setting up a new environment

🔗 See [docs/creating-environments.md](../docs/creating-environments.md) to learn how to create a new environment.

### Running JS Lambda Tests

To run the [test suite](../docs/tests.md):

```
npm test
```

Update _all_ [Jest snapshots](../docs/tests.md#Snapshot%20tests), accepting any updates as expected changes:

```
npm run test:update-snapshot
```

Run the project's test suite in watch mode:

```
npm run test:watch
```

> By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.

## Directory Structure

Standalone folders:

```
└── constants           🏡 infrastructure data shared across all applications and all environments, e.g. a common block of aws tags

└── pfml-aws            🏡 infrastructure for AWS and VPCs, shared across envs e.g. developer IAM roles,
                           docker registries, and network load balancers for each VPC.

└── monitoring          🏡 configuration for pagerduty schedules, on-call policies, and New Relic/Cloudwatch alerts.
```

Component folders:

```
└── api                 🏡 infrastructure for a PFML api environment
    └── template        🏗  shared template for api env
    └── environments
        └── test        ⛱  test env, deployed on every merged commit.
        └── stage       ⛱  staging env
        └── prod        ⛱  production env

└── ecs-tasks           🏡 infrastructure for adhoc PFML API ECS tasks
    └── template        🏗  shared template for API ecs tasks
    └── environments

└── env-shared          🏡 infrastructure for an environment, shared across applications e.g. an API Gateway and ECS cluster.
    └── template        🏗  shared template for an env

└── portal              🏡 infrastructure for a PFML portal environment
    └── template        🏗  shared template for portal env
    └── environments

```

Re-usable module folders (used by other folders):

```
└── modules                  🏡 reusable modules.
    └──  ecs_task_scheduler  ⛱ Creates a scheduled ECS task job.
    └──  s3_ecs_trigger      ⛱ Creates an ECS task triggered by S3 events
    └──  alarms_api          ⛱ Creates alarms for the API application in a given environment.
    └──  alarms_portal       ⛱ Creates alarms for the Portal application in a given environment.
    └──  ...
```

## tfstate files

Each environment for a component has a `.tfstate` file that is stored in S3 and synchronized using a DynamoDB lock table.
Terraform relies on this state file for every command and must acquire the lock in order to use it, so only one person or system can run a terraform command at a time.

```
S3
└── massgov-pfml-aws-account-mgmt
    └── terraform
        └── aws.tfstate
        └── monitoring.tfstate
└── massgov-pfml-test-env-mgmt
    └── terraform
        └── env-shared.tfstate
        └── portal.tfstate
        └── api.tfstate
        └── ecs-tasks.tfstate
```
