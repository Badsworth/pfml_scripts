#
# FINEOS client - FINEOS implementation.
#

import datetime
import os.path
import urllib.parse
import xml.etree.ElementTree
from typing import Any, Callable, Dict, List, Optional, Union

import defusedxml.ElementTree
import oauthlib.oauth2
import pydantic
import requests
import requests_oauthlib
import xmlschema

import massgov.pfml.util.logging
from massgov.pfml.util.converters.json_to_obj import set_empty_dates_to_none

from . import client, exception, models

logger = massgov.pfml.util.logging.get_logger(__name__)
MILLISECOND = datetime.timedelta(milliseconds=1)

employee_register_request_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "EmployeeRegisterService.Request.xsd")
)


def client_response_json_to_document(response_json: dict) -> models.customer_api.Document:
    # Document effectiveFrom and effectiveTo are empty and set to empty strings
    # These fields are not set by the portal. Set to none to avoid validation errors.
    if response_json["effectiveFrom"] == "":
        response_json["effectiveFrom"] = None

    if response_json["effectiveTo"] == "":
        response_json["effectiveTo"] = None

    return models.customer_api.Document.parse_obj(response_json)


class FINEOSClient(client.AbstractFINEOSClient):
    """FINEOS API client."""

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
        logger.debug("%s %s start", method, url)
        try:
            response = request_function(method, url, timeout=(6.1, 60), headers=headers, **args)
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

    def _customer_api(
        self,
        method: str,
        path: str,
        user_id: str,
        header_content_type: Optional[str] = "application/json",
        **args: Any,
    ) -> requests.Response:
        """Make a request to the Customer API."""
        url = urllib.parse.urljoin(self.customer_api_url, path)
        content_type_header = (
            {} if header_content_type is None else {"Content-Type": header_content_type}
        )
        headers = dict({"userid": user_id}, **content_type_header)
        response = self._request(self.oauth_session.request, method, url, headers, **args)
        return response

    def _wscomposer_request(self, method: str, path: str, xml_data: str) -> requests.Response:
        """Make a request to the Web Services Composer API."""
        url = urllib.parse.urljoin(self.wscomposer_url, path)
        headers = {"Content-Type": "application/xml"}
        return self._request(requests.request, method, url, headers, data=xml_data)

    def find_employer(self, employer_fein: str) -> str:
        response = self._wscomposer_request(
            "GET", "ReadEmployer?userid=CONTENT&param_str_taxId={}".format(employer_fein), ""
        )
        root = defusedxml.ElementTree.fromstring(response.text)
        if len(root) > 0:
            customer_nbr = str(root[0].find("CustomerNo").text)
            return customer_nbr
        else:
            raise exception.FINEOSNotFound("Employer not found.")

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
                        "CustomerNumber": str(employee_registration.customer_number or ""),
                        "DateOfBirth": str(employee_registration.date_of_birth),
                        "Email": employee_registration.email,
                        "EmployeeExternalId": employee_registration.user_id,
                        "EmployerId": employee_registration.employer_id,
                        "FirstName": employee_registration.first_name,
                        "LastName": employee_registration.last_name,
                        "NationalInsuranceNo": employee_registration.national_insurance_no,
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

    def update_customer_details(self, user_id: str, customer: models.customer_api.Customer) -> None:
        """Update customer details."""
        self._customer_api(
            "POST", "customer/updateCustomerDetails", user_id, data=customer.json(exclude_none=True)
        )

    def start_absence(
        self, user_id: str, absence_case: models.customer_api.AbsenceCase
    ) -> models.customer_api.AbsenceCaseSummary:
        logger.info("absence_case %s", absence_case.json(exclude_none=True))
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

        set_empty_dates_to_none(
            json[0], ["accidentDate", "expectedDeliveryDate", "actualDeliveryDate"]
        )

        # Doesn't match OpenAPI file - API returns a single-item list instead of the object.
        return models.customer_api.NotificationCaseSummary.parse_obj(json[0])

    def get_absences(self, user_id: str) -> List[models.customer_api.AbsenceCaseSummary]:
        response = self._customer_api("GET", "customer/absence/absences", user_id)
        json = response.json()
        logger.debug("json %r", json)
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        for item in json:
            set_empty_dates_to_none(item, ["startDate", "endDate"])

        return pydantic.parse_obj_as(List[models.customer_api.AbsenceCaseSummary], json)

    def get_absence(self, user_id: str, absence_id: str) -> models.customer_api.AbsenceDetails:
        response = self._customer_api("GET", f"customer/absence/absences/{absence_id}", user_id)
        return models.customer_api.AbsenceDetails.parse_obj(response.json())

    def get_absence_occupations(
        self, user_id: str, absence_id: str
    ) -> List[models.customer_api.ReadCustomerOccupation]:
        response = self._customer_api("GET", f"customer/cases/{absence_id}/occupations", user_id,)

        json = response.json()
        for item in json:
            set_empty_dates_to_none(item, ["dateJobBegan", "dateJobEnded"])

        return pydantic.parse_obj_as(List[models.customer_api.ReadCustomerOccupation], json)

    def add_payment_preference(
        self, user_id: str, payment_preference: models.customer_api.NewPaymentPreference
    ) -> models.customer_api.PaymentPreferenceResponse:
        response = self._customer_api(
            "POST",
            "customer/addPaymentPreference",
            user_id,
            data=payment_preference.json(exclude_none=True),
        )
        return models.customer_api.PaymentPreferenceResponse.parse_obj(response.json())

    def upload_document(
        self,
        user_id: str,
        absence_id: str,
        document_type: str,
        file_content: bytes,
        file_name: str,
        content_type: str,
        description: str,
    ) -> models.customer_api.Document:
        files = {"documentContents": (file_name, file_content, content_type)}

        data = {"documentDescription": description}

        # fineos upload endpoint returns errors when any Content-Type header value is set
        header_content_type = None

        response = self._customer_api(
            "POST",
            f"customer/cases/{absence_id}/documents/upload/{document_type}",
            user_id,
            header_content_type=header_content_type,
            files=files,
            data=data,
        )

        response_json = response.json()

        return client_response_json_to_document(response_json)

    def get_documents(self, user_id: str, absence_id: str) -> List[models.customer_api.Document]:
        header_content_type = None

        response = self._customer_api(
            "GET",
            f"customer/cases/{absence_id}/documents",
            user_id,
            header_content_type=header_content_type,
        )

        documents = response.json()

        return [client_response_json_to_document(doc) for doc in documents]

    def get_week_based_work_pattern(
        self, user_id: str, occupation_id: Union[str, int],
    ) -> models.customer_api.WeekBasedWorkPattern:

        response = self._customer_api(
            "GET", f"customer/occupations/{occupation_id}/week-based-work-pattern", user_id,
        )

        json = response.json()
        set_empty_dates_to_none(json, ["patternStartDate"])

        return models.customer_api.WeekBasedWorkPattern.parse_obj(json)

    def add_week_based_work_pattern(
        self,
        user_id: str,
        occupation_id: Union[str, int],
        week_based_work_pattern: models.customer_api.WeekBasedWorkPattern,
    ) -> models.customer_api.WeekBasedWorkPattern:

        response = self._customer_api(
            "POST",
            f"customer/occupations/{occupation_id}/week-based-work-pattern",
            user_id,
            data=week_based_work_pattern.json(exclude_none=True),
        )

        json = response.json()
        set_empty_dates_to_none(json, ["patternStartDate"])

        return models.customer_api.WeekBasedWorkPattern.parse_obj(json)

    def update_week_based_work_pattern(
        self,
        user_id: str,
        occupation_id: Union[str, int],
        week_based_work_pattern: models.customer_api.WeekBasedWorkPattern,
    ) -> models.customer_api.WeekBasedWorkPattern:

        response = self._customer_api(
            "POST",
            f"customer/occupations/{occupation_id}/week-based-work-pattern/replace",
            user_id,
            data=week_based_work_pattern.json(exclude_none=True),
        )

        json = response.json()

        return models.customer_api.WeekBasedWorkPattern.parse_obj(json)
