# Database Migrations

With zero-downtime deploys and long running background tasks, multiple versions
of application code can be running the same time. This means shared resources,
like the database must account for this and database migrations must be created
thoughtfully.

At a high-level, this generally means database changes need to be broken up:

1. A release with preparatory database migration and code changes
2. Once everything is running that release (or later), the next release can
   include the cleanup/finalization database migration and code changes.

Every database change must be compatible with the previous and next versions of
application code when it's released.

## Add a column with non-null default

With PostgreSQL >= 11 this can generally be done without a problem. The only
case that needs care are new columns that use "volatile" functions for defaults.
A volatile function can be considered anything that returns a different value
every time it is called.

For example, `current_timestamp`/`now` are fine to use as they return the same
value within a given transaction. But `gen_uuid_random` is not safe to use, as
it returns a different value every time it is called.

Adding a new non-null column whose default is a volatile function will trigger
an exclusive lock on the table until all the existing columns are backfilled.

If a new non-null column needs to be added to a table with a volatile default,
it should be split across two releases:

1. Release 1
   - Add new column, defaulting to null
   - Update code to populate value with default if missing (covering new rows)
2. After release 1, run script to backfill existing rows
   - This would could mean packaging something up as an ECS task to trigger
   - Simpler backfills may be accomplished via execute-sql
3. Release 2
   - Add non-null constraint and proper default
   - Update code to make use of column for needed non-null use cases

## Remove a column

1. Release 1
   - Update model, marking column(s) that will be removed with `deferred()` function
   - Update application code to not reference the column to be removed
2. Release 2
   - Migration to drop the column

https://docs.sqlalchemy.org/en/14/orm/loading_columns.html#deferred-column-loading

Use the `deferred()` function on the column so it is only loaded when explicitly requested.

```python
from sqlalchemy.orm import deferred
from sqlalchemy import Integer, String, Text, Binary, Column

class Book(Base):
    __tablename__ = 'book'

    book_id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    summary = Column(String(2000))
    excerpt = deferred(Column(Text))
    photo = deferred(Column(Binary))
```

## Rename a column

1. Release 1
   - Migration to backfill new column with old column value
   - Update code to read from both columns (preferring new column)
   - Update code to write to new column
2. Release 2
   - Update model, marking columns that will be removed with `deferred()` function
   - Migration to backfill new column with old column value
   - Update application code to not reference the column to be removed
3. Release 3
   - Migration to drop the column

Or

1. Release 1
   - Update code to write to both columns (code still reads from old column)
2. Release 2
   - Update model, marking columns that will be removed with `deferred()` function
   - Migration to backfill new column with old column value
   - Update application code to not reference the column to be removed (only read/write to new column)
3. Release 3
   - Migration to drop the column
