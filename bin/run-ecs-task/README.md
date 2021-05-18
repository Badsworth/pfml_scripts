This shell script is a wrapper around the `aws ecs run-task` CLI utility that allows running ECS Tasks in the PFML AWS environments.

Beware of PII! ECS Task output will be in the AWS CloudWatch logs. Do not run commands that will potentially reveal PII in the output.

## Requirements

* [AWS Command Line Interface](https://aws.amazon.com/cli)
* [EOTSS/PFML AWS Account](../../infra/README.md#eotsspfml-aws-account)

Optional:

* [saw](https://github.com/TylerBrock/saw): Fast, multi-purpose tool for AWS CloudWatch Logs

## Usage

1. [Authenticate with Centrify](../../infra/README.md#eotsspfml-aws-account)
2. Run the `run-task.sh` shell script:

```bash
./bin/run-ecs-task/run-task.sh <env> <ecs-task-name> <firstname>.<lastname> [command]
```

Notes:

* `<env>` can be: `test`, `stage` or `prod`
* `<ecs-task-name>` can be any of the keys in the `[tool.poetry.scripts]` section of [pyproject.toml](../../api/pyproject.toml)
* Pass in your `<firstname>.<lastname>`. This is shown in the AWS CloudWatch logs as the person running the ECS Task
* `command`: see instructions in the specific ECS Task python file (e.g. [`execute_sql.py`](../../api/massgov/pfml/db/execute_sql.py)) you are running
