# Database Migrations

- [Running migrations](#running-migrations)
- [Creating new migrations](#creating-new-migrations)
- [Multi-head situations](#multi-head-situations)
- [Deployment](#deployment)
  - [Removing a column](#removing-a-column)
  - [Removing a table](#removing-a-table)

## Running migrations

When you're first setting up your environment, ensure that migrations are run
against your db so it has all the required tables. `make init` does this, but if
needing to work with the migrations directly, some common commands:

```sh
make db-upgrade       # Apply pending migrations to db
make db-downgrade     # Rollback last migration to db
make db-downgrade-all # Rollback all migrations
```

## Creating new migrations

If you've changed a python object model, auto-generate a migration file for the database and run it:

```sh
$ make db-migrate-create MIGRATE_MSG="<brief description of change>"
$ make db-upgrade
```

<details>
    <summary>Example: Adding a new column to an existing table:</summary>

1. Manually update the database models with the changes (`massgov/pfml/db/models/employees.py` in this example)
```python
class Address(Base):
    ...
    created_at = Column(TIMESTAMP(timezone=True)) # Newly added line
```

2. Automatically generate a migration file with `make db-migrate-create MIGRATE_MSG="Add created_at timestamp to address table"`
```python
...
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("address", sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("address", "created_at")
    # ### end Alembic commands ###
```

3. Manually adjust the migration file as needed. Some changes will not fully auto-generate (like foreign keys), so make sure that all desired changes are included.
</details>

## Multi-head situations

Alembic migrations form an ordered history, with each migration having at least
one parent migration as specified by the `down_revision` variable. This can be
visualized by:

```sh
make db-migrate-history
```

When multiple migrations are created that point to the same `down_revision` a
branch is created, with the tip of each branch being a "head". The above history
command will show this, but a list of just the heads can been retrieved with:

```sh
make db-migrate-heads
```

CI/CD runs migrations to reach the "head". When there are multiple, Alembic
can't resolve which migrations need to be run. If you run into this error,
you'll need to fix the migration branches/heads before merging to `main`.

If the migrations don't depend on each other, which is likely if they've
branched, then you can just run:

``` sh
make db-migrate-merge-heads
```

Which will create a new migration pointing to all current "head"s, effectively
pulling them all together.

When branched migrations do need to happen in a defined order, then manually
update the `down_revision` of one that should happen second to reference to the
migration that should happen first.

## Deployment
Our deployment is a two-step process:

1. Run database migrations, which will update table schemas.
2. Update API code.

Since we're updating two independent services, we should consider how code changes across the API and database might cause integration issues during rollout (similar to code changes across the portal and api).

Part of the reason DB migrations run before app deploys (instead of after) is so that additions don???t need to be split out, i.e. migrations that add columns for new features don???t need delayed treatment. A new column can be added to the DB before the app code using it is deployed so they can go out in the same commit/release.

However, if we are removing a column or table from the DB, we need to split this across two deploys. Otherwise, the app is likely to break, since in between steps 1 & 2 above, the app may try to access a table or column that no longer exists in our databse.

### Removing a column

**First Deploy**

In order to remove a column, we'll first need to remove all usage of the column in the API code base. 

However, since the column will still be in the database model, SQLAlchemy will still include it in `SELECT`s and `INSERT`s for the table. We'll need to set this column to `deferred`, in order to exclude it from queries, and to `evaluates_none`, to stop inserting null for it. We have a function `deprecated_column` that handles both of those changes, so we can easily make this change by updating `column_to_remove = Column(...)` to `column_to_remove = deprecated_column(...)`.

**Second Deploy**

Once the column usage removal has been deployed (including deprecating the column in the database model), we can safely remove the column from the database model and the actual database. To do so, simply delete the deprecated column from the database model and create a corresponding database migration.

### Removing a table

**First Deploy**

Removing a table is similar to, but simpler than, removing a column. You'll still start by removing all usage of the table in the API code base. No further steps are required at this point, since SQLAlchemy won't be interacting with the table at this point.

**Second Deploy**

Once the table usage removal has been deployed, we can safely remove the table from the database model and the actual database. Again, simply delete the table from the database model and create a corresponding migration.