import enum
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    Claim,
    Employee,
    EmployeePubEftPair,
    EmployeeReferenceFile,
    PaymentMethod,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    State,
    TaxIdentifier,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVbiRequestedAbsenceSom,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)

# folder constants
RECEIVED_FOLDER = "received"
PROCESSED_FOLDER = "processed"
SKIPPED_FOLDER = "skipped"
ERRORED_FOLDER = "errored"

REQUESTED_ABSENCES_FILE_NAME = "VBI_REQUESTEDABSENCE_SOM.csv"
EMPLOYEE_FEED_FILE_NAME = "Employee_feed.csv"

expected_file_names = [
    REQUESTED_ABSENCES_FILE_NAME,
    EMPLOYEE_FEED_FILE_NAME,
]


@dataclass
class ExtractMultiple:
    file_location: str
    indexed_data: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)


class ExtractData:
    requested_absence_info: ExtractMultiple
    employee_feed: ExtractMultiple

    date_str: str

    reference_file: ReferenceFile

    def __init__(self, s3_locations: List[str], date_str: str):
        for s3_location in s3_locations:
            if s3_location.endswith(REQUESTED_ABSENCES_FILE_NAME):
                self.requested_absence_info = ExtractMultiple(s3_location)
            elif s3_location.endswith(EMPLOYEE_FEED_FILE_NAME):
                self.employee_feed = ExtractMultiple(s3_location)

        self.date_str = date_str

        self.reference_file = ReferenceFile(
            file_location=os.path.join(
                payments_config.get_s3_config().pfml_fineos_extract_archive_path,
                "received",
                self.date_str,
            ),
            reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        logger.debug("Intialized extract data: %s", self.reference_file.file_location)


class ClaimantData:
    """
    A class for containing any and all claim/claimant data. Handles validation
    and pulling values out of the dictionaries of the files we processed.
    """

    validation_container: payments_util.ValidationContainer

    count_incrementer: Optional[Callable[[str], None]]

    absence_case_id: str
    is_id_proofed: bool = False

    fineos_notification_id: Optional[str] = None
    claim_type_raw: Optional[str] = None
    absence_case_status: Optional[str] = None
    absence_start_date: Optional[str] = None
    absence_end_date: Optional[str] = None

    fineos_customer_number: Optional[str] = None
    employee_tax_identifier: Optional[str] = None
    date_of_birth: Optional[str] = None
    payment_method: Optional[str] = None

    routing_nbr: Optional[str] = None
    account_nbr: Optional[str] = None
    account_type: Optional[str] = None
    should_do_eft_operations: bool = False

    def __init__(
        self,
        extract_data: ExtractData,
        absence_case_id: str,
        requested_absences: List[Dict[str, str]],
        count_incrementer: Optional[Callable[[str], None]] = None,
    ):
        self.absence_case_id = absence_case_id
        self.validation_container = payments_util.ValidationContainer(self.absence_case_id)

        self.count_incrementer = count_incrementer

        self._process_requested_absences(requested_absences)
        self._process_employee_feed(extract_data)

    def _process_requested_absences(self, requested_absences: List[Dict[str, str]]) -> None:
        for requested_absence in requested_absences:
            # If any of the requested absence records are ID proofed, then
            # we consider the entire claim valid
            evidence_result_type = requested_absence.get("LEAVEREQUEST_EVIDENCERESULTTYPE")
            if evidence_result_type == "Satisfied":
                self.is_id_proofed = True
                break

        # Ideally, we would be able to distinguish and separate out the
        # various leave requests that make up a claim, but we don't
        # have this concept in our system at the moment. Until we support
        # that, we're leaving these other fields alone and always choosing the
        # latest one to keep the behavior identical, but incorrect
        requested_absence = requested_absences[-1]

        # Note this should be identical regardless of absence case
        self.fineos_notification_id = payments_util.validate_csv_input(
            "NOTIFICATION_CASENUMBER", requested_absence, self.validation_container, True
        )
        self.claim_type_raw = payments_util.validate_csv_input(
            "ABSENCEREASON_COVERAGE", requested_absence, self.validation_container, True
        )

        self.absence_case_status = payments_util.validate_csv_input(
            "ABSENCE_CASESTATUS",
            requested_absence,
            self.validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(AbsenceStatus),
        )

        self.absence_start_date = payments_util.validate_csv_input(
            "ABSENCEPERIOD_START", requested_absence, self.validation_container, True
        )

        self.absence_end_date = payments_util.validate_csv_input(
            "ABSENCEPERIOD_END", requested_absence, self.validation_container, True
        )

        # Note this should be identical regardless of absence case
        self.fineos_customer_number = payments_util.validate_csv_input(
            "EMPLOYEE_CUSTOMERNO", requested_absence, self.validation_container, True
        )

    def _process_employee_feed(self, extract_data: ExtractData) -> None:
        # If there isn't a FINEOS Customer Number, we can't lookup the employee record
        if not self.fineos_customer_number:
            return

        # The employee feed data is a list of records associated
        # with the employee feed. There will be a mix of records with
        # DEFPAYMENTPREF set to Y/N. Y indicating that it's the default payment
        # preference. We always prefer the default, but there can be many of each.
        employee_feed_records = extract_data.employee_feed.indexed_data.get(
            self.fineos_customer_number
        )
        if employee_feed_records is None:
            error_msg = (
                f"Employee in VBI_REQUESTEDABSENCE_SOM with absence id {self.absence_case_id} and customer nbr {self.fineos_customer_number} "
                "not found in employee feed file"
            )
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, error_msg
            )
            logger.warning(
                "Skipping: %s", error_msg, extra=self.get_traceable_details(),
            )
            if self.count_incrementer:
                self.count_incrementer(
                    ClaimantExtractStep.Metrics.NO_EMPLOYEE_FEED_RECORDS_FOUND_COUNT
                )

            # Can't process subsequent records as they pull from employee_feed
            return

        employee_feed = self._determine_employee_feed_info(employee_feed_records)

        self.employee_tax_identifier = payments_util.validate_csv_input(
            "NATINSNO", employee_feed, self.validation_container, True
        )

        self.date_of_birth = payments_util.validate_csv_input(
            "DATEOFBIRTH", employee_feed, self.validation_container, True
        )

        self._process_payment_preferences(employee_feed)

    def _process_payment_preferences(self, employee_feed: Dict[str, str]) -> None:
        # We only care about the payment preference fields if it is the default payment
        # preference record, otherwise we can't set these fields
        is_default_payment_pref = employee_feed.get("DEFPAYMENTPREF") == "Y"
        if not is_default_payment_pref:
            message = f"No default payment preference set for FINEOS customer number {self.fineos_customer_number}"
            logger.warning(message, extra=self.get_traceable_details())
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, message
            )
            if self.count_incrementer:
                self.count_incrementer(
                    ClaimantExtractStep.Metrics.NO_DEFAULT_PAYMENT_PREFERENCE_COUNT
                )
            return

        self.payment_method = payments_util.validate_csv_input(
            "PAYMENTMETHOD",
            employee_feed,
            self.validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(
                PaymentMethod,
                disallowed_lookup_values=[
                    cast(str, PaymentMethod.DEBIT.payment_method_description)
                ],
            ),
        )

        eft_required = self.payment_method == PaymentMethod.ACH.payment_method_description
        if eft_required:
            nbr_of_validation_issues = len(self.validation_container.validation_issues)

            self.routing_nbr = payments_util.validate_csv_input(
                "SORTCODE",
                employee_feed,
                self.validation_container,
                eft_required,
                min_length=9,
                max_length=9,
            )

            self.account_nbr = payments_util.validate_csv_input(
                "ACCOUNTNO", employee_feed, self.validation_container, eft_required, max_length=40,
            )

            self.account_type = payments_util.validate_csv_input(
                "ACCOUNTTYPE",
                employee_feed,
                self.validation_container,
                eft_required,
                custom_validator_func=payments_util.lookup_validator(BankAccountType),
            )

            if nbr_of_validation_issues == len(self.validation_container.validation_issues):
                self.should_do_eft_operations = True

    def _determine_employee_feed_info(
        self, employee_feed_records: List[Dict[str, str]]
    ) -> Dict[str, str]:
        # No records shouldn't be possible
        # based on the calling logic, but this
        # makes the linter happy
        if len(employee_feed_records) == 0:
            return {}

        # If there is only one record, just use it
        if len(employee_feed_records) == 1:
            return employee_feed_records[0]

        # Try filtering to just DEFPAYMENTPREF = 'Y'
        defpaymentpref_records = list(
            filter(lambda record: record.get("DEFPAYMENTPREF") == "Y", employee_feed_records)
        )

        # If there are any default payment preference records
        # Just use one of them, they should all be identical
        if len(defpaymentpref_records) > 0:
            return defpaymentpref_records[0]

        # Otherwise, we're fine with any DEFPAYMENTPREF value here
        return employee_feed_records[0]

    def get_traceable_details(self) -> Dict[str, Optional[Any]]:
        return {
            "absence_case_id": self.absence_case_id,
            "fineos_customer_number": self.fineos_customer_number,
        }


