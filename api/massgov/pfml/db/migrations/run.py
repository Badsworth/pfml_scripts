# Convenience script for running alembic migration commands through a pyscript
# rather than the command line. This allows poetry to package and alias it for
# running on the production docker image from any directory.
import os

from alembic import command
from alembic.config import Config

alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "./alembic.ini"))

# Override the script_location to be absolute based on this file's directory.
alembic_cfg.set_main_option("script_location", os.path.dirname(__file__))


def up(revision="head"):
    command.upgrade(alembic_cfg, revision)


def down(revision="-1"):
    command.downgrade(alembic_cfg, revision)


def downall(revision="base"):
    command.downgrade(alembic_cfg, revision)
