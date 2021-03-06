# Convenience script for running alembic migration commands through a pyscript
# rather than the command line. This allows poetry to package and alias it for
# running on the production docker image from any directory.
import itertools
import os
from typing import List

import sqlalchemy
from alembic import command, script
from alembic.config import Config
from alembic.operations.ops import MigrationScript
from alembic.runtime import migration

import massgov.pfml.util.logging
from massgov.pfml.util.bg import background_task

logger = massgov.pfml.util.logging.get_logger(__name__)
alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "./alembic.ini"))

# Override the script_location to be absolute based on this file's directory.
alembic_cfg.set_main_option("script_location", os.path.dirname(__file__))


@background_task("db-migrate-up")
def up(revision="head"):
    command.upgrade(alembic_cfg, revision)


@background_task("db-migrate-down")
def down(revision="-1"):
    command.downgrade(alembic_cfg, revision)


@background_task("db-migrate-downall")
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


def check_model_parity() -> None:
    revisions: List[MigrationScript] = []

    def process_revision_directives(context, revision, directives):
        nonlocal revisions
        revisions = list(directives)
        # Prevent actually generating a migration
        directives[:] = []

    command.revision(
        config=alembic_cfg,
        autogenerate=True,
        process_revision_directives=process_revision_directives,
    )
    diff = list(
        itertools.chain.from_iterable(
            op.as_diffs() for script in revisions for op in script.upgrade_ops_list
        )
    )

    message = (
        "The application models are not in sync with the migrations. You should generate "
        "a new automigration or update your local migration file. "
        "If there are unexpected errors you may need to merge main into your branch."
    )

    if diff:
        for line in diff:
            print("::error title=Missing migration::Missing migration:", line)

        logger.error(message, extra={"issues": str(diff)})
        raise Exception(message)
