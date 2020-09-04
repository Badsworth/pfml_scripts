from typing import Any, Callable

from bouncer.constants import CREATE, EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.db.models.employees import User


def create_authorization(
    enable_employees: bool, enable_employers: bool
) -> Callable[[User, Any], None]:
    def define_authorization(user: User, they: RuleList) -> None:
        users(user, they)
        applications(user, they)
        documents(user, they)
        if enable_employees:
            employees(user, they)
        if enable_employers:
            employers(user, they)

    return define_authorization


def users(user: User, they: RuleList) -> None:
    they.can((EDIT, READ), "User", user_id=user.user_id)


def employers(user: User, they: RuleList) -> None:
    they.can((EDIT, READ), "Employer")


def employees(user: User, they: RuleList) -> None:
    they.can((READ, EDIT), "Employee")


def applications(user: User, they: RuleList) -> None:
    they.can(CREATE, "Application")
    they.can((EDIT, READ), "Application", user_id=user.user_id)


def documents(user: User, they: RuleList) -> None:
    they.can(
        CREATE,
        "Document",
        lambda d: d.user_id == user.user_id and user.consented_to_data_sharing is True,
    )
