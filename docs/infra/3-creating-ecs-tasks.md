# Creating ECS Tasks

This page describes the technical architecture for defining an ECS task.

## Creating a Barebones ECS Task

### Building the Entrypoint

All ECS tasks rely on and eventually run one of the Poetry scripts defined in [pyproject.toml](../../api/pyproject.toml). These scripts reference a specific entrypoint method in the codebase, e.g.

```toml
# Run the "up" entrypoint method in massgov/pfml/db/migrations/run.py
db-migrate-up = "massgov.pfml.db.migrations.run:up"
```

To create a new entrypoint, it is sufficient to add a new method in the API codebase:

```py
# massgov/pfml/some/task.py
from massgov.pfml.util.bg import background_task

@background_task("my-new-task-name")
def main():
    pass
```

and to reference it in a new Poetry script:

```toml
my-new-task-name = "massgov.pfml.some.task:main"
```

### Creating the ECS Task Definition

Once you have a poetry script, you can build the ECS task infrastructure following the instructions in [tasks.tf](../../infra/ecs-tasks/template/tasks.tf).

### Scheduling and Triggers

If you need to run the ECS task on a schedule or trigger it based off of an AWS S3 event, you can do so using the existing patterns in [cloudwatch.tf](../../infra/ecs-tasks/template/cloudwatch.tf) and [s3_subscriptions.tf](../../infra/ecs-tasks/template/s3_subscriptions.tf).

## Testing

### Testing the Entrypoint

The entrypoint is runnable locally using poetry, outside of the context of an ECS task, and is the fastest way to test functionality live without a deployment. 

Log into the docker container if needed with `make login` then run the following command:

```sh
$ poetry run my-new-task-name
```

This should run the `main` method and print some standardized log output.

If your ECS task requires custom environment variables, you can provide it in the `docker-compose.yml` file temporarily. Personal AWS credentials can also be passed into the docker container following the instructions in [docker-compose.override.yml](../../api/docker-compose.override.yml).

### Testing the ECS Task

All ECS tasks, including the Paid Leave API, are built on top of a shared set of code compiled into a single docker image. This docker image is built and pushed to ECR using `make build-and-publish`.

In normal scenarios, the docker build process is managed by the API Deploy Github Actions workflow. However, if you need a tighter test loop, it is recommended that you follow the steps in [Deployment](../deployment.md) to disable API TEST auto-deploys and do the docker image updates manually:

```
# Build and publish the docker image to ECR
$ make --directory=api build-and-publish

# Update ECS tasks in the TEST environment to use the new docker image
$ terraform -chdir=infra/ecs-tasks/environments/test/ apply --var service_docker_tag=$(git rev-parse HEAD)
```

Once ECS tasks are updated in TEST, you can manually run your ECS task. We have a custom script to do this easily:

```
$ ./bin/run-ecs-task/run-task.sh test my-new-task-name kevin.yeh
```

If your task is scheduled or based on a trigger, you can wait for the task to run or do the appropriate action for triggering the task. If your schedule is infrequent, change it to a frequent schedule for testing. This is recommended to ensure that permissions are properly set up for the ECS task to run automatically based on a time or S3 event trigger.

#### Viewing Task logs

See [Viewing ECS Task Logs](./4-viewing-ecs-task-logs.md).
