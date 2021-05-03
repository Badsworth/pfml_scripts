#
# FINEOS client - FINEOS implementation.
#

import base64
import datetime
import json
import os.path
import urllib.parse
import xml.etree.ElementTree
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

import flask
import newrelic.agent
import oauthlib.oauth2
import pydantic
import requests
import xmlschema

import massgov.pfml.util.logging
from massgov.pfml.fineos.transforms.to_fineos.base import EFormBody
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

occupation_detail_update_service_request_schema = xmlschema.XMLSchema(
    os.path.join(
        os.path.dirname(__file__), "wscomposer", "OccupationDetailUpdateService.Request.xsd"
    )
)

read_employer_response_schema = xmlschema.XMLSchema(
    os.path.join(os.path.dirname(__file__), "wscomposer", "ReadEmployer.Response.xsd")
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


def get_fineos_correlation_id(response: requests.Response) -> Optional[Any]:
    try:
        response_payload_json = response.json()
        if isinstance(response_payload_json, dict):
            return response_payload_json.get("correlationId", "")
    except ValueError:
        pass

    return None


class FINEOSClient(client.AbstractFINEOSClient):
    """FINEOS API client."""

    integration_services_api_url: str
    group_client_api_url: str
    customer_api_url: str
    wscomposer_url: str
    wscomposer_user_id: str
    oauth2_url: str
    client_id: str
    client_secret: str
    request_count: int
    oauth_session: Any

    def __init__(
        self,
        integration_services_api_url,
        group_client_api_url,
        customer_api_url,
        wscomposer_url,
        wscomposer_user_id,
        oauth2_url,
        client_id,
        client_secret,
        oauth_session,
    ):
        self.integration_services_api_url = integration_services_api_url
        self.group_client_api_url = group_client_api_url
        self.customer_api_url = customer_api_url
        self.wscomposer_url = wscomposer_url
        self.wscomposer_user_id = wscomposer_user_id
        self.oauth2_url = oauth2_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_session = oauth_session
        self.request_count = 0
        logger.info(
            "customer_api_url %s, wscomposer_url %s, group_client_api_url %s, "
            "integration_services_api_url %s",
            customer_api_url,
            wscomposer_url,
            group_client_api_url,
            integration_services_api_url,
        )
        self._init_oauth_session()

    def _init_oauth_session(self):
        """Set up an OAuth session and get a token."""
        try:
            token = self.oauth_session.fetch_token(
                token_url=self.oauth2_url,
                client_id=self.client_id,
                client_secret=self.client_secret,
                timeout=5,
            )
        except (
            oauthlib.oauth2.OAuth2Error,
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
        ) as ex:
            self._handle_client_side_exception("POST", self.oauth2_url, ex)

        logger.info(
            "POST %s => type %s, expires %is (at %s)",
            self.oauth2_url,
            token["token_type"],
            token["expires_in"],
            datetime.datetime.utcfromtimestamp(token["expires_at"]),
        )

    def _handle_client_side_exception(self, method: str, url: str, ex: Exception) -> None:
        # Make sure New Relic records errors from FINEOS, even if the API does not ultimately
        # return an error.
        has_flask_context = flask.has_request_context()
        newrelic.agent.record_custom_event(
            "FineosError",
            {
                "fineos.error.class": type(ex).__name__,
                "fineos.error.message": str(ex),
                "fineos.request.method": method,
                "fineos.request.uri": url,
                "api.request.method": flask.request.method if has_flask_context else None,
                "api.request.uri": flask.request.path if has_flask_context else None,
                "api.request.headers.x-amzn-requestid": flask.request.headers.get(
                    "x-amzn-requestid", None
                )
                if has_flask_context
                else None,
            },
        )

        if isinstance(ex, requests.exceptions.Timeout) or isinstance(
            ex, oauthlib.oauth2.TemporarilyUnavailableError
        ):
            logger.warning("%s %s => %r", method, url, ex)
            raise exception.FINEOSFatalUnavailable(cause=ex)
        else:
            logger.exception("%s %s => %r", method, url, ex)
            raise exception.FINEOSFatalClientSideError(cause=ex)

    def _request(
        self, method: str, url: str, headers: Dict[str, str], **args: Any,
    ) -> requests.Response:
        """Make a request and handle errors."""
        self.request_count += 1
        has_flask_context = flask.has_request_context()
        logger.debug("%s %s start", method, url)

        # Increase the timeout drastically. Past 29 seconds, FINEOS returns a 504
        # timeout, so the request client is really just waiting until the last second.
        #
        # Note that this is longer than our API Gateway timeout (also 29 seconds),
        # so it's very plausible that a request times out on the API Gateway side,
        # especially for application submission since /complete-intake is long and
        # there are other calls to the claims processing system (CPS) included in submission.
        #
        # However, we're allowing the request to complete on the API (as long as it's under 29s)
        # even if the response never makes it to the claimant, to try and ensure a consistent
        # CPS <--> Paid Leave API state and prevent additional long calls when the claimant retries.
        #
        request_timeout = 29

        try:
            try:
                response = self.oauth_session.request(
                    method, url, timeout=(6.1, request_timeout), headers=headers, **args
                )
            except oauthlib.oauth2.TokenExpiredError:
                logger.info("token expired, starting new OAuth session")
                self._init_oauth_session()
                response = self.oauth_session.request(
                    method, url, timeout=(6.1, request_timeout), headers=headers, **args
                )
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as ex:
            self._handle_client_side_exception(method, url, ex)

        if response.status_code != requests.codes.ok:

            # Try to parse correlation ID as metadata from the response.
            fineos_correlation_id = get_fineos_correlation_id(response)

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
                    "fineos.error.class": "FINEOSClientBadResponse",
                    "fineos.error.correlation_id": fineos_correlation_id,
                    "fineos.error.message": response.text,
                    "fineos.response.status": response.status_code,
                    "fineos.request.method": method,
                    "fineos.request.uri": url,
                    "fineos.request.response_millis": response.elapsed / MILLISECOND,
                    "api.request.method": flask.request.method if has_flask_context else None,
                    "api.request.uri": flask.request.path if has_flask_context else None,
                    "api.request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )

            err: exception.FINEOSClientError

            if (
                response.status_code
                in (requests.codes.SERVICE_UNAVAILABLE, requests.codes.GATEWAY_TIMEOUT,)
                or "ESOCKETTIMEDOUT" in response.text
            ):
                # The service is unavailable for some reason. Log a warning and don't tell sentry -- there should be a
                # percentage-based alarm for when there are too many of these.
                #
                # Ideally we would never get GATEWAY_TIMEOUT and would instead always keep our client-side timeout lower than the
                # FINEOS 29s timeout; however, the program has requested that we keep them as high as possible. We should still
                # manage them the same as a client-side timeout exception.
                err = exception.FINEOSFatalUnavailable(
                    response_status=response.status_code, message=response.text
                )
                log_fn = logger.warning
            elif response.status_code in (
                requests.codes.UNPROCESSABLE_ENTITY,
                requests.codes.NOT_FOUND,
                requests.codes.FORBIDDEN,
            ):
                # Ideally we'd raise exceptions that distinguish between 403/404/422 but we'll leave that for another time.
                err = exception.FINEOSClientBadResponse(
                    requests.codes.ok, response.status_code, message=response.text
                )
                log_fn = logger.warning
            else:
                # We should never see anything other than these. Log an error and notify Sentry if we do. These include issues
                # like 400 BAD REQUEST (misformatted request), 500 INTERNAL SERVER ERROR, and 413 SIZE TOO LARGE.
                err = exception.FINEOSFatalResponseError(
                    response_status=response.status_code, message=response.text
                )
                log_fn = logger.error

            log_fn(
                "%s %s => %s (%ims)",
                method,
                url,
                response.status_code,
                response.elapsed / MILLISECOND,
                extra={
                    "response.text": response.text,
                    "response.fineos_correlation_id": fineos_correlation_id,
                },
                exc_info=err,
            )

            raise err

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
        response = self._request(method, url, headers, **args)
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
        response = self._request(method, url, headers, **args)
        return response

    def _integration_services_api(
        self,
        method: str,
        path: str,
        user_id: str,
        header_content_type: Optional[str] = "application/xml; charset=utf-8",
        **args: Any,
    ) -> requests.Response:
        """Make a request to the Integration Services API."""
        url = urllib.parse.urljoin(self.integration_services_api_url, path)
        content_type_header = {"Content-Type": header_content_type} if header_content_type else {}
        headers = dict({"userid": user_id}, **content_type_header)
        response = self._request(method, url, headers, **args)
        return response

    def _wscomposer_request(
        self, method: str, path: str, query: Mapping[str, str], xml_data: str
    ) -> requests.Response:
        """Make a request to the Web Services Composer API."""
        query_with_user_id = dict(query)
        query_with_user_id["userid"] = self.wscomposer_user_id
        path_with_query = path + "?" + urllib.parse.urlencode(query_with_user_id)
        url = urllib.parse.urljoin(self.wscomposer_url, path_with_query)
        headers = {"Content-Type": "application/xml; charset=utf-8"}
        return self._request(method, url, headers, data=xml_data.encode("utf-8"))

    def read_employer(self, employer_fein: str) -> models.OCOrganisation:
        """Retrieves FINEOS employer info given an FEIN.

        Raises
        ------
        FINEOSNotFound
            If no employer exists in FINEOS that matches the given FEIN.
        """
        response = self._wscomposer_request(
            "GET", "ReadEmployer", {"param_str_taxId": employer_fein}, ""
        )
        response_decoded = read_employer_response_schema.decode(response.text)

        if "OCOrganisation" not in response_decoded:
            raise exception.FINEOSNotFound("Employer not found.")

        return models.OCOrganisation.parse_obj(response_decoded)

    def find_employer(self, employer_fein: str) -> str:
        """Retrieves the FINEOS customer number for an employer given an FEIN.

        Raises
        ------
        FINEOSNotFound
            If no employer exists in FINEOS that matches the given FEIN.
        """
        employer_response = self.read_employer(employer_fein)

        customer_nbr = str(employer_response.OCOrganisation[0].CustomerNo)
        return customer_nbr

    def register_api_user(self, employee_registration: models.EmployeeRegistration) -> None:
        """Creates the employee account registration.

        Raises
        ------
        FINEOSNotFound
            If no employee-employer combination exists in FINEOS
            that matches the given SSN + employer FEIN.
        """
        xml_body = self._register_api_user_payload(employee_registration)

        try:
            self._wscomposer_request(
                "POST", "webservice", {"config": "EmployeeRegisterService"}, xml_body
            )
        except exception.FINEOSFatalResponseError as err:
            # Expected 500 errors. See #3 and #7 here:
            # https://lwd.atlassian.net/wiki/spaces/DD/pages/874905740/FINEOS+error+responses
            #
            # Although #2 (More than One Employee Details Found) is possible here,
            # we want to let it bubble up and raise so that it can be triaged.
            if err.response_status == 500 and (
                "The employee does not have an occupation linked" in err.message  # noqa: B306
                or "No Employee Details" in err.message  # noqa: B306
            ):
                raise exception.FINEOSNotFound(err.message)  # noqa: B306

            # If not an expected error, bubble it up.
            raise

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

    def read_customer_contact_details(self, user_id: str) -> models.customer_api.ContactDetails:
        """Update customer contact details."""
        response = self._customer_api("GET", "customer/readCustomerContactDetails", user_id,)

        return models.customer_api.ContactDetails.parse_obj(response.json())

    def update_customer_contact_details(
        self, user_id: str, contact_details: models.customer_api.ContactDetails
    ) -> models.customer_api.ContactDetails:
        """Update customer contact details."""
        response = self._customer_api(
            "POST",
            "customer/updateCustomerContactDetails",
            user_id,
            data=contact_details.json(exclude_none=True),
        )

        return models.customer_api.ContactDetails.parse_obj(response.json())

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
            json[0],
            [
                "accidentDate",
                "expectedDeliveryDate",
                "actualDeliveryDate",
                "dateFirstMissingWork",
                "expectedRTWDate",
            ],
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
        try:
            response = self._group_client_api(
                "GET",
                f"groupClient/absences/absence-period-decisions?absenceId={absence_id}",
                user_id,
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_absence_period_decisions",
                extra={"method_name": "get_absence_period_decisions"},
                exc_info=error,
            )
            error.method_name = "get_absence_period_decisions"
            raise error
        absence_periods = response.json()
        set_empty_dates_to_none(absence_periods, ["startDate", "endDate"])
        return models.group_client_api.PeriodDecisions.parse_obj(absence_periods)

    def get_customer_info(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerInfo:
        try:
            response = self._group_client_api(
                "GET", f"groupClient/customers/{customer_id}/customer-info", user_id
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_customer_info",
                extra={"method_name": "get_customer_info"},
                exc_info=error,
            )
            error.method_name = "get_customer_info"
            raise error
        json = response.json()
        set_empty_dates_to_none(json, ["dateOfBirth"])
        return models.group_client_api.CustomerInfo.parse_obj(json)

    def get_customer_occupations(
        self, user_id: str, customer_id: str
    ) -> models.group_client_api.CustomerOccupations:
        try:
            response = self._group_client_api(
                "GET", f"groupClient/customers/{customer_id}/customer-occupations", user_id
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_customer_occupations",
                extra={"method_name": "get_customer_occupations"},
                exc_info=error,
            )
            error.method_name = "get_customer_occupations"
            raise error
        json = response.json()
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        for item in json["elements"]:
            set_empty_dates_to_none(item, ["jobStartDate", "jobEndDate"])
        return models.group_client_api.CustomerOccupations.parse_obj(json)

    def get_outstanding_information(
        self, user_id: str, case_id: str
    ) -> List[models.group_client_api.OutstandingInformationItem]:
        try:
            """Get outstanding information"""
            response = self._group_client_api(
                "GET", f"groupClient/cases/{case_id}/outstanding-information", user_id
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_outstanding_information",
                extra={"method_name": "get_outstanding_information"},
                exc_info=error,
            )
            error.method_name = "get_outstanding_information"
            raise error
        return pydantic.parse_obj_as(
            List[models.group_client_api.OutstandingInformationItem], response.json()
        )

    def update_outstanding_information_as_received(
        self,
        user_id: str,
        case_id: str,
        outstanding_information: models.group_client_api.OutstandingInformationData,
    ) -> None:
        try:
            """Update outstanding information received"""
            self._group_client_api(
                "POST",
                f"groupClient/cases/{case_id}/outstanding-information-received",
                user_id,
                data=outstanding_information.json(exclude_none=True),
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: update_outstanding_information_as_received",
                extra={"method_name": "update_outstanding_information_as_received"},
                exc_info=error,
            )
            error.method_name = "update_outstanding_information_as_received"
            raise error

    def get_eform_summary(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.EFormSummary]:
        try:
            response = self._group_client_api(
                "GET", f"groupClient/cases/{absence_id}/eforms", user_id
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_eform_summary",
                extra={"method_name": "get_eform_summary"},
                exc_info=error,
            )
            error.method_name = "get_eform_summary"
            raise error
        json = response.json()
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        for item in json:
            set_empty_dates_to_none(item, ["effectiveDateFrom", "effectiveDateTo"])
        return pydantic.parse_obj_as(List[models.group_client_api.EFormSummary], json)

    def get_eform(
        self, user_id: str, absence_id: str, eform_id: str
    ) -> models.group_client_api.EForm:
        try:
            response = self._group_client_api(
                "GET", f"groupClient/cases/{absence_id}/eforms/{eform_id}/readEform", user_id
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_eform",
                extra={"method_name": "get_eform"},
                exc_info=error,
            )
            error.method_name = "get_eform"
            raise error
        json = response.json()
        for eformAttribute in json["eformAttributes"]:
            set_empty_dates_to_none(eformAttribute, ["dateValue"])
        return models.group_client_api.EForm.parse_obj(json)

    def create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        encoded_eform_type = urllib.parse.quote(eform.eformType)
        try:
            self._group_client_api(
                "POST",
                f"groupClient/cases/{absence_id}/addEForm/{encoded_eform_type}",
                user_id,
                data=json.dumps(eform.eformAttributes),
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: create_eform",
                extra={"method_name": "create_eform"},
                exc_info=error,
            )
            error.method_name = "create_eform"
            raise error

    def customer_create_eform(self, user_id: str, absence_id: str, eform: EFormBody) -> None:
        encoded_eform_type = urllib.parse.quote(eform.eformType)

        self._customer_api(
            "POST",
            f"customer/cases/{absence_id}/addEForm/{encoded_eform_type}",
            user_id,
            data=json.dumps(eform.eformAttributes),
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
        json = response.json()
        # Workaround empty strings in response instead of null. These cause parse_obj to fail.
        set_empty_dates_to_none(json, ["effectiveFrom", "effectiveTo"])
        return models.customer_api.PaymentPreferenceResponse.parse_obj(json)

    def update_occupation(
        self,
        occupation_id: int,
        employment_status: Optional[str],
        hours_worked_per_week: Optional[Decimal],
        NAICS_occupation: Optional[str],
    ) -> None:
        xml_body = self._create_update_occupation_payload(
            occupation_id, employment_status, hours_worked_per_week, NAICS_occupation
        )
        self._wscomposer_request(
            "POST", "webservice", {"config": "OccupationDetailUpdateService"}, xml_body
        )

    @staticmethod
    def _create_update_occupation_payload(
        occupation_id: int,
        employment_status: Optional[str],
        hours_worked_per_week: Optional[Decimal],
        NAICS_occupation: Optional[str],
    ) -> str:
        additional_data_set = models.AdditionalDataSet()

        # Occupation ID is the only identifier we use to specify which occupation record we want to update in FINEOS.
        additional_data_set.additional_data.append(
            models.AdditionalData(name="OccupationId", value=occupation_id)
        )

        # Application's hours_worked_per_week field is optional so we only update this value in FINEOS
        # if we've set it on the Application object in our database.
        if hours_worked_per_week:
            additional_data_set.additional_data.append(
                models.AdditionalData(name="HoursPerWeek", value=hours_worked_per_week)
            )

        if employment_status:
            additional_data_set.additional_data.append(
                models.AdditionalData(name="EmploymentStatus", value=employment_status)
            )

        if NAICS_occupation:
            additional_data_set.additional_data.append(
                models.AdditionalData(name="EEOCcategory", value=NAICS_occupation)
            )

        # @todo: AdditionalData name
        # if NAICS_occupation_title:
        #     additional_data_set.additional_data.append(
        #         models.AdditionalData(name="employment-title", value=NAICS_occupation)
        #     )
        # if NAICS_occupation_custom:
        #     additional_data_set.additional_data.append(
        #         models.AdditionalData(name="jobtitle", value=NAICS_occupation)
        #     )

        # Put the XML object together properly.
        service_data = models.OccupationDetailUpdateData()
        service_data.additional_data_set = additional_data_set

        service_request = models.OccupationDetailUpdateRequest()
        service_request.update_data = service_data

        payload_as_dict = service_request.dict(by_alias=True)
        xml_element = occupation_detail_update_service_request_schema.encode(payload_as_dict)
        return xml.etree.ElementTree.tostring(xml_element, encoding="unicode", xml_declaration=True)

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
            "fileExtension": file_extension.lower(),
            "base64EncodedFileContents": encoded_file_contents,
            "fileSizeInBytes": file_size,
            "description": description,
            "managedReqId": None,
        }

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
        try:
            header_content_type = None

            response = self._group_client_api(
                "GET",
                f"groupClient/cases/{absence_id}/documents",
                user_id,
                header_content_type=header_content_type,
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: group_client_get_documents",
                extra={"method_name": "group_client_get_documents"},
                exc_info=error,
            )
            error.method_name = "group_client_get_documents"
            raise error
        documents = response.json()
        return [
            models.group_client_api.GroupClientDocument.parse_obj(
                fineos_document_empty_dates_to_none(doc)
            )
            for doc in documents
        ]

    def get_managed_requirements(
        self, user_id: str, absence_id: str
    ) -> List[models.group_client_api.ManagedRequirementDetails]:
        try:
            header_content_type = None

            response = self._group_client_api(
                "GET",
                f"groupClient/cases/{absence_id}/managedRequirements",
                user_id,
                header_content_type=header_content_type,
            )

        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: get_managed_requirements",
                extra={"method_name": "get_managed_requirements"},
                exc_info=error,
            )
            error.method_name = "get_managed_requirements"
            raise error
        managed_reqs = response.json()
        return [
            models.group_client_api.ManagedRequirementDetails.parse_obj(
                set_empty_dates_to_none(
                    req,
                    [
                        "dateRequested",
                        "notProceedingWithDate",
                        "dateLastFollowedUp",
                        "followUpDate",
                        "dateCompleted",
                        "creationDate",
                        "dateSuppressed",
                    ],
                )
            )
            for req in managed_reqs
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

    def download_document_as_leave_admin(
        self, user_id: str, absence_id: str, fineos_document_id: str
    ) -> models.group_client_api.Base64EncodedFileData:
        try:
            header_content_type = None

            response = self._group_client_api(
                "GET",
                f"groupClient/cases/{absence_id}/documents/{fineos_document_id}/base64Download",
                user_id,
                header_content_type=header_content_type,
            )
        except exception.FINEOSClientError as error:
            logger.error(
                "FINEOS Client Exception: download_document_as_leave_admin",
                extra={"method_name": "download_document_as_leave_admin"},
                exc_info=error,
            )
            error.method_name = "download_document_as_leave_admin"
            raise error
        response_json = response.json()
        # populate spec required field missing in fineos response
        if "fileSizeInBytes" not in response_json:
            response_json["fileSizeInBytes"] = len(
                base64.b64decode(response_json["base64EncodedFileContents"].encode("ascii"))
            )
        return models.group_client_api.Base64EncodedFileData.parse_obj(response_json)

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
            self.wscomposer_user_id,
            data=xml_body.encode("utf-8"),
        )

    def create_or_update_employer(
        self,
        employer_create_or_update: models.CreateOrUpdateEmployer,
        existing_organization: Optional[models.OCOrganisationItem] = None,
    ) -> Tuple[str, int]:
        """Create or update an employer in FINEOS."""
        xml_body = self._create_or_update_employer_payload(
            employer_create_or_update, existing_organization
        )
        response = self._wscomposer_request(
            "POST", "webservice", {"config": "UpdateOrCreateParty"}, xml_body
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
            raise exception.FINEOSFatalResponseError(
                Exception(
                    f"Employer not created. Response Code: {response_code_value}, {validation_msg_value}"
                )
            )
        else:
            fineos_employer_id_value = fineos_employer_id.get("value")
            logger.info(
                f"Employer ID created or updated is {fineos_employer_id_value} for "
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
        existing_organization: Optional[models.OCOrganisationItem] = None,
    ) -> str:

        organization_default = models.OCOrganisationDefaultItem(
            CustomerNo=employer_create_or_update.fineos_customer_nbr,
            CorporateTaxNumber=employer_create_or_update.employer_fein,
            DoingBusinessAs=employer_create_or_update.employer_dba,
            LegalBusinessName=employer_create_or_update.employer_legal_name,
            Name=employer_create_or_update.employer_legal_name,
            ShortName=employer_create_or_update.employer_legal_name[0:8],
            UpperName=employer_create_or_update.employer_legal_name.upper(),
            UpperShortName=employer_create_or_update.employer_legal_name[0:8].upper(),
        )

        # The ReadEmployer endpoint doesn't return an OCOrganisationDefaultItem
        # as a part of its response, so using the top-level attributes to
        # populate the OCOrganisationDefaultItem in the update
        # OAR Dec 18, 2020 - Removed Name from sync. DOR is source of truth for legal name.
        if existing_organization:
            organization_default.PronouncedAs = existing_organization.PronouncedAs
            organization_default.AccountingDate = existing_organization.AccountingDate
            organization_default.FinancialYearEnd = existing_organization.FinancialYearEnd
            organization_default.PartyType = existing_organization.PartyType
            organization_default.DateBusinessCommenced = existing_organization.DateBusinessCommenced
            organization_default.DateOfIncorporation = existing_organization.DateOfIncorporation
            organization_default.GroupClient = existing_organization.GroupClient
            organization_default.SecuredClient = existing_organization.SecuredClient
            organization_default.NotificationIssued = existing_organization.NotificationIssued

        organization_name = models.OCOrganisationNameItem(
            DoingBusinessAs=employer_create_or_update.employer_dba,
            LegalBusinessName=employer_create_or_update.employer_legal_name,
            Name=employer_create_or_update.employer_legal_name,
            ShortName=employer_create_or_update.employer_legal_name[0:8],
            UpperName=employer_create_or_update.employer_legal_name.upper(),
            UpperShortName=employer_create_or_update.employer_legal_name[0:8].upper(),
            organisationWithDefault=models.OCOrganisationWithDefault(
                OCOrganisation=[organization_default]
            ),
        )

        # The ReadEmployer endpoint doesn't return an OCOrganisationName as a
        # part of its response, so using the top-level attributes to populate
        # the OCOrganisationName in the update
        # OAR Dec 18, 2020 - Removed Name from sync. DOR is source of truth for legal name.
        if existing_organization:
            organization_name.PronouncedAs = existing_organization.PronouncedAs

        organization = models.OCOrganisationItem(
            CustomerNo=employer_create_or_update.fineos_customer_nbr,
            CorporateTaxNumber=employer_create_or_update.employer_fein,
            DoingBusinessAs=employer_create_or_update.employer_dba,
            LegalBusinessName=employer_create_or_update.employer_legal_name,
            Name=employer_create_or_update.employer_legal_name,
            ShortName=employer_create_or_update.employer_legal_name[0:8],
            UpperName=employer_create_or_update.employer_legal_name.upper(),
            UpperShortName=employer_create_or_update.employer_legal_name[0:8].upper(),
            names=models.OCOrganisationName(OCOrganisationName=[organization_name]),
        )

        if existing_organization:
            organization.PronouncedAs = existing_organization.PronouncedAs
            organization.AccountingDate = existing_organization.AccountingDate
            organization.FinancialYearEnd = existing_organization.FinancialYearEnd
            organization.PartyType = existing_organization.PartyType
            organization.DateBusinessCommenced = existing_organization.DateBusinessCommenced
            organization.DateOfIncorporation = existing_organization.DateOfIncorporation
            organization.GroupClient = existing_organization.GroupClient
            organization.SecuredClient = existing_organization.SecuredClient
            organization.NotificationIssued = existing_organization.NotificationIssued

        party_dto = models.PartyIntegrationDTOItem(
            organisation=models.OCOrganisation(OCOrganisation=[organization])
        )

        employer_create_payload = models.UpdateOrCreatePartyRequest()
        employer_create_payload.update_data = models.UpdateData(PartyIntegrationDTO=[party_dto])

        payload_as_dict = employer_create_payload.dict(by_alias=True)
        xml_element = update_or_create_party_request_schema.encode(payload_as_dict)
        return xml.etree.ElementTree.tostring(xml_element, encoding="unicode", xml_declaration=True)

    def create_service_agreement_for_employer(
        self,
        fineos_employer_id: int,
        service_agreement_inputs: models.CreateOrUpdateServiceAgreement,
    ) -> str:
        """Create a Service Agreement for an employer in FINEOS."""
        xml_body = self._create_service_agreement_payload(
            fineos_employer_id, service_agreement_inputs
        )

        response = self._wscomposer_request(
            "POST", "webservice", {"config": "ServiceAgreementService"}, xml_body
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
            raise exception.FINEOSFatalResponseError(
                Exception(
                    f"Could not create service agreement for FINEOS employer id: {fineos_employer_id}"
                )
            )
        else:
            fineos_customer_nbr_value = fineos_customer_nbr.get("value")

        return str(fineos_customer_nbr_value)

    @staticmethod
    def _create_service_agreement_payload(
        fineos_employer_id: int, service_agreement_inputs: models.CreateOrUpdateServiceAgreement
    ) -> str:
        fineos_employer_id_data = models.AdditionalData(
            name="CustomerNumber", value=str(fineos_employer_id)
        )
        absence_management_data = models.AdditionalData(
            name="AbsenceManagement", value=service_agreement_inputs.absence_management_flag
        )
        leave_plans_data = models.AdditionalData(
            name="LeavePlans", value=service_agreement_inputs.leave_plans
        )
        unlink_leave_plans_data = models.AdditionalData(
            name="UnlinkAllExistingLeavePlans", value=True
        )

        additional_data_set = models.AdditionalDataSet()
        additional_data_set.additional_data.append(fineos_employer_id_data)
        if service_agreement_inputs.absence_management_flag:
            additional_data_set.additional_data.append(leave_plans_data)
        else:
            additional_data_set.additional_data.append(absence_management_data)

        additional_data_set.additional_data.append(unlink_leave_plans_data)

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
