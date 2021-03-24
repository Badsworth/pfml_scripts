import os
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Address,
    BankAccountType,
    Claim,
    CtrAddressPair,
    Employee,
    EmployeeAddress,
    EmployeePubEftPair,
    EmployeeReferenceFile,
    GeoState,
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
class Extract:
    file_location: str
    indexed_data: Dict[str, Dict[str, str]] = field(default_factory=dict)


class ExtractData:
    requested_absence_info: Extract
    employee_feed: Extract

    date_str: str

    reference_file: ReferenceFile

    def __init__(self, s3_locations: List[str], date_str: str):
        for s3_location in s3_locations:
            if s3_location.endswith(REQUESTED_ABSENCES_FILE_NAME):
                self.requested_absence_info = Extract(s3_location)
            elif s3_location.endswith(EMPLOYEE_FEED_FILE_NAME):
                self.employee_feed = Extract(s3_location)

        self.date_str = date_str

        self.reference_file = ReferenceFile(
            file_location=os.path.join(
                payments_config.get_s3_config().pfml_fineos_inbound_path, "received", self.date_str
            ),
            reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        logger.debug("Intialized extract data: %s", self.reference_file.file_location)


class ClaimantExtractStep(Step):
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

                self.extract_to_staging_tables(extract_data)

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

    # TODO move to payments_util
    def download_and_index_data(self, extract_data: ExtractData, download_directory: str) -> None:
        logger.info(
            "Downloading and indexing claimant extract data files.",
            extra={
                "employee_feed_file": extract_data.employee_feed.file_location,
                "requested_absence_file": extract_data.requested_absence_info.file_location,
            },
        )

        # Index employee file for easy search.
        employee_indexed_data: Dict[str, Dict[str, str]] = {}
        employee_rows = payments_util.download_and_parse_csv(
            extract_data.employee_feed.file_location, download_directory
        )

        for row in employee_rows:
            default_payment_flag = row.get("DEFPAYMENTPREF")
            if default_payment_flag is not None and default_payment_flag == "Y":
                employee_indexed_data[str(row.get("CUSTOMERNO"))] = row
                logger.debug(
                    "indexed employee feed file row with Customer NO: %s",
                    str(row.get("CUSTOMERNO")),
                )
        extract_data.employee_feed.indexed_data = employee_indexed_data

        requested_absence_indexed_data: Dict[str, Dict[str, str]] = {}
        requested_absence_rows = payments_util.download_and_parse_csv(
            extract_data.requested_absence_info.file_location, download_directory
        )
        for row in requested_absence_rows:
            requested_absence_indexed_data[str(row.get("ABSENCE_CASENUMBER"))] = row
            logger.debug(
                "indexed requested absence file row with Absence case no: %s",
                str(row.get("ABSENCE_CASENUMBER")),
            )

        extract_data.requested_absence_info.indexed_data = requested_absence_indexed_data

        logger.info("Successfully downloaded and indexed claimant extract data files.")

    def process_records_to_db(self, extract_data: ExtractData) -> None:
        logger.info("Processing claimant extract data into db: %s", extract_data.date_str)

        requested_absences = extract_data.requested_absence_info.indexed_data.values()
        updated_employee_ids = set()
        for requested_absence in requested_absences:
            self.increment("processed_requested_absence_count")
            absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
            # TODO should we skip if absence case id is None?
            if absence_case_id is not None:
                logger.info(
                    "Processing absence_case_id %s",
                    absence_case_id,
                    extra={"absence_case_id": absence_case_id},
                )
            evidence_result_type = requested_absence.get("LEAVEREQUEST_EVIDENCERESULTTYPE")
            if evidence_result_type is None or evidence_result_type != "Satisfied":
                if absence_case_id is not None:
                    logger.info(
                        "Skipping: absence_case_id %s is not id proofed",
                        absence_case_id,
                        extra={"absence_case_id": absence_case_id},
                    )
                    self.increment("evidence_not_id_proofed_count")
                continue

            employee_pfml_entry = None
            try:
                # Add / update entry on claim table
                validation_container, claim = self.create_or_update_claim(
                    extract_data, requested_absence
                )

                # Update employee info
                if claim is not None:
                    employee_pfml_entry = self.update_employee_info(
                        extract_data, requested_absence, claim, validation_container
                    )
            except Exception as e:
                logger.exception(
                    "Unexpected error %s while processing claimant: %s",
                    type(e),
                    absence_case_id,
                    extra={"absence_case_id": absence_case_id},
                )
                continue

            if employee_pfml_entry is not None:
                if employee_pfml_entry.employee_id not in updated_employee_ids:
                    self.generate_employee_reference_file(
                        extract_data, employee_pfml_entry, validation_container
                    )

                    self.manage_state_log(extract_data, employee_pfml_entry, validation_container)

                    updated_employee_ids.add(employee_pfml_entry.employee_id)
                else:
                    logger.info(
                        "Skipping adding a reference file and state_log for employee %s",
                        employee_pfml_entry.employee_id,
                    )

        logger.info(
            "Successfully processed claimant extract data into db: %s", extract_data.date_str
        )
        return None

    def create_or_update_claim(
        self, extract_data: ExtractData, requested_absence: Dict[str, str],
    ) -> Tuple[payments_util.ValidationContainer, Claim]:
        absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
        validation_container = payments_util.ValidationContainer(absence_case_id)
        try:
            claim_pfml: Optional[Claim] = self.db_session.query(Claim).filter(
                Claim.fineos_absence_id == absence_case_id
            ).one_or_none()
        except SQLAlchemyError as e:
            logger.exception(
                "Unexpected error %s with one_or_none when querying for claim",
                type(e),
                extra={"absence_case_id": absence_case_id},
            )
            raise

        if claim_pfml is None:
            claim_pfml = Claim(claim_id=uuid.uuid4())
            claim_pfml.fineos_absence_id = absence_case_id
            logger.info(
                "Creating new claim for absence_case_id: %s",
                absence_case_id,
                extra={"absence_case_id": absence_case_id},
            )
            self.increment("claim_created_count")
        else:
            logger.info(
                "Found existing claim for absence_case_id: %s",
                absence_case_id,
                extra={"absence_case_id": absence_case_id},
            )

        # Update, or finish formatting new,  claim row.
        # TODO: Couldn't this overwrite the db with an empty value if it's missing?
        claim_pfml.fineos_notification_id = requested_absence.get("NOTIFICATION_CASENUMBER")

        # Get claim type.
        claim_type_header = "ABSENCEREASON_COVERAGE"
        claim_type_raw = requested_absence.get(claim_type_header)
        if claim_type_raw:
            try:
                claim_type_mapped = payments_util.get_mapped_claim_type(claim_type_raw)
                claim_pfml.claim_type_id = claim_type_mapped.claim_type_id
            except ValueError:
                validation_container.add_validation_issue(
                    payments_util.ValidationReason.INVALID_VALUE, claim_type_header
                )
        else:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_FIELD, claim_type_header
            )

        case_status = payments_util.validate_csv_input(
            "ABSENCE_CASESTATUS",
            requested_absence,
            validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(AbsenceStatus),
        )

        if case_status is not None:
            try:
                claim_pfml.fineos_absence_status_id = AbsenceStatus.get_id(case_status)
            except KeyError:
                pass

        absence_start_date = payments_util.validate_csv_input(
            "ABSENCEPERIOD_START", requested_absence, validation_container, True
        )

        if absence_start_date is not None:
            claim_pfml.absence_period_start_date = payments_util.datetime_str_to_date(
                absence_start_date
            )

        absence_end_date = payments_util.validate_csv_input(
            "ABSENCEPERIOD_END", requested_absence, validation_container, True
        )

        if absence_end_date is not None:
            claim_pfml.absence_period_end_date = payments_util.datetime_str_to_date(
                absence_end_date
            )

        evidence_result_type = requested_absence.get("LEAVEREQUEST_EVIDENCERESULTTYPE")
        claim_pfml.is_id_proofed = evidence_result_type == "Satisfied"

        # Return claim but do not persist to DB as it should not be persisted
        # if employee info cannot be found in PFML DB.

        return validation_container, claim_pfml

    def update_employee_info(
        self,
        extract_data: ExtractData,
        requested_absence: Dict[str, str],
        claim: Claim,
        validation_container: payments_util.ValidationContainer,
    ) -> Optional[Employee]:
        """Returns the employee if found and updates its info"""
        fineos_customer_number = payments_util.validate_csv_input(
            "EMPLOYEE_CUSTOMERNO", requested_absence, validation_container, True
        )

        if fineos_customer_number is None:
            employee_feed_entry = None
        else:
            employee_feed_entry = extract_data.employee_feed.indexed_data.get(
                fineos_customer_number
            )

        # As we filter out all employee feed entries that do not have the default payment flag
        # set to Y this may be a possible condition: employee exists in FINEOS but has no
        # payment address set properly.
        if employee_feed_entry is None:
            absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
            error_msg = (
                f"Employee in VBI_REQUESTEDABSENCE_SOM with absence id {absence_case_id} and customer nbr {fineos_customer_number} "
                "not found in employee feed file with default payment flag set to Y."
            )
            validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, error_msg
            )
            logger.warning(
                "Skipping: %s",
                error_msg,
                extra={
                    "absence_case_id": absence_case_id,
                    "fineos_customer_number": fineos_customer_number,
                },
            )
            self.increment("employee_not_found_count")
            return None

        employee_tax_identifier = payments_util.validate_csv_input(
            "NATINSNO", employee_feed_entry, validation_container, True
        )

        employee_pfml_entry = None

        if employee_tax_identifier is not None:
            try:
                tax_identifier_id = (
                    self.db_session.query(TaxIdentifier.tax_identifier_id)
                    .filter(TaxIdentifier.tax_identifier == employee_tax_identifier)
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
                    extra={
                        "absence_case_id": absence_case_id,
                        "fineos_customer_number": fineos_customer_number,
                    },
                )
                raise

        # Assumption is we should not be creating employees in the PFML DB through this extract.
        if employee_pfml_entry is None:
            logger.exception(
                f"Employee in employee file with customer nbr {fineos_customer_number} not found in PFML DB.",
            )
            return None

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            self.db_session, employee_pfml_entry, commit=False
        ):
            # Use employee feed entry to update PFML DB
            date_of_birth = payments_util.validate_csv_input(
                "DATEOFBIRTH", employee_feed_entry, validation_container, True
            )

            if date_of_birth is not None:
                employee_pfml_entry.date_of_birth = payments_util.datetime_str_to_date(
                    date_of_birth
                )

            self.update_mailing_address(
                employee_feed_entry, employee_pfml_entry, validation_container
            )

            payment_method = payments_util.validate_csv_input(
                "PAYMENTMETHOD",
                employee_feed_entry,
                validation_container,
                True,
                custom_validator_func=payments_util.lookup_validator(
                    PaymentMethod,
                    disallowed_lookup_values=[
                        cast(str, PaymentMethod.DEBIT.payment_method_description)
                    ],
                ),
            )

            payment_method_id = None
            if payment_method is not None:
                payment_method_id = PaymentMethod.get_id(payment_method)

            self.update_eft_info(
                employee_feed_entry, employee_pfml_entry, payment_method_id, validation_container
            )

            fineos_customer_number = payments_util.validate_csv_input(
                "CUSTOMERNO", employee_feed_entry, validation_container, True
            )

            if fineos_customer_number is not None:
                employee_pfml_entry.fineos_customer_number = fineos_customer_number

            # Associate claim with employee in case it is a new claim.
            claim.employee_id = employee_pfml_entry.employee_id

            if len(validation_container.validation_issues) == 0:
                self.db_session.add(employee_pfml_entry)
                self.db_session.add(claim)

        return employee_pfml_entry

    def update_mailing_address(
        self,
        employee_feed_entry: Dict[str, str],
        employee_pfml_entry: Employee,
        validation_container: payments_util.ValidationContainer,
    ) -> bool:
        """Return True if there are mailing address updates; False otherwise"""
        nbr_of_validation_errors = len(validation_container.validation_issues)

        address_line_one = payments_util.validate_csv_input(
            "ADDRESS1", employee_feed_entry, validation_container, True
        )
        address_line_two = payments_util.validate_csv_input(
            "ADDRESS2", employee_feed_entry, validation_container, False
        )
        address_city = payments_util.validate_csv_input(
            "ADDRESS4", employee_feed_entry, validation_container, True
        )
        address_state = payments_util.validate_csv_input(
            "ADDRESS6",
            employee_feed_entry,
            validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(GeoState),
        )
        address_zip_code = payments_util.validate_csv_input(
            "POSTCODE",
            employee_feed_entry,
            validation_container,
            True,
            min_length=5,
            max_length=10,
        )

        if nbr_of_validation_errors == len(validation_container.validation_issues):
            mailing_address = Address(
                address_id=uuid.uuid4(),
                address_line_one=address_line_one,
                address_line_two=address_line_two,
                city=address_city,
                geo_state_id=GeoState.get_id(address_state),
                zip_code=address_zip_code,
            )

            # If ctr_address_pair exists, compare the exisiting fineos_address with the payment_data address
            #   If they're the same, nothing needs to be done, so we can return
            #   If they're different or if no ctr_address_pair exists, create a new CtrAddressPair
            ctr_address_pair = employee_pfml_entry.ctr_address_pair
            if ctr_address_pair:
                if payments_util.is_same_address(ctr_address_pair.fineos_address, mailing_address):
                    return False

            new_ctr_address_pair = CtrAddressPair(fineos_address=mailing_address)
            employee_pfml_entry.ctr_address_pair = new_ctr_address_pair
            self.db_session.add(mailing_address)
            self.db_session.add(new_ctr_address_pair)
            self.db_session.add(employee_pfml_entry)

            # We also want to make sure the address is linked in the EmployeeAddress table
            employee_address = EmployeeAddress(
                employee=employee_pfml_entry, address=mailing_address
            )
            self.db_session.add(employee_address)
            return True

        return False

    def update_eft_info(
        self,
        employee_feed_entry: Dict[str, str],
        employee_pfml_entry: Employee,
        payment_method_id: Optional[int],
        validation_container: payments_util.ValidationContainer,
    ) -> None:
        """Returns True if there have been EFT updates; False otherwise"""
        nbr_of_validation_errors = len(validation_container.validation_issues)
        eft_required = (
            payment_method_id is not None
            and payment_method_id == PaymentMethod.ACH.payment_method_id
        )

        routing_nbr = payments_util.validate_csv_input(
            "SORTCODE",
            employee_feed_entry,
            validation_container,
            eft_required,
            min_length=9,
            max_length=9,
        )

        account_nbr = payments_util.validate_csv_input(
            "ACCOUNTNO", employee_feed_entry, validation_container, eft_required, max_length=40
        )

        account_type = payments_util.validate_csv_input(
            "ACCOUNTTYPE",
            employee_feed_entry,
            validation_container,
            eft_required,
            custom_validator_func=payments_util.lookup_validator(BankAccountType),
        )

        if eft_required and nbr_of_validation_errors == len(validation_container.validation_issues):
            # Always create an EFT object, we'll use this
            # to try and find an existing match of PUB eft info
            # Casts satisfy picky linting on values we validated above
            new_eft = PubEft(
                pub_eft_id=uuid.uuid4(),
                routing_nbr=cast(str, routing_nbr),
                account_nbr=cast(str, account_nbr),
                bank_account_type_id=BankAccountType.get_id(account_type),
                prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id,  # If this is new, we want it to be pending
            )

            existing_eft = payments_util.find_existing_eft(employee_pfml_entry, new_eft)
            # If we found a match, do not need to create anything
            # but do need to add an error to the report if the EFT
            # information is invalid
            if existing_eft:
                logger.info(
                    "Found existing EFT info for claimant in prenote state %s",
                    existing_eft.prenote_state.prenote_state_description,
                    extra={
                        "employee_id": employee_pfml_entry.employee_id,
                        "pub_eft_id": existing_eft.pub_eft_id,
                    },
                )
                if existing_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id:
                    validation_container.add_validation_issue(
                        payments_util.ValidationReason.EFT_PRENOTE_REJECTED,
                        f"EFT prenote was rejected at {existing_eft.prenote_response_at}",
                    )

            else:
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
                    outcome=state_log_util.build_outcome(
                        "Claimant with new EFT information found, adding to the EFT flow"
                    ),
                    db_session=self.db_session,
                )

    def generate_employee_reference_file(
        self,
        extract_data: ExtractData,
        employee_pfml_entry: Employee,
        validation_container: payments_util.ValidationContainer,
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
        self,
        extract_data: ExtractData,
        employee_pfml_entry: Employee,
        validation_container: payments_util.ValidationContainer,
    ) -> None:
        """Manages the DELEGATED_CLAIMANT states"""
        validation_container.record_key = employee_pfml_entry.employee_id

        # If there are validation issues, add to claimant extract error report.
        if validation_container.has_validation_issues():
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_CLAIMANT_ADD_TO_CLAIMANT_EXTRACT_ERROR_REPORT,
                associated_model=employee_pfml_entry,
                outcome=state_log_util.build_outcome(
                    f"Employee {employee_pfml_entry.employee_id} had validation issues in FINEOS claimant extract {extract_data.date_str}",
                    validation_container,
                ),
                db_session=self.db_session,
            )
            self.increment("errored_claimant_count")

        else:
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS,
                associated_model=employee_pfml_entry,
                outcome=state_log_util.build_outcome(
                    f"Employee {employee_pfml_entry.employee_id} successfully extracted from FINEOS claimant extract {extract_data.date_str}"
                ),
                db_session=self.db_session,
            )
            self.increment("valid_claimant_count")

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
            RECEIVED_FOLDER, f"{date_group_folder}"
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

    def extract_to_staging_tables(self, extract_data: ExtractData):
        ref_file = extract_data.reference_file
        self.db_session.add(ref_file)
        requested_absence_info_data = [
            payments_util.make_keys_lowercase(v)
            for v in extract_data.requested_absence_info.indexed_data.values()
        ]
        employee_feed_data = [
            payments_util.make_keys_lowercase(v)
            for v in extract_data.employee_feed.indexed_data.values()
        ]

        for data in requested_absence_info_data:
            vbi_requested_absence_som = payments_util.create_staging_table_instance(
                data, FineosExtractVbiRequestedAbsenceSom, ref_file, self.get_import_log_id()
            )
            self.db_session.add(vbi_requested_absence_som)

        for data in employee_feed_data:
            employee_feed = payments_util.create_staging_table_instance(
                data, FineosExtractEmployeeFeed, ref_file, self.get_import_log_id()
            )
            self.db_session.add(employee_feed)
