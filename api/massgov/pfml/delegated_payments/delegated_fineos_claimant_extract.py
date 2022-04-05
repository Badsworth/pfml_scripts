import enum
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.absences import (
    AbsencePeriodType,
    AbsenceReason,
    AbsenceReasonQualifierOne,
    AbsenceReasonQualifierTwo,
    AbsenceStatus,
)
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    BankAccountType,
    Claim,
    Employee,
    EmployeePubEftPair,
    Employer,
    LeaveRequestDecision,
    OrganizationUnit,
    PaymentMethod,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    TaxIdentifier,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVbiRequestedAbsence,
    FineosExtractVbiRequestedAbsenceSom,
)
from massgov.pfml.db.models.state import State
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.util.datetime import datetime_str_to_date

logger = logging.get_logger(__name__)

# folder constants
RECEIVED_FOLDER = "received"
PROCESSED_FOLDER = "processed"
SKIPPED_FOLDER = "skipped"
ERRORED_FOLDER = "errored"


@dataclass
class AbsencePair:
    """Class containing the two raw VBI Requested Absence Records"""

    # The SOM version is always present as we iterate over the dataset
    requested_absence_som: FineosExtractVbiRequestedAbsenceSom

    # While rare, it's possible to not find the non-SOM record
    # This will be a validation issue, but won't prevent processing
    # As of Jan 2022, we expect ~100 / 160,000 to be missing
    requested_absence_additional: Optional[FineosExtractVbiRequestedAbsence]


