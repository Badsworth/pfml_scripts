# Convenience script for running alembic migration commands through a pyscript
# rather than the command line. This allows poetry to package and alias it for
# running on the production docker image from any directory.
import os

import sqlalchemy
from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration

import massgov.pfml.util.logging
from massgov.pfml.util.sentry import initialize_sentry

logger = massgov.pfml.util.logging.get_logger(__name__)
alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "./alembic.ini"))

# Override the script_location to be absolute based on this file's directory.
alembic_cfg.set_main_option("script_location", os.path.dirname(__file__))


def up(revision="head"):
    initialize_sentry()
    command.upgrade(alembic_cfg, revision)


def down(revision="-1"):
    command.downgrade(alembic_cfg, revision)


def downall(revision="base"):
    command.downgrade(alembic_cfg, revision)


def have_all_migrations_run(db_engine: sqlalchemy.engine.Engine) -> None:
    directory = script.ScriptDirectory.from_config(alembic_cfg)
    with db_engine.begin() as connection:
        context = migration.MigrationContext.configure(connection)
        current_heads = set(context.get_current_heads())
        expected_heads = set(directory.get_heads())

        logger.info(
            "The current migration head is at {} and Alembic is expecting {}".format(
                current_heads, expected_heads
            )
        )

        # Only throw _if_ it's been migrated and doesn't match expectations.
        # Otherwise, don't bother with this - most likely running in a testing environment.
        if current_heads != expected_heads:
            raise Exception(
                "The database schema is not in sync with the migrations. Please verify that the "
                "migrations have been run up to {}; currently at {}".format(
                    expected_heads, current_heads
                )
            )
