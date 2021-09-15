from typing import Any, Callable, List, Union

from bouncer.constants import CREATE, EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.api.models.applications.responses import DocumentResponse
from massgov.pfml.db.models.applications import (
    Application,
    Document,
    DocumentType,
    Notification,
    RMVCheck,
)
from massgov.pfml.db.models.employees import Employee, LkRole, Role, User


def has_role_in(user: User, accepted_roles: List[LkRole]) -> bool:
    accepted_role_ids = set(role.role_id for role in accepted_roles)
    for role in user.roles:
        if role.role_id in accepted_role_ids:
            return True

    return False


def create_authorization(enable_employees: bool) -> Callable[[User, Any], None]:
    def define_authorization(user: User, they: RuleList) -> None:
        # FINEOS endpoint auth
        if has_role_in(user, [Role.FINEOS]):
            financial_eligibility(user, they)
            rmv_check(user, they)
            notifications(user, they)
        else:
            users(user, they)
            applications(user, they)
            documents(user, they)
            leave_admins(user, they)
            if enable_employees:
                employees(user, they)

    return define_authorization


def leave_admins(user: User, they: RuleList) -> None:
    if has_role_in(user, [Role.EMPLOYER]):
        they.can((EDIT, READ), "EMPLOYER_API")


def financial_eligibility(user: User, they: RuleList) -> None:
    they.can(CREATE, "Financial Eligibility Calculation")


def rmv_check(user: User, they: RuleList) -> None:
    they.can(CREATE, RMVCheck)


def can_download(user: User, doc: Union[Document, DocumentResponse]) -> bool:
    # FINEOS users should not be permitted to download.
    if has_role_in(user, [Role.FINEOS]):
        return False

    # Employer users have TBD download permissions.
    if has_role_in(user, [Role.EMPLOYER]):
        return False

    # Regular users can download a limited number of doc types.
    if not user.roles:
        regular_user_allowed_doc_types = [
            d.lower()
            for d in [
                DocumentType.APPROVAL_NOTICE.document_type_description,
                DocumentType.REQUEST_FOR_MORE_INFORMATION.document_type_description,
                DocumentType.DENIAL_NOTICE.document_type_description,
                DocumentType.WITHDRAWAL_NOTICE.document_type_description,
                DocumentType.APPEAL_ACKNOWLEDGMENT.document_type_description,
            ]
        ]

        if (
            isinstance(doc, Document)
            and doc.document_type_instance.document_type_description.lower()
            in regular_user_allowed_doc_types
        ):
            return True

        if (
            isinstance(doc, DocumentResponse)
            and doc.document_type
            and doc.document_type.lower() in regular_user_allowed_doc_types
        ):
            return True

    return False


def users(user: User, they: RuleList) -> None:
    they.can((EDIT, READ), User, user_id=user.user_id)


def employees(user: User, they: RuleList) -> None:
    they.can((READ, EDIT), Employee)


def applications(user: User, they: RuleList) -> None:
    they.can(CREATE, Application)
    they.can((EDIT, READ), Application, user_id=user.user_id)


def documents(user: User, they: RuleList) -> None:
    they.can(
        CREATE,
        Document,
        lambda d: d.user_id == user.user_id and user.consented_to_data_sharing is True,
    )

    they.can(
        READ, Document, lambda d: d.user_id == user.user_id and can_download(user, d),
    )

    they.can(
        READ, DocumentResponse, lambda d: d.user_id == user.user_id and can_download(user, d),
    )


def notifications(user: User, they: RuleList) -> None:
    they.can(CREATE, Notification)
