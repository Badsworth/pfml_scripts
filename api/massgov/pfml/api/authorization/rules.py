from typing import Any, Callable, List

from bouncer.constants import CREATE, EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.db.models.employees import LkRole, Role, User


def has_role_in(user: User, accepted_roles: List[LkRole]) -> bool:
    accepted_role_ids = set(role.role_id for role in accepted_roles)
    for role in user.roles:
        if role.role_id in accepted_role_ids:
            return True

    return False


def create_authorization(
    enable_employees: bool, enable_employers: bool
) -> Callable[[User, Any], None]:
    def define_authorization(user: User, they: RuleList) -> None:
        # FINEOS endpoint auth
        if has_role_in(user, [Role.FINEOS]):
            financial_eligibility(user, they)
            # TODO: Add auth for /rmv-check https://lwd.atlassian.net/browse/API-628
        else:
            users(user, they)
            applications(user, they)
            documents(user, they)
            leave_admins(user, they)
            if enable_employees:
                employees(user, they)
            if enable_employers:
                employers(user, they)

    return define_authorization


def leave_admins(user: User, they: RuleList) -> None:
    if has_role_in(user, [Role.EMPLOYER]):
        they.can((EDIT, READ), "EMPLOYER_API")


def financial_eligibility(user: User, they: RuleList) -> None:
    they.can(CREATE, "Financial Eligibility Calculation")


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
