# ECS Task Infrastructure

Infrastructure for background ECS tasks is defined in this directory.

**Pre-requisites**: This module assumes that an ECS cluster and VPC already exists for housing ECS tasks. see [Creating Environments](../../docs/creating-environments.md).

## Key Components

### ECS Task Definitions

This module creates ECS task definitions for background jobs in [tasks.tf](./template/tasks.tf). The task definitions rely on the same ECR docker images as the Paid Leave API and specify different commands to be run. 

For more details on how the API code connects to the ECS task infrastructure, see [docs/infra/creating-ecs-tasks.md](../../docs/infra/creating-ecs-tasks.md).

### DOR ETL Step Function

The Department of Revenue (DOR) ETL process loads employee/employer and wage data from DOR into the Paid Leave API database, and syncs data with FINEOS.

This is managed using an [AWS step function](https://aws.amazon.com/step-functions/) as defined in [step_functions.tf](./template/step_functions.tf).

### Logs

All ECS task logs are configured to send to a cloudwatch log group, and are forwarded to New Relic using the global New Relic lambda forwarder as defined in [cloudwatch.tf](./template/cloudwatch.tf).

## Running tasks

### Scheduled Tasks

Some ECS tasks are directly scheduled using EventBridge via the [ecs\_task\_scheduler](../modules/ecs_task_scheduler/) module. All schedules are defined in [cloudwatch.tf](./template/cloudwatch.tf).

### Triggered Tasks

Some ECS tasks are triggered when S3 objects are created, as specified in [s3_subscriptions.tf](./template/s3_subscriptions.tf). 

Since ECS tasks are not directly triggerable by S3 events, we instead trigger lambda functions, which will run the ECS task using boto3. This lambda is created using the [s3\_ecs\_trigger](../modules/s3_ecs_trigger/) module.

### Running Tasks Manually

Any ECS task can be run using a custom run-ecs-task script. See [bin/run-ecs-task](../../bin/run-ecs-task/README.md) for more details.

## Deployment

This module is deployed through the API CI Deploy workflow in Github Actions. See: [docs/deployment.md](../../docs/deployment.md).
