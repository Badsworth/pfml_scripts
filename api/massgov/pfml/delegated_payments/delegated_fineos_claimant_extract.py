import enum
import uuid
from datetime import date
from typing import Any, Callable, Dict, List, Optional, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    AbsenceStatus,
    BankAccountType,
    Claim,
    Employee,
    EmployeePubEftPair,
    Employer,
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


class AbsencePeriodContainer:
    class_id: int
    index_id: int
    leave_request_id: Optional[int]
    is_id_proofed: Optional[bool]
    start_date: Optional[date]
    end_date: Optional[date]

    def __init__(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        class_id: str,
        index_id: str,
        is_id_proofed: Optional[bool],
        leave_request_id: Optional[str],
    ):
        self.start_date = payments_util.datetime_str_to_date(start_date)
        self.end_date = payments_util.datetime_str_to_date(end_date)
        self.class_id = int(class_id)
        self.index_id = int(index_id)
        self.is_id_proofed = is_id_proofed
        self.leave_request_id = int(leave_request_id) if leave_request_id else None


class ClaimantData:
    """
    A class for containing any and all claim/claimant data. Handles validation
    and pulling values out of the dictionaries of the files we processed.
    """

    validation_container: payments_util.ValidationContainer

    count_incrementer: Optional[Callable[[str], None]]

    absence_case_id: str
    is_claim_id_proofed: bool = False

    fineos_notification_id: Optional[str] = None
    claim_type_raw: Optional[str] = None
    absence_case_status: Optional[str] = None
    absence_start_date: Optional[str] = None
    absence_end_date: Optional[str] = None

    fineos_customer_number: Optional[str] = None
    employer_customer_number: Optional[str] = None
    employee_tax_identifier: Optional[str] = None
    employee_first_name: Optional[str] = None
    employee_middle_name: Optional[str] = None
    employee_last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    payment_method: Optional[str] = None

    routing_nbr: Optional[str] = None
    account_nbr: Optional[str] = None
    account_type: Optional[str] = None
    should_do_eft_operations: bool = False

    absence_period_data: List[AbsencePeriodContainer]

    def __init__(
        self,
        absence_case_id: str,
        requested_absences: List[FineosExtractVbiRequestedAbsenceSom],
        employee_records: List[FineosExtractEmployeeFeed],
        count_incrementer: Optional[Callable[[str], None]] = None,
    ):
        self.absence_period_data = []
        self.absence_case_id = absence_case_id
        self.validation_container = payments_util.ValidationContainer(self.absence_case_id)

        self.count_incrementer = count_incrementer

        self._process_requested_absences(requested_absences)
        self._process_employee_feed(employee_records)

    def _process_requested_absences(
        self, requested_absences: List[FineosExtractVbiRequestedAbsenceSom]
    ) -> None:
        for requested_absence in requested_absences:
            # If any of the requested absence records are ID proofed, then
            # we consider the entire claim valid
            evidence_result_type = requested_absence.leaverequest_evidenceresulttype
            is_absence_period_id_proofed: Optional[bool]

            if evidence_result_type == "Satisfied":
                self.is_claim_id_proofed = True
                is_absence_period_id_proofed = True
            elif evidence_result_type is not None and evidence_result_type.strip() == "":
                is_absence_period_id_proofed = None
            else:
                is_absence_period_id_proofed = False

            start_date = payments_util.validate_db_input(
                "ABSENCEPERIOD_START", requested_absence, self.validation_container, True
            )
            end_date = payments_util.validate_db_input(
                "ABSENCEPERIOD_END", requested_absence, self.validation_container, True
            )
            class_id = payments_util.validate_db_input(
                "ABSENCEPERIOD_CLASSID", requested_absence, self.validation_container, True
            )
            index_id = payments_util.validate_db_input(
                "ABSENCEPERIOD_INDEXID", requested_absence, self.validation_container, True
            )
            fineos_leave_request_id = payments_util.validate_db_input(
                "LEAVEREQUEST_ID", requested_absence, self.validation_container, True
            )

            if class_id is None or index_id is None:
                log_attributes = {
                    "absence_period_class_id": requested_absence.absenceperiod_classid,
                    "absence_period_index_id": requested_absence.absenceperiod_indexid,
                }
                logger.warning(
                    "Unable to extract class_id and/or index_id from requested_absence.",
                    extra=log_attributes,
                )

                if self.count_incrementer:
                    self.count_incrementer(
                        ClaimantExtractStep.Metrics.ABSENCE_PERIOD_CLASS_ID_OR_INDEX_ID_NOT_FOUND_COUNT
                    )

                continue

            absence_period = AbsencePeriodContainer(
                start_date=start_date,
                end_date=end_date,
                class_id=class_id,
                index_id=index_id,
                is_id_proofed=is_absence_period_id_proofed,
                leave_request_id=fineos_leave_request_id,
            )

            self.absence_period_data.append(absence_period)

        # Ideally, we would be able to distinguish and separate out the
        # various leave requests that make up a claim, but we don't
        # have this concept in our system at the moment. Until we support
        # that, we're leaving these other fields alone and always choosing the
        # latest one to keep the behavior identical, but incorrect
        requested_absence = requested_absences[-1]

        # Note this should be identical regardless of absence case
        self.fineos_notification_id = payments_util.validate_db_input(
            "NOTIFICATION_CASENUMBER", requested_absence, self.validation_container, True
        )
        self.claim_type_raw = payments_util.validate_db_input(
            "ABSENCEREASON_COVERAGE", requested_absence, self.validation_container, True
        )

        self.absence_case_status = payments_util.validate_db_input(
            "ABSENCE_CASESTATUS",
            requested_absence,
            self.validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(AbsenceStatus),
        )

        self.absence_start_date = payments_util.validate_db_input(
            "ABSENCEPERIOD_START", requested_absence, self.validation_container, True
        )

        self.absence_end_date = payments_util.validate_db_input(
            "ABSENCEPERIOD_END", requested_absence, self.validation_container, True
        )

        # Note this should be identical regardless of absence case
        self.fineos_customer_number = payments_util.validate_db_input(
            "EMPLOYEE_CUSTOMERNO", requested_absence, self.validation_container, True
        )

        # Note this should be identical regardless of absence case
        self.employer_customer_number = payments_util.validate_db_input(
            "EMPLOYER_CUSTOMERNO", requested_absence, self.validation_container, True
        )

    def _process_employee_feed(
        self, employee_feed_records: List[FineosExtractEmployeeFeed]
    ) -> None:
        # If there isn't a FINEOS Customer Number, we can't lookup the employee record
        if not self.fineos_customer_number:
            return

        # The employee feed data is a list of records associated
        # with the employee feed. There will be a mix of records with
        # DEFPAYMENTPREF set to Y/N. Y indicating that it's the default payment
        # preference. We always prefer the default, but there can be many of each.
        if not employee_feed_records:
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
        # Shouldn't be possible, but making the linter happy
        if employee_feed:
            self.employee_tax_identifier = payments_util.validate_db_input(
                "NATINSNO", employee_feed, self.validation_container, True
            )

            self.date_of_birth = payments_util.validate_db_input(
                "DATEOFBIRTH", employee_feed, self.validation_container, True
            )

            self.employee_first_name = payments_util.validate_db_input(
                "FIRSTNAMES", employee_feed, self.validation_container, True
            )

            self.employee_middle_name = payments_util.validate_db_input(
                "INITIALS", employee_feed, self.validation_container, False
            )

            self.employee_last_name = payments_util.validate_db_input(
                "LASTNAME", employee_feed, self.validation_container, True
            )

            self._process_payment_preferences(employee_feed)

    def _process_payment_preferences(self, employee_feed: FineosExtractEmployeeFeed) -> None:
        # We only care about the payment preference fields if it is the default payment
        # preference record, otherwise we can't set these fields
        is_default_payment_pref = employee_feed.defpaymentpref == "Y"
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

        self.payment_method = payments_util.validate_db_input(
            "PAYMENTMETHOD",
            employee_feed,
            self.validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(
                PaymentMethod,
                disallowed_lookup_values=[PaymentMethod.DEBIT.payment_method_description],
            ),
        )

        eft_required = self.payment_method == PaymentMethod.ACH.payment_method_description
        if eft_required:
            nbr_of_validation_issues = len(self.validation_container.validation_issues)

            self.routing_nbr = payments_util.validate_db_input(
                "SORTCODE",
                employee_feed,
                self.validation_container,
                eft_required,
                min_length=9,
                max_length=9,
                custom_validator_func=payments_util.routing_number_validator,
            )

            self.account_nbr = payments_util.validate_db_input(
                "ACCOUNTNO", employee_feed, self.validation_container, eft_required, max_length=17,
            )

            self.account_type = payments_util.validate_db_input(
                "ACCOUNTTYPE",
                employee_feed,
                self.validation_container,
                eft_required,
                custom_validator_func=payments_util.lookup_validator(BankAccountType),
            )

            if nbr_of_validation_issues == len(self.validation_container.validation_issues):
                self.should_do_eft_operations = True

    def _determine_employee_feed_info(
        self, employee_feed_records: List[FineosExtractEmployeeFeed]
    ) -> Optional[FineosExtractEmployeeFeed]:
        # No records shouldn't be possible
        # based on the calling logic, but this
        # makes the linter happy
        if len(employee_feed_records) == 0:
            return None

        # If there is only one record, just use it
        if len(employee_feed_records) == 1:
            return employee_feed_records[0]

        # Try filtering to just DEFPAYMENTPREF = 'Y'
        defpaymentpref_records = list(
            filter(lambda record: record.defpaymentpref == "Y", employee_feed_records)
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
        EXTRACT_PATH = "extract_path"
        CLAIM_NOT_FOUND_COUNT = "claim_not_found_count"
        CLAIM_PROCESSED_COUNT = "claim_processed_count"
        EFT_FOUND_COUNT = "eft_found_count"
        EFT_REJECTED_COUNT = "eft_rejected_count"
        EMPLOYEE_FEED_RECORD_COUNT = "employee_feed_record_count"
        EMPLOYEE_NOT_FOUND_IN_FEED_COUNT = "employee_not_found_in_feed_count"
        EMPLOYEE_NOT_FOUND_IN_DATABASE_COUNT = "employee_not_found_in_database_count"
        TAX_IDENTIFIER_MISSING_IN_DB_COUNT = "tax_identifier_missing_in_db_count"
        EMPLOYEE_PROCESSED_MULTIPLE_TIMES = "employee_processed_multiple_times"
        CLAIM_UPDATE_EXCEPTION_COUNT = "claim_update_exception_count"
        ERRORED_CLAIMANT_COUNT = "errored_claimant_count"
        ERRORED_CLAIM_COUNT = "errored_claim_count"
        EVIDENCE_NOT_ID_PROOFED_COUNT = "evidence_not_id_proofed_count"
        NEW_EFT_COUNT = "new_eft_count"
        PROCESSED_EMPLOYEE_COUNT = "processed_employee_count"
        PROCESSED_REQUESTED_ABSENCE_COUNT = "processed_requested_absence_count"
        VALID_CLAIM_COUNT = "valid_claim_count"
        VBI_REQUESTED_ABSENCE_SOM_RECORD_COUNT = "vbi_requested_absence_som_record_count"
        NO_EMPLOYEE_FEED_RECORDS_FOUND_COUNT = "no_employee_feed_records_found_count"
        NO_DEFAULT_PAYMENT_PREFERENCE_COUNT = "no_default_payment_preference_count"
        EMPLOYER_NOT_FOUND_COUNT = "employer_not_found_count"
        EMPLOYER_FOUND_COUNT = "employer_found_count"
        ABSENCE_PERIOD_CLASS_ID_OR_INDEX_ID_NOT_FOUND_COUNT = (
            "absence_period_class_id_or_index_id_not_found_count"
        )

    def run_step(self) -> None:
        self.process_claimant_extract_data()

    def process_claimant_extract_data(self) -> None:

        logger.info("Processing claimant extract data")

        try:
            self.process_records_to_db()
            self.db_session.commit()
        except Exception:
            # If there was a file-level exception anywhere in the processing,
            # we move the file from received to error
            # Add this function:
            self.db_session.rollback()
            logger.exception("Error processing claimant extract data")
            raise

        logger.info("Done processing claimant extract data")

    def process_records_to_db(self) -> None:
        reference_file = (
            self.db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
            )
            .order_by(ReferenceFile.created_at.desc())
            .first()
        )
        if not reference_file:
            raise Exception(
                "This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
            )
        if reference_file.processed_import_log_id:
            logger.warning(
                "Already processed the most recent extracts for %s in import run %s",
                reference_file.file_location,
                reference_file.processed_import_log_id,
            )
            return
        records = (
            self.db_session.query(FineosExtractVbiRequestedAbsenceSom)
            .filter(
                FineosExtractVbiRequestedAbsenceSom.reference_file_id
                == reference_file.reference_file_id
            )
            .order_by(FineosExtractVbiRequestedAbsenceSom.absence_casenumber)
            .all()
        )

        # We grab the first record from the list so we
        # can setup the grouping logic without dealing with nulls
        record_iter = iter(records)
        record = next(record_iter, None)
        if record:
            records_in_same_absence_case = [record]
            curr_absence_case_number = record.absence_casenumber
            self.increment(self.Metrics.VBI_REQUESTED_ABSENCE_SOM_RECORD_COUNT)

            # We want to group all records from the same absence case
            # We know they are adjacent because the query sorted them
            for record in record_iter:
                self.increment(self.Metrics.VBI_REQUESTED_ABSENCE_SOM_RECORD_COUNT)
                if curr_absence_case_number != record.absence_casenumber:
                    # We've reached the end of a chunk of absence cases,
                    # and need to process them + setup the next chunk
                    self.process_absence_case(
                        cast(str, curr_absence_case_number),
                        records_in_same_absence_case,
                        reference_file,
                    )

                    # Setup the next pass
                    records_in_same_absence_case = [record]
                    curr_absence_case_number = record.absence_casenumber

                else:
                    # The absence case matches and belongs to the current set
                    records_in_same_absence_case.append(record)

            # Process the last record
            self.process_absence_case(
                cast(str, curr_absence_case_number), records_in_same_absence_case, reference_file
            )

    def process_absence_case(
        self,
        absence_case_id: str,
        requested_absences: List[FineosExtractVbiRequestedAbsenceSom],
        reference_file: ReferenceFile,
    ) -> None:
        self.increment(self.Metrics.PROCESSED_REQUESTED_ABSENCE_COUNT)
        customerno = requested_absences[0].employee_customerno

        employee_records = (
            self.db_session.query(FineosExtractEmployeeFeed)
            .filter(
                FineosExtractEmployeeFeed.customerno == customerno,
                FineosExtractEmployeeFeed.reference_file_id == reference_file.reference_file_id,
            )
            .all()
        )
        self.increment(self.Metrics.EMPLOYEE_FEED_RECORD_COUNT, len(employee_records))

        claimant_data = ClaimantData(
            absence_case_id, requested_absences, employee_records, self.increment
        )

        logger.info(
            "Processing absence_case_id %s",
            absence_case_id,
            extra=claimant_data.get_traceable_details(),
        )

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
            self.increment(self.Metrics.CLAIM_UPDATE_EXCEPTION_COUNT)
            return

        try:
            # Update employee info
            if claim is not None:
                employee_pfml_entry = self.update_employee_info(claimant_data, claim)
                self.attach_employer_to_claim(claimant_data, claim)

                # Add / update entry on absence period table
                for absence_period_info in claimant_data.absence_period_data:
                    self.create_or_update_absence_period(absence_period_info, claim, claimant_data)
        except Exception as e:
            logger.exception(
                "Unexpected error %s while processing claimant: %s",
                type(e),
                absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )
            self.increment(self.Metrics.ERRORED_CLAIMANT_COUNT)
            return

        if employee_pfml_entry is not None:
            self.add_employee_reference_file(employee_pfml_entry, reference_file)

        if claim is not None:
            self.manage_state_log(claim, claimant_data)

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

        if not claimant_data.is_claim_id_proofed:
            logger.info(
                "Absence_case_id %s is not id proofed yet",
                claimant_data.absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )
            self.increment(self.Metrics.EVIDENCE_NOT_ID_PROOFED_COUNT)

            claimant_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.CLAIM_NOT_ID_PROOFED,
                "Claim has not been ID proofed, LEAVEREQUEST_EVIDENCERESULTTYPE is not Satisfied",
            )

        claim_pfml.is_id_proofed = claimant_data.is_claim_id_proofed

        # Return claim, we want to create this even if the employee
        # has issues or there were some validation issues
        self.db_session.add(claim_pfml)
        self.increment(self.Metrics.CLAIM_PROCESSED_COUNT)

        return claim_pfml

    def create_or_update_absence_period(
        self, absence_period_info: AbsencePeriodContainer, claim: Claim, claimant_data: ClaimantData
    ) -> Optional[AbsencePeriod]:

        log_attributes = claimant_data.get_traceable_details()

        # Add / update entry on absence period table
        logger.info("Updating Absence Period Table", extra=log_attributes)

        # check if absence period is present
        db_absence_period = (
            self.db_session.query(AbsencePeriod)
            .filter(
                AbsencePeriod.fineos_absence_period_class_id == absence_period_info.class_id,
                AbsencePeriod.fineos_absence_period_index_id == absence_period_info.index_id,
            )
            .one_or_none()
        )

        if db_absence_period and db_absence_period.claim_id != claim.claim_id:
            logger.error(
                "Found absence period with claim_id different from claim associated with the absence period received.",
                extra={
                    **log_attributes,
                    "claim.claim_id": claim.claim_id,
                    "db_absence_period.claim_id": db_absence_period.claim_id,
                    "absence_period_class_id": absence_period_info.class_id,
                    "absence_period_index_id": absence_period_info.index_id,
                },
            )

            claimant_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.CLAIMANT_MISMATCH,
                "Claim.claim_id does not match db_absence_period.claim_id",
            )

            return None

        if db_absence_period is None:
            db_absence_period = AbsencePeriod()
            db_absence_period.claim_id = claim.claim_id
            db_absence_period.fineos_absence_period_class_id = absence_period_info.class_id
            db_absence_period.fineos_absence_period_index_id = absence_period_info.index_id
            self.db_session.add(db_absence_period)

        if absence_period_info.is_id_proofed is not None:
            db_absence_period.is_id_proofed = absence_period_info.is_id_proofed

        if absence_period_info.start_date is not None:
            db_absence_period.absence_period_start_date = absence_period_info.start_date

        if absence_period_info.end_date is not None:
            db_absence_period.absence_period_end_date = absence_period_info.end_date

        if absence_period_info.leave_request_id is not None:
            db_absence_period.fineos_leave_request_id = absence_period_info.leave_request_id

        return db_absence_period

    def update_employee_info(self, claimant_data: ClaimantData, claim: Claim) -> Optional[Employee]:
        """Returns the employee if found and updates its info"""
        self.increment(self.Metrics.PROCESSED_EMPLOYEE_COUNT)
        if not claimant_data.employee_tax_identifier:
            # When we did validation, we would have added an error for this
            self.increment(self.Metrics.EMPLOYEE_NOT_FOUND_IN_FEED_COUNT)
            return None

        employee_pfml_entry = None
        try:
            tax_identifier_id = (
                self.db_session.query(TaxIdentifier.tax_identifier_id)
                .filter(TaxIdentifier.tax_identifier == claimant_data.employee_tax_identifier)
                .one_or_none()
            )
            if tax_identifier_id is None:
                self.increment(self.Metrics.TAX_IDENTIFIER_MISSING_IN_DB_COUNT)
                claimant_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.MISSING_IN_DB,
                    f"tax_identifier: {claimant_data.employee_tax_identifier}",
                )
            else:
                employee_pfml_entry = (
                    self.db_session.query(Employee)
                    .filter(Employee.tax_identifier_id == tax_identifier_id)
                    .one_or_none()
                )
                if not employee_pfml_entry:
                    self.increment(self.Metrics.EMPLOYEE_NOT_FOUND_IN_DATABASE_COUNT)
                    claimant_data.validation_container.add_validation_issue(
                        payments_util.ValidationReason.MISSING_IN_DB,
                        f"tax_identifier: {claimant_data.employee_tax_identifier}",
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
            # We added validation issues above for the scenarios that cause this
            logger.warning(
                f"Employee in employee file with customer nbr {claimant_data.fineos_customer_number} not found in PFML DB.",
            )
            return None

        # Use employee feed entry to update PFML DB
        if claimant_data.date_of_birth is not None:
            employee_pfml_entry.date_of_birth = payments_util.datetime_str_to_date(
                claimant_data.date_of_birth
            )

        if claimant_data.fineos_customer_number is not None:
            employee_pfml_entry.fineos_customer_number = claimant_data.fineos_customer_number

        if claimant_data.employee_first_name is not None:
            employee_pfml_entry.fineos_employee_first_name = claimant_data.employee_first_name
            employee_pfml_entry.fineos_employee_middle_name = claimant_data.employee_middle_name

        if claimant_data.employee_last_name is not None:
            employee_pfml_entry.fineos_employee_last_name = claimant_data.employee_last_name

        self.update_eft_info(claimant_data, employee_pfml_entry)

        # Associate claim with employee in case it is a new claim.
        claim.employee_id = employee_pfml_entry.employee_id
        # NOTE: fix to address test issues with query cache using a claim with the employee_id not set in other steps
        # This will make the employee object available in memory for the same transaction
        # TODO settle on approach after further investigation
        claim.employee = employee_pfml_entry

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
                prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id,  # If this is new, we want it to be pending,
                fineos_employee_first_name=claimant_data.employee_first_name,
                fineos_employee_middle_name=claimant_data.employee_middle_name,
                fineos_employee_last_name=claimant_data.employee_last_name,
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

    def attach_employer_to_claim(self, claimant_data: ClaimantData, claim: Claim) -> None:
        if claimant_data.employer_customer_number is None:
            return None

        employer_pfml_entry = (
            self.db_session.query(Employer)
            .filter(Employer.fineos_employer_id == claimant_data.employer_customer_number)
            .one_or_none()
        )

        if not employer_pfml_entry:
            logger.warning(
                "Employer %s not found in DB for claim %s",
                claimant_data.employer_customer_number,
                claimant_data.absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )
            claimant_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB,
                f"employer customer number: {claimant_data.employer_customer_number}",
            )
            self.increment(self.Metrics.EMPLOYER_NOT_FOUND_COUNT)
            return None

        self.increment(self.Metrics.EMPLOYER_FOUND_COUNT)
        claim.employer_id = employer_pfml_entry.employer_id
        logger.info(
            "Attached employer %s to claim %s",
            claimant_data.employer_customer_number,
            claimant_data.absence_case_id,
            extra=claimant_data.get_traceable_details(),
        )

    def manage_state_log(self, claim: Claim, claimant_data: ClaimantData) -> None:
        """Manages the DELEGATED_CLAIMANT states"""
        validation_container = claimant_data.validation_container

        # If there are validation issues, add to claimant extract error report.
        if validation_container.has_validation_issues():
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT,
                associated_model=claim,
                import_log_id=self.get_import_log_id(),
                outcome=state_log_util.build_outcome(
                    f"Claim {claim.fineos_absence_id} had validation issues in FINEOS claimant extract",
                    validation_container,
                ),
                db_session=self.db_session,
            )
            self.increment(self.Metrics.ERRORED_CLAIM_COUNT)

        else:
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
                associated_model=claim,
                import_log_id=self.get_import_log_id(),
                outcome=state_log_util.build_outcome(
                    f"Claim {claim.fineos_absence_id} successfully extracted from FINEOS claimant extract"
                ),
                db_session=self.db_session,
            )
            self.increment(self.Metrics.VALID_CLAIM_COUNT)
