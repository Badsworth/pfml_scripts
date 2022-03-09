import enum
import os
import pathlib
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.sql.functions import func

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.experian.address_validate_soap.models as sm
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    Claim,
    Employee,
    ExperianAddressPair,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    StateLog,
)
from massgov.pfml.db.models.geo import GeoState
from massgov.pfml.db.models.payments import FineosExtractEmployeeFeed, MmarsPaymentData
from massgov.pfml.delegated_payments.address_validation import _get_experian_soap_client
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.experian.address_validate_soap.layouts import Layout
from massgov.pfml.experian.address_validate_soap.service import (
    experian_verification_response_to_address,
)
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)


class Constants:
    MESSAGE_KEY = "Result"
    EXPERIAN_RESULT_KEY = "experian_result"
    CONFIDENCE_KEY = "Result"
    INPUT_ADDRESS_KEY = "Address Provided"
    OUTPUT_ADDRESS_KEY_PREFIX = "Experian Address Recommendation #"
    PREVIOUSLY_VERIFIED = "Previously verified"
    VERIFIED = "Verification Level"
    UNKNOWN = "Unknown"
    FIRST_NAME = "First Name"
    LAST_NAME = "Last Name"
    CUSTOMER_NUMBER = "Customer Number"
    NTN_NUMBER = "NTN Number"

    MESSAGE_ALREADY_VALIDATED = "Address has already been validated"
    MESSAGE_INVALID_EXPERIAN_RESPONSE = "Invalid response from Experian search API"
    MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE = "Invalid response from Experian format API"
    # MESSAGE_VALID_ADDRESS = "Address validated by Experian"
    # MESSAGE_VALID_MATCHING_ADDRESS = "Matching address validated by Experian"
    MESSAGE_INVALID_ADDRESS = "Address not valid in Experian"
    MESSAGE_EXPERIAN_EXCEPTION_FORMAT = "An exception was thrown by Experian: {}"
    MESSAGE_ADDRESS_MISSING_PART = (
        "The address is missing a required component and cannot be validated"
    )
    CLAIMANT_ADDRESS_VALIDATION_FILENAME = "Claimant-Address-Validation-Report"
    CLAIMANT_ADDRESS_VALIDATION_FILENAME_FORMAT = (
        f"%Y-%m-%d-%H-%M-%S-{CLAIMANT_ADDRESS_VALIDATION_FILENAME}"
    )

    CLAIMANT_ADDRESS_VALIDATION_FIELDS = [
        CUSTOMER_NUMBER,
        FIRST_NAME,
        LAST_NAME,
        INPUT_ADDRESS_KEY,
        CONFIDENCE_KEY,
        OUTPUT_ADDRESS_KEY_PREFIX + "1",
        OUTPUT_ADDRESS_KEY_PREFIX + "2",
        OUTPUT_ADDRESS_KEY_PREFIX + "3",
        OUTPUT_ADDRESS_KEY_PREFIX + "4",
        OUTPUT_ADDRESS_KEY_PREFIX + "5",
        OUTPUT_ADDRESS_KEY_PREFIX + "6",
        OUTPUT_ADDRESS_KEY_PREFIX + "7",
        OUTPUT_ADDRESS_KEY_PREFIX + "8",
    ]
    TRANSACTION_FILES_SENT_COUNT = "transaction_files_sent_count"


