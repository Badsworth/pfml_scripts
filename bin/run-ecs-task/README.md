This shell script is a wrapper around the `aws ecs run-task` CLI utility that allows running ECS Tasks in the PFML AWS environments.

Beware of PII! ECS Task output will be in the AWS CloudWatch logs. Do not run commands that will potentially reveal PII in the output.

## Requirements

* [terraform](https://www.terraform.io)
* [jq](https://stedolan.github.io/jq)
* [AWS Command Line Interface](https://aws.amazon.com/cli)
* [EOTSS/PFML AWS Account](../../docs/infra/1-first-time-setup.md#Configure-AWS)

Optional:

* [saw](https://github.com/TylerBrock/saw): Fast, multi-purpose tool for AWS CloudWatch Logs

## Usage

* [Authenticate with AWS](../../docs/infra/1-first-time-setup.md#Configure-AWS)
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
* `[command]`: see instructions in the specific ECS Task python file (e.g. [`execute_sql.py`](../../api/massgov/pfml/db/execute_sql.py)) you are running. This can be any of the keys in the `[tool.poetry.scripts]` section of [pyproject.toml](../../api/pyproject.toml) and can include arguments or flags passed to the `[command]`. You can find the accepted arguments or flags by searching the python file for `parser.add_argument`.
* Often the `<ecs-task-name>` and the `[command]` are named the same, but they don't have to be. Multiple commands can use the same task definition
* Sometimes the `run-task.sh` command will timeout. That's ok. It initiates the creation of a container in AWS, but doesn't control it after it is initiated


For example, to run the `execute-sql` command in the test environment:

```sh
./bin/run-ecs-task/run-task.sh test execute-sql <firstname>.<lastname> execute-sql \
    "SELECT COUNT(*) FROM employer" "SELECT * FROM lk_geo_state;"
```

## Container Overrides

You can override specific env vars, settings, etc by making changes to `container_overrides.json.tpl`. If you DO NOT want overrides, make sure to run `git checkout` on the file before executing the `run-task.sh` command.

## Viewing logs

The logs for your ECS task will be sent to Cloudwatch Logs and New Relic. See [Viewing ECS Task Logs](../../docs/infra/4-viewing-ecs-task-logs.md).
