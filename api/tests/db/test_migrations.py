from alembic.script import ScriptDirectory

from massgov.pfml.db.migrations.run import alembic_cfg


def test_only_single_head_revision_in_migrations():
    script = ScriptDirectory.from_config(alembic_cfg)

    # This will raise if there are multiple heads
    script.get_current_head()
