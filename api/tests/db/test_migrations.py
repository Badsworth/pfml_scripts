from alembic.script import ScriptDirectory
from alembic.script.revision import MultipleHeads
from alembic.util.exc import CommandError

from massgov.pfml.db.migrations.run import alembic_cfg


def test_only_single_head_revision_in_migrations():
    script = ScriptDirectory.from_config(alembic_cfg)

    try:
        # This will raise if there are multiple heads
        script.get_current_head()
        multihead_situation = False
    except CommandError as e:
        # re-raise anything not expected
        if not isinstance(e.__cause__, MultipleHeads):
            raise

        multihead_situation = True

    # raising assertion error here instead of in `except` block to avoid pytest
    # printing the huge stacktrace of the multi-head exception, which in this
    # case we don't really care about the details, just using it as a flag
    if multihead_situation:
        raise AssertionError(
            "See 'Multi-head situations' section of README.md. TL;DR: run `make db-migrate-merge-heads`"
        )


def test_running_migrations_fixture(logging_fix, test_db_via_migrations):
    pass


def test_running_migrations_session_fixture(logging_fix, test_db_session_via_migrations):
    pass
