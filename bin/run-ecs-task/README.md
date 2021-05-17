This shell script is a wrapper around the `aws ecs run-task` CLI utility that allows running ECS Tasks in the PFML AWS environments.

Beware of PII! ECS Task output will be in the AWS CloudWatch logs. Do not run commands that will potentially reveal PII in the output.

## Requirements

* [terraform](https://www.terraform.io)
* [jq](https://stedolan.github.io/jq)
* [AWS Command Line Interface](https://aws.amazon.com/cli)
* [EOTSS/PFML AWS Account](../../infra/README.md#eotsspfml-aws-account)

Optional:

* [saw](https://github.com/TylerBrock/saw): Fast, multi-purpose tool for AWS CloudWatch Logs

## Usage

1. [Authenticate with Centrify](../../infra/README.md#eotsspfml-aws-account)
2. Initialize terraform for the environment you want to run the ECS task in

```sh
cd infra/ecs-tasks/environments/test
terraform init
```

3. Run the `run-task.sh` shell script:

```sh
./bin/run-ecs-task/run-task.sh <env> <ecs-task-name> <firstname>.<lastname> [command]
```

Notes:

* `<env>`: a PFML environment, such as `test`, `stage`, `prod`, etc
* `<ecs-task-name>`: a task defined in [infra/ecs-tasks/template/tasks.tf](../../infra/ecs-tasks/template/tasks.tf)
* Pass in your `<firstname>.<lastname>`. This is shown in the AWS CloudWatch logs as the person running the ECS Task
* `[command]`: see instructions in the specific ECS Task python file (e.g. [`execute_sql.py`](../../api/massgov/pfml/db/execute_sql.py)) you are running. This can be any of the keys in the `[tool.poetry.scripts]` section of [pyproject.toml](../../api/pyproject.toml) and can include arguments or flags passed to the `[command]`
* Often the `<ecs-task-name>` and the `[command]` are named the same, but they don't have to be. Multiple commands can use the same task definition
* Sometimes the `run-task.sh` command will timeout. That's ok. It initiates the creation of a container in AWS, but doesn't control it after it is initiated

For example, to run the `execute-sql` command in the test environment:

```sh
./bin/run-ecs-task/run-task.sh test execute-sql <firstname>.<lastname> execute-sql \
    "SELECT COUNT(*) FROM employer" "SELECT * FROM lk_geo_state;"
```


## Container Overrides

You can override specific env vars, settings, etc by making changes to `container_overrides.json.tpl`. If you DO NOT want overrides, make sure to run `git checkout` on the file before executing the `run-task.sh` command.

## Using with `saw`

If you want to use `saw` to tail logs on the CLI while running tasks, use:

```sh
saw watch --raw <aws cloudwatch log group> | python3 massgov/pfml/util/logging/decodelog.py

# For example, this will show all the logs for ECS tasks in the Test environment:
saw watch --raw service/pfml-api-test/ecs-tasks | python3 massgov/pfml/util/logging/decodelog.py
```

