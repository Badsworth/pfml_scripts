#
# FINEOS client - FINEOS implementation.
#

import datetime
import os.path
import urllib.parse
import xml.etree.ElementTree
from typing import Any, Callable, Dict, List

import oauthlib.oauth2
import pydantic
import requests
import requests_oauthlib
import xmlschema

import massgov.pfml.util.logging

from . import client, exception, models

logger = massgov.pfml.util.logging.get_logger(__name__)
MILLISECOND = datetime.timedelta(milliseconds=1)

employee_register_request_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "EmployeeRegisterService.Request.xsd")
)


class FINEOSClient(client.AbstractFINEOSClient):
    """FINEOS API client."""

    api_url: str
    wscomposer_url: str
    customer_api_url: str
    request_count: int
    oauth_session: requests_oauthlib.OAuth2Session

    def __init__(self, customer_api_url, wscomposer_url, oauth2_url, client_id, client_secret):
        self.customer_api_url = customer_api_url
        self.wscomposer_url = wscomposer_url
        self.oauth2_url = oauth2_url
        self.request_count = 0
        logger.info("customer_api_url %s, wscomposer_url %s", customer_api_url, wscomposer_url)
        self._init_oauth_session(oauth2_url, client_id, client_secret)

    def _init_oauth_session(self, token_url, client_id, client_secret):
        """Set up an OAuth session and get a token."""
        backend = oauthlib.oauth2.BackendApplicationClient(client_id=client_id)
        session = requests_oauthlib.OAuth2Session(client=backend, scope="service-gateway/all")

        try:
            token = session.fetch_token(
                token_url=token_url, client_id=client_id, client_secret=client_secret, timeout=5,
            )
        except oauthlib.oauth2.OAuth2Error as ex:
            logger.error("POST %s => %r", token_url, ex)
            raise exception.FINEOSClientError(cause=ex)
        except requests.exceptions.RequestException as ex:
            logger.error("POST %s => %r", token_url, ex)
            raise exception.FINEOSClientError(cause=ex)

        logger.info(
            "POST %s => type %s, expires %is (at %s)",
            token_url,
            token["token_type"],
            token["expires_in"],
            datetime.datetime.utcfromtimestamp(token["expires_at"]),
        )
        self.oauth_session = session

    def _request(
        self,
        request_function: Callable[..., requests.Response],
        method: str,
        url: str,
        headers: Dict[str, str],
        **args: Any,
    ) -> requests.Response:
        """Make a request and handle errors."""
        self.request_count += 1
        try:
            response = request_function(method, url, timeout=(3.1, 15), headers=headers, **args)
        except requests.exceptions.RequestException as ex:
            logger.error("%s %s => %r", method, url, ex)
            raise exception.FINEOSClientError(cause=ex)

        if response.status_code != requests.codes.ok:
            logger.warning(
                "%s %s => %s (%ims)",
                method,
                url,
                response.status_code,
                response.elapsed / MILLISECOND,
                extra={"text": response.text},
            )
            raise exception.FINEOSClientBadResponse(requests.codes.ok, response.status_code)

        logger.info(
            "%s %s => %s (%ims)", method, url, response.status_code, response.elapsed / MILLISECOND
        )
        return response

    def _customer_api(self, method: str, path: str, user_id: str, **args: Any) -> requests.Response:
        """Make a request to the Customer API."""
        url = urllib.parse.urljoin(self.customer_api_url, path)
        headers = {"userid": user_id, "Content-Type": "application/json"}
        return self._request(self.oauth_session.request, method, url, headers, **args)

    def _wscomposer_request(self, method: str, path: str, xml_data: str) -> requests.Response:
        """Make a request to the Web Services Composer API."""
        url = urllib.parse.urljoin(self.wscomposer_url, path)
        headers = {"Content-Type": "application/xml"}
        return self._request(requests.request, method, url, headers, data=xml_data)

    def register_api_user(self, employee_registration: models.EmployeeRegistration) -> None:
        """Create the employee account registration."""
        xml_body = self._register_api_user_payload(employee_registration)
        self._wscomposer_request(
            "POST", "webservice?userid=CONTENT&config=EmployeeRegisterService", xml_body
        )

    @staticmethod
    def _register_api_user_payload(employee_registration: models.EmployeeRegistration,) -> str:
        parameters = {
            "@xmlns:p": "http://www.fineos.com/wscomposer/EmployeeRegisterService",
            "config-name": "EmployeeRegisterService",
            "update-data": {
                "EmployeeRegistrationDTO": [
                    {
                        "CustomerNumber": str(employee_registration.customer_number),
                        "DateOfBirth": str(employee_registration.date_of_birth),
                        "Email": employee_registration.email,
                        "EmployeeExternalId": employee_registration.user_id,
                        "EmployerId": str(employee_registration.employer_id),
                        "FirstName": employee_registration.first_name,
                        "LastName": employee_registration.last_name,
                        "NationalInsuranceNo": None,
                    }
                ]
            },
        }
        xml_element = employee_register_request_schema.encode(parameters)
        return xml.etree.ElementTree.tostring(xml_element, encoding="unicode", xml_declaration=True)

    def health_check(self, user_id: str) -> bool:
        """Health check API."""
        response = self._customer_api("GET", "healthcheck", user_id)
        return response.text == "ALIVE"

    def read_customer_details(self, user_id: str) -> models.customer_api.Customer:
        """Read customer details."""
        response = self._customer_api("GET", "customer/readCustomerDetails", user_id)
        return models.customer_api.Customer.parse_obj(response.json())

    def start_absence(
        self, user_id: str, absence_case: models.customer_api.AbsenceCase
    ) -> models.customer_api.AbsenceCaseSummary:
        response = self._customer_api(
            "POST",
            "customer/absence/startAbsence",
            user_id,
            data=absence_case.json(exclude_none=True),
        )
        json = response.json()
        logger.debug("json %r", json)
        new_case = models.customer_api.AbsenceCaseSummary.parse_obj(json)
        logger.info(
            "absence %s, notification case %s", new_case.absenceId, new_case.notificationCaseId
        )
        return new_case

    def complete_intake(
        self, user_id: str, notification_case_id: str
    ) -> models.customer_api.NotificationCaseSummary:
        response = self._customer_api(
            "POST",
            f"customer/absence/notifications/{notification_case_id}/complete-intake",
            user_id,
        )
        json = response.json()
        logger.debug("json %r", json)
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        for prop in ("accidentDate", "expectedDeliveryDate", "actualDeliveryDate"):
            if json[0][prop] == "":
                json[0][prop] = None
        # Doesn't match OpenAPI file - API returns a single-item list instead of the object.
        return models.customer_api.NotificationCaseSummary.parse_obj(json[0])

    def get_absences(self, user_id: str) -> List[models.customer_api.AbsenceCaseSummary]:
        response = self._customer_api("GET", "customer/absence/absences", user_id)
        json = response.json()
        logger.debug("json %r", json)
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        for item in json:
            for prop in ("startDate", "endDate"):
                if item[prop] == "":
                    item[prop] = None
        return pydantic.parse_obj_as(List[models.customer_api.AbsenceCaseSummary], json)

    def get_absence(self, user_id: str, absence_id: str) -> models.customer_api.AbsenceDetails:
        response = self._customer_api("GET", f"customer/absence/absences/{absence_id}", user_id)
        return models.customer_api.AbsenceDetails.parse_obj(response.json())

    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        response = self._customer_api(
            "POST",
            "customer/addPaymentPreference",
            user_id,
            json=payment_preference.json(exclude_none=True),
        )
        return models.customer_api.PaymentPreferenceResponse.parse_obj(response.json())