class AbsencePeriodContainer:
    class_id: int
    index_id: int
    leave_request_id: Optional[int]
    is_id_proofed: Optional[bool]
    start_date: Optional[date]
    end_date: Optional[date]
    raw_absence_period_type: Optional[str]
    raw_absence_reason_qualifier_1: Optional[str]
    raw_absence_reason_qualifier_2: Optional[str]
    raw_absence_reason: Optional[str]
    raw_leave_request_decision: Optional[str]

    def __init__(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        class_id: str,
        index_id: str,
        is_id_proofed: Optional[bool],
        leave_request_id: Optional[str],
        raw_absence_period_type: Optional[str],
        raw_absence_reason_qualifier_1: Optional[str],
        raw_absence_reason_qualifier_2: Optional[str],
        raw_absence_reason: Optional[str],
        raw_leave_request_decision: Optional[str],
    ):
        self.start_date = datetime_str_to_date(start_date)
        self.end_date = datetime_str_to_date(end_date)
        self.class_id = int(class_id)
        self.index_id = int(index_id)
        self.is_id_proofed = is_id_proofed
        self.leave_request_id = int(leave_request_id) if leave_request_id else None

        self.raw_absence_period_type = raw_absence_period_type
        self.raw_absence_reason_qualifier_1 = raw_absence_reason_qualifier_1
        self.raw_absence_reason_qualifier_2 = raw_absence_reason_qualifier_2
        self.raw_absence_reason = raw_absence_reason
        self.raw_leave_request_decision = raw_leave_request_decision

    def _members(self):
        # _members only contains the values from the SOM version of the
        # file as we want to dedupe records from that file with this,
        # and aren't concerned with the non-SOM file
        return (
            self.start_date,
            self.end_date,
            self.class_id,
            self.index_id,
            self.is_id_proofed,
            self.leave_request_id,
        )

    def __eq__(self, other):
        if not isinstance(other, AbsencePeriodContainer):
            return False

        return self._members() == other._members()

    def __hash__(self):
        return hash(
            (
                self.start_date,
                self.end_date,
                self.class_id,
                self.index_id,
                self.is_id_proofed,
                self.leave_request_id,
            )
        )

    def get_log_extra(self) -> Dict[str, Any]:
        return {
            "absence_period_class_id": self.class_id,
            "absence_period_index_id": self.index_id,
            "absence_period_start_date": self.start_date.isoformat() if self.start_date else None,
            "absence_period_end_date": self.end_date.isoformat() if self.end_date else None,
            "fineos_leave_request_id": self.leave_request_id,
            "absence_period_type": self.raw_absence_period_type,
            "leave_request_decision": self.raw_leave_request_decision,
        }


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
    organization_unit_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    payment_method: Optional[str] = None

    routing_nbr: Optional[str] = None
    account_nbr: Optional[str] = None
    account_type: Optional[str] = None
    should_do_eft_operations: bool = False

    mass_id_number: Optional[str] = None
    out_of_state_id_number: Optional[str] = None

    absence_period_data: List[AbsencePeriodContainer]

    def __init__(
        self,
        absence_case_id: str,
        requested_absences: List[AbsencePair],
        employee_record: Optional[FineosExtractEmployeeFeed],
        count_incrementer: Optional[Callable[[str], None]] = None,
    ):
        self.absence_period_data = []
        self.absence_case_id = absence_case_id
        self.validation_container = payments_util.ValidationContainer(self.absence_case_id)

        self.count_incrementer = count_incrementer

        self._process_requested_absences(requested_absences)
        self._process_employee_feed(employee_record)

    def increment(self, metric: str) -> None:
        if self.count_incrementer:
            self.count_incrementer(metric)

    def _process_requested_absences(self, requested_absences: List[AbsencePair]) -> None:

        start_dates: List[str] = []
        end_dates = []

        # Keep track of all the values across all absence periods
        # Used for validation at end of function as we expect these to be the same
        employer_customer_numbers = []
        claimant_customer_numbers = []
        absence_case_statuses = []
        organization_unit_names = []

        # We dedupe absence periods as sometimes the extracts
        # exact duplicates and it causes performance issues
        absence_period_set = set()
        for requested_absence_pair in requested_absences:
            requested_absence = requested_absence_pair.requested_absence_som
            requested_absence_additional = requested_absence_pair.requested_absence_additional

            # Add the raw values of a few fields to lists for later validation
            employer_customer_numbers.append(requested_absence.employer_customerno)
            claimant_customer_numbers.append(requested_absence.employee_customerno)
            absence_case_statuses.append(requested_absence.absence_casestatus)
            if requested_absence.orgunit_name:  # skip records with empty org unit name
                organization_unit_names.append(requested_absence.orgunit_name)

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

            # Values exclusive to the "additional" requested absence record
            raw_absence_period_type = None
            raw_absence_reason_qualifier_1 = None
            raw_absence_reason_qualifier_2 = None
            raw_absence_reason = None
            raw_leave_request_decision = None
            if requested_absence_additional:
                raw_absence_period_type = payments_util.validate_db_input(
                    "ABSENCEPERIOD_TYPE",
                    requested_absence_additional,
                    self.validation_container,
                    True,
                    custom_validator_func=payments_util.lookup_validator(AbsencePeriodType),
                )

                raw_absence_reason_qualifier_1 = payments_util.validate_db_input(
                    "ABSENCEREASON_QUALIFIER1",
                    requested_absence_additional,
                    self.validation_container,
                    True,
                    custom_validator_func=payments_util.lookup_validator(AbsenceReasonQualifierOne),
                )

                # 2 isn't required as only ~half of claims have a 2nd qualifier
                raw_absence_reason_qualifier_2 = payments_util.validate_db_input(
                    "ABSENCEREASON_QUALIFIER2",
                    requested_absence_additional,
                    self.validation_container,
                    False,
                    custom_validator_func=payments_util.lookup_validator(AbsenceReasonQualifierTwo),
                )

                raw_absence_reason = payments_util.validate_db_input(
                    "ABSENCEREASON_NAME",
                    requested_absence_additional,
                    self.validation_container,
                    True,
                    custom_validator_func=payments_util.lookup_validator(AbsenceReason),
                )

                raw_leave_request_decision = payments_util.validate_db_input(
                    "LEAVEREQUEST_DECISION",
                    requested_absence_additional,
                    self.validation_container,
                    True,
                    custom_validator_func=payments_util.lookup_validator(LeaveRequestDecision),
                )

            else:
                msg = "Could not find VBI_REQUESTEDABSENCE record to pair with VBI_REQUESTEDABSENCE_SOM data, cannot populate all absence period data"
                logger.info(msg, extra=self.get_traceable_details())
                self.validation_container.add_validation_issue(
                    payments_util.ValidationReason.MISSING_DATASET, msg
                )
                self.increment(
                    ClaimantExtractStep.Metrics.NO_ADDITIONAL_REQUESTED_ABSENCE_FOUND_COUNT
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
                self.increment(
                    ClaimantExtractStep.Metrics.ABSENCE_PERIOD_CLASS_ID_OR_INDEX_ID_NOT_FOUND_COUNT
                )

                continue

            if start_date:
                start_dates.append(start_date)
            if end_date:
                end_dates.append(end_date)

            absence_period = AbsencePeriodContainer(
                start_date=start_date,
                end_date=end_date,
                class_id=class_id,
                index_id=index_id,
                is_id_proofed=is_absence_period_id_proofed,
                leave_request_id=fineos_leave_request_id,
                raw_absence_period_type=raw_absence_period_type,
                raw_absence_reason_qualifier_1=raw_absence_reason_qualifier_1,
                raw_absence_reason_qualifier_2=raw_absence_reason_qualifier_2,
                raw_absence_reason=raw_absence_reason,
                raw_leave_request_decision=raw_leave_request_decision,
            )

            # The absence period data has many duplicate records
            # on values we don't need for our processing. To improve
            # performance, we dedupe to avoid rewriting the same records
            # to the DB hundreds of times potentially.
            if absence_period in absence_period_set and self.count_incrementer:
                self.count_incrementer(ClaimantExtractStep.Metrics.DUPLICATE_ABSENCE_PERIOD_COUNT)
            absence_period_set.add(absence_period)

        self.absence_period_data = list(absence_period_set)
        all_start_end_dates_valid = len(requested_absences) == len(start_dates) == len(end_dates)

        if all_start_end_dates_valid:
            # We don't need to convert to date to do comparisons (min/max)
            # This is because the current string format (Y-M-D...) preserves the chronological sort order
            self.absence_start_date = min(start_dates)
            self.absence_end_date = max(end_dates)

        else:
            self.increment(ClaimantExtractStep.Metrics.START_DATE_OR_END_DATE_NOT_FOUND_COUNT)

        # Ideally, we would be able to distinguish and separate out the
        # various leave requests that make up a claim, but we don't
        # have this concept in our system at the moment. Until we support
        # that, we're leaving these other fields alone and always choosing the
        # latest one to keep the behavior identical, but incorrect
        requested_absence = requested_absences[-1].requested_absence_som

        # Note this should be identical regardless of absence case
        self.fineos_notification_id = payments_util.validate_db_input(
            "NOTIFICATION_CASENUMBER", requested_absence, self.validation_container, False
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

        # Note this should be identical regardless of absence case
        self.fineos_customer_number = payments_util.validate_db_input(
            "EMPLOYEE_CUSTOMERNO", requested_absence, self.validation_container, True
        )

        # Note this should be identical regardless of absence case
        self.employer_customer_number = payments_util.validate_db_input(
            "EMPLOYER_CUSTOMERNO", requested_absence, self.validation_container, True
        )

        self.organization_unit_name = None
        org_unit_names_set = set(organization_unit_names)
        if len(org_unit_names_set) == 1:
            self.organization_unit_name = list(org_unit_names_set)[0]

        # Sanity test that the fields we expect to be the exact same
        # for every requested absence record are in fact the same.
        # If we've encountered a strange scenario, set the value to
        # None so it won't get attached to the claim (this likely indicates a FINEOS issue)
        if (dupe_number := len(set(employer_customer_numbers))) > 1:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.UNEXPECTED_RECORD_VARIANCE,
                f"Expected only a single employer customer number for claim, and received {dupe_number}: {employer_customer_numbers}",
            )
            self.employer_customer_number = None
            self.increment(ClaimantExtractStep.Metrics.MULTIPLE_EMPLOYER_FOR_CLAIM_ISSUE_COUNT)

        if (dupe_number := len(set(claimant_customer_numbers))) > 1:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.UNEXPECTED_RECORD_VARIANCE,
                f"Expected only a single employee customer number for claim, and received {dupe_number}: {claimant_customer_numbers}",
            )
            self.fineos_customer_number = None
            self.increment(ClaimantExtractStep.Metrics.MULTIPLE_CLAIMANT_FOR_CLAIM_ISSUE_COUNT)

        if (dupe_number := len(set(absence_case_statuses))) > 1:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.UNEXPECTED_RECORD_VARIANCE,
                f"Expected only a single absence case status for claim, and received {dupe_number}: {absence_case_statuses}",
            )
            self.absence_case_status = None
            self.increment(
                ClaimantExtractStep.Metrics.MULTIPLE_ABSENCE_STATUSES_FOR_CLAIM_ISSUE_COUNT
            )

        if (dupe_number := len(org_unit_names_set)) > 1:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.UNEXPECTED_RECORD_VARIANCE,
                f"Expected only a single organization unit name for claim, and received {dupe_number}: {organization_unit_names}",
            )
            self.organization_unit_name = None
            self.increment(
                ClaimantExtractStep.Metrics.MULTIPLE_ORGANIZATION_UNIT_NAMES_FOR_CLAIM_ISSUE_COUNT
            )

    def _process_employee_feed(
        self, employee_feed_record: Optional[FineosExtractEmployeeFeed]
    ) -> None:
        # If there isn't a FINEOS Customer Number, we can't lookup the employee record
        if not self.fineos_customer_number:
            return

        # The employee feed data is a list of records associated
        # with the employee feed. There will be a mix of records with
        # DEFPAYMENTPREF set to Y/N. Y indicating that it's the default payment
        # preference. We always prefer the default, but there can be many of each.
        if not employee_feed_record:
            error_msg = (
                f"Employee in VBI_REQUESTEDABSENCE_SOM with absence id {self.absence_case_id} and customer nbr {self.fineos_customer_number} "
                "not found in employee feed file"
            )
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, error_msg
            )
            logger.warning("Skipping: %s", error_msg, extra=self.get_traceable_details())
            self.increment(ClaimantExtractStep.Metrics.NO_EMPLOYEE_FEED_RECORDS_FOUND_COUNT)

            # Can't process subsequent records as they pull from employee_feed
            return

        # Shouldn't be possible, but making the linter happy
        if employee_feed_record:
            self.employee_tax_identifier = payments_util.validate_db_input(
                "NATINSNO", employee_feed_record, self.validation_container, True
            )

            self.date_of_birth = payments_util.validate_db_input(
                "DATEOFBIRTH", employee_feed_record, self.validation_container, True
            )

            self.employee_first_name = payments_util.validate_db_input(
                "FIRSTNAMES", employee_feed_record, self.validation_container, True
            )

            self.employee_middle_name = payments_util.validate_db_input(
                "INITIALS", employee_feed_record, self.validation_container, False
            )

            self.employee_last_name = payments_util.validate_db_input(
                "LASTNAME", employee_feed_record, self.validation_container, True
            )

            self.mass_id_number = payments_util.validate_db_input(
                "EXTMASSID",
                employee_feed_record,
                self.validation_container,
                False,
                custom_validator_func=payments_util.mass_id_validator,
            )

            self.out_of_state_id_number = payments_util.validate_db_input(
                "EXTOUTOFSTATEID", employee_feed_record, self.validation_container, False
            )

            self._process_payment_preferences(employee_feed_record)

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
            self.increment(ClaimantExtractStep.Metrics.NO_DEFAULT_PAYMENT_PREFERENCE_COUNT)
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
                "ACCOUNTNO", employee_feed, self.validation_container, eft_required, max_length=17
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

    def get_traceable_details(self) -> Dict[str, Optional[Any]]:
        return {
            "absence_case_id": self.absence_case_id,
            "fineos_customer_number": self.fineos_customer_number,
            "absence_start_date": self.absence_start_date,
            "absence_end_date": self.absence_end_date,
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
        PAYMENT_REQUESTED_ABSENCE_RECORD_COUNT = "payment_requested_absence_record_count"
        NO_EMPLOYEE_FEED_RECORDS_FOUND_COUNT = "no_employee_feed_records_found_count"
        NO_DEFAULT_PAYMENT_PREFERENCE_COUNT = "no_default_payment_preference_count"
        EMPLOYER_NOT_FOUND_COUNT = "employer_not_found_count"
        EMPLOYER_FOUND_COUNT = "employer_found_count"
        ORG_UNIT_NOT_FOUND_COUNT = "org_unit_not_found_count"
        ORG_UNIT_FOUND_COUNT = "org_unit_found_count"
        ABSENCE_PERIOD_CLASS_ID_OR_INDEX_ID_NOT_FOUND_COUNT = (
            "absence_period_class_id_or_index_id_not_found_count"
        )
        START_DATE_OR_END_DATE_NOT_FOUND_COUNT = "start_date_or_end_date_not_found_count"
        DUPLICATE_ABSENCE_PERIOD_COUNT = "duplicate_absence_period_count"

        MULTIPLE_EMPLOYER_FOR_CLAIM_ISSUE_COUNT = "multiple_employer_for_claim_issue_count"
        MULTIPLE_CLAIMANT_FOR_CLAIM_ISSUE_COUNT = "multiple_claimant_for_claim_issue_count"
        MULTIPLE_ABSENCE_STATUSES_FOR_CLAIM_ISSUE_COUNT = (
            "multiple_absence_statuses_for_claim_issue_count"
        )
        MULTIPLE_ORGANIZATION_UNIT_NAMES_FOR_CLAIM_ISSUE_COUNT = (
            "multiple_organization_unit_names_for_claim_issue_count"
        )

        EMPLOYER_CHANGED_COUNT = "employer_changed_count"
        EMPLOYEE_CHANGED_COUNT = "employee_changed_count"

        MULTIPLE_ADDITIONAL_REQUESTED_ABSENCE_FOUND_COUNT = (
            "multiple_additional_requested_absence_found_count"
        )
        NO_ADDITIONAL_REQUESTED_ABSENCE_FOUND_COUNT = "no_additional_requested_absence_found_count"
        ADDITIONAL_REQUESTED_ABSENCE_CI_MISSING_COUNT = (
            "additional_requested_absence_ci_missing_count"
        )

    def run_step(self) -> None:
        self.process_claimant_extract_data()

    def process_claimant_extract_data(self) -> None:

        logger.info("Processing claimant extract data")
        self.process_records_to_db()
        logger.info("Done processing claimant extract data")

    def get_employee_feed_map(
        self, reference_file: ReferenceFile
    ) -> Dict[str, FineosExtractEmployeeFeed]:
        """
        Querying the DB to cache all of the employee feed info
        that is from the same batch as the requested absence data
        we are processing.
        """
        employee_feed_records = (
            self.db_session.query(FineosExtractEmployeeFeed)
            .filter(FineosExtractEmployeeFeed.reference_file_id == reference_file.reference_file_id)
            .all()
        )

        # The same customerno can appear many times in the employee feed.
        # We want to prefer using a record with the default payment pref
        # set to true, but are fine if it's not, just can't do EFT processing later.
        employee_feed_mapping: Dict[str, FineosExtractEmployeeFeed] = {}
        for employee_feed_record in employee_feed_records:
            self.increment(self.Metrics.EMPLOYEE_FEED_RECORD_COUNT)
            customerno = employee_feed_record.customerno

            # Adding to make the type checker happy
            if not customerno:
                logger.warning(
                    "Customer number not set for employee feed record %s",
                    employee_feed_record.employee_feed_id,
                )
                continue

            # Associate the first record we come across with the customerno
            # regardless of default payment preference status
            existing_record = employee_feed_mapping.get(customerno)
            if not existing_record:
                employee_feed_mapping[customerno] = employee_feed_record
                continue

            # All default payment preferences are the same for
            # the records we care about, so if the record is already
            # set as such, just continue and don't update
            if existing_record.defpaymentpref == "Y":
                continue

            # The record being processed is a defpaymentpref, use it
            # over whatever we previously found
            if employee_feed_record.defpaymentpref == "Y":
                employee_feed_mapping[customerno] = employee_feed_record

        return employee_feed_mapping

    def get_vbi_requested_absence_map(
        self, reference_file: ReferenceFile
    ) -> Dict[Tuple[str, str], FineosExtractVbiRequestedAbsence]:
        """
        NOTE: This is a separate similarly named requested absence file we get from
        FINEOS that we use in the payment extract that has additional columns in it
        that we want for absence periods. Ideally we'd use just one of these files,
        but despite matching on many core columns, they differ on a few key ones
        """
        requested_absence_records = (
            self.db_session.query(FineosExtractVbiRequestedAbsence)
            .filter(
                FineosExtractVbiRequestedAbsence.reference_file_id
                == reference_file.reference_file_id
            )
            .all()
        )

        requested_absence_mapping: Dict[Tuple[str, str], FineosExtractVbiRequestedAbsence] = {}
        for requested_absence_record in requested_absence_records:
            self.increment(self.Metrics.PAYMENT_REQUESTED_ABSENCE_RECORD_COUNT)

            c_value = requested_absence_record.absenceperiod_classid
            i_value = requested_absence_record.absenceperiod_indexid

            # Shouldn't happen, but making mypy happy
            if c_value is None or i_value is None:
                logger.warning(
                    "One of the C/I values for VBI_REQUESTEDABSENCE is None: %s,%s",
                    c_value,
                    i_value,
                )
                self.increment(self.Metrics.ADDITIONAL_REQUESTED_ABSENCE_CI_MISSING_COUNT)
                continue

            id = (c_value, i_value)

            # As of Jan 2022, there are 3 records I found
            # that had duplicate records where the only difference
            # was the employer in the file. We don't use employer data
            # so this isn't an issue, but keep track of a metric
            # so we can follow this over time especially with future file changes
            if id in requested_absence_mapping:
                logger.warning(
                    "Found multiple records for requested absences in VBI_REQUESTEDABSENCE for C/I values: %s",
                    id,
                )
                self.increment(self.Metrics.MULTIPLE_ADDITIONAL_REQUESTED_ABSENCE_FOUND_COUNT)

            requested_absence_mapping[id] = requested_absence_record

        return requested_absence_mapping

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
                "No claimant files consumed. This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
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

        employee_feed_map = self.get_employee_feed_map(reference_file)
        requested_absence_map = self.get_vbi_requested_absence_map(reference_file)

        # Process the records
        if records:
            records_in_same_absence_case: List[AbsencePair] = []
            # Initialize the absence case number to the first one
            curr_absence_case_number = records[0].absence_casenumber

            # We want to group all records from the same absence case
            # We know they are adjacent because the query sorted them
            for record in records:
                self.increment(self.Metrics.VBI_REQUESTED_ABSENCE_SOM_RECORD_COUNT)

                c_value = record.absenceperiod_classid
                i_value = record.absenceperiod_indexid

                if c_value is None or i_value is None:
                    # This shouldn't happen, but it's here to make mypy happy
                    logger.warning(
                        "One of the C/I values for VBI_REQUESTEDABSENCE_SOM is None: %s,%s",
                        c_value,
                        i_value,
                    )
                    additional_requested_absence = None
                else:
                    additional_requested_absence = requested_absence_map.get(
                        (c_value, i_value), None
                    )
                absence_pair = AbsencePair(record, additional_requested_absence)

                if curr_absence_case_number != record.absence_casenumber:
                    # We've reached the end of a chunk of absence cases,
                    # and need to process them + setup the next chunk
                    self.process_absence_case(
                        cast(str, curr_absence_case_number),
                        records_in_same_absence_case,
                        employee_feed_map,
                        reference_file,
                    )

                    # Setup the next pass
                    records_in_same_absence_case = [absence_pair]
                    curr_absence_case_number = record.absence_casenumber

                else:
                    # The absence case matches and belongs to the current set
                    records_in_same_absence_case.append(absence_pair)

            # Process the last record
            self.process_absence_case(
                cast(str, curr_absence_case_number),
                records_in_same_absence_case,
                employee_feed_map,
                reference_file,
            )
            reference_file.processed_import_log_id = self.get_import_log_id()

    def process_absence_case(
        self,
        absence_case_id: str,
        requested_absences: List[AbsencePair],
        employee_feed_map: Dict[str, FineosExtractEmployeeFeed],
        reference_file: ReferenceFile,
    ) -> None:
        self.increment(self.Metrics.PROCESSED_REQUESTED_ABSENCE_COUNT)
        customerno = requested_absences[0].requested_absence_som.employee_customerno

        # Just here to make type checker happy, shouldn't realistically happen
        # But if the customer number isn't set, the error log will let us know
        if customerno:
            employee_record = employee_feed_map.get(customerno)
        else:
            employee_record = None
            logger.error(
                "No employee customer number found for requested absence record %s",
                requested_absences[0].requested_absence_som.vbi_requested_absence_som_id,
            )

        claimant_data = ClaimantData(
            absence_case_id, requested_absences, employee_record, self.increment
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
                self.attach_organization_unit_to_claim(claimant_data, claim)

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
        claim_pfml: Optional[Claim] = (
            self.db_session.query(Claim)
            .filter(Claim.fineos_absence_id == claimant_data.absence_case_id)
            .one_or_none()
        )

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
            claim_pfml.absence_period_start_date = datetime_str_to_date(
                claimant_data.absence_start_date
            )

        if claimant_data.absence_end_date is not None:
            claim_pfml.absence_period_end_date = datetime_str_to_date(
                claimant_data.absence_end_date
            )

        if not claimant_data.is_claim_id_proofed:
            logger.info(
                "Absence_case_id %s is not id proofed yet",
                claimant_data.absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )
            self.increment(self.Metrics.EVIDENCE_NOT_ID_PROOFED_COUNT)

        claim_pfml.is_id_proofed = claimant_data.is_claim_id_proofed

        # Return claim, we want to create this even if the employee
        # has issues or there were some validation issues
        self.db_session.add(claim_pfml)
        self.increment(self.Metrics.CLAIM_PROCESSED_COUNT)

        return claim_pfml

    def create_or_update_absence_period(
        self, absence_period_info: AbsencePeriodContainer, claim: Claim, claimant_data: ClaimantData
    ) -> Optional[AbsencePeriod]:

        log_attributes: Dict[str, Any] = {
            **claimant_data.get_traceable_details(),
            **absence_period_info.get_log_extra(),
        }

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
                },
            )

            claimant_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.CLAIMANT_MISMATCH,
                "Claim.claim_id does not match db_absence_period.claim_id",
            )

            return None

        if db_absence_period is None:
            logger.info("Absence period not found, creating it", extra=log_attributes)
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

        if absence_period_info.raw_absence_period_type is not None:
            db_absence_period.absence_period_type_id = AbsencePeriodType.get_id(
                absence_period_info.raw_absence_period_type
            )

        if absence_period_info.raw_absence_reason_qualifier_1 is not None:
            db_absence_period.absence_reason_qualifier_one_id = AbsenceReasonQualifierOne.get_id(
                absence_period_info.raw_absence_reason_qualifier_1
            )

        # This field is optional and can be blank, so None/blank are skipped
        if absence_period_info.raw_absence_reason_qualifier_2:
            db_absence_period.absence_reason_qualifier_two_id = AbsenceReasonQualifierTwo.get_id(
                absence_period_info.raw_absence_reason_qualifier_2
            )

        if absence_period_info.raw_absence_reason is not None:
            db_absence_period.absence_reason_id = AbsenceReason.get_id(
                absence_period_info.raw_absence_reason
            )

        if absence_period_info.raw_leave_request_decision is not None:
            db_absence_period.leave_request_decision_id = LeaveRequestDecision.get_id(
                absence_period_info.raw_leave_request_decision
            )

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
                    claimant_data.employee_tax_identifier,
                    "tax_identifier",
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
                        claimant_data.employee_tax_identifier,
                        "employee",
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
                f"Employee in employee file with customer nbr {claimant_data.fineos_customer_number} not found in PFML DB."
            )
            return None

        # Use employee feed entry to update PFML DB
        if claimant_data.date_of_birth is not None:
            employee_pfml_entry.date_of_birth = datetime_str_to_date(claimant_data.date_of_birth)

        if claimant_data.fineos_customer_number is not None:
            employee_pfml_entry.fineos_customer_number = claimant_data.fineos_customer_number

        if claimant_data.employee_first_name is not None:
            employee_pfml_entry.fineos_employee_first_name = claimant_data.employee_first_name
            employee_pfml_entry.fineos_employee_middle_name = claimant_data.employee_middle_name

        if claimant_data.employee_last_name is not None:
            employee_pfml_entry.fineos_employee_last_name = claimant_data.employee_last_name

        if claimant_data.mass_id_number:
            employee_pfml_entry.mass_id_number = claimant_data.mass_id_number

        if claimant_data.out_of_state_id_number:
            employee_pfml_entry.out_of_state_id_number = claimant_data.out_of_state_id_number

        self.update_eft_info(claimant_data, employee_pfml_entry)

        if claim.employee and claim.employee_id != employee_pfml_entry.employee_id:
            self.increment(self.Metrics.EMPLOYEE_CHANGED_COUNT)
            logger.warning(
                "Employee for claim %s is changing from %s to %s",
                claimant_data.absence_case_id,
                claim.employee.fineos_customer_number,
                claimant_data.fineos_customer_number,
                extra=claimant_data.get_traceable_details(),
            )

        # Associate claim with employee in case it is a new claim.
        claim.employee_id = employee_pfml_entry.employee_id
        # NOTE: fix to address test issues with query cache using a claim with the employee_id not set in other steps
        # This will make the employee object available in memory for the same transaction
        # TODO settle on approach after further investigation
        claim.employee = employee_pfml_entry

        self.db_session.add(employee_pfml_entry)

        return employee_pfml_entry

    def update_eft_info(self, claimant_data: ClaimantData, employee_pfml_entry: Employee) -> None:
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
            extra = claimant_data.get_traceable_details()
            if existing_eft:
                extra |= payments_util.get_traceable_pub_eft_details(
                    existing_eft, employee_pfml_entry
                )
                self.increment(self.Metrics.EFT_FOUND_COUNT)
                logger.info("Found existing EFT info for claimant", extra=extra)
                if existing_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id:
                    msg = "EFT prenote was rejected - cannot pay with this account info"
                    logger.info(msg, extra=extra)
                    claimant_data.validation_container.add_validation_issue(
                        payments_util.ValidationReason.EFT_PRENOTE_REJECTED, msg
                    )
                    self.increment(self.Metrics.EFT_REJECTED_COUNT)

            else:
                self.increment(self.Metrics.NEW_EFT_COUNT)
                # This EFT info is new, it needs to be linked to the employee
                # and added to the EFT prenoting flow
                extra |= payments_util.get_traceable_pub_eft_details(
                    new_eft, employee_pfml_entry, state=State.DELEGATED_EFT_SEND_PRENOTE
                )
                logger.info("Initiating DELEGATED_EFT prenote flow for employee", extra=extra)

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
                claimant_data.employer_customer_number,
                "employer_customer_number",
            )
            self.increment(self.Metrics.EMPLOYER_NOT_FOUND_COUNT)
            return None

        # Log a warning if the claim is changing employers
        if claim.employer and claim.employer_id != employer_pfml_entry.employer_id:
            self.increment(self.Metrics.EMPLOYER_CHANGED_COUNT)
            logger.warning(
                "Employer for claim %s is changing from %s to %s",
                claimant_data.absence_case_id,
                claim.employer.fineos_employer_id,
                claimant_data.employer_customer_number,
                extra=claimant_data.get_traceable_details(),
            )

        self.increment(self.Metrics.EMPLOYER_FOUND_COUNT)
        claim.employer_id = employer_pfml_entry.employer_id
        logger.info(
            "Attached employer %s to claim %s",
            claimant_data.employer_customer_number,
            claimant_data.absence_case_id,
            extra=claimant_data.get_traceable_details(),
        )

    def attach_organization_unit_to_claim(self, claimant_data: ClaimantData, claim: Claim) -> None:
        """Connects the claim to its FINEOS organization unit"""
        if not claim.employer_id or not claimant_data.organization_unit_name:
            return None

        organization_unit = (
            self.db_session.query(OrganizationUnit)
            .filter(
                OrganizationUnit.name == claimant_data.organization_unit_name,
                OrganizationUnit.employer_id == claim.employer_id,
            )
            .one_or_none()
        )

        if not organization_unit:
            # Didn't import this organization unit from FINEOS yet
            logger.warning(
                "Organization unit %s not found in DB for claim %s",
                claimant_data.organization_unit_name,
                claimant_data.absence_case_id,
                extra=claimant_data.get_traceable_details(),
            )
            claimant_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB,
                claimant_data.organization_unit_name,
                "organization_unit_name",
            )
            self.increment(self.Metrics.ORG_UNIT_NOT_FOUND_COUNT)
            return None

        self.increment(self.Metrics.ORG_UNIT_FOUND_COUNT)
        claim.organization_unit_id = organization_unit.organization_unit_id
        logger.info(
            "Attached organization unit %s to claim %s",
            claimant_data.organization_unit_name,
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

            # For claims that failed validation, log their reason codes
            # and field names so that we can collect metrics  on the
            # most common error types
            extra = claimant_data.get_traceable_details()
            for (
                reason,
                field_name,
            ) in claimant_data.validation_container.get_reasons_with_field_names():
                # Replaced each iteration
                extra["validation_reason"] = str(reason)
                extra["field_name"] = field_name
                logger.info("Claim failed validation", extra=extra)

        else:
            # Don't update state log for successful claims
            # as it doesn't get used / degrades performance
            self.increment(self.Metrics.VALID_CLAIM_COUNT)
