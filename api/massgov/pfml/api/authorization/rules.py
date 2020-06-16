from bouncer.constants import EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.db.models.employees import User


def define_authorization(user: User, they: RuleList) -> None:
    # users(user, they)
    pass


def users(user: User, they: RuleList) -> None:
    if user.consented_to_data_sharing:
        they.can(READ, "User")
        they.can(EDIT, "User")
