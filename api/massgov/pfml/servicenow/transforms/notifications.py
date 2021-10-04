import os
from typing import List

from pydantic import BaseModel, HttpUrl, parse_obj_as

import massgov.pfml.util.logging
from massgov.pfml.api.models.notifications.requests import NotificationRequest, RecipientDetails
from massgov.pfml.api.services.administrator_fineos_actions import LEAVE_ADMIN_INFO_REQUEST_TYPE
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.servicenow.models import Claimant, OutboundMessage, Recipient

logger = massgov.pfml.util.logging.get_logger(__name__)

RECIPIENT_TYPE_MAPPING = {"Leave Administrator": "leave_administrator", "Claimant": "claimant"}

SOURCE_MAPPING = {"Self-Service": "portal", "Call Center": "call_center"}

PORTAL_BASE_URL = os.environ.get("PORTAL_BASE_URL")


def is_leave_administrator(notification_request: NotificationRequest) -> bool:
    return notification_request.recipient_type == "Leave Administrator"


def create_leave_admin_recipient_string(recipient: RecipientDetails) -> str:
    split_name = recipient.full_name.split(" ", 1) if recipient.full_name else []

    return Recipient(
        first_name=split_name[0],
        last_name=split_name[1] if len(split_name) == 2 else "",
        id=recipient.contact_id,
        email=recipient.email_address,
    ).json()


def create_claimant_recipient_string(
    notification_request: NotificationRequest, recipient: RecipientDetails
) -> str:
    return Recipient(
        first_name=recipient.first_name,
        last_name=recipient.last_name,
        id=notification_request.claimant_info.customer_id,
        email=recipient.email_address,
    ).json()


def format_recipients(notification_request: NotificationRequest) -> List[str]:
    if is_leave_administrator(notification_request):
        return [
            create_leave_admin_recipient_string(recipient)
            for recipient in notification_request.recipients
        ]

    return [
        create_claimant_recipient_string(notification_request, recipient)
        for recipient in notification_request.recipients
    ]


def format_link(notification_request: NotificationRequest) -> str:
    if not PORTAL_BASE_URL:
        logger.error("PORTAL_BASE_URL is not set")
        return ""

    if is_leave_administrator(notification_request):
        if notification_request.trigger == LEAVE_ADMIN_INFO_REQUEST_TYPE:
            return f"{PORTAL_BASE_URL}/employers/applications/new-application/?absence_id={notification_request.absence_case_id}"

        return f"{PORTAL_BASE_URL}/employers/applications/status/?absence_id={notification_request.absence_case_id}"

    return f"{PORTAL_BASE_URL}/applications"


def format_document_type(notification_request: NotificationRequest) -> str:
    document_type = getattr(notification_request, "document_type", "") or ""
    return document_type.lower().replace(" ", "_")


class TransformNotificationRequest(BaseModel):
    @classmethod
    def to_service_now(
        cls, notification_request: NotificationRequest, employer: Employer
    ) -> OutboundMessage:
        if not employer.fineos_employer_id:
            raise ValueError(
                "Employer must have a Fineos employer ID to send a ServiceNow notification."
            )
        return OutboundMessage(
            u_absence_id=notification_request.absence_case_id,
            u_document_type=format_document_type(notification_request),
            u_source=SOURCE_MAPPING[notification_request.source],
            u_user_type=RECIPIENT_TYPE_MAPPING[notification_request.recipient_type],
            u_trigger=notification_request.trigger,
            u_link=parse_obj_as(HttpUrl, format_link(notification_request)),
            u_recipients=format_recipients(notification_request),
            u_organization_name=notification_request.organization_name,
            u_employer_customer_number=employer.fineos_employer_id,
            u_claimant_info=Claimant(
                first_name=notification_request.claimant_info.first_name,
                last_name=notification_request.claimant_info.last_name,
                dob=notification_request.claimant_info.date_of_birth.strftime("%m/%d/****"),
                id=notification_request.claimant_info.customer_id,
            ).json(),
        )
