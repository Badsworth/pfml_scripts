#
# FINEOS client - FINEOS implementation.
#

import base64
import datetime
import json
import os.path
import urllib.parse
import xml.etree.ElementTree
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import defusedxml.ElementTree
import flask
import newrelic.agent
import oauthlib.oauth2
import pydantic
import requests
import requests_oauthlib
import xmlschema

import massgov.pfml.util.logging
from massgov.pfml.fineos.transforms.to_fineos.eforms import EFormBody
from massgov.pfml.util.converters.json_to_obj import set_empty_dates_to_none

from . import client, exception, models

logger = massgov.pfml.util.logging.get_logger(__name__)
MILLISECOND = datetime.timedelta(milliseconds=1)

employee_register_request_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "EmployeeRegisterService.Request.xsd")
)

update_or_create_party_request_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "UpdateOrCreateParty.Request.xsd")
)

update_or_create_party_response_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "UpdateOrCreateParty.Response.xsd")
)

create_or_update_leave_admin_request_schema = xmlschema.XMLSchema(
    os.path.join(
        os.path.dirname(__file__), "leave_admin_creation", "CreateOrUpdateLeaveAdmin.Request.xsd"
    )
)

service_agreement_service_request_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "ServiceAgreementService.Request.xsd")
)

service_agreement_service_response_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "ServiceAgreementService.Response.xsd")
)


def fineos_document_empty_dates_to_none(response_json: dict) -> dict:
    # Document effectiveFrom and effectiveTo are empty and set to empty strings
    # These fields are not set by the portal. Set to none to avoid validation errors.

    if response_json["effectiveFrom"] == "":
        response_json["effectiveFrom"] = None

    if response_json["effectiveTo"] == "":
        response_json["effectiveTo"] = None

    # Documents uploaded through FINEOS use "dateCreated" instead of "receivedDate"
    if response_json["receivedDate"] == "":
        if response_json["dateCreated"]:
            response_json["receivedDate"] = response_json["dateCreated"]
        else:
            response_json["receivedDate"] = None

    return response_json


