from bouncer.constants import EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.db.models.employees import User


def define_authorization(user: User, they: RuleList) -> None:
    users(user, they)
    pass


def users(user: User, they: RuleList) -> None:
    they.can((EDIT, READ), "User", user_id=user.user_id)
