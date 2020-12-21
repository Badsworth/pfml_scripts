from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.db.models.employees import Employer
from massgov.pfml.servicenow.factory import create_client
from massgov.pfml.servicenow.transforms.notifications import TransformNotificationRequest


def send_notification_to_service_now(
    notification_request: NotificationRequest, employer: Employer
) -> None:
    transformed_notification_request = TransformNotificationRequest.to_service_now(
        notification_request, employer
    )

    service_now_client = create_client()

    service_now_client.send_message(transformed_notification_request)