class FINEOSClient(client.AbstractFINEOSClient):
    """FINEOS API client."""

    integration_services_api_url: str
    wscomposer_url: str
    group_client_api_url: str
    customer_api_url: str
    request_count: int
    oauth_session: requests_oauthlib.OAuth2Session

    def __init__(
        self,
        integration_services_api_url,
        group_client_api_url,
        customer_api_url,
        wscomposer_url,
        oauth2_url,
        client_id,
        client_secret,
    ):
        self.integration_services_api_url = integration_services_api_url
        self.group_client_api_url = group_client_api_url
        self.customer_api_url = customer_api_url
        self.wscomposer_url = wscomposer_url
        self.oauth2_url = oauth2_url
        self.request_count = 0
        logger.info(
            "customer_api_url %s, wscomposer_url %s, group_client_api_url %s, integration_services_api_url %s",
            customer_api_url,
            wscomposer_url,
            group_client_api_url,
            integration_services_api_url,
        )
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
            has_flask_context = flask.has_request_context()
            response = request_function(method, url, timeout=(6.1, 60), headers=headers, **args)
        except requests.exceptions.RequestException as ex:
            logger.error("%s %s => %r", method, url, ex)
            # Make sure New Relic records errors from FINEOS, even if the API does not ultimately
            # return an error.
            newrelic.agent.record_custom_event(
                "FineosError",
                {
                    "error.class": type(ex).__name__,
                    "error.message": str(ex),
                    "request.method": flask.request.method if has_flask_context else None,
                    "request.uri": flask.request.path if has_flask_context else None,
                    "request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )
            raise exception.FINEOSClientError(cause=ex)

        if response.status_code != requests.codes.ok:
            logger.warning(
                "%s %s => %s (%ims)",
                method,
                url,
                response.status_code,
                response.elapsed / MILLISECOND,
                extra={"response.text": response.text},
            )
            logger.debug(
                "%s %s detail",
                method,
                url,
                extra={"request.headers": headers, "request.args": args},
            )
            # FINEOS returned an error. Record it in New Relic before raising the exception.
            newrelic.agent.record_custom_event(
                "FineosError",
                {
                    "error.class": "FINEOSClientBadResponse",
                    "error.message": response.text,
                    "response.status": response.status_code,
                    "request.method": flask.request.method if has_flask_context else None,
                    "request.uri": flask.request.path if has_flask_context else None,
                    "request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
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
        content_type_header = {"Content-Type": header_content_type} if header_content_type else {}
        headers = dict({"userid": user_id}, **content_type_header)
        response = self._request(self.oauth_session.request, method, url, headers, **args)
        return response

    def _group_client_api(
        self,
        method: str,
        path: str,
        user_id: str,
        header_content_type: Optional[str] = "application/json",
        **args: Any,
    ) -> requests.Response:
        """Make a request to the Group Client API."""
        url = urllib.parse.urljoin(self.group_client_api_url, path)
        content_type_header = {"Content-Type": header_content_type} if header_content_type else {}
        headers = dict({"userid": user_id}, **content_type_header)
        response = self._request(self.oauth_session.request, method, url, headers, **args)
        return response

    def _integration_services_api(
        self,
        method: str,
        path: str,
        user_id: str,
        header_content_type: Optional[str] = "application/xml",
        **args: Any,
    ) -> requests.Response:
        """Make a request to the Integration Services API."""
        url = urllib.parse.urljoin(self.integration_services_api_url, path)
        content_type_header = {"Content-Type": header_content_type} if header_content_type else {}
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

    def get_absence_period_decisions(
        self, user_id: str, absence_id: str
    ) -> models.group_client_api.PeriodDecisions:
        response = self._group_client_api(
            "GET", f"groupClient/absences/absence-period-decisions?absenceId={absence_id}", user_id
        )
        return models.group_client_api.PeriodDecisions.parse_obj(response.json())

    def get_customer_info(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerInfo:
        response = self._group_client_api(
            "GET", f"groupClient/customers/{customer_id}/customer-info", user_id
        )
        json = response.json()
        set_empty_dates_to_none(json, ["dateOfBirth"])

        return models.group_client_api.CustomerInfo.parse_obj(json)

    def get_eform_summary(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.EFormSummary]:
        response = self._group_client_api("GET", f"groupClient/cases/{absence_id}/eforms", user_id)
        json = response.json()
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        for item in json:
            set_empty_dates_to_none(item, ["effectiveDateFrom", "effectiveDateTo"])

        return pydantic.parse_obj_as(List[models.group_client_api.EFormSummary], json)

    def get_eform(
        self, user_id: str, absence_id: str, eform_id: str
    ) -> models.group_client_api.EForm:
        response = self._group_client_api(
            "GET", f"groupClient/cases/{absence_id}/eforms/{eform_id}/readEform", user_id
        )
        return models.group_client_api.EForm.parse_obj(response.json())

    def create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        eform_json = []
        for eformAttribute in eform.eformAttributes:
            cleanedEformAttribute = dict()
            for key, value in dict(eformAttribute).items():
                if value is not None:
                    cleanedEformAttribute[key] = value
            if len(cleanedEformAttribute) > 1:
                eform_json.append(cleanedEformAttribute)

        encoded_eform_type = urllib.parse.quote(eform.eformType)

        self._group_client_api(
            "POST",
            f"groupClient/cases/{absence_id}/addEForm/{encoded_eform_type}",
            user_id,
            data=json.dumps(eform_json),
        )

    def get_case_occupations(
        self, user_id: str, case_id: str
    ) -> List[models.customer_api.ReadCustomerOccupation]:
        response = self._customer_api("GET", f"customer/cases/{case_id}/occupations", user_id,)

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
        file_size = len(file_content)
        encoded_file_contents = base64.b64encode(file_content).decode("utf-8")
        file_name_root, file_extension = os.path.splitext(file_name)

        data = {
            "fileName": file_name_root,
            "fileExtension": file_extension,
            "base64EncodedFileContents": encoded_file_contents,
            "fileSizeInBytes": file_size,
            "description": description,
            "managedReqId": None,
        }

        # ** Temporary debugging code **
        logger.warning(
            "File MD5 - encoded_file_contents",
            extra={"encoded_file_contents": encoded_file_contents},
        )

        response = self._customer_api(
            "POST",
            f"customer/cases/{absence_id}/documents/base64Upload/{document_type}",
            user_id,
            json=data,
        )

        response_json = response.json()

        return models.customer_api.Document.parse_obj(
            fineos_document_empty_dates_to_none(response_json)
        )

    def group_client_get_documents(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.GroupClientDocument]:
        header_content_type = None

        response = self._group_client_api(
            "GET",
            f"groupClient/cases/{absence_id}/documents",
            user_id,
            header_content_type=header_content_type,
        )

        documents = response.json()

        return [
            models.group_client_api.GroupClientDocument.parse_obj(
                fineos_document_empty_dates_to_none(doc)
            )
            for doc in documents
        ]

    def get_documents(self, user_id: str, absence_id: str) -> List[models.customer_api.Document]:
        header_content_type = None

        response = self._customer_api(
            "GET",
            f"customer/cases/{absence_id}/documents",
            user_id,
            header_content_type=header_content_type,
        )

        documents = response.json()

        return [
            models.customer_api.Document.parse_obj(fineos_document_empty_dates_to_none(doc))
            for doc in documents
        ]

    def download_document(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> models.customer_api.Base64EncodedFileData:
        header_content_type = None

        response = self._customer_api(
            "GET",
            f"customer/cases/{absence_id}/documents/{fineos_document_id}/base64Download",
            user_id,
            header_content_type=header_content_type,
        )

        response_json = response.json()
        # populate spec required field missing in fineos response
        if "fileSizeInBytes" not in response_json:
            response_json["fileSizeInBytes"] = len(
                base64.b64decode(response_json["base64EncodedFileContents"].encode("ascii"))
            )

        return models.customer_api.Base64EncodedFileData.parse_obj(response_json)

    def mark_document_as_received(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> None:
        self._customer_api(
            "POST",
            f"customer/cases/{absence_id}/documents/{fineos_document_id}/doc-received-for-outstanding-supporting-evidence",
            user_id,
        )

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

    def create_or_update_leave_admin(
        self, leave_admin_create_or_update: models.CreateOrUpdateLeaveAdmin
    ) -> None:
        """Create or update a leave admin in FINEOS."""
        xml_body = self._create_or_update_leave_admin_payload(leave_admin_create_or_update)
        self._integration_services_api(
            "POST",
            "rest/externalUserProvisioningService/createOrUpdateEmployerViewpointUser",
            "CONTENT",
            data=xml_body,
        )

    def create_or_update_employer(
        self, employer_create_or_update: models.CreateOrUpdateEmployer
    ) -> Tuple[str, int]:
        """Create or update an employer in FINEOS."""
        xml_body = self._create_or_update_employer_payload(employer_create_or_update)
        response = self._wscomposer_request(
            "POST", "webservice?userid=CONTENT&config=UpdateOrCreateParty", xml_body
        )
        response_decoded = update_or_create_party_response_schema.decode(response.text)

        # The value returned in CUSTOMER_NUMBER is the organization's primary key
        # in FINEOS which we store as fineos_employer_id in the employer model.
        fineos_employer_id: dict = next(
            (
                item
                for item in response_decoded["additional-data-set"]["additional-data"]
                if item["name"] == "CUSTOMER_NUMBER"
            ),
            {},
        )

        if fineos_employer_id == {}:
            response_code: dict = next(
                (
                    item
                    for item in response_decoded["additional-data-set"]["additional-data"]
                    if item["name"] == "SERVICE_RESPONSE_CODE"
                ),
                {},
            )
            response_code_value = response_code.get("value")
            validation_msg: dict = next(
                (
                    item
                    for item in response_decoded["additional-data-set"]["additional-data"]
                    if item["name"] == "VALIDATION_MESSAGE"
                ),
                {},
            )
            validation_msg_value = validation_msg.get("value")
            raise exception.FINEOSClientError(
                Exception(
                    f"Employer not created. Response Code: {response_code_value}, {validation_msg_value}"
                )
            )
        else:
            fineos_employer_id_value = fineos_employer_id.get("value")
            logger.info(
                f"Employer ID created is {fineos_employer_id_value} for "
                f"CustomerNo {employer_create_or_update.fineos_customer_nbr}"
            )
            fineos_employer_id_int = int(str(fineos_employer_id_value))

        return employer_create_or_update.fineos_customer_nbr, fineos_employer_id_int

    @staticmethod
    def _create_or_update_leave_admin_payload(
        leave_admin_create_or_update: models.CreateOrUpdateLeaveAdmin,
    ) -> str:
        leave_admin_phone = models.PhoneNumber(
            area_code=leave_admin_create_or_update.admin_area_code,
            contact_number=leave_admin_create_or_update.admin_phone_number,
        )
        leave_admin_create_payload = models.CreateOrUpdateLeaveAdminRequest(
            full_name=leave_admin_create_or_update.admin_full_name,
            party_reference=leave_admin_create_or_update.fineos_employer_id,
            user_id=leave_admin_create_or_update.fineos_web_id,
            email=leave_admin_create_or_update.admin_email,
            phone=leave_admin_phone,
        )
        payload_as_dict = leave_admin_create_payload.dict(by_alias=True)
        xml_element = create_or_update_leave_admin_request_schema.encode(payload_as_dict)
        return xml.etree.ElementTree.tostring(xml_element, encoding="unicode", xml_declaration=True)

    @staticmethod
    def _create_or_update_employer_payload(
        employer_create_or_update: models.CreateOrUpdateEmployer,
    ) -> str:

        organization_default = models.OCOrganisationDefaultItem(
            CustomerNo=employer_create_or_update.fineos_customer_nbr,
            CorporateTaxNumber=employer_create_or_update.employer_fein,
            DoingBusinessAs=employer_create_or_update.employer_dba,
            LegalBusinessName=employer_create_or_update.employer_legal_name,
            Name=employer_create_or_update.employer_legal_name,
        )

        organization_name = models.OCOrganisationNameItem(
            DoingBusinessAs=employer_create_or_update.employer_dba,
            LegalBusinessName=employer_create_or_update.employer_legal_name,
            Name=employer_create_or_update.employer_legal_name,
            organisationWithDefault=models.OCOrganisationWithDefault(
                OCOrganisation=[organization_default]
            ),
        )

        organization = models.OCOrganisationItem(
            CustomerNo=employer_create_or_update.fineos_customer_nbr,
            CorporateTaxNumber=employer_create_or_update.employer_fein,
            DoingBusinessAs=employer_create_or_update.employer_dba,
            LegalBusinessName=employer_create_or_update.employer_legal_name,
            Name=employer_create_or_update.employer_legal_name,
            names=models.OCOrganisationName(OCOrganisationName=[organization_name]),
        )

        party_dto = models.PartyIntegrationDTOItem(
            organisation=models.OCOrganisation(OCOrganisation=[organization])
        )

        employer_create_payload = models.UpdateOrCreatePartyRequest()
        employer_create_payload.update_data = models.UpdateData(PartyIntegrationDTO=[party_dto])

        payload_as_dict = employer_create_payload.dict(by_alias=True)
        xml_element = update_or_create_party_request_schema.encode(payload_as_dict)
        return xml.etree.ElementTree.tostring(xml_element, encoding="unicode", xml_declaration=True)

    def create_service_agreement_for_employer(
        self, fineos_employer_id: int, leave_plans: str
    ) -> str:
        """Create a Service Agreement for an employer in FINEOS."""
        xml_body = self._create_service_agreement_payload(fineos_employer_id, leave_plans)

        response = self._wscomposer_request(
            "POST", "webservice?userid=CONTENT&config=ServiceAgreementService", xml_body
        )
        response_decoded = service_agreement_service_response_schema.decode(response.text)

        # The value returned in CustomerNumber is the organization's primary key
        # in FINEOS which we store as fineos_employer_id in the employer model.
        fineos_customer_nbr: dict = next(
            (
                item
                for item in response_decoded["additional-data-set"]["additional-data"]
                if item["name"] == "CustomerNumber"
            ),
            {},
        )

        if fineos_customer_nbr == {}:
            raise exception.FINEOSClientError(
                Exception(
                    f"Could not create service agreement for FINEOS employer id: {fineos_employer_id}"
                )
            )
        else:
            fineos_customer_nbr_value = fineos_customer_nbr.get("value")

        return str(fineos_customer_nbr_value)

    @staticmethod
    def _create_service_agreement_payload(fineos_employer_id: int, leave_plans: str) -> str:
        fineos_employer_id_data = models.AdditionalData(
            name="CustomerNumber", value=str(fineos_employer_id)
        )
        leave_plans_data = models.AdditionalData(name="LeavePlans", value=leave_plans)

        additional_data_set = models.AdditionalDataSet()
        additional_data_set.additional_data.append(fineos_employer_id_data)
        additional_data_set.additional_data.append(leave_plans_data)

        service_data = models.ServiceAgreementData()
        service_data.additional_data_set = additional_data_set

        service_request = models.ServiceAgreementServiceRequest()
        service_request.update_data = service_data

        payload_as_dict = service_request.dict(by_alias=True)

        xml_element = service_agreement_service_request_schema.encode(payload_as_dict)

        return xml.etree.ElementTree.tostring(xml_element, encoding="unicode", xml_declaration=True)

    def update_reflexive_questions(
        self,
        user_id: str,
        absence_id: Optional[str],
        additional_information: models.customer_api.AdditionalInformation,
    ) -> None:
        """Update reflexive questions."""
        self._customer_api(
            "POST",
            f"customer/absence/{absence_id}/reflexive-questions",
            user_id,
            data=additional_information.json(exclude_none=True),
        )
