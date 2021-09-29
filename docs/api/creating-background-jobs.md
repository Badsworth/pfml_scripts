# Creating Background Jobs

1. Create Python module for job somewhere under `massgov/pfml/` (location as appropriate)
1. Create `pyproject.toml` script entry for module (in `[tool.poetry.scripts]` section)
1. Create ECS Task definition in `infra/ecs-tasks/template/tasks.tf`. See
   comment at top of `tasks.tf` for more info.
   1. Task name should match `pyproject.toml` script name
   1. Set environment variables (utilizing groups from `task_config.tf` as appropriate)
   1. Create dedicated IAM role in `iam.tf` if necessary and set `task_role`
      parameter to it
1. If this task will be running automatically, add new task to alarms list,
   `infra/modules/alarms_api/alarms-aws.tf`
1. Add default development environment variables task might need to
   `api/config/local.env`
1. [Optional] Add recipe to run script to `api/Makefile`

## Automatic job triggers

Currently supported ways of automatically triggering a job:
- Time based
- S3 event

### Time based

Add entry to `infra/ecs-tasks/template/cloudwatch.tf`

If needing to sequence a series of jobs, can look at AWS Step Functions,
currently used to orchestrate the DOR-FINEOS ETL pipeline at
`infra/ecs-tasks/template/step_functions.tf` and
`infra/ecs-tasks/template/step_function/dor_fineos_etl.json`.

### S3 event

Add entry to `infra/ecs-tasks/template/s3_subscriptions.tf`.

There are some limitations to this, as noted in the terraform module:

> # NOTE: There can only be one S3 bucket notification resource per bucket.

## Configurable behavior

### Environment Variables

Use environment variables for configuration that is specific to a particular
application environment (e.g., `test`, `stage`, etc.).

For example:
- S3 locations (typically there are different S3 buckets configured for each environment)
- Service credentials and locations

### CLI Arguments

Use CLI Arguments for things that might want to be configured at runtime.

Tasks currently use the [argparse module from the Python standard
library](https://docs.python.org/3/library/argparse.html) for this.

## Code Templates

### Basic setup

```python
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = logging.get_logger(__name__)


# The PydanticBaseSettings class will automatically load values from environment
# variables matching the field names, as well as loading `api/config/local.env`.
class MyTaskConfig(PydanticBaseSettings):
    configurable_behavior: str
    # add to imports: from pydantic import Field
    # configurable_behavior_with_specific_env_var_name: str = Field(..., env="SPECIAL_ENV_VAR_NAME")
    optional_config: Optional[int] = None
    config_that_has_a_default: int = 5


@background_task("my-task")
def main():
    # do any CLI args parsing

    # potentially set configuration parameters with CLI args
    config = MyTaskConfig()

    # create any other serivce clients

    with db.session_scope(db.init(), close=True) as db_session:
        # call code to perform task
```


### Combined environment variables and CLI arguments

```python
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = logging.get_logger(__name__)


class MyTaskConfig(PydanticBaseSettings):
    configurable_behavior: str
    # add to imports: from pydantic import Field
    # configurable_behavior_with_specific_env_var_name: str = Field(..., env="SPECIAL_ENV_VAR_NAME")
    optional_config: Optional[int] = None
    config_that_has_a_default: int = 5


def get_config(input_args: List[str]):
    parser = argparse.ArgumentParser(
        description="Retrieve and process payment files from agencies and/or generate report files for agencies"
    )
    parser.add_argument("foo")

    args = parser.parse_args(input_args)

    # potentially set configuration parameters with `args`
    config = MyTaskConfig(configurable_behavior=args.foo)

    # may want to dynamically set config based on optional arguments
    # if args.whatever:
    #     config.config_that_has_a_default = args.whatever

    return config


@background_task("my-task")
def main():
    config = get_config(sys.argv[1:])

    # create any other serivce clients

    with db.session_scope(db.init(), close=True) as db_session:
        # call code to perform task
```


### Using `LogEntry`

```python
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = logging.get_logger(__name__)


class MyTaskConfig(PydanticBaseSettings):
    configurable_behavior: str
    # add to imports: from pydantic import Field
    # configurable_behavior_with_specific_env_var_name: str = Field(..., env="SPECIAL_ENV_VAR_NAME")
    optional_config: Optional[int] = None
    config_that_has_a_default: int = 5


@background_task("my-task")
def main():
    # do any CLI args parsing

    # potentially set configuration parameters with CLI args
    config = MyTaskConfig()

    # create any other serivce clients

    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with LogEntry(log_entry_db_session, "My Batch Job Name") as log_entry:
            # call code to perform task, passing in `log_entry`
            #
            # log_entry.increment("my_super_metric")
            # log_entry.set_metrics({"the_file": filename})
```