class ClaimantExtractStep(Step):
    class Metrics(str, enum.Enum):
        CLAIM_NOT_FOUND_COUNT = "claim_not_found_count"
        EFT_FOUND_COUNT = "eft_found_count"
        EFT_REJECTED_COUNT = "eft_rejected_count"
        EMPLOYEE_FEED_RECORD_COUNT = "employee_feed_record_count"
        EMPLOYEE_NOT_FOUND_IN_FEED_COUNT = "employee_not_found_in_feed_count"
        EMPLOYEE_NOT_FOUND_IN_DATABASE_COUNT = "employee_not_found_in_database_count"
        EMPLOYEE_PROCESSED_MULTIPLE_TIMES = "employee_processed_multiple_times"
        ERRORED_CLAIMANT_COUNT = "errored_claimant_count"
        EVIDENCE_NOT_ID_PROOFED_COUNT = "evidence_not_id_proofed_count"
        NEW_EFT_COUNT = "new_eft_count"
        PROCESSED_EMPLOYEE_COUNT = "processed_employee_count"
        PROCESSED_REQUESTED_ABSENCE_COUNT = "processed_requested_absence_count"
        VALID_CLAIMANT_COUNT = "valid_claimant_count"
        VBI_REQUESTED_ABSENCE_SOM_RECORD_COUNT = "vbi_requested_absence_som_record_count"
        NO_EMPLOYEE_FEED_RECORDS_FOUND_COUNT = "no_employee_feed_records_found_count"
        NO_DEFAULT_PAYMENT_PREFERENCE_COUNT = "no_default_payment_preference_count"

    def run_step(self) -> None:
        self.process_claimant_extract_data()

    def process_claimant_extract_data(self) -> None:

        logger.info("Processing claimant extract files")

        payments_util.copy_fineos_data_to_archival_bucket(
            self.db_session, expected_file_names, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        )
        data_by_date = payments_util.group_s3_files_by_date(expected_file_names)
        download_directory = tempfile.mkdtemp().__str__()

        previously_processed_date = set()

        logger.info("Dates in /received folder: %s", ", ".join(data_by_date.keys()))

        if bool(data_by_date):
            latest_date_str = sorted(data_by_date.keys())[-1]

        for date_str, s3_file_locations in data_by_date.items():

            logger.info(
                "Processing files in date group: %s", date_str, extra={"date_group": date_str}
            )

            try:
                extract_data = ExtractData(s3_file_locations, date_str)

                if date_str != latest_date_str:
                    self.move_files_from_received_to_skipped(extract_data)
                    logger.info(
                        "Successfully skipped claimant extract files in date group: %s",
                        date_str,
                        extra={"date_group": date_str},
                    )
                    continue

                if (
                    date_str in previously_processed_date
                    or payments_util.payment_extract_reference_file_exists_by_date_group(
                        self.db_session, date_str, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
                    )
                ):
                    logger.warning(
                        "Found existing ReferenceFile record for date group in /processed folder: %s",
                        date_str,
                        extra={"date_group": date_str},
                    )
                    previously_processed_date.add(date_str)
                    continue

                extract_data = ExtractData(s3_file_locations, date_str)
                self.download_and_index_data(extract_data, download_directory)

                self.process_records_to_db(extract_data)
                self.move_files_from_received_to_processed(extract_data)
                logger.info(
                    "Successfully processed claimant extract files in date group: %s",
                    date_str,
                    extra={"date_group": date_str},
                )
                self.db_session.commit()
            except Exception:
                # If there was a file-level exception anywhere in the processing,
                # we move the file from received to error
                # Add this function:
                self.db_session.rollback()
                logger.exception(
                    "Error processing claimant extract files in date_group: %s",
                    date_str,
                    extra={"date_group": date_str},
                )
                self.move_files_from_received_to_error(extract_data)
                raise

        logger.info("Done processing claimant extract files")

    def download_and_index_data(self, extract_data: ExtractData, download_directory: str) -> None:
        logger.info(
            "Downloading and indexing claimant extract data files.",
            extra={
                "employee_feed_file": extract_data.employee_feed.file_location,
                "requested_absence_file": extract_data.requested_absence_info.file_location,
            },
        )
        ref_file = extract_data.reference_file

        # Index employee file for easy search.
        employee_indexed_data: Dict[str, List[Dict[str, str]]] = {}
        employee_rows = payments_util.download_and_parse_csv(
            extract_data.employee_feed.file_location, download_directory
        )

        for row in employee_rows:
            # We want to cache all of the employee records for a customer number
            # We will filter this down later.
            index = str(row.get("CUSTOMERNO"))
            if index not in employee_indexed_data:
                employee_indexed_data[index] = []

            employee_indexed_data[index].append(row)
            logger.debug(
                "indexed employee feed file row with Customer NO: %s", index,
            )

            lower_key_record = payments_util.make_keys_lowercase(row)
            employee_feed_record = payments_util.create_staging_table_instance(
                lower_key_record, FineosExtractEmployeeFeed, ref_file, self.get_import_log_id()
            )
            self.db_session.add(employee_feed_record)
            self.increment(self.Metrics.EMPLOYEE_FEED_RECORD_COUNT)

        extract_data.employee_feed.indexed_data = employee_indexed_data

        requested_absence_indexed_data: Dict[str, List[Dict[str, str]]] = {}
        requested_absence_rows = payments_util.download_and_parse_csv(
            extract_data.requested_absence_info.file_location, download_directory
        )
        for row in requested_absence_rows:
            # Multiple leaves can be associated with the same absence case number
            index = str(row.get("ABSENCE_CASENUMBER"))
            if index not in requested_absence_indexed_data:
                requested_absence_indexed_data[index] = []

            requested_absence_indexed_data[index].append(row)
            logger.debug("indexed requested absence file row with Absence case no: %s", index)

            lower_key_record = payments_util.make_keys_lowercase(row)
            vbi_requested_absence_som_record = payments_util.create_staging_table_instance(
                lower_key_record,
                FineosExtractVbiRequestedAbsenceSom,
                ref_file,
                self.get_import_log_id(),
            )
            self.db_session.add(vbi_requested_absence_som_record)
            self.increment(self.Metrics.VBI_REQUESTED_ABSENCE_SOM_RECORD_COUNT)

        extract_data.requested_absence_info.indexed_data = requested_absence_indexed_data

        logger.info("Successfully downloaded and indexed claimant extract data files.")

    def process_records_to_db(self, extract_data: ExtractData) -> None:
        logger.info("Processing claimant extract data into db: %s", extract_data.date_str)

        updated_employee_ids = set()
        for (
            absence_case_id,
            requested_absences,
        ) in extract_data.requested_absence_info.indexed_data.items():
            if not absence_case_id:
                logger.error(
                    "Rows in the requested absence SOM file were missing ABSENCE_CASENUMBER"
                )
                continue

            self.increment(self.Metrics.PROCESSED_REQUESTED_ABSENCE_COUNT)
            claimant_data = ClaimantData(
                extract_data, absence_case_id, requested_absences, self.increment
            )

            logger.info(
                "Processing absence_case_id %s",
                absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )

            if not claimant_data.is_id_proofed:
                logger.info(
                    "Absence_case_id %s is not id proofed yet",
                    absence_case_id,
                    extra=claimant_data.get_traceable_details(),
                )
                self.increment(self.Metrics.EVIDENCE_NOT_ID_PROOFED_COUNT)

            employee_pfml_entry = None
            try:
                # Add / update entry on claim table
                claim = self.create_or_update_claim(claimant_data)
            except Exception as e:
                logger.exception(
                    "Unexpected error %s while processing claim: %s",
                    type(e),
                    absence_case_id,
                    extra=claimant_data.get_traceable_details(),
                )
                # TODO: Add some logging that indicates that we errored while trying to create
                # a claim.

                continue

            try:
                # Update employee info
                if claim is not None:
                    employee_pfml_entry = self.update_employee_info(claimant_data, claim)
            except Exception as e:
                logger.exception(
                    "Unexpected error %s while processing claimant: %s",
                    type(e),
                    absence_case_id,
                    extra=claimant_data.get_traceable_details(),
                )
                self.increment(self.Metrics.ERRORED_CLAIMANT_COUNT)
                continue

            if employee_pfml_entry is not None:
                if employee_pfml_entry.employee_id not in updated_employee_ids:
                    self.generate_employee_reference_file(extract_data, employee_pfml_entry)

                    self.manage_state_log(extract_data, employee_pfml_entry, claimant_data)

                    updated_employee_ids.add(employee_pfml_entry.employee_id)
                else:
                    logger.info(
                        "Skipping adding a reference file and state_log for employee %s",
                        employee_pfml_entry.employee_id,
                    )
                    self.increment(self.Metrics.EMPLOYEE_PROCESSED_MULTIPLE_TIMES)

        logger.info(
            "Successfully processed claimant extract data into db: %s", extract_data.date_str
        )
        return None

    def create_or_update_claim(self, claimant_data: ClaimantData) -> Claim:
        claim_pfml: Optional[Claim] = self.db_session.query(Claim).filter(
            Claim.fineos_absence_id == claimant_data.absence_case_id
        ).one_or_none()

        if claim_pfml is None:
            claim_pfml = Claim(claim_id=uuid.uuid4())
            claim_pfml.fineos_absence_id = claimant_data.absence_case_id
            logger.info(
                "No existing claim found for absence_case_id: %s",
                claimant_data.absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )
            # Note that this claim might not get made if there are
            # validation issues found for the claimant
            self.increment(self.Metrics.CLAIM_NOT_FOUND_COUNT)
        else:
            logger.info(
                "Found existing claim for absence_case_id: %s",
                claimant_data.absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )

        if claimant_data.fineos_notification_id is not None:
            claim_pfml.fineos_notification_id = claimant_data.fineos_notification_id

        # Get claim type.
        if claimant_data.claim_type_raw:
            try:
                claim_type_mapped = payments_util.get_mapped_claim_type(
                    claimant_data.claim_type_raw
                )
                claim_pfml.claim_type_id = claim_type_mapped.claim_type_id
            except ValueError:
                claimant_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.INVALID_VALUE, "ABSENCEREASON_COVERAGE"
                )

        if claimant_data.absence_case_status is not None:
            claim_pfml.fineos_absence_status_id = AbsenceStatus.get_id(
                claimant_data.absence_case_status
            )

        if claimant_data.absence_start_date is not None:
            claim_pfml.absence_period_start_date = payments_util.datetime_str_to_date(
                claimant_data.absence_start_date
            )

        if claimant_data.absence_end_date is not None:
            claim_pfml.absence_period_end_date = payments_util.datetime_str_to_date(
                claimant_data.absence_end_date
            )

        claim_pfml.is_id_proofed = claimant_data.is_id_proofed

        # Return claim, we want to create this even if the employee
        # has issues or there were some validation issues
        self.db_session.add(claim_pfml)

        return claim_pfml

    def update_employee_info(self, claimant_data: ClaimantData, claim: Claim) -> Optional[Employee]:
        """Returns the employee if found and updates its info"""
        self.increment(self.Metrics.PROCESSED_EMPLOYEE_COUNT)

        if not claimant_data.employee_tax_identifier:
            self.increment(self.Metrics.EMPLOYEE_NOT_FOUND_IN_FEED_COUNT)
            return None

        employee_pfml_entry = None
        try:
            tax_identifier_id = (
                self.db_session.query(TaxIdentifier.tax_identifier_id)
                .filter(TaxIdentifier.tax_identifier == claimant_data.employee_tax_identifier)
                .one_or_none()
            )
            if tax_identifier_id is not None:
                employee_pfml_entry = (
                    self.db_session.query(Employee)
                    .filter(Employee.tax_identifier_id == tax_identifier_id)
                    .one_or_none()
                )

        except SQLAlchemyError as e:
            logger.exception(
                "Unexpected error %s with one_or_none when querying for tin/employee",
                type(e),
                extra=claimant_data.get_traceable_details(),
            )
            raise

        # Assumption is we should not be creating employees in the PFML DB through this extract.
        if employee_pfml_entry is None:
            logger.warning(
                f"Employee in employee file with customer nbr {claimant_data.fineos_customer_number} not found in PFML DB.",
            )

            self.increment(self.Metrics.EMPLOYEE_NOT_FOUND_IN_DATABASE_COUNT)
            return None

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            self.db_session, employee_pfml_entry, commit=False
        ):
            # Use employee feed entry to update PFML DB
            if claimant_data.date_of_birth is not None:
                employee_pfml_entry.date_of_birth = payments_util.datetime_str_to_date(
                    claimant_data.date_of_birth
                )

            if claimant_data.fineos_customer_number is not None:
                employee_pfml_entry.fineos_customer_number = claimant_data.fineos_customer_number

            self.update_eft_info(claimant_data, employee_pfml_entry)

            # Associate claim with employee in case it is a new claim.
            claim.employee_id = employee_pfml_entry.employee_id

            self.db_session.add(employee_pfml_entry)

        return employee_pfml_entry

    def update_eft_info(self, claimant_data: ClaimantData, employee_pfml_entry: Employee,) -> None:
        """Updates EFT info and starts prenoting process if necessary"""

        if claimant_data.should_do_eft_operations:
            # Always create an EFT object, we'll use this
            # to try and find an existing match of PUB eft info
            # Casts satisfy picky linting on values we validated above
            new_eft = PubEft(
                pub_eft_id=uuid.uuid4(),
                routing_nbr=cast(str, claimant_data.routing_nbr),
                account_nbr=cast(str, claimant_data.account_nbr),
                bank_account_type_id=BankAccountType.get_id(claimant_data.account_type),
                prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id,  # If this is new, we want it to be pending
            )

            existing_eft = payments_util.find_existing_eft(employee_pfml_entry, new_eft)
            # If we found a match, do not need to create anything
            # but do need to add an error to the report if the EFT
            # information is invalid
            if existing_eft:
                self.increment(self.Metrics.EFT_FOUND_COUNT)
                logger.info(
                    "Found existing EFT info for claimant in prenote state %s",
                    existing_eft.prenote_state.prenote_state_description,
                    extra={
                        "employee_id": employee_pfml_entry.employee_id,
                        "pub_eft_id": existing_eft.pub_eft_id,
                    },
                )
                if existing_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id:
                    claimant_data.validation_container.add_validation_issue(
                        payments_util.ValidationReason.EFT_PRENOTE_REJECTED,
                        "EFT prenote was rejected - cannot pay with this account info",
                    )
                    self.increment(self.Metrics.EFT_REJECTED_COUNT)

            else:
                self.increment(self.Metrics.NEW_EFT_COUNT)
                # This EFT info is new, it needs to be linked to the employee
                # and added to the EFT prenoting flow
                logger.info(
                    "Initiating DELEGATED_EFT flow for employee",
                    extra={
                        "end_state_id": State.DELEGATED_EFT_SEND_PRENOTE.state_id,
                        "employee_id": employee_pfml_entry.employee_id,
                    },
                )

                employee_pub_eft_pair = EmployeePubEftPair(
                    employee_id=employee_pfml_entry.employee_id, pub_eft_id=new_eft.pub_eft_id
                )
                self.db_session.add(new_eft)
                self.db_session.add(employee_pub_eft_pair)

                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_EFT_SEND_PRENOTE,
                    associated_model=employee_pfml_entry,
                    import_log_id=self.get_import_log_id(),
                    outcome=state_log_util.build_outcome(
                        "Claimant with new EFT information found, adding to the EFT flow"
                    ),
                    db_session=self.db_session,
                )

    def generate_employee_reference_file(
        self, extract_data: ExtractData, employee_pfml_entry: Employee
    ) -> None:
        """Create an EmployeeReferenceFile record if none already exists

        This will not create duplicate records if the employee appears multiple
        times in the same claimant extract.
        """

        # Check to see if an EmployeeReferenceFile record already exists
        # TODO -- We should eliminate this db query by tracking employees that
        #         have already appeared in this file, but beware of memory issues
        #         in case the number is too big to store in a list
        employee_reference_file = (
            self.db_session.query(EmployeeReferenceFile)
            .filter(
                EmployeeReferenceFile.employee_id == employee_pfml_entry.employee_id,
                EmployeeReferenceFile.reference_file_id
                == extract_data.reference_file.reference_file_id,
            )
            .first()
        )

        # If none exists, create one
        if employee_reference_file is None:
            logger.info(
                "Creating an EmployeeReferenceFile for employee with customer nbr %s and reference file with reference_file_id %s",
                employee_pfml_entry.fineos_customer_number,
                extract_data.reference_file.reference_file_id,
                extra={
                    "fineos_customer_number": employee_pfml_entry.fineos_customer_number,
                    "reference_file_id": extract_data.reference_file.reference_file_id,
                },
            )
            employee_reference_file = EmployeeReferenceFile(
                employee=employee_pfml_entry, reference_file=extract_data.reference_file,
            )
            self.db_session.add(employee_reference_file)

        # If one exists, skip
        else:
            logger.info(
                "An EmployeeReferenceFile already exists for employee with customer nbr %s and reference file with reference_file_id %s",
                employee_pfml_entry.fineos_customer_number,
                extract_data.reference_file.reference_file_id,
                extra={
                    "fineos_customer_number": employee_pfml_entry.fineos_customer_number,
                    "reference_file_id": extract_data.reference_file.reference_file_id,
                },
            )

    def manage_state_log(
        self, extract_data: ExtractData, employee_pfml_entry: Employee, claimant_data: ClaimantData
    ) -> None:
        """Manages the DELEGATED_CLAIMANT states"""
        validation_container = claimant_data.validation_container
        validation_container.record_key = employee_pfml_entry.employee_id

        # If there are validation issues, add to claimant extract error report.
        if validation_container.has_validation_issues():
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_CLAIMANT_ADD_TO_CLAIMANT_EXTRACT_ERROR_REPORT,
                associated_model=employee_pfml_entry,
                import_log_id=self.get_import_log_id(),
                outcome=state_log_util.build_outcome(
                    f"Employee {employee_pfml_entry.employee_id} had validation issues in FINEOS claimant extract {extract_data.date_str}",
                    validation_container,
                ),
                db_session=self.db_session,
            )
            self.increment(self.Metrics.ERRORED_CLAIMANT_COUNT)

        else:
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS,
                associated_model=employee_pfml_entry,
                import_log_id=self.get_import_log_id(),
                outcome=state_log_util.build_outcome(
                    f"Employee {employee_pfml_entry.employee_id} successfully extracted from FINEOS claimant extract {extract_data.date_str}"
                ),
                db_session=self.db_session,
            )
            self.increment(self.Metrics.VALID_CLAIMANT_COUNT)

    # TODO move to payments_util
    def move_files_from_received_to_processed(self, extract_data: ExtractData) -> None:
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
        # to
        # s3://bucket/path/to/processed/2020-01-01-11-30-00-payment-extract/2020-01-01-11-30-00-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        )
        new_requested_absence_info_s3_path = extract_data.requested_absence_info.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(
            extract_data.requested_absence_info.file_location, new_requested_absence_info_s3_path
        )
        logger.debug(
            "Moved requested absence info file to processed folder.",
            extra={
                "source": extract_data.requested_absence_info.file_location,
                "destination": new_requested_absence_info_s3_path,
            },
        )

        new_employee_feed_s3_path = extract_data.employee_feed.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.employee_feed.file_location, new_employee_feed_s3_path)
        logger.debug(
            "Moved employee feed file to processed folder.",
            extra={
                "source": extract_data.employee_feed.file_location,
                "destination": new_employee_feed_s3_path,
            },
        )

        # Update the reference file DB record to point to the new folder for these files
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            RECEIVED_FOLDER, PROCESSED_FOLDER
        )
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            extract_data.date_str, date_group_folder
        )
        self.db_session.add(extract_data.reference_file)
        logger.debug(
            "Updated reference file location for claimant extract data.",
            extra={"reference_file_location": extract_data.reference_file.file_location},
        )

        logger.info("Successfully moved claimant files to processed folder.")

    # TODO move to payments_util
    def move_files_from_received_to_skipped(self, extract_data: ExtractData) -> None:
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
        # to
        # s3://bucket/path/to/skipped/2020-01-01-11-30-00-payment-extract/2020-01-01-11-30-00-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        )
        new_requested_absence_info_s3_path = extract_data.requested_absence_info.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(
            extract_data.requested_absence_info.file_location, new_requested_absence_info_s3_path
        )
        logger.debug(
            "Moved requested absence info file to skipped folder.",
            extra={
                "source": extract_data.requested_absence_info.file_location,
                "destination": new_requested_absence_info_s3_path,
            },
        )

        new_employee_feed_s3_path = extract_data.employee_feed.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.employee_feed.file_location, new_employee_feed_s3_path)
        logger.debug(
            "Moved employee feed file to skipped folder.",
            extra={
                "source": extract_data.employee_feed.file_location,
                "destination": new_employee_feed_s3_path,
            },
        )

        # Update the reference file DB record to point to the new folder for these files
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            RECEIVED_FOLDER, SKIPPED_FOLDER
        )
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            extract_data.date_str, date_group_folder
        )
        self.db_session.add(extract_data.reference_file)
        logger.debug(
            "Updated reference file location for claimant extract data.",
            extra={"reference_file_location": extract_data.reference_file.file_location},
        )

        logger.info("Successfully moved claimant files to skipped folder.")

    # TODO move to payments_util
    def move_files_from_received_to_error(self, extract_data: ExtractData) -> None:
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-file.csv
        # to
        # s3://bucket/path/to/errored/2020-01-01/2020-01-01-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        )
        new_requested_absence_info_s3_path = extract_data.requested_absence_info.file_location.replace(
            RECEIVED_FOLDER, f"{ERRORED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(
            extract_data.requested_absence_info.file_location, new_requested_absence_info_s3_path
        )
        logger.debug(
            "Moved requested absence info file to error folder.",
            extra={
                "source": extract_data.requested_absence_info.file_location,
                "destination": new_requested_absence_info_s3_path,
            },
        )

        new_employee_feed_s3_path = extract_data.employee_feed.file_location.replace(
            RECEIVED_FOLDER, f"{ERRORED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.employee_feed.file_location, new_employee_feed_s3_path)
        logger.debug(
            "Moved employee feed file to error folder.",
            extra={
                "source": extract_data.employee_feed.file_location,
                "destination": new_employee_feed_s3_path,
            },
        )

        # We still want to create the reference file, just use the one that is
        # created in the __init__ of the extract data object and set the path.
        # Note that this will not be attached to a payment
        extract_data.reference_file.file_location = file_util.get_directory(
            new_requested_absence_info_s3_path
        )
        self.db_session.add(extract_data.reference_file)
        logger.debug(
            "Updated reference file location for claimant extract data.",
            extra={"reference_file_location": extract_data.reference_file.file_location},
        )

        logger.info("Successfully moved claimant files to error folder.")
