import os
import pathlib
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from sqlalchemy.sql.functions import func

import massgov.pfml.db as db
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
    EmployeeAddress,
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
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.experian.address_validate_soap.service import (
    address_to_experian_verification_search,
    experian_verification_response_to_address,
)
from massgov.pfml.experian.physical_address.client import Client
from massgov.pfml.experian.physical_address.service import (
    address_to_experian_suggestion_text_format,
)

logger = logging.get_logger(__name__)


class ClaimantAddressValidationStep(AddressValidationStep):
    # use_experian_soap_client: bool = False

    def run_step(self) -> None:

        self.process_address_data()
        self.db_session.commit()
        return

    # Query the database table and get latest customer records
    def get_fineos_employee_feed(self) -> List[FineosExtractEmployeeFeed]:
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
            employee_feed_data: List[FineosExtractEmployeeFeed] = self.db_session.query(
                subquery
            ).filter(subquery.c.R == 1)
        except Exception:
            self.db_session.rollback()
            logger.exception("Error processing addresses")
            raise

        logger.info("Number of rows retrieved from table %s", len(list(employee_feed_data)))
        return employee_feed_data

    # Query the employee table and return employee record that
    # matches the customer number given
    def get_employee_record(self, customerno) -> Employee:
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
        has_address_update = False
        addressResults = []
        try:
            experian_soap_client = _get_experian_soap_client()
            fin_employee_feed_data = self.get_fineos_employee_feed()

            for f_employee_data in fin_employee_feed_data:
                logger.info("Customer number from fineos %s", f_employee_data.customerno)
                employee = self.get_employee_record(f_employee_data.customerno)
                if employee:
                    logger.info("There is an employee match %s", employee.employee_id)
                    employee_feed_address_data = self.construct_address_data(f_employee_data)
                    logger.info(
                        "Constructed address object from fineos employee feed %s",
                        employee_feed_address_data.address_line_one,
                    )
                    address_pair, has_address_update = self.is_address_new_or_updated(
                        employee_feed_address_data, employee
                    )
                    logger.debug("Is address new or updated", has_address_update)
                    # Call validation on this address
                    result = self._validate_claimant_address(
                        employee_feed_address_data, address_pair, experian_soap_client
                    )
                    self.increment(self.Metrics.VALIDATED_ADDRESS_COUNT)
                    addressResults.append(result.get("experian_result"))

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
        # Construct an Address from the employee_feed_data
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

    """Checks if the address is in employee fineos table, if not add the address
        Returns:
            bool: True if address_data has address updates; False otherwise
        """

    def is_address_new_or_updated(
        self, employee_feed_address_data: Address, employee: Employee
    ) -> Tuple[Optional[ExperianAddressPair], bool]:

        # If existing_address_pair exists, compare the existing fineos_address with the employee_feed_data address
        #  If they're the same, nothing needs to be done, so we can return the address
        logger.info("check to see if the address exists in previous claims %s", employee)
        existing_address_pair = payments_util.find_existing_address_pair(
            employee, employee_feed_address_data, self.db_session
        )
        logger.info("Is there an address pair %s", existing_address_pair)
        if existing_address_pair:
            return existing_address_pair, False
        """Checks if this process has already validated the address before
        by checking the employee address table.
        """
        logger.info("check to see if the address exists in employee address")
        existing_address_pair = payments_util.find_existing_address_pair_in_employee_address(
            employee, employee_feed_address_data, self.db_session
        )

        if existing_address_pair:
            logger.info(
                "There is an existing address pair in employee address %s", existing_address_pair
            )
            return existing_address_pair, False

        # We need to add the address to the employee.
        new_experian_address_pair = ExperianAddressPair(fineos_address=employee_feed_address_data)
        logger.info(
            "Going to add the address to Employee fineos Address %s",
            new_experian_address_pair.fineos_address,
        )
        logger.info("The uuid is %s", employee_feed_address_data.address_id)
        self.db_session.add(employee_feed_address_data)
        self.db_session.add(new_experian_address_pair)

        # We also want to make sure the address is linked in the EmployeeAddress table
        employee_address = EmployeeAddress(employee=employee, address=employee_feed_address_data)
        self.db_session.add(employee_address)
        return new_experian_address_pair, True

    """ Checks if address has already been validated,missing address lines
        and calls the function to validate address using Experian
    """

    def _validate_claimant_address(
        self,
        address: Address,
        address_pair: ExperianAddressPair,
        experian_soap_client: soap_api.Client,
    ) -> Dict[str, Any]:

        # already validated
        if address_pair.experian_address is not None:
            logger.info("Address in experian address pair %s", address_pair.experian_address)
            self.increment(self.Metrics.PREVIOUSLY_VALIDATED_MATCH_COUNT)
            addr_result = self._build_experian_outcome(
                Constants.MESSAGE_ALREADY_VALIDATED,
                cast(Address, address_pair.experian_address),
                Constants.PREVIOUSLY_VERIFIED,
            )
            return addr_result
        # Does it have all the address lines
        if not self._does_address_have_all_parts(address):
            self.increment(self.Metrics.ADDRESS_MISSING_COMPONENT_COUNT)
            addr_result = self._build_experian_outcome(
                Constants.MESSAGE_ADDRESS_MISSING_PART,
                cast(Address, address),
                Constants.MESSAGE_ADDRESS_MISSING_PART,
            )
            return addr_result

        addr_result = self._process_address_via_soap_api(
            experian_soap_client, address, address_pair
        )
        return addr_result

    """Calls experian using SOAP call to validate address
        Returns the result of the call as a dictionary object"""

    def _process_address_via_soap_api(
        self,
        experian_soap_client: soap_api.Client,
        address: Address,
        address_pair: ExperianAddressPair,
    ) -> Dict[str, Any]:

        try:
            logger.info("Calling experian on the address %s", address.address_line_one)
            response = self._experian_soap_response_for_address(experian_soap_client, address)
            logger.debug("Response from experian %s", response)
            if response:
                logger.info("Response %s", response.verify_level)
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

            if not self._does_address_have_all_parts(address):
                self.increment(self.Metrics.INVALID_EXPERIAN_FORMAT)
                outcome = self._outcome_for_search_result(
                    response, Constants.MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE, address,
                )
                logger.info("Experian return address has missing parts, wasnt supposed to occur")
            else:
                # formatted_address.address_id = uuid.uuid4()
                formatted_address.address_type_id = AddressType.MAILING.address_type_id
                address_pair.experian_address = formatted_address
                # new_experian_address_pair = ExperianAddressPair(
                # experian_address=formatted_address
                # )
                logger.info(
                    "Going to add the addrss to Employee experian Address %s",
                    address_pair.fineos_address,
                )
                self.db_session.add(formatted_address)
                # self.db_session.add(new_experian_address_pair)
                outcome = self._outcome_for_search_result(
                    response, Constants.MESSAGE_VALID_ADDRESS, address,
                )
                self.increment(self.Metrics.VALID_EXPERIAN_FORMAT)
                logger.info("Valid verified experian address was returned")
            return outcome

        # Experian returned a non-verified scenario, all of these
        # are cases that are considered errors
        self.increment(self.Metrics.NO_EXPERIAN_MATCH_COUNT)
        outcome = self._outcome_for_search_result(
            response, Constants.MESSAGE_INVALID_ADDRESS, address,
        )
        logger.info("No matches for the search address%s", address)
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
        # outcome = self._build_experian_outcome(msg, address, verify_level)

        # Right now we only have the one result.
        response_address = experian_verification_response_to_address(result)
        if response_address:
            response_text = address_to_experian_suggestion_text_format(response_address)
            return self._build_experian_outcome(msg, address, verify_level, response_text)
        else:
            return self._build_experian_outcome(msg, address, verify_level)
        # logger.info("In %s", type(outcome))
        # return outcome

    """Builds a dicitonary object of messages and/or address returned from
        experian call"""

    def _build_experian_outcome(
        self, msg: str, address: Address, confidence: str, experian_address=None
    ) -> Dict[str, Any]:
        # print(address, msg)
        logger.info("Building experian address outcome...")
        exp_outcome: Dict[str, Any] = {
            Constants.EXPERIAN_RESULT_KEY: {
                Constants.INPUT_ADDRESS_KEY: address_to_experian_suggestion_text_format(address),
                Constants.CONFIDENCE_KEY: confidence,
                Constants.OUTPUT_ADDRESS_KEY_PREFIX: experian_address,
                Constants.MESSAGE_KEY: msg,
            },
        }
        return exp_outcome

    """Generates the report from the list of validation results.
        Called from upload_results_s3"""

    def create_address_report(self, addr_reports: List[Dict], file_name, pathName) -> pathlib.Path:
        logger.debug("Address results,%s", addr_reports)
        return file_util.create_csv_from_list(
            addr_reports, Constants.CLAIMANT_ADDRESS_VALIDATION_FIELDS, file_name, pathName
        )
        # return file_util.create_csv_from_list(claimants, Constants.CLAIMANT_ADDRESS_VALIDATION_FIELDS, file_name,s3_config.pfml_error_reports_archive_path)

    """Calls the create file function and uploads the created
        file to S3 location specified"""

    def upload_results_s3(self, addr_reports: List[Dict]) -> ReferenceFile:

        s3_config = payments_config.get_s3_config()
        now = payments_util.get_now()
        file_name = now.strftime(Constants.CLAIMANT_ADDRESS_VALIDATION_FILENAME_FORMAT)
        address_report_source_path = s3_config.pfml_error_reports_archive_path
        dfml_sharepoint_outgoing_path = s3_config.dfml_report_outbound_path
        address_report_source_path = os.path.join(
            address_report_source_path, "sent", now.strftime("%Y-%m-%d")
        )
        address_report_csv_path = self.create_address_report(
            addr_reports, file_name, address_report_source_path
        )
        logger.info("File path is %s", address_report_csv_path)
        outgoing_s3_path = os.path.join(
            dfml_sharepoint_outgoing_path, Constants.CLAIMANT_ADDRESS_VALIDATION_FILENAME
        )
        file_util.upload_to_s3(str(address_report_csv_path), outgoing_s3_path)
        logger.info("Wrote address validation report file to s3 path %s", outgoing_s3_path)
        return ReferenceFile(
            file_location=os.path.join(address_report_source_path, file_name),
            reference_file_type_id=ReferenceFileType.CLAIMANT_ADDRESS_VALIDATION_REPORT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
