import json
from datetime import date
from typing import Any, Dict, Optional

import pydantic
import requests
from pydantic.json import pydantic_encoder
from werkzeug.exceptions import InternalServerError, ServiceUnavailable

import massgov.pfml.db as db
import massgov.pfml.rmv.errors as rmv_errors
import massgov.pfml.util.logging
from massgov.pfml.db.models.applications import RMVCheck, RMVCheckApiErrorCode
from massgov.pfml.rmv.client import RmvClient
from massgov.pfml.rmv.models import (
    RmvAcknowledgement,
    VendorLicenseInquiryRequest,
    VendorLicenseInquiryResponse,
)
from massgov.pfml.util.converters.json_to_obj import get_json_from_object
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import MassIdStr
from massgov.pfml.util.strings import join_with_coordinating_conjunction

logger = massgov.pfml.util.logging.get_logger(__name__)


class RMVCheckRequest(PydanticBaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    ssn_last_4: str
    mass_id_number: MassIdStr
    residential_address_line_1: str
    residential_address_line_2: Optional[str]
    residential_address_city: str
    residential_address_zip_code: str
    absence_case_id: str

    class Config:
        extra = pydantic.Extra.forbid


class RMVCheckResponse(PydanticBaseModel):
    verified: bool
    description: str


def handle_rmv_check_request(
    db_session: db.Session, rmv_client: RmvClient, request_body: RMVCheckRequest
) -> RMVCheck:
    rmv_check_record = RMVCheck(absence_case_id=request_body.absence_case_id)
    db_session.add(rmv_check_record)
    db_session.commit()

    logger.info("RMV Check started", extra=rmv_check_for_log(rmv_check_record))

    try:
        vendor_license_inquiry_request = VendorLicenseInquiryRequest(
            first_name=request_body.first_name,
            last_name=request_body.last_name,
            date_of_birth=request_body.date_of_birth,
            ssn_last_4=request_body.ssn_last_4,
        )
    except pydantic.ValidationError:
        rmv_check_record.api_error_code = RMVCheckApiErrorCode.FAILED_TO_BUILD_REQUEST

        logger.info(
            "Could not construct RMV API request object", extra=rmv_check_for_log(rmv_check_record),
        )

        return rmv_check_record

    try:
        rmv_check_record.request_to_rmv_started_at = utcnow()
        license_inquiry_response = rmv_client.vendor_license_inquiry(vendor_license_inquiry_request)
    except rmv_errors.RmvError:
        rmv_check_record.api_error_code = RMVCheckApiErrorCode.UNKNOWN_RMV_ISSUE

        logger.exception(
            "RMV Check failed due to unknown error", extra=rmv_check_for_log(rmv_check_record),
        )

        return rmv_check_record
    except pydantic.ValidationError:
        rmv_check_record.api_error_code = RMVCheckApiErrorCode.FAILED_TO_PARSE_RESPONSE

        logger.exception(
            "Could not parse response from the RMV API", extra=rmv_check_for_log(rmv_check_record),
        )

        return rmv_check_record
    except (requests.ConnectionError, requests.Timeout):
        rmv_check_record.api_error_code = RMVCheckApiErrorCode.NETWORKING_ISSUES

        logger.exception(
            "RMV Check had networking issues connecting to RMV API",
            extra=rmv_check_for_log(rmv_check_record),
        )

        return rmv_check_record
    finally:
        rmv_check_record.request_to_rmv_completed_at = utcnow()

    if isinstance(license_inquiry_response, RmvAcknowledgement):
        rmv_check_record.rmv_error_code = license_inquiry_response

        logger.info(
            "RMV Check finished without being able to retrieve record from RMV API",
            extra=rmv_check_for_log(rmv_check_record),
        )

        return rmv_check_record

    rmv_check_record.rmv_customer_key = license_inquiry_response.customer_key

    result = do_checks(request_body, license_inquiry_response, rmv_check_record)

    logger.info("RMV Check finished", extra=rmv_check_for_log(result))

    return result


def do_checks(
    request_body: RMVCheckRequest,
    license_inquiry_response: VendorLicenseInquiryResponse,
    rmv_check_record: RMVCheck,
) -> RMVCheck:
    expiration_date_cut_off = date.today()

    check_expiration_license_1 = license_inquiry_response.license1_expiration_date is not None and (
        license_inquiry_response.license1_expiration_date > expiration_date_cut_off
    )

    check_expiration_license_2 = license_inquiry_response.license2_expiration_date is not None and (
        license_inquiry_response.license2_expiration_date > expiration_date_cut_off
    )

    # License1 is for a full License. License2 is for a permit.
    #
    # Doesn't matter which kind is issued to the person, one of them just needs
    # to valid.
    rmv_check_record.check_expiration = check_expiration_license_1 or check_expiration_license_2

    rmv_check_record.check_customer_inactive = not license_inquiry_response.is_customer_inactive

    rmv_check_record.check_active_fraudulent_activity = not (
        license_inquiry_response.cfl_sanctions and license_inquiry_response.cfl_sanctions_active
    )

    rmv_check_record.check_mass_id_number = (
        request_body.mass_id_number == license_inquiry_response.license_id
    )

    rmv_check_record.check_residential_address_line_1 = (
        request_body.residential_address_line_1.lower() == license_inquiry_response.street1.lower()
    )

    if not license_inquiry_response.street2:
        # if there's no second line on record, then it does not matter if user
        # provided anything on the line, we'll pass them for the check
        rmv_check_record.check_residential_address_line_2 = True
    elif not request_body.residential_address_line_2:
        # if there *is* second line on record and the user doesn't provide
        # input, then that's a fail
        rmv_check_record.check_residential_address_line_2 = False
    else:
        rmv_check_record.check_residential_address_line_2 = (
            request_body.residential_address_line_2.strip().lower()
            == license_inquiry_response.street2.strip().lower()
        )

    rmv_check_record.check_residential_city = (
        request_body.residential_address_city.lower() == license_inquiry_response.city.lower()
    )

    rmv_check_record.check_residential_zip_code = (
        request_body.residential_address_zip_code[:5] == license_inquiry_response.zip[:5]
    )

    return rmv_check_record


CHECKS_AND_THEIR_FAILURE_DESCRIPTIONS = {
    "check_expiration": "ID is expired",
    "check_customer_inactive": "ID holder is deceased",
    "check_active_fraudulent_activity": "ID is marked for active fraudulent activity",
    "check_mass_id_number": "ID number mismatch",
    "check_residential_address_line_1": "residential address line 1 mismatch",
    "check_residential_address_line_2": "residential address line 2 mismatch",
    "check_residential_city": "residential city mismatch",
    "check_residential_zip_code": "residential zip code mismatch",
}


def make_response_from_rmv_check(rmv_check_record: RMVCheck) -> RMVCheckResponse:
    # first determine if we had issues even getting record from the RMV
    if rmv_check_record.rmv_error_code:
        if rmv_check_record.rmv_error_code is RmvAcknowledgement.CUSTOMER_NOT_FOUND:
            return RMVCheckResponse(
                verified=False,
                description="Verification failed because no record could be found for given ID information.",
            )

        if rmv_check_record.rmv_error_code is RmvAcknowledgement.MULTIPLE_CUSTOMERS_FOUND:
            return RMVCheckResponse(
                verified=False,
                description="Verification failed because multiple records were found that could match ID information.",
            )

        if rmv_check_record.rmv_error_code is RmvAcknowledgement.CREDENTIAL_NOT_FOUND:
            return RMVCheckResponse(
                verified=False,
                description="Verification failed because no record could be found for given ID information.",
            )

        if rmv_check_record.rmv_error_code is RmvAcknowledgement.REQUIRED_FIELDS_MISSING:
            # we didn't provide the RMV API with all the required information,
            # that's an internal API error
            raise InternalServerError

    # then check if there was some other issue
    if rmv_check_record.api_error_code:
        if rmv_check_record.api_error_code is RMVCheckApiErrorCode.NETWORKING_ISSUES:
            raise ServiceUnavailable

        raise InternalServerError

    # then figure out if all checks passed
    failed_checks = []

    for check in CHECKS_AND_THEIR_FAILURE_DESCRIPTIONS.keys():
        try:
            check_result = getattr(rmv_check_record, check)
        except AttributeError:
            logger.exception(
                f"Could not find attribute '{check}' on an RMVCheck instance, check for typos in the keys of CHECKS_AND_THEIR_FAILURE_DESCRIPTIONS"
            )

            raise InternalServerError

        if not check_result:
            failed_checks.append(check)

    if len(failed_checks) != 0:
        failed_check_descriptions = list(
            map(lambda k: CHECKS_AND_THEIR_FAILURE_DESCRIPTIONS[k], failed_checks)
        )

        description = f"Verification failed because {join_with_coordinating_conjunction(failed_check_descriptions)}."

        return RMVCheckResponse(verified=False, description=description)

    return RMVCheckResponse(verified=True, description="Verification check passed.")


def rmv_check_for_log(rmv_check_record: RMVCheck) -> Dict[str, Any]:
    dict_version = get_json_from_object(rmv_check_record)

    # this is due to imprecise typing on `get_json_from_object`, it only returns
    # None if None is provided as input, otherwise it's always a dictionary
    if dict_version is None:
        raise ValueError("Got back None for a non-None input. Should not happen.")

    keys_to_log = {
        "rmv_check_id",
        "created_at",
        "updated_at",
        "request_to_rmv_started_at",
        "request_to_rmv_completed_at",
        "check_expiration",
        "check_customer_inactive",
        "check_active_fraudulent_activity",
        "check_mass_id_number",
        "check_residential_address_line_1",
        "check_residential_address_line_2",
        "check_residential_city",
        "check_residential_zip_code",
        "rmv_error_code",
        "api_error_code",
        "absence_case_id",
        "rmv_customer_key",
    }

    # silly dance to serialize record into dictionary with basic types using
    # better encoders than the default (e.g., Enums are represented by their
    # values), before it gets processed by our JSON log formatter, which just
    # uses the default string representation for all types
    json_version = json.loads(json.dumps(dict_version, default=pydantic_encoder))

    # filter to just keys we will log and prefix keys with `rmv_check.` for the extra logging attributes
    return {f"rmv_check.{key}": value for key, value in json_version.items() if key in keys_to_log}
