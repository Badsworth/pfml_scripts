from typing import Any, Callable

from bouncer.constants import CREATE, EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.db.models.employees import User


def create_authorization(enable_employees: bool) -> Callable[[User, Any], None]:
    def define_authorization(user: User, they: RuleList) -> None:
        users(user, they)
        if enable_employees:
            employees(user, they)

    return define_authorization


def employees(user: User, they: RuleList) -> None:
    they.can((READ, EDIT), "Employee")


def users(user: User, they: RuleList) -> None:
    they.can((EDIT, READ), "User", user_id=user.user_id)
