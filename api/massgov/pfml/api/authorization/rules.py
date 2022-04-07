from typing import Callable, Union

from bouncer.constants import CREATE, EDIT, READ  # noqa: F401 F403
from bouncer.models import RuleList
from flask_bouncer import Bouncer  # noqa: F401

from massgov.pfml.api.authentication.azure import AzureUser
from massgov.pfml.api.models.applications.common import DocumentResponse
from massgov.pfml.db.models.applications import (
    Application,
    Document,
    DocumentType,
    Notification,
    RMVCheck,
)
from massgov.pfml.db.models.azure import AzurePermission
from massgov.pfml.db.models.employees import Role, User
from massgov.pfml.util.users import has_role_in


def create_authorization(
    enable_employees: bool,
) -> Callable[[Union[User, AzureUser], RuleList], None]:
    def define_authorization(user: Union[User, AzureUser], they: RuleList) -> None:
        # Admin portal azure authentication/authorization
        if isinstance(user, AzureUser):
            administrator(user, they)

        # FINEOS endpoint auth
        elif has_role_in(user, [Role.FINEOS]):
            financial_eligibility(user, they)
            rmv_check(user, they)
            notifications(user, they)
        elif has_role_in(user, [Role.PFML_CRM]):
            if enable_employees:
                employees(user, they)
        else:
            users(user, they)
            applications(user, they)
            documents(user, they)
            leave_admins(user, they)

    return define_authorization


def administrator(azure_user: AzureUser, they: RuleList) -> None:
    they.can((EDIT, READ), AzureUser, sub_id=azure_user.sub_id)

    for permission in AzurePermission.get_all():
        if permission.azure_permission_id in azure_user.permissions:
            # If user can do something else than READ, they can also READ
            # Deduplicate by first creating a set. Otherwise, the tuple would
            # READ, READ if the action was READ.
            access = tuple({READ, permission.azure_permission_action})
            they.can(access, permission)


def leave_admins(user: User, they: RuleList) -> None:
    if has_role_in(user, [Role.EMPLOYER]):
        they.can(EDIT, "EMPLOYER_API")


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
    if user.is_worker_user:
        regular_user_allowed_doc_types = [
            d.lower()
            for d in [
                DocumentType.APPROVAL_NOTICE.document_type_description,
                DocumentType.REQUEST_FOR_MORE_INFORMATION.document_type_description,
                DocumentType.DENIAL_NOTICE.document_type_description,
                DocumentType.WITHDRAWAL_NOTICE.document_type_description,
                DocumentType.APPEAL_ACKNOWLEDGMENT.document_type_description,
                DocumentType.MAXIMUM_WEEKLY_BENEFIT_CHANGE_NOTICE.document_type_description,
                DocumentType.BENEFIT_AMOUNT_CHANGE_NOTICE.document_type_description,
                DocumentType.LEAVE_ALLOTMENT_CHANGE_NOTICE.document_type_description,
                DocumentType.APPROVED_TIME_CANCELLED.document_type_description,
                DocumentType.CHANGE_REQUEST_APPROVED.document_type_description,
                DocumentType.CHANGE_REQUEST_DENIED.document_type_description,
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
    return None


def applications(user: User, they: RuleList) -> None:
    if user.is_worker_user:
        they.can(CREATE, Application)
    they.can((EDIT, READ), Application, user_id=user.user_id)


def documents(user: User, they: RuleList) -> None:
    they.can(
        CREATE,
        Document,
        lambda d: d.user_id == user.user_id and user.consented_to_data_sharing is True,
    )

    they.can(READ, Document, lambda d: d.user_id == user.user_id and can_download(user, d))

    they.can(READ, DocumentResponse, lambda d: d.user_id == user.user_id and can_download(user, d))


def notifications(user: User, they: RuleList) -> None:
    they.can(CREATE, Notification)
