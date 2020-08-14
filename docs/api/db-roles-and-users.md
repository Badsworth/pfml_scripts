# Database Users

Access to the database is broken into two parts:
- Roles, which are the permission sets for data access
- Users, what authenticates with the database and are granted Roles

## Roles

Database roles are managed through the migrations (search for `CREATE ROLE` or
`GRANT`/`REVOKE` in the migrations).

Current roles:
- `app`, general purpose role with wide access, automatically granted all
  permissions on any table created in the application schema (currently
  `public`)

## Users

Database users are declared in
[/api/massgov/pfml/db/admin.py](/api/massgov/pfml/db/admin.py) in the
`user_configs` variable, where the list of roles (as created in migrations) they
should have.

For AWS environments, an IAM policy needs to be created and connected to the
systems that should be able to connect as that user.

There is a helper script,
[/api/bin/create-db-user-config.py](/api/bin/create-db-user-config.py), that
will print out the configuration required for adding a new user.

### Local environment

To create the database users locally, run:
```bash
make db-create-users
```

This will create the all users with the password specified by the environment
variable `DB_PASSWORD` (since the actual password doesn't matter in local
development).

### AWS environments

CI will automatically run the `db-admin-create-db-users` task to create users
after migrations on every deploy. So should generally not require manually
action.

But if needed, to run the task manually:
```bash
../../bin/run-ecs-task/run-task.sh <env> db-admin-create-db-users <first name>.<last name>
```

AWS database users use [IAM
authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html)
instead of regular passwords.

High level implications of IAM auth:
- RDS IAM authentication requires connecting to DB over SSL
- DB users needing to authenticate with IAM must be granted the `rds_iam` role
- IAM policy attached to service IAM roles/users allowing connection to DB as
  given user
- Output of the RDS SDK `generate_db_auth_token()` function used as password
  when connecting as user
