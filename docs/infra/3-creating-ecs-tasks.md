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

#### Viewing ECS Task logs

The logs for your ECS task will be sent to Cloudwatch Logs and New Relic. There are two distinct methods that people use:

##### Stream logs to your terminal

Lots of folks use [saw](https://github.com/TylerBrock/saw) and pipe it through a developer utility for pretty-printing logs:

```sh
saw watch --raw service/pfml-api-test/ecs-tasks | python3 api/massgov/pfml/util/logging/decodelog.py
```

You can also use the AWS CLI v2, which has built in support for tailing Cloudwatch logs:

```sh
aws logs tail service/pfml-api-test/ecs-tasks --follow
```

##### Searching logs in New Relic

Alternatively, you can use the New Relic Logs UI to search and filter for logs. There is a saved view for [ECS task logs in TEST](https://one.newrelic.com/launcher/logger.log-launcher?platform[accountId]=2837112&platform[$isFallbackTimeRange]=true&platform[timeRange][duration]=1800000&launcher=eyJxdWVyeSI6ImF3cy5sb2dHcm91cDpcInNlcnZpY2UvcGZtbC1hcGktdGVzdC9lY3MtdGFza3NcIiAtbGV2ZWxuYW1lOkFVRElUIiwiZXZlbnRUeXBlcyI6WyJMb2ciXSwiYWN0aXZlVmlldyI6IlZpZXcgQWxsIExvZ3MiLCJpc0VudGl0bGVkIjp0cnVlLCJhdHRycyI6WyJhd3MubG9nU3RyZWFtIiwibGV2ZWxuYW1lIiwidGltZXN0YW1wIiwibmFtZSIsImZ1bmNOYW1lIiwiYXdzLmxvZ0dyb3VwIiwibWVzc2FnZSJdLCJiZWdpbiI6bnVsbCwiZW5kIjpudWxsfQ==&pane=eyJuZXJkbGV0SWQiOiJsb2dnZXIuaG9tZSIsIiRzZGtWZXJzaW9uIjozfQ==&state=40e1ffea-4230-c73f-5e18-4f1427542446), and you can further filter based on the task name:

```
aws.logStream:*my-new-task-name*
```

##### Viewing start failure reasons

If your task does not start successfully, there will be no logs. Instead, there will be a Slack notification in #mass-pfml-pd-warnings with a description of your error.
