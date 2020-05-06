import sys
from logging.config import fileConfig

from alembic import context

# Alembic cli seems to reset the path on load causing issues with local module imports.
# Workaround is to force set the path to the current run directory (top level api folder)
# See database migrations section in `api/README.md` for details about running migrations.
sys.path.insert(0, ".")  # noqa: E402

import massgov.pfml.db as db  # isort:skip
from massgov.pfml.db.models.base import Base  # isort:skip

# import models module to trigger loading of all modules into the Base
import massgov.pfml.db.models  # noqa: F401 isort:skip

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

if not config.get_main_option("sqlalchemy.url"):
    uri = db.get_connection_uri()

    config.set_main_option("sqlalchemy.url", uri)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    url = config.get_main_option("sqlalchemy.url")
    connectable = db.create_engine(url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
