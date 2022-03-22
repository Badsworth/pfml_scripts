#!/usr/bin/env python3
from typing import Iterable

import click


@click.command()
@click.argument("username")
@click.argument("roles", nargs=-1)
def main(username: str, roles: Iterable[str]) -> None:
    print(
        f"""
Add user configuration to /api/massgov/pfml/db/admin.py::create_users, such as:

```
UserConfig(username="{username}", roles={repr(list(roles))}),
```

For deployed environments also need to add an IAM policy to allow the relevant
systems to use the DB user, this is done in /infra/api/template/iam.tf or
/infra/ecs-tasks/template/iam.tf with something like:

```
data "aws_iam_policy_document" "db_user_{username}" {{
  # Policy to allow connection to RDS via IAM database authentication as {username} user
  # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.IAMPolicy.html
  statement {{
    actions = [
      "rds-db:connect"
    ]

    resources = [
      "${{local.iam_db_user_arn_prefix}}/{username}"
    ]
  }}
}}

resource "aws_iam_policy" "db_user_{username}" {{
  name   = "${{local.app_name}}-${{var.environment_name}}-db_user_{username}-policy"
  policy = data.aws_iam_policy_document.db_user_{username}.json
}}

resource "aws_iam_role_policy_attachment" "db_user_{username}_to_<service role>_attachment" {{
  role       = aws_iam_role.<service role>.name
  policy_arn = aws_iam_policy.db_user_{username}.arn
}}
```

If the user will only be used by ECS tasks, the policy declaration can live in
/infra/ecs-tasks/template/iam.tf. If the user will be shared between things in
/infra/api and /infra/ecs-tasks, create the policy in /infra/api/template/iam.tf
and look it up with a data provider in /infra/ecs-tasks/template/iam.tf to
connect to the IAM role/user.
    """
    )


if __name__ == "__main__":
    main()
