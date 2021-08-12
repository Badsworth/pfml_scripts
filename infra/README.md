# Infrastructure

This directory houses the configuration needed for maintaining PFML infrastructure.
We use [Terraform](https://terraform.io) to manage our infra in a modular, concise, and reusable fashion and Github Actions to automatically deploy infrastructure.

## First-time Setup

For first-time setup, see [docs/infra/first-time-setup.md](../docs/infra/first-time-setup.md).

## Directory Structure

This directory contains three standalone modules:

- `constants` provide shared values for other terraform modules.
- `pfml-aws` is account-level infrastructure that must be manually deployed by an infra-admin.
- `monitoring` is monitoring infrastructure that is automatically deployed when changed in the main branch.

```
└── constants           🏡 infrastructure data shared across all applications and all environments, e.g. a common block of aws tags

└── pfml-aws            🏡 infrastructure for AWS and VPCs, shared across envs e.g. machine IAM users,
                           docker registries, and network load balancers for each VPC.

└── monitoring          🏡 configuration for pagerduty schedules, on-call policies, and New Relic/Cloudwatch alerts.
```

Additionally, we have several components that are duplicated within each environment:

```
└── api                 🏡 infrastructure for a PFML api environment
    └── template        🏗  shared template for api env
    └── environments
        └── test        ⛱  test env, deployed on every merged commit.
        └── stage       ⛱  staging env
        └── prod        ⛱  production env

└── ecs-tasks           🏡 infrastructure for background PFML API ECS tasks
    └── template        🏗  shared template for API ecs tasks
    └── environments

└── env-shared          🏡 infrastructure for an environment, shared across applications e.g. an API Gateway and ECS cluster.
    └── template        🏗  shared template for an env
    └── environments

└── portal              🏡 infrastructure for a PFML portal environment
    └── template        🏗  shared template for portal env
    └── environments
```

Several re-usable modules have also been created for use by the terraform folders above:

```
└── modules                  🏡 reusable modules.
    └──  ecs_task_scheduler  ⛱ Creates a scheduled ECS task job.
    └──  s3_ecs_trigger      ⛱ Creates an ECS task triggered by S3 events
    └──  alarms_api          ⛱ Creates alarms for the API application in a given environment.
    └──  alarms_portal       ⛱ Creates alarms for the Portal application in a given environment.
    └──  ...
```

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