class ClaimantAddressValidationStep(Step):

    validation_container: payments_util.ValidationContainer

    class Metrics(str, enum.Enum):
        EXPERIAN_SEARCH_EXCEPTION_COUNT = "experian_search_exception_count"
        INVALID_EXPERIAN_FORMAT = "invalid_experian_format"
        INVALID_EXPERIAN_RESPONSE = "invalid_experian_response"
        MULTIPLE_EXPERIAN_MATCHES = "multiple_experian_matches"
        NO_EXPERIAN_MATCH_COUNT = "no_experian_match_count"
        PREVIOUSLY_VALIDATED_MATCH_COUNT = "previously_validated_match_count"
        VALID_EXPERIAN_FORMAT = "valid_experian_format"
        VALIDATED_ADDRESS_COUNT = "validated_address_count"
        VERIFIED_EXPERIAN_MATCH = "verified_experian_match"
        ADDRESS_MISSING_COMPONENT_COUNT = "address_missing_component_count"

    def run_step(self) -> None:

        self.process_address_data()
        self.db_session.commit()
        return

    # Query the database table and get latest customer records
    def get_fineos_employee_feed(self) -> List[Any]:
        employee_feed_data = [Any]

        year = pfml_1099_util.get_tax_year()

        try:

            # SELECT *
            # FROM (
            #   SELECT FINEOS_EXTRACT_EMPLOYEE_FEED.*,
            #       RANK() OVER (
            #           PARTITION BY FINEOS_EXTRACT_EMPLOYEE_FEED.CUSTOMERNO
            #           ORDER BY FINEOS_EXTRACT_EMPLOYEE_FEED.FINEOS_EXTRACT_IMPORT_LOG_ID DESC,
            #                   FINEOS_EXTRACT_EMPLOYEE_FEED.EFFECTIVEFROM DESC,
            #                   FINEOS_EXTRACT_EMPLOYEE_FEED.EFFECTIVETO DESC,
            #                   FINEOS_EXTRACT_EMPLOYEE_FEED.CREATED_AT DESC
            #       ) AS R
            # FROM FINEOS_EXTRACT_EMPLOYEE_FEED) AS EF
            # INNER JOIN EMPLOYEE E ON E.FINEOS_CUSTOMER_NUMBER = EF.CUSTOMERNO
            # WHERE EF.R = 1
            # AND E.EMPLOYEE_ID IN (
            #   SELECT E.EMPLOYEE_ID
            #   FROM MMARS_PAYMENT_DATA MPD
            #   INNER JOIN EMPLOYEE E ON MPD.VENDOR_CUSTOMER_CODE = E.CTR_VENDOR_CUSTOMER_CODE
            #   UNION ALL
            #   SELECT E.EMPLOYEE_ID
            #   FROM EMPLOYEE E
            #   INNER JOIN CLAIM CL ON CL.EMPLOYEE_ID = E.EMPLOYEE_ID
            #   INNER JOIN PAYMENT P ON P.CLAIM_ID = CL.CLAIM_ID
            #   INNER JOIN STATE_LOG SL ON P.PAYMENT_ID = SL.PAYMENT_ID
            #   AND SL.END_STATE_ID IN (137, 139)
            #   AND DATE_PART('YEAR', SL.ENDED_AT) = 2021)
            mmars_employees = self.db_session.query(Employee.employee_id).join(
                MmarsPaymentData,
                Employee.ctr_vendor_customer_code == MmarsPaymentData.vendor_customer_code,
            )
            pub_employees = (
                self.db_session.query(Employee.employee_id)
                .join(Claim)
                .join(Payment)
                .join(StateLog)
                .filter(
                    StateLog.end_state_id.in_(payments_util.Constants.PAYMENT_SENT_STATE_IDS),
                    func.extract("YEAR", StateLog.ended_at) == year,
                )
            )

            employees = mmars_employees.union_all(pub_employees)

            employee_subquery = self.db_session.query(
                FineosExtractEmployeeFeed,
                func.rank()
                .over(
                    order_by=[
                        FineosExtractEmployeeFeed.fineos_extract_import_log_id.desc(),
                        FineosExtractEmployeeFeed.effectivefrom.desc(),
                        FineosExtractEmployeeFeed.effectiveto.desc(),
                        FineosExtractEmployeeFeed.created_at.desc(),
                    ],
                    partition_by=FineosExtractEmployeeFeed.customerno,
                )
                .label("R"),
            ).subquery()

            employee_feed_data = list(
                self.db_session.query(employee_subquery)
                .join(Employee, employee_subquery.c.customerno == Employee.fineos_customer_number)
                .filter(employee_subquery.c.R == 1)
                .filter(Employee.employee_id.in_(employees))
            )

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

    # Validate address if not validated and
    # create a report that is uploaded to S3 bucket
    def process_address_data(self) -> None:
        address_pair = None
        addressResults = []
        logger.info("Claimant Address Validation Step - Start")
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
                        self.increment(self.Metrics.PREVIOUSLY_VALIDATED_MATCH_COUNT)
                    # Does it have all the address lines
                    elif not self._does_address_have_all_parts(employee_feed_address_data):
                        logger.info(
                            "Address missing parts for customer %s", f_employee_data.customerno
                        )
                        self.increment(self.Metrics.ADDRESS_MISSING_COMPONENT_COUNT)
                        result = self._outcome_for_search_result(
                            None,
                            Constants.MESSAGE_ADDRESS_MISSING_PART,
                            employee_feed_address_data,
                            f_employee_data.customerno,
                            f_employee_data.firstnames,
                            f_employee_data.lastname,
                        )
                        addressResults.append(result.get("experian_result"))
                    else:
                        if not address_pair:
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
                            f_employee_data.customerno,
                            f_employee_data.firstnames,
                            f_employee_data.lastname,
                        )
                        self.increment(self.Metrics.VALIDATED_ADDRESS_COUNT)
                        if result_soap:
                            addressResults.append(result_soap.get("experian_result"))
            logger.info("Uploading results ")
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
        employee_feed_data_address = self._validate_incoming_address(employee_data)
        return employee_feed_data_address

    """Calls experian using SOAP call to validate address
        Returns the result of the call as a dictionary object"""

    def process_address_via_soap_api(
        self,
        experian_soap_client: soap_api.Client,
        address: Address,
        address_pair: ExperianAddressPair,
        new_address: bool,
        customer_number: str,
        first_name: str,
        last_name: str,
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
                None,
                Constants.MESSAGE_EXPERIAN_EXCEPTION_FORMAT,
                address,
                customer_number,
                first_name,
                last_name,
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
                        response,
                        Constants.MESSAGE_INVALID_EXPERIAN_FORMAT_RESPONSE,
                        address,
                        customer_number,
                        first_name,
                        last_name,
                    )
                    logger.debug(
                        "Experian return address has missing parts, wasnt supposed to occur"
                    )
                    self.increment(self.Metrics.INVALID_EXPERIAN_FORMAT)
                    return outcome
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
        else:
            self.increment(self.Metrics.NO_EXPERIAN_MATCH_COUNT)
            outcome = self._outcome_for_search_result(
                response,
                Constants.MESSAGE_INVALID_ADDRESS,
                address,
                customer_number,
                first_name,
                last_name,
            )
            logger.debug("Outcome for search %s", outcome)
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

    """Massage the returned address and or error messages from experian
        and calls build_experian_outcome to save the result as dict
        Returns dict object"""

    def _outcome_for_search_result(
        self,
        result: Optional[sm.SearchResponse],
        msg: str,
        address: Address,
        customer_no: str,
        first_name: str,
        last_name: str,
    ) -> Dict[str, Any]:
        verify_level = result.verify_level.value if result and result.verify_level else msg
        outcome: Dict[str, Any] = self._build_experian_outcome(
            customer_no, first_name, last_name, msg, address, verify_level
        )

        if result is None:
            return outcome
        else:
            logger.debug("Result Address is %s", result)
            self.increment(self.Metrics.MULTIPLE_EXPERIAN_MATCHES)
            if result.picklist and result.picklist.picklist_entries is not None:
                pList = list(result.picklist.picklist_entries)
                for i, pickList in enumerate(pList):
                    if pickList.partial_address is not None:
                        logger.debug(pickList.partial_address)
                        logger.debug(pickList.score)
                        label = Constants.OUTPUT_ADDRESS_KEY_PREFIX + str(1 + i)
                        outcome[Constants.EXPERIAN_RESULT_KEY][label] = pickList.partial_address

            else:
                # Right now we only have the one result.
                response_address = experian_verification_response_to_address(result)
                if response_address:
                    label = Constants.OUTPUT_ADDRESS_KEY_PREFIX + "1"
                    outcome[Constants.EXPERIAN_RESULT_KEY][
                        label
                    ] = self.address_to_experian_suggestion_text_format(response_address)
        return outcome

    """Builds a dicitonary object of messages and/or address returned from
        experian call"""

    def _build_experian_outcome(
        self,
        customer_no: str,
        first_name: str,
        last_name: str,
        msg: str,
        address: Address,
        confidence: str,
    ) -> Dict[str, Any]:

        logger.debug("Building experian address outcome...")
        exp_outcome: Dict[str, Any] = {
            Constants.EXPERIAN_RESULT_KEY: {
                Constants.CUSTOMER_NUMBER: customer_no,
                Constants.FIRST_NAME: first_name,
                Constants.LAST_NAME: last_name,
                Constants.INPUT_ADDRESS_KEY: self.address_to_experian_suggestion_text_format(
                    address
                ),
                Constants.MESSAGE_KEY: confidence,
                # Constants.MESSAGE_KEY: msg,
            }
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
        now = get_now_us_eastern()
        file_name = now.strftime(Constants.CLAIMANT_ADDRESS_VALIDATION_FILENAME_FORMAT)
        address_report_source_path = s3_config.pfml_error_reports_archive_path
        dfml_sharepoint_outgoing_path = s3_config.dfml_report_outbound_path
        address_report_source_path = os.path.join(
            address_report_source_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            now.strftime("%Y-%m-%d"),
        )
        logger.info("Path name sent to create file is %s", address_report_source_path)
        address_report_csv_path = self.create_address_report(
            addr_reports, file_name, address_report_source_path
        )
        logger.info("Path returned after create file is %s", address_report_csv_path)
        file_name_path = address_report_csv_path.name
        logger.info("File name from path is %s", file_name_path)
        file_source_path = os.path.join(address_report_source_path, file_name_path)
        logger.info("Source file path is %s", file_source_path)
        out_file_name = Constants.CLAIMANT_ADDRESS_VALIDATION_FILENAME + ".csv"
        outgoing_s3_path = os.path.join(dfml_sharepoint_outgoing_path, out_file_name)
        logger.info("Destination file path is %s", outgoing_s3_path)
        if file_util.is_s3_path(outgoing_s3_path):
            if file_util.is_s3_path(file_source_path):
                file_util.copy_file(str(file_source_path), outgoing_s3_path)
            else:
                file_util.upload_to_s3(str(file_source_path), outgoing_s3_path)
        else:
            if not file_util.is_s3_path(file_source_path):
                file_util.copy_file(str(file_source_path), outgoing_s3_path)
            else:
                file_util.download_from_s3(str(file_source_path), outgoing_s3_path)

        logger.info("claimant address validation report file added")
        return ReferenceFile(
            file_location=os.path.join(address_report_source_path, file_name),
            reference_file_type_id=ReferenceFileType.CLAIMANT_ADDRESS_VALIDATION_REPORT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )

    # Updated the code as it was not pulling in the correct state description
    def address_to_experian_suggestion_text_format(self, address: Address) -> str:

        address_lines = [address.address_line_one, address.address_line_two]
        address_line_str = " ".join([p for p in address_lines if p])

        postal_parts = [
            str(p)
            for p in [
                address.city,
                GeoState.get_description(address.geo_state_id) if address.geo_state_id else None,
                address.zip_code,
            ]
            if p
        ]
        postal_part_str = " ".join([p for p in postal_parts if p])

        return ", ".join([address_line_str, postal_part_str])

    """Formats the address lines to
        one suitable for experian cal
        self, experian_soap_client: soap_api.Cll and then makes the soap call.
        This chain of methods had to be updated to pick up state code correctly.
    """

    def _experian_soap_response_for_address(
        self, experian_soap_client: soap_api.Client, address: Address
    ) -> sm.SearchResponse:
        request = self.address_to_experian_verification_search(address)
        return experian_soap_client.search(request)

    def address_to_experian_verification_search(self, address: Address) -> sm.SearchRequest:
        return sm.SearchRequest(
            engine=sm.EngineEnum.VERIFICATION,
            search=self.address_to_experian_suggestion_text_format(address),
            layout=Layout.StateMA,
        )

    def _validate_incoming_address(self, employee_data: FineosExtractEmployeeFeed) -> Address:
        address_required = True
        c_value = employee_data.c
        i_value = employee_data.i
        self.validation_container = payments_util.ValidationContainer(
            str(f"C={c_value},I={i_value}")
        )
        address_line_one = payments_util.validate_db_input(
            "address1", employee_data, self.validation_container, address_required
        )
        address_line_two = payments_util.validate_db_input(
            "address2", employee_data, self.validation_container, False
        )
        city = payments_util.validate_db_input(
            "address4", employee_data, self.validation_container, address_required
        )

        state = payments_util.validate_db_input(
            "address6",
            employee_data,
            self.validation_container,
            address_required,
            custom_validator_func=payments_util.lookup_validator(GeoState),
        )

        zip_code = payments_util.validate_db_input(
            "postcode",
            employee_data,
            self.validation_container,
            address_required,
            min_length=5,
            max_length=10,
            custom_validator_func=payments_util.zip_code_validator,
        )
        if self.validation_container.has_validation_issues():
            logger.error(
                "Address validation issues for employee %s", employee_data.employee_feed_id
            )
            logger.error(self.validation_container.validation_issues)
        empty_string = ""
        employee_address = Address(
            address_id=uuid.uuid4(),
            address_line_one=address_line_one if address_line_one else empty_string,
            address_line_two=address_line_two if address_line_two else empty_string,
            city=city if city else empty_string,
            geo_state_id=GeoState.get_id(state) if state else empty_string,
            zip_code=zip_code if zip_code else empty_string,
            address_type_id=AddressType.MAILING.address_type_id,
        )
        return employee_address
