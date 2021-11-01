import os
import pathlib
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.sql.functions import func

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.util.address.constant as Constants
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.experian.address_validate_soap.models as sm
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    Employee,
    ExperianAddressPair,
    GeoState,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.payments import FineosExtractEmployeeFeed
from massgov.pfml.delegated_payments.address_validation import (
    AddressValidationStep,
    _get_experian_soap_client,
)
from massgov.pfml.experian.address_validate_soap.service import (
    address_to_experian_verification_search,
    experian_verification_response_to_address,
)
from massgov.pfml.experian.physical_address.service import (
    address_to_experian_suggestion_text_format,
)

logger = logging.get_logger(__name__)


class ClaimantAddressValidationStep(AddressValidationStep):
    def run_step(self) -> None:

        self.process_address_data()
        self.db_session.commit()
        return

    # Query the database table and get latest customer records
    def get_fineos_employee_feed(self) -> List[Any]:
        employee_feed_data = [Any]
        try:
            subquery = self.db_session.query(
                FineosExtractEmployeeFeed,
                func.rank()
                .over(
                    order_by=FineosExtractEmployeeFeed.created_at.desc(),
                    partition_by=FineosExtractEmployeeFeed.customerno,
                )
                .label("R"),
            ).subquery()
            logger.debug("Subquery for employee feed %s", subquery)
            employee_feed_data = list(self.db_session.query(subquery).filter(subquery.c.R == 1))
            logger.debug(employee_feed_data)

        except Exception:
            self.db_session.rollback()
            logger.exception("Error processing addresses")
            raise

        return employee_feed_data

    """Query the employee table and return employee record that
    matches the customer number given. Will query the existing
    payments associated with this employee in the next steps.
    """

    def get_employee_record(self, customerno: Optional[str]) -> Optional[Employee]:
        if customerno:
            employee = (
                self.db_session.query(Employee)
                .filter(Employee.fineos_customer_number == customerno)
                .one_or_none()
            )
        return employee

    # Process all the logic needed to validate address if not validated and
    # create a report that is uploaded to S3 bucket
    def process_address_data(self) -> None:
        address_pair = None
        addressResults = []
        try:
            experian_soap_client = _get_experian_soap_client()
            fin_employee_feed_data = self.get_fineos_employee_feed()

            for f_employee_data in fin_employee_feed_data:
                logger.debug("Customer number from fineos %s", f_employee_data.customerno)
                employee = self.get_employee_record(f_employee_data.customerno)
                if employee:
                    logger.debug("There is an employee match %s", employee.employee_id)
                    employee_feed_address_data = self.construct_address_data(f_employee_data)
                    logger.debug(
                        "Check if there is an existing address pair for this address %s",
                        employee_feed_address_data.address_line_one,
                    )
                    address_pair = payments_util.find_existing_address_pair(
                        employee, employee_feed_address_data, self.db_session
                    )
                    if address_pair and address_pair.experian_address is not None:
                        logger.debug("Address has been previously validated")
                        self.increment(self.Metrics.PREVIOUSLY_VALIDATED_MATCH_COUNT)
                    # Does it have all the address lines
                    elif not self._does_address_have_all_parts(employee_feed_address_data):
                        self.increment(self.Metrics.ADDRESS_MISSING_COMPONENT_COUNT)
                        result = self._build_experian_outcome(
                            Constants.MESSAGE_ADDRESS_MISSING_PART,
                            employee_feed_address_data,
                            Constants.MESSAGE_ADDRESS_MISSING_PART,
                        )
                        addressResults.append(result.get("experian_result"))
                    else:
                        if not address_pair:
                            logger.debug("Address is new or updated")
                            address_pair = ExperianAddressPair(
                                fineos_address=employee_feed_address_data
                            )
                            new_address = True
                        else:
                            new_address = False
                        # Call validation if new address or address not validated
                        result_soap = self.process_address_via_soap_api(
                            experian_soap_client,
                            employee_feed_address_data,
                            address_pair,
                            new_address,
                        )
                        self.increment(self.Metrics.VALIDATED_ADDRESS_COUNT)
                        if result_soap:
                            addressResults.append(result_soap.get("experian_result"))
            ref_file = self.upload_results_s3(addressResults)
            self.increment(Constants.TRANSACTION_FILES_SENT_COUNT)
            self.db_session.add(ref_file)
        except Exception:
            self.db_session.rollback()
            logger.exception("Error processing addresses")
            raise
        return None

    # Constructs an address object from the FineosExtractEmployeeFeed address lines
    def construct_address_data(self, employee_data: FineosExtractEmployeeFeed) -> Address:
        logger.debug("Constructing an address object from fineos employee address lines")
        employee_feed_data_address = Address(
            address_id=uuid.uuid4(),
            address_line_one=employee_data.address1,
            address_line_two=employee_data.address2 if employee_data.address2 else None,
            city=employee_data.address4,
            geo_state_id=GeoState.get_id(employee_data.address6)
            if employee_data.address6
            else None,
            zip_code=employee_data.postcode,
            address_type_id=AddressType.MAILING.address_type_id,
        )
        logger.debug("Constructed an address object from finoes employee address lines")
        return employee_feed_data_address

    """Calls experian using SOAP call to validate address
        Returns the result of the call as a dictionary object"""

    def process_address_via_soap_api(
        self,
        experian_soap_client: soap_api.Client,
        address: Address,
        address_pair: ExperianAddressPair,
        new_address: bool,
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.debug("Calling experian on the address %s", address.address_line_one)
            response = self._experian_soap_response_for_address(experian_soap_client, address)
            logger.debug("Response from experian %s", response)
            if response:
                logger.debug("Response %s", response.verify_level)
        except Exception as e:
            logger.exception(
                "An exception occurred when querying the address for address ID %s: %s"
                % (address.address_id, type(e).__name__)
            )
            outcome = self._outcome_for_search_result(
                None, Constants.MESSAGE_EXPERIAN_EXCEPTION_FORMAT, address,
            )
            self.increment(self.Metrics.EXPERIAN_SEARCH_EXCEPTION_COUNT)
            return outcome

        # Address was verified
        if response.verify_level == sm.VerifyLevel.VERIFIED:
            self.increment(self.Metrics.VERIFIED_EXPERIAN_MATCH)
            formatted_address = experian_verification_response_to_address(response)
            if formatted_address:
                if not self._does_address_have_all_parts(formatted_address):
                    self.increment(self.Metrics.INVALID_EXPERIAN_FORMAT)
                    outcome = self._outcome_for_search_result(
                        response, Constants.MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE, address,
                    )
                    logger.debug(
                        "Experian return address has missing parts, wasnt supposed to occur"
                    )
                else:
                    if not new_address:
                        formatted_address.address_type_id = AddressType.MAILING.address_type_id
                        address_pair.experian_address = formatted_address
                        logger.debug(
                            "Adding the experian address to db since there was an existing fineos address %s",
                            address_pair.experian_address,
                        )

                        self.db_session.add(formatted_address)
                    self.increment(self.Metrics.VALID_EXPERIAN_FORMAT)
                    logger.debug("Valid verified experian address was returned")
                    return None

        # Experian returned a non-verified scenario, all of these
        # are cases that are considered errors

        self.increment(self.Metrics.NO_EXPERIAN_MATCH_COUNT)
        outcome = self._outcome_for_search_result(
            response, Constants.MESSAGE_INVALID_ADDRESS, address,
        )
        logger.debug("No matches for the search address%s", address)
        return outcome

    """Checks if all required address lines exist
    Returns a boolean value, True is all lines exist, False if missing"""

    def _does_address_have_all_parts(self, address: Address) -> bool:
        if (
            not address.address_line_one
            or not address.city
            or not address.zip_code
            or not address.geo_state_id
        ):
            return False

        return True

    """Formats the address lines to
        one suitable for experian call and then makes the soap call
    """

    def _experian_soap_response_for_address(
        self, experian_soap_client: soap_api.Client, address: Address
    ) -> sm.SearchResponse:
        request = address_to_experian_verification_search(address)
        return experian_soap_client.search(request)

    """Massage the returned address and or error messages from experian
        and calls build_experian_outcome to save the result as dict
        Returns dict object"""

    def _outcome_for_search_result(
        self, result: Optional[sm.SearchResponse], msg: str, address: Address,
    ) -> Dict[str, Any]:
        verify_level = (
            result.verify_level.value if result and result.verify_level else Constants.UNKNOWN
        )

        # The address passed into this is the incoming address validated.
        outcome = self._build_experian_outcome(msg, address, verify_level)
        logger.debug("Result Address is %s", result)
        # Right now we only have the one result.
        response_address = experian_verification_response_to_address(result)
        if response_address:
            label = Constants.OUTPUT_ADDRESS_KEY_PREFIX
            outcome[Constants.EXPERIAN_RESULT_KEY][
                label
            ] = address_to_experian_suggestion_text_format(response_address)
        return outcome

    """Builds a dicitonary object of messages and/or address returned from
        experian call"""

    def _build_experian_outcome(
        self, msg: str, address: Address, confidence: str
    ) -> Dict[str, Any]:
        # print(address, msg)
        logger.debug("Building experian address outcome...")
        exp_outcome: Dict[str, Any] = {
            Constants.EXPERIAN_RESULT_KEY: {
                Constants.INPUT_ADDRESS_KEY: address_to_experian_suggestion_text_format(address),
                Constants.CONFIDENCE_KEY: confidence,
                Constants.MESSAGE_KEY: msg,
            },
        }
        return exp_outcome

    """Generates the report from the list of validation results.
        Called from upload_results_s3"""

    def create_address_report(
        self, addr_reports: List[Dict], file_name: str, pathName: str
    ) -> pathlib.Path:
        logger.debug("Address results,%s", addr_reports)
        return file_util.create_csv_from_list(
            addr_reports, Constants.CLAIMANT_ADDRESS_VALIDATION_FIELDS, file_name, pathName
        )

    """Calls the create file function and uploads the created
        file to S3 location specified"""

    def upload_results_s3(self, addr_reports: List[Any]) -> ReferenceFile:

        s3_config = payments_config.get_s3_config()
        now = payments_util.get_now()
        file_name = now.strftime(Constants.CLAIMANT_ADDRESS_VALIDATION_FILENAME_FORMAT)
        address_report_source_path = s3_config.pfml_error_reports_archive_path
        dfml_sharepoint_outgoing_path = s3_config.dfml_report_outbound_path
        address_report_source_path = payments_util.build_archive_path(
            address_report_source_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            now.strftime("%Y-%m-%d"),
        )
        address_report_csv_path = self.create_address_report(
            addr_reports, file_name, address_report_source_path
        )
        logger.debug("File path is %s", address_report_csv_path)
        outgoing_s3_path = os.path.join(
            dfml_sharepoint_outgoing_path, Constants.CLAIMANT_ADDRESS_VALIDATION_FILENAME
        )
        file_util.copy_file(str(address_report_csv_path), outgoing_s3_path)
        logger.debug("Copied address validation report file to s3 path %s", outgoing_s3_path)
        return ReferenceFile(
            file_location=os.path.join(address_report_source_path, file_name),
            reference_file_type_id=ReferenceFileType.CLAIMANT_ADDRESS_VALIDATION_REPORT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
