import csv
import enum
import os
import pathlib
import tempfile
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    BankAccountType,
    Claim,
    Employee,
    EmployeeAddress,
    EmployeePubEftPair,
    ExperianAddressPair,
    Flow,
    GeoState,
    LatestStateLog,
    LkPaymentTransactionType,
    LkState,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    PaymentTransactionType,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.payments import (
    FineosExtractVbiRequestedAbsence,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
)
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.payments.payments_util import get_now

logger = logging.get_logger(__name__)

# waiting period for pending prenote
PRENOTE_PRENDING_WAITING_PERIOD = 7

# folder constants
RECEIVED_FOLDER = "received"
PROCESSED_FOLDER = "processed"
SKIPPED_FOLDER = "skipped"

# Expected file names
VBI_REQUESTED_ABSENCE_FILE_NAME = "VBI_REQUESTEDABSENCE.csv"
PEI_EXPECTED_FILE_NAME = "vpei.csv"
PAYMENT_DETAILS_EXPECTED_FILE_NAME = "vpeipaymentdetails.csv"
CLAIM_DETAILS_EXPECTED_FILE_NAME = "vpeiclaimdetails.csv"

expected_file_names = [
    VBI_REQUESTED_ABSENCE_FILE_NAME,
    PEI_EXPECTED_FILE_NAME,
    PAYMENT_DETAILS_EXPECTED_FILE_NAME,
    CLAIM_DETAILS_EXPECTED_FILE_NAME,
]

CANCELLATION_PAYMENT_TRANSACTION_TYPE = "PaymentOut Cancellation"
OVERPAYMENT_PAYMENT_TRANSACTION_TYPES = set(
    ["Overpayment", "Overpayment Actual Recovery", "Overpayment Recovery", "Overpayment Adjustment"]
)  # There are multiple types of overpayments
PAYMENT_OUT_TRANSACTION_TYPE = "PaymentOut"
AUTO_ALT_EVENT_REASON = "Automatic Alternate Payment"

TAX_IDENTIFICATION_NUMBER = "Tax Identification Number"


@dataclass(frozen=True, eq=True)
class CiIndex:
    c: str
    i: str


@dataclass
class Extract:
    file_location: str
    indexed_data: Dict[CiIndex, Dict[str, str]] = field(default_factory=dict)


@dataclass
class ExtractMultiple:
    """A extract that has multiple rows per key CiIndex."""

    file_location: str
    # Mapping from a CiIndex to a list of CSV rows that contain data for that record. Each CSV row
    # is a raw dict from field name to value, as returned by csv.DictReader().
    indexed_data: Dict[CiIndex, List[Dict[str, str]]] = field(default_factory=dict)


class ExtractData:
    pei: Extract
    payment_details: ExtractMultiple
    claim_details: Extract
    requested_absence: Extract

    date_str: str

    reference_file: ReferenceFile

    def __init__(self, s3_locations: List[str], date_str: str):
        for s3_location in s3_locations:
            if s3_location.endswith(PEI_EXPECTED_FILE_NAME):
                self.pei = Extract(s3_location)
            elif s3_location.endswith(PAYMENT_DETAILS_EXPECTED_FILE_NAME):
                self.payment_details = ExtractMultiple(s3_location)
            elif s3_location.endswith(CLAIM_DETAILS_EXPECTED_FILE_NAME):
                self.claim_details = Extract(s3_location)
            elif s3_location.endswith(VBI_REQUESTED_ABSENCE_FILE_NAME):
                self.requested_absence = Extract(s3_location)

        self.date_str = date_str

        file_location = os.path.join(
            payments_config.get_s3_config().pfml_fineos_extract_archive_path,
            RECEIVED_FOLDER,
            self.date_str,
        )
        self.reference_file = ReferenceFile(
            file_location=file_location,
            reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        logger.debug("Initialized extract data: %s", self.reference_file.file_location)


class PaymentData:
    """A class for containing any and all payment data. Handles validation and
       pulling values out of the various types

       All values are pulled from the CSV as-is and as strings. Values prefixed with raw_ need
       to be converted from the FINEOS value to one of our DB values (usually a lookup enum)
    """

    validation_container: payments_util.ValidationContainer

    c_value: str
    i_value: str

    tin: Optional[str] = None
    absence_case_number: Optional[str] = None

    leave_request_id: Optional[str] = None
    leave_request_decision: Optional[str] = None

    full_name: Optional[str] = None
    payee_identifier: Optional[str] = None

    address_line_one: Optional[str] = None
    address_line_two: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    raw_payment_method: Optional[str] = None
    event_type: Optional[str] = None
    event_reason: Optional[str] = None
    payment_start_period: Optional[str] = None
    payment_end_period: Optional[str] = None
    payment_date: Optional[str] = None
    payment_amount: Optional[Decimal] = None

    claim_type_raw: Optional[str] = None

    routing_nbr: Optional[str] = None
    account_nbr: Optional[str] = None
    raw_account_type: Optional[str] = None

    payment_transaction_type: LkPaymentTransactionType
    is_standard_payment: bool

    def __init__(
        self,
        extract_data: ExtractData,
        index: CiIndex,
        pei_record: Dict[str, str],
        count_incrementer: Optional[Callable[[str], None]] = None,
    ):
        self.validation_container = payments_util.ValidationContainer(str(index))
        self.c_value = index.c
        self.i_value = index.i

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS ALWAYS REQUIRED FOR ALL PAYMENTS
        #######################################

        # Grab every value we might need out of the datasets
        self.tin = payments_util.validate_csv_input(
            "PAYEESOCNUMBE", pei_record, self.validation_container, True
        )

        self.payee_identifier = payments_util.validate_csv_input(
            "PAYEEIDENTIFI", pei_record, self.validation_container, True
        )

        self.event_type = payments_util.validate_csv_input(
            "EVENTTYPE", pei_record, self.validation_container, True
        )

        # Not required as some valid scenarios won't set this (Overpayments)
        self.event_reason = payments_util.validate_csv_input(
            "EVENTREASON", pei_record, self.validation_container, False
        )

        self.payment_date = payments_util.validate_csv_input(
            "PAYMENTDATE",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=self.payment_period_date_validator,
        )

        self.payment_amount = self.get_payment_amount(pei_record)

        self.payment_transaction_type = self.get_payment_transaction_type()
        # We only want to do specific checks if it is a standard payment
        # There is no need to error a cancellation/overpayment/etc. if the payment
        # is missing EFT or address info that we are never going to use.
        self.is_standard_payment = (
            self.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.STANDARD.payment_transaction_type_id
        )

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS ALWAYS REQUIRED FOR STANDARD PAYMENTS
        #######################################

        # Find the record in the other datasets.
        payment_details = extract_data.payment_details.indexed_data.get(index)
        claim_details = extract_data.claim_details.indexed_data.get(index)
        if not payment_details and self.is_standard_payment:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "payment_details"
            )
        if not claim_details and self.is_standard_payment:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "claim_details"
            )

        if claim_details:
            self.process_claim_details(claim_details, extract_data, count_incrementer)
        elif self.is_standard_payment:
            # We require the absence case number, if claim details doesn't exist
            # we want to set the validation issue manually here
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_FIELD, "ABSENCECASENU"
            )

        if payment_details:
            self.aggregate_payment_details(payment_details)

        self.raw_payment_method = payments_util.validate_csv_input(
            "PAYMENTMETHOD",
            pei_record,
            self.validation_container,
            self.is_standard_payment,
            custom_validator_func=payments_util.lookup_validator(
                PaymentMethod,
                disallowed_lookup_values=[
                    cast(str, PaymentMethod.DEBIT.payment_method_description)
                ],
            ),
        )

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS REQUIRED FOR CHECKS + STANDARD PAYMENT
        #######################################

        # Address values are only required if we are paying by check
        address_required = (
            self.raw_payment_method == PaymentMethod.CHECK.payment_method_description
            and self.is_standard_payment
        )
        self.address_line_one = payments_util.validate_csv_input(
            "PAYMENTADD1", pei_record, self.validation_container, address_required
        )
        self.address_line_two = payments_util.validate_csv_input(
            "PAYMENTADD2",
            pei_record,
            self.validation_container,
            False,  # Address line two always optional
        )
        self.city = payments_util.validate_csv_input(
            "PAYMENTADD4", pei_record, self.validation_container, address_required
        )
        self.state = payments_util.validate_csv_input(
            "PAYMENTADD6",
            pei_record,
            self.validation_container,
            address_required,
            custom_validator_func=payments_util.lookup_validator(GeoState),
        )

        self.zip_code = payments_util.validate_csv_input(
            "PAYMENTPOSTCO",
            pei_record,
            self.validation_container,
            address_required,
            min_length=5,
            max_length=10,
            custom_validator_func=payments_util.zip_code_validator,
        )

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS REQUIRED FOR EFT + STANDARD PAYMENT
        #######################################

        # These are only required if payment_method is for EFT
        eft_required = (
            self.raw_payment_method == PaymentMethod.ACH.payment_method_description
            and self.is_standard_payment
        )
        self.routing_nbr = payments_util.validate_csv_input(
            "PAYEEBANKSORT",
            pei_record,
            self.validation_container,
            eft_required,
            min_length=9,
            max_length=9,
        )
        self.account_nbr = payments_util.validate_csv_input(
            "PAYEEACCOUNTN", pei_record, self.validation_container, eft_required, max_length=40
        )
        self.raw_account_type = payments_util.validate_csv_input(
            "PAYEEACCOUNTT",
            pei_record,
            self.validation_container,
            eft_required,
            custom_validator_func=payments_util.lookup_validator(BankAccountType),
        )

    def get_payment_amount(self, pei_record: Dict[str, str]) -> Optional[Decimal]:
        def amount_validator(amount_str: str) -> Optional[payments_util.ValidationReason]:
            try:
                Decimal(amount_str)
            except (InvalidOperation, TypeError):  # Amount is not numeric
                return payments_util.ValidationReason.INVALID_VALUE
            return None

        raw_payment_amount = payments_util.validate_csv_input(
            "AMOUNT_MONAMT",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=amount_validator,
        )
        if raw_payment_amount:
            return Decimal(raw_payment_amount)
        return None

    def get_payment_transaction_type(self) -> LkPaymentTransactionType:
        """
        Determine the payment transaction type of the data we have processed.
        This document details the order of precedence in how we handle payments that
        could potentially fall into multiple payment types.
        https://lwd.atlassian.net/wiki/spaces/API/pages/1336901700/Types+of+Payments
        """

        # Zero dollar payments overrule all other payment types
        if self.payment_amount == Decimal("0"):
            return PaymentTransactionType.ZERO_DOLLAR

        # Employer reimbursements reimbursements are a very specific set of records
        if (
            self.event_reason == AUTO_ALT_EVENT_REASON
            and self.event_type == PAYMENT_OUT_TRANSACTION_TYPE
            and self.payee_identifier == TAX_IDENTIFICATION_NUMBER
        ):
            return PaymentTransactionType.EMPLOYER_REIMBURSEMENT

        # Note that Overpayments can be positive or negative
        if self.event_type in OVERPAYMENT_PAYMENT_TRANSACTION_TYPES:
            return PaymentTransactionType.OVERPAYMENT

        # Cancellations
        if self.event_type == CANCELLATION_PAYMENT_TRANSACTION_TYPE:
            return PaymentTransactionType.CANCELLATION

        # The bulk of the payments we process will be standard payments
        if (
            self.event_type == PAYMENT_OUT_TRANSACTION_TYPE
            and self.payment_amount
            and self.payment_amount > Decimal("0")
        ):
            return PaymentTransactionType.STANDARD

        # We should always have been able to figure out the payment type
        # from the above checks, this shouldn't happen and should go
        # to the error report as it's not clear what we should do with it
        self.validation_container.add_validation_issue(
            payments_util.ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
            f"Unknown payment scenario encountered. Payment Amount: {self.payment_amount}, Event Type: {self.event_type}, Event Reason: {self.event_reason}",
        )
        return PaymentTransactionType.UNKNOWN

    def process_claim_details(
        self,
        claim_details: Dict[str, str],
        extract_data: ExtractData,
        count_incrementer: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.absence_case_number = payments_util.validate_csv_input(
            "ABSENCECASENU", claim_details, self.validation_container, self.is_standard_payment
        )
        self.leave_request_id = payments_util.validate_csv_input(
            "LEAVEREQUESTI", claim_details, self.validation_container, self.is_standard_payment
        )

        requested_absence = None
        if self.leave_request_id:
            requested_absence = extract_data.requested_absence.indexed_data.get(
                CiIndex(c=self.leave_request_id, i="")
            )
        if requested_absence:

            def leave_request_decision_validator(
                leave_request_decision: str,
            ) -> Optional[payments_util.ValidationReason]:
                if leave_request_decision not in ["In Review", "Pending", "Approved"]:
                    if count_incrementer is not None:
                        count_incrementer(
                            PaymentExtractStep.Metrics.NOT_PENDING_OR_APPROVED_LEAVE_REQUEST_COUNT
                        )
                    return payments_util.ValidationReason.INVALID_VALUE
                return None

            self.leave_request_decision = payments_util.validate_csv_input(
                "LEAVEREQUEST_DECISION",
                requested_absence,
                self.validation_container,
                self.is_standard_payment,
                custom_validator_func=leave_request_decision_validator,
            )

            self.claim_type_raw = payments_util.validate_csv_input(
                "ABSENCEREASON_COVERAGE", requested_absence, self.validation_container, True
            )

        elif self.is_standard_payment:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISMATCHED_DATA,
                f"Payment leave request ID not found in requested absence file: {self.leave_request_id}",
            )

    def aggregate_payment_details(self, payment_details):
        """Aggregate payment period dates across all the payment details for this payment.

        Pseudocode:
           payment_start_period = min(payment_detail[1..N].PAYMENTSTARTP)
           payment_end_period = max(payment_detail[1..N].PAYMENTENDP)
        """
        start_periods = []
        end_periods = []
        for payment_detail_row in payment_details:
            row_start_period = payments_util.validate_csv_input(
                "PAYMENTSTARTP",
                payment_detail_row,
                self.validation_container,
                self.is_standard_payment,
                custom_validator_func=self.payment_period_date_validator,
            )
            row_end_period = payments_util.validate_csv_input(
                "PAYMENTENDPER",
                payment_detail_row,
                self.validation_container,
                self.is_standard_payment,
                custom_validator_func=self.payment_period_date_validator,
            )
            if row_start_period is not None:
                start_periods.append(row_start_period)
            if row_end_period is not None:
                end_periods.append(row_end_period)
        if start_periods:
            self.payment_start_period = min(start_periods)
        if end_periods:
            self.payment_end_period = max(end_periods)

    def payment_period_date_validator(
        self, payment_period_date_str: str
    ) -> Optional[payments_util.ValidationReason]:
        # Convert the str into a date to validate the format
        datetime.strptime(payment_period_date_str, "%Y-%m-%d %H:%M:%S")
        return None

    def get_traceable_details(self) -> Dict[str, Optional[Any]]:
        # For logging purposes, this returns useful, traceable details
        # about a payment that isn't PII. Recommended usage is as:
        # logger.info("...", extra=payment_data.get_traceable_details())
        return {
            "c_value": self.c_value,
            "i_value": self.i_value,
            "absence_case_number": self.absence_case_number,
        }


class PaymentExtractStep(Step):
    class Metrics(str, enum.Enum):
        ACTIVE_PAYMENT_ERROR_COUNT = "active_payment_error_count"
        ALREADY_ACTIVE_PAYMENT_COUNT = "already_active_payment_count"
        APPROVED_PRENOTE_COUNT = "approved_prenote_count"
        CANCELLATION_COUNT = "cancellation_count"
        CLAIM_DETAILS_RECORD_COUNT = "claim_details_record_count"
        CLAIM_NOT_FOUND_COUNT = "claim_not_found_count"
        CLAIMANT_MISMATCH_COUNT = "claimant_mismatch_count"
        EFT_FOUND_COUNT = "eft_found_count"
        EMPLOYEE_MISSING_IN_DB_COUNT = "employee_in_payment_extract_missing_in_db_count"
        EMPLOYER_REIMBURSEMENT_COUNT = "employer_reimbursement_count"
        ERRORED_PAYMENT_COUNT = "errored_payment_count"
        NEW_EFT_COUNT = "new_eft_count"
        NOT_APPROVED_PRENOTE_COUNT = "not_approved_prenote_count"
        NOT_PENDING_OR_APPROVED_LEAVE_REQUEST_COUNT = "not_pending_or_approved_leave_request_count"
        OVERPAYMENT_COUNT = "overpayment_count"
        PAYMENT_DETAILS_RECORD_COUNT = "payment_details_record_count"
        PEI_RECORD_COUNT = "pei_record_count"
        PRENOTE_PAST_WAITING_PERIOD_APPROVED_COUNT = "prenote_past_waiting_period_approved_count"
        PROCESSED_PAYMENT_COUNT = "processed_payment_count"
        REQUESTED_ABSENCE_RECORD_COUNT = "requested_absence_record_count"
        STANDARD_VALID_PAYMENT_COUNT = "standard_valid_payment_count"
        TAX_IDENTIFIER_MISSING_IN_DB_COUNT = "tax_identifier_missing_in_db_count"
        ZERO_DOLLAR_PAYMENT_COUNT = "zero_dollar_payment_count"

    def run_step(self):
        with tempfile.TemporaryDirectory() as download_directory:
            self.process_extract_data(pathlib.Path(download_directory))

    def get_active_payment_state(self, payment: Payment) -> Optional[LkState]:
        """ For the given payment, determine if the payment is being processed or complete
            and if so, return the active state.
            Returns:
              - If being processed, the state the active payment is in, else None
        """
        # Get all payments associated with C/I value
        payment_ids = (
            self.db_session.query(Payment.payment_id)
            .filter(
                Payment.fineos_pei_c_value == payment.fineos_pei_c_value,
                Payment.fineos_pei_i_value == payment.fineos_pei_i_value,
            )
            .all()
        )

        # For each payment, check whether it's currently in any state that is not restartable.
        active_state = (
            self.db_session.query(StateLog)
            .join(LatestStateLog)
            .join(Payment)
            .join(LkState, StateLog.end_state_id == LkState.state_id)
            .filter(
                Payment.payment_id.in_(payment_ids),
                StateLog.end_state_id.notin_(payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS),
                LkState.flow_id == Flow.DELEGATED_PAYMENT.flow_id,
            )
            .first()
        )

        if active_state:
            logger.warning(
                "Payment with C=%s I=%s received from FINEOS that is already in active state: [%s] - active payment ID: %s",
                payment.fineos_pei_c_value,
                payment.fineos_pei_i_value,
                active_state.end_state.state_description,
                active_state.payment.payment_id,
            )
            self.increment(self.Metrics.ALREADY_ACTIVE_PAYMENT_COUNT)
            return active_state.end_state

        return None

    def download_and_extract_data(
        self, extract_data: ExtractData, download_directory: pathlib.Path
    ) -> None:
        logger.info(
            "Downloading and indexing payment extract data files.",
            extra={
                "pei_file": extract_data.pei.file_location,
                "payment_details_file": extract_data.payment_details.file_location,
                "claim_details_file": extract_data.claim_details.file_location,
                "requested_absence_file": extract_data.requested_absence.file_location,
            },
        )
        # To make processing simpler elsewhere, we index each extract file object on a key
        # that will let us join it with the PEI file later.
        ref_file = extract_data.reference_file

        # VPEI file
        pei_data = self.download_and_parse_data(extract_data.pei.file_location, download_directory)

        # This doesn't specifically need to be indexed, but it lets us be consistent
        for record in pei_data:
            extract_data.pei.indexed_data[CiIndex(record["C"], record["I"])] = record

            lower_key_record = payments_util.make_keys_lowercase(record)
            vpei_record = payments_util.create_staging_table_instance(
                lower_key_record, FineosExtractVpei, ref_file, self.get_import_log_id()
            )
            self.db_session.add(vpei_record)
            self.increment(self.Metrics.PEI_RECORD_COUNT)

            logger.debug("indexed pei file row with CI: %s, %s", record["C"], record["I"])

        # Payment details file
        payment_details = self.download_and_parse_data(
            extract_data.payment_details.file_location, download_directory
        )
        # claim details needs to be indexed on PECLASSID and PEINDEXID
        # which point to the vpei.C and vpei.I columns
        for record in payment_details:
            index = CiIndex(record["PECLASSID"], record["PEINDEXID"])
            if index not in extract_data.payment_details.indexed_data:
                extract_data.payment_details.indexed_data[index] = []
            extract_data.payment_details.indexed_data[index].append(record)

            lower_key_record = payments_util.make_keys_lowercase(record)
            claim_details_record = payments_util.create_staging_table_instance(
                lower_key_record, FineosExtractVpeiClaimDetails, ref_file, self.get_import_log_id()
            )
            self.db_session.add(claim_details_record)
            self.increment(self.Metrics.PAYMENT_DETAILS_RECORD_COUNT)
            logger.debug(
                "indexed payment details file row with CI: %s, %s",
                record["PECLASSID"],
                record["PEINDEXID"],
            )

        # Claim details file
        claim_details = self.download_and_parse_data(
            extract_data.claim_details.file_location, download_directory
        )
        # claim details needs to be indexed on PECLASSID and PEINDEXID
        # which point to the vpei.C and vpei.I columns
        for record in claim_details:
            extract_data.claim_details.indexed_data[
                CiIndex(record["PECLASSID"], record["PEINDEXID"])
            ] = record

            lower_key_record = payments_util.make_keys_lowercase(record)
            payment_details_record = payments_util.create_staging_table_instance(
                lower_key_record,
                FineosExtractVpeiPaymentDetails,
                ref_file,
                self.get_import_log_id(),
            )
            self.db_session.add(payment_details_record)
            self.increment(self.Metrics.CLAIM_DETAILS_RECORD_COUNT)
            logger.debug(
                "indexed claim details file row with CI: %s, %s",
                record["PECLASSID"],
                record["PEINDEXID"],
            )

        # Requested absence file
        requested_absences = self.download_and_parse_data(
            extract_data.requested_absence.file_location, download_directory
        )
        for record in requested_absences:
            leave_request_id = str(record.get("LEAVEREQUEST_ID"))
            extract_data.requested_absence.indexed_data[CiIndex(c=leave_request_id, i="")] = record

            lower_key_record = payments_util.make_keys_lowercase(record)
            requested_absence_record = payments_util.create_staging_table_instance(
                lower_key_record,
                FineosExtractVbiRequestedAbsence,
                ref_file,
                self.get_import_log_id(),
            )
            self.db_session.add(requested_absence_record)
            self.increment(self.Metrics.REQUESTED_ABSENCE_RECORD_COUNT)

        logger.info("Successfully downloaded and indexed payment extract data files.")

    def determine_field_names(self, download_location: pathlib.Path) -> List[str]:
        field_names: Dict[str, int] = OrderedDict()
        # Read the first line of the file and handle duplicate field names.
        with open(download_location) as extract_file:
            reader = csv.reader(extract_file, delimiter=",")

            # If duplicates are found, they'll be named
            # field_name_1, field_name_2,..
            for field_name in next(reader):
                if field_name in field_names:
                    new_field_name = f"{field_name}_{field_names[field_name]}"
                    field_names[field_name] += 1
                    field_names[new_field_name] = 1
                else:
                    field_names[field_name] = 1

        return list(field_names.keys())

    def download_and_parse_data(
        self, s3_path: str, download_directory: pathlib.Path
    ) -> List[Dict[str, str]]:
        file_name = s3_path.split("/")[-1]
        download_location = download_directory / file_name
        logger.info("download %s to %s", s3_path, download_location)
        if s3_path.startswith("s3:/"):
            file_util.download_from_s3(s3_path, str(download_location))
        else:
            file_util.copy_file(s3_path, str(download_location))

        raw_extract_data = []

        field_names = self.determine_field_names(download_location)
        with open(download_location) as extract_file:
            dict_reader = csv.DictReader(extract_file, delimiter=",", fieldnames=field_names)
            # Each data object represents a row from the CSV as a dictionary
            # The keys are column headers
            # The rows are the corresponding value in the row
            next(dict_reader)  # Because we specify the fieldnames, skip the header row
            raw_extract_data = list(dict_reader)

        logger.info("read %s: %i records", download_location, len(raw_extract_data))
        return raw_extract_data

    def get_employee_and_claim(
        self, payment_data: PaymentData
    ) -> Tuple[Optional[Employee], Optional[Claim]]:

        # Get the TIN, employee and claim associated with the payment to be made
        employee, claim = None, None
        try:
            # If the payment transaction type is for the employer
            # We know we aren't going to find an employee, so don't look
            if (
                payment_data.payment_transaction_type.payment_transaction_type_id
                != PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
            ):
                tax_identifier = (
                    self.db_session.query(TaxIdentifier)
                    .filter_by(tax_identifier=payment_data.tin)
                    .one_or_none()
                )
                if not tax_identifier:
                    self.increment(self.Metrics.TAX_IDENTIFIER_MISSING_IN_DB_COUNT)
                    payment_data.validation_container.add_validation_issue(
                        payments_util.ValidationReason.MISSING_IN_DB,
                        f"tax_identifier: {payment_data.tin}",
                    )
                else:
                    employee = (
                        self.db_session.query(Employee)
                        .filter_by(tax_identifier=tax_identifier)
                        .one_or_none()
                    )

                    if not employee:
                        self.increment(self.Metrics.EMPLOYEE_MISSING_IN_DB_COUNT)
                        payment_data.validation_container.add_validation_issue(
                            payments_util.ValidationReason.MISSING_IN_DB,
                            f"employee: {payment_data.tin}",
                        )

            claim = (
                self.db_session.query(Claim)
                .filter_by(fineos_absence_id=payment_data.absence_case_number)
                .one_or_none()
            )
        except SQLAlchemyError as e:
            logger.exception(
                "Unexpected error %s with one_or_none when querying for tin/employee/claim",
                type(e),
                extra=payment_data.get_traceable_details(),
            )
            raise

        # If we cannot find the claim, we want to error only for standard
        # payments. While we'd like to attach the claim to other payment types
        # it's less of a concern to us.
        if not claim and payment_data.is_standard_payment:
            payment_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB,
                f"claim: {payment_data.absence_case_number}",
            )
            self.increment(self.Metrics.CLAIM_NOT_FOUND_COUNT)
            return None, None

        # Perform various validations on the claim. We require
        # A claim to be ID Proofed
        # A claim to have a claim type
        # The employee we fetched above to already be connected to the claim
        if claim:
            # TODO - ask Mass about non-standard payments
            if not claim.is_id_proofed:
                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.CLAIM_NOT_ID_PROOFED,
                    f"Claim {payment_data.absence_case_number} has not been ID proofed",
                )

            # If the employee we found does not match what is already attached
            # to the claim, we can't accept the payment.
            if employee and claim.employee_id != employee.employee_id:

                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.CLAIMANT_MISMATCH,
                    f"Claimant {claim.employee_id} is attached to claim {claim.fineos_absence_id}, but claimant {employee.employee_id} was found.",
                )
                self.increment(self.Metrics.CLAIMANT_MISMATCH_COUNT)
                return None, None

        return employee, claim

    def update_experian_address_pair_fineos_address(
        self, payment_data: PaymentData, employee: Employee
    ) -> Tuple[Optional[ExperianAddressPair], bool]:
        """Create or update the employee's EFT record

        Returns:
            bool: True if payment_data has address updates; False otherwise
        """
        # Only update if the employee is using Check for payments
        if payment_data.validation_container.has_validation_issues():
            # We will only update address information if the payment has no issues up to
            # this point in the processing, meaning that required fields are present.
            return None, False

        # Construct an Address from the payment_data
        payment_data_address = Address(
            address_id=uuid.uuid4(),
            address_line_one=payment_data.address_line_one,
            address_line_two=payment_data.address_line_two
            if payment_data.address_line_two
            else None,
            city=payment_data.city,
            geo_state_id=GeoState.get_id(payment_data.state) if payment_data.state else None,
            zip_code=payment_data.zip_code,
            address_type_id=AddressType.MAILING.address_type_id,
        )

        # If existing_address_pair exists, compare the existing fineos_address with the payment_data address
        #   If they're the same, nothing needs to be done, so we can return the address
        existing_address_pair = payments_util.find_existing_address_pair(
            employee, payment_data_address, self.db_session
        )
        if existing_address_pair:
            return existing_address_pair, False

        # We need to add the address to the employee.
        # TODO - If FINEOS provides a value that indicates an address
        # has been validated, we would also set the experian_address here.
        # When already verified address is supported, also add a happy path test scenario.
        new_experian_address_pair = ExperianAddressPair(fineos_address=payment_data_address)

        self.db_session.add(payment_data_address)
        self.db_session.add(new_experian_address_pair)

        # We also want to make sure the address is linked in the EmployeeAddress table
        employee_address = EmployeeAddress(employee=employee, address=payment_data_address)
        self.db_session.add(employee_address)
        return new_experian_address_pair, True

    def create_payment(
        self,
        payment_data: PaymentData,
        claim: Optional[Claim],
        validation_container: payments_util.ValidationContainer,
    ) -> Payment:
        # We always create a new payment record. This may be completely new
        # or a payment might have been created before. We'll check that later.

        logger.info(
            "Creating new payment for CI: %s, %s",
            payment_data.c_value,
            payment_data.i_value,
            extra=payment_data.get_traceable_details(),
        )
        payment = Payment(payment_id=uuid.uuid4())

        # set the payment method
        if payment_data.raw_payment_method:
            payment.disb_method_id = PaymentMethod.get_id(payment_data.raw_payment_method)

        # Note that these values may have validation issues
        # that is fine as it will get moved to an error state
        if claim:
            payment.claim = claim
        payment.period_start_date = payments_util.datetime_str_to_date(
            payment_data.payment_start_period
        )
        payment.period_end_date = payments_util.datetime_str_to_date(
            payment_data.payment_end_period
        )
        payment.payment_date = payments_util.datetime_str_to_date(payment_data.payment_date)

        payment.payment_transaction_type_id = (
            payment_data.payment_transaction_type.payment_transaction_type_id
        )

        if payment_data.payment_amount is not None:
            payment.amount = payment_data.payment_amount
        else:
            # In the unlikely scenario where payment amount isn't set
            # we need to set something as the DB requires this to be set
            payment.amount = Decimal("0")

            # As a sanity check, make certain that missing amount was caught
            # by the earlier validation logic, this if statement shouldn't
            # ever happen. This exists to show we're not ever accidentally
            # setting a payment that is going further in processing.
            if not validation_container.has_validation_issues():
                raise Exception(
                    "A payment without an amount was found and not caught by validation."
                )

        payment.fineos_pei_c_value = payment_data.c_value
        payment.fineos_pei_i_value = payment_data.i_value
        payment.fineos_extraction_date = payments_util.get_now().date()
        payment.fineos_extract_import_log_id = self.get_import_log_id()
        payment.leave_request_decision = payment_data.leave_request_decision

        if payment_data.claim_type_raw:
            try:
                claim_type_mapped = payments_util.get_mapped_claim_type(payment_data.claim_type_raw)
                payment.claim_type_id = claim_type_mapped.claim_type_id
            except ValueError:
                validation_container.add_validation_issue(
                    payments_util.ValidationReason.INVALID_VALUE, "ABSENCEREASON_COVERAGE"
                )

        # If the payment is already being processed,
        # then FINEOS sent us a payment they should not have
        # whether that's a FINEOS issue or writeback issue, we
        # need to error the payment.
        active_state = self.get_active_payment_state(payment)
        if active_state:
            self.increment(self.Metrics.ACTIVE_PAYMENT_ERROR_COUNT)
            validation_container.add_validation_issue(
                payments_util.ValidationReason.RECEIVED_PAYMENT_CURRENTLY_BEING_PROCESSED,
                f"We received a payment that is already being processed. It is currently in state [{active_state.state_description}].",
            )

        self.db_session.add(payment)

        return payment

    def update_eft(
        self, payment_data: PaymentData, employee: Employee
    ) -> Tuple[Optional[PubEft], bool]:
        """Create or update the employee's EFT records

        Returns:
            bool: True if the payment_data includes EFT updates; False otherwise
        """

        # Only update if the employee is using ACH for payments
        if payment_data.raw_payment_method != PaymentMethod.ACH.payment_method_description:
            # Any existing EFT information is left alone in the event they switch back
            return None, False

        if payment_data.validation_container.has_validation_issues():
            # We will only update EFT information if the payment has no issues up to
            # this point in the processing, meaning that required fields are present.
            return None, False

        if not payment_data.is_standard_payment:
            # If it's any non-standard payment (cancellation, overpayment, employer, etc.)
            # There isn't a need to prenote, as it's not going to be paid directly anyways
            # and we don't want to error the payment because it needs to be prenoted.
            return None, False

        # Need to cast these values as str rather than Optional[str] as we've
        # already validated they're not None for linting
        # Construct an EFT object.
        new_eft = PubEft(
            pub_eft_id=uuid.uuid4(),
            routing_nbr=cast(str, payment_data.routing_nbr),
            account_nbr=cast(str, payment_data.account_nbr),
            bank_account_type_id=BankAccountType.get_id(payment_data.raw_account_type),
            prenote_state_id=PrenoteState.PENDING_PRE_PUB.prenote_state_id,  # If this is new, we want it to be pending
        )

        # Retrieve the employee's existing EFT data, if any
        existing_eft = payments_util.find_existing_eft(employee, new_eft)

        # If we found a match, do not need to create anything
        # but do need to add an error to the report if the EFT
        # information is invalid or pending. We can't pay someone
        # unless they have been prenoted
        extra = payment_data.get_traceable_details()
        extra["employee_id"] = employee.employee_id
        if existing_eft:
            extra["pub_eft_id"] = existing_eft.pub_eft_id
            self.increment(self.Metrics.EFT_FOUND_COUNT)
            logger.info(
                "Found existing EFT info for claimant in prenote state %s",
                existing_eft.prenote_state.prenote_state_description,
                extra=extra,
            )

            if PrenoteState.APPROVED.prenote_state_id == existing_eft.prenote_state_id:
                self.increment(self.Metrics.APPROVED_PRENOTE_COUNT)
            elif (
                (PrenoteState.PENDING_WITH_PUB.prenote_state_id == existing_eft.prenote_state_id)
                and existing_eft.prenote_sent_at
                and (get_now() - existing_eft.prenote_sent_at).days
                >= PRENOTE_PRENDING_WAITING_PERIOD
            ):
                self.increment(self.Metrics.PRENOTE_PAST_WAITING_PERIOD_APPROVED_COUNT)
            else:
                self.increment(self.Metrics.NOT_APPROVED_PRENOTE_COUNT)
                reason = (
                    payments_util.ValidationReason.EFT_PRENOTE_REJECTED
                    if existing_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id
                    else payments_util.ValidationReason.EFT_PRENOTE_PENDING
                )
                payment_data.validation_container.add_validation_issue(
                    reason,
                    f"EFT prenote has not been approved, is currently in state [{existing_eft.prenote_state.prenote_state_description}]",
                )

            return existing_eft, False

        else:
            # This EFT info is new, it needs to be linked to the employee
            # and added to the EFT prenoting flow

            # We will only add it if the EFT info we require is valid and exists
            employee_pub_eft_pair = EmployeePubEftPair(
                employee_id=employee.employee_id, pub_eft_id=new_eft.pub_eft_id
            )

            self.db_session.add(new_eft)
            self.db_session.add(employee_pub_eft_pair)

            extra["pub_eft_id"] = new_eft.pub_eft_id
            logger.info(
                "Initiating DELEGATED_EFT flow for employee associated with payment", extra=extra,
            )

            # We need to put the payment in an error state if it's not prenoted
            payment_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.EFT_PRENOTE_PENDING,
                "New EFT info found, prenote required",
            )
            self.increment(self.Metrics.NEW_EFT_COUNT)

            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_EFT_SEND_PRENOTE,
                associated_model=employee,
                outcome=state_log_util.build_outcome(
                    "Initiated DELEGATED_EFT flow for employee associated with payment"
                ),
                db_session=self.db_session,
            )
            return new_eft, True

    def add_records_to_db(
        self,
        payment_data: PaymentData,
        employee: Optional[Employee],
        claim: Optional[Claim],
        reference_file: ReferenceFile,
    ) -> Payment:
        # Only update the employee if it exists and there
        # are no validation issues. Employees are used in
        # many contexts, so we want to be careful about modifying
        # them with problematic data.
        has_address_update, has_eft_update = False, False
        payment_eft, address_pair = None, None
        if employee and not payment_data.validation_container.has_validation_issues():
            # Update the mailing address with values from FINEOS
            address_pair, has_address_update = self.update_experian_address_pair_fineos_address(
                payment_data, employee
            )

            # Update the EFT info with values from FINEOS
            payment_eft, has_eft_update = self.update_eft(payment_data, employee)

        # Create the payment record
        payment = self.create_payment(payment_data, claim, payment_data.validation_container)

        # Specify whether the Payment has an address update
        # TODO - is this still needed?
        payment.has_address_update = has_address_update

        # Specify whether the Payment has an EFT update
        # TODO - Is this still needed?
        payment.has_eft_update = has_eft_update

        # Attach the EFT info used to the payment
        if payment_eft:
            payment.pub_eft = payment_eft

        # Attach the address info used to the payment
        if address_pair:
            payment.experian_address_pair = address_pair

        # Link the payment object to the payment_reference_file
        payment_reference_file = PaymentReferenceFile(
            payment=payment, reference_file=reference_file,
        )
        self.db_session.add(payment_reference_file)

        return payment

    def process_payment_data_record(
        self, payment_data: PaymentData, reference_file: ReferenceFile
    ) -> Payment:
        employee, claim = self.get_employee_and_claim(payment_data)

        # If the employee is set, we need to wrap the DB queries
        # to avoid adding additional employee log entries
        if employee:
            with fineos_log_tables_util.update_entity_and_remove_log_entry(
                self.db_session, employee, commit=False
            ):
                payment = self.add_records_to_db(payment_data, employee, claim, reference_file)
        else:
            payment = self.add_records_to_db(payment_data, None, claim, reference_file)

        return payment

    def _setup_state_log(self, payment: Payment, payment_data: PaymentData) -> None:

        # https://lwd.atlassian.net/wiki/spaces/API/pages/1336901700/Types+of+Payments
        # Does the payment have validation issues
        # If so, add to that error state
        if payment_data.validation_container.has_validation_issues():
            end_state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
            message = "Error processing payment record"
            self.increment(self.Metrics.ERRORED_PAYMENT_COUNT)

        # Employer reimbursements are added to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        ):
            end_state = (
                State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_EMPLOYER_REIMBURSEMENT
            )
            message = "Employer reimbursement added to pending state for FINEOS writeback"
            self.increment(self.Metrics.EMPLOYER_REIMBURSEMENT_COUNT)

        # Zero dollar payments are added to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
        ):
            end_state = State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT
            message = "Zero dollar payment added to pending state for FINEOS writeback"
            self.increment(self.Metrics.ZERO_DOLLAR_PAYMENT_COUNT)

        # Overpayments are added to to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.OVERPAYMENT.payment_transaction_type_id
        ):
            end_state = State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT
            message = "Overpayment payment added to pending state for FINEOS writeback"
            self.increment(self.Metrics.OVERPAYMENT_COUNT)

        # Cancellations are added to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
        ):
            end_state = State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION
            message = "Cancellation payment added to pending state for FINEOS writeback"
            self.increment(self.Metrics.CANCELLATION_COUNT)

        else:
            end_state = State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK
            message = "Success"
            self.increment(self.Metrics.STANDARD_VALID_PAYMENT_COUNT)

        state_log_util.create_finished_state_log(
            end_state=end_state,
            outcome=state_log_util.build_outcome(message, payment_data.validation_container),
            associated_model=payment,
            db_session=self.db_session,
        )

    def process_records_to_db(self, extract_data: ExtractData) -> None:
        logger.info("Processing payment extract data into db: %s", extract_data.date_str)

        # Add the files to the DB
        # Note a single payment reference file is used for all files collectively
        self.db_session.add(extract_data.reference_file)

        for index, record in extract_data.pei.indexed_data.items():
            try:
                self.increment(self.Metrics.PROCESSED_PAYMENT_COUNT)
                # Construct a payment data object for easier organization of the many params
                payment_data = PaymentData(
                    extract_data, index, record, count_incrementer=self.increment
                )
                logger.debug(
                    "Constructed payment data for extract with CI: %s, %s", index.c, index.i
                )

                logger.info(
                    f"Processing payment record - absence case number: {payment_data.absence_case_number}",
                    extra=payment_data.get_traceable_details(),
                )

                payment = self.process_payment_data_record(
                    payment_data, extract_data.reference_file
                )

                # Create and finish the state log. If there were any issues, this'll set the
                # record to an error state which'll send out a report to address it, otherwise
                # it will move onto the next step in processing
                self._setup_state_log(
                    payment, payment_data,
                )

                logger.info(
                    f"Done processing payment record - absence case number: {payment_data.absence_case_number}",
                    extra=payment_data.get_traceable_details(),
                )
            except Exception:
                # An exception during processing would indicate
                # either a bug or a scenario that we believe invalidates
                # an entire file and warrants investigating
                logger.exception(
                    "An error occurred while processing payment for CI: %s, %s", index.c, index.i,
                )
                raise

        logger.info("Successfully processed payment extract into db: %s", extract_data.date_str)
        return None

    # TODO move to payments_util
    def move_files_from_received_to_processed(self, extract_data: ExtractData) -> None:
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
        # to
        # s3://bucket/path/to/processed/2020-01-01-11-30-00-payment-export/2020-01-01-11-30-00-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )
        new_pei_s3_path = extract_data.pei.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)
        logger.debug(
            "Moved PEI file to processed folder.",
            extra={"source": extract_data.pei.file_location, "destination": new_pei_s3_path},
        )

        new_payment_s3_path = extract_data.payment_details.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.payment_details.file_location, new_payment_s3_path)
        logger.debug(
            "Moved payments details file to processed folder.",
            extra={
                "source": extract_data.payment_details.file_location,
                "destination": new_payment_s3_path,
            },
        )

        new_claim_s3_path = extract_data.claim_details.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)
        logger.debug(
            "Moved claim details file to processed folder.",
            extra={
                "source": extract_data.claim_details.file_location,
                "destination": new_claim_s3_path,
            },
        )

        new_requested_absence_s3_path = extract_data.requested_absence.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(
            extract_data.requested_absence.file_location, new_requested_absence_s3_path
        )
        logger.debug(
            "Moved requested absence file to processed folder.",
            extra={
                "source": extract_data.requested_absence.file_location,
                "destination": new_requested_absence_s3_path,
            },
        )

        # Update the reference file DB record to point to the new folder for these files
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            RECEIVED_FOLDER, f"{PROCESSED_FOLDER}"
        )
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            extract_data.date_str, date_group_folder
        )
        self.db_session.add(extract_data.reference_file)
        logger.debug(
            "Updated reference file location for payment extract data.",
            extra={"reference_file_location": extract_data.reference_file.file_location},
        )

        logger.info("Successfully moved payments files to processed folder.")

    # TODO move to payments_util
    def move_files_from_received_to_skipped(self, extract_data: ExtractData) -> None:
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
        # to
        # s3://bucket/path/to/processed/2020-01-01-11-30-00-payment-export/2020-01-01-11-30-00-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )
        new_pei_s3_path = extract_data.pei.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)
        logger.debug(
            "Moved PEI file to skipped folder.",
            extra={"source": extract_data.pei.file_location, "destination": new_pei_s3_path},
        )

        new_payment_s3_path = extract_data.payment_details.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.payment_details.file_location, new_payment_s3_path)
        logger.debug(
            "Moved payments details file to skipped folder.",
            extra={
                "source": extract_data.payment_details.file_location,
                "destination": new_payment_s3_path,
            },
        )

        new_claim_s3_path = extract_data.claim_details.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)
        logger.debug(
            "Moved claim details file to skipped folder.",
            extra={
                "source": extract_data.claim_details.file_location,
                "destination": new_claim_s3_path,
            },
        )

        new_requested_absence_s3_path = extract_data.requested_absence.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}/{date_group_folder}"
        )
        file_util.rename_file(
            extract_data.requested_absence.file_location, new_requested_absence_s3_path
        )
        logger.debug(
            "Moved requested absence file to processed folder.",
            extra={
                "source": extract_data.requested_absence.file_location,
                "destination": new_requested_absence_s3_path,
            },
        )

        # Update the reference file DB record to point to the new folder for these files
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            RECEIVED_FOLDER, f"{SKIPPED_FOLDER}"
        )
        extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
            extract_data.date_str, date_group_folder
        )
        self.db_session.add(extract_data.reference_file)
        logger.debug(
            "Updated reference file location for payment extract data.",
            extra={"reference_file_location": extract_data.reference_file.file_location},
        )

        logger.info("Successfully moved payments files to skipped folder.")

    # TODO move to payments_util
    def move_files_from_received_to_error(self, extract_data: Optional[ExtractData]) -> None:
        if not extract_data:
            logger.error("Cannot move files to error directory, as path is not known")
            return
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
        # to
        # s3://bucket/path/to/error/2020-01-01-11-30-00-payment-export/2020-01-01-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )
        new_pei_s3_path = extract_data.pei.file_location.replace(
            RECEIVED_FOLDER, f"error/{date_group_folder}"
        )
        file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)
        logger.debug(
            "Moved PEI file to error folder.",
            extra={"source": extract_data.pei.file_location, "destination": new_pei_s3_path},
        )

        new_payment_s3_path = extract_data.payment_details.file_location.replace(
            RECEIVED_FOLDER, f"error/{date_group_folder}"
        )
        file_util.rename_file(extract_data.payment_details.file_location, new_payment_s3_path)
        logger.debug(
            "Moved payments details file to error folder.",
            extra={
                "source": extract_data.payment_details.file_location,
                "destination": new_payment_s3_path,
            },
        )

        new_claim_s3_path = extract_data.claim_details.file_location.replace(
            RECEIVED_FOLDER, f"error/{date_group_folder}"
        )
        file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)
        logger.debug(
            "Moved claim details file to error folder.",
            extra={
                "source": extract_data.claim_details.file_location,
                "destination": new_claim_s3_path,
            },
        )

        new_requested_absence_s3_path = extract_data.requested_absence.file_location.replace(
            RECEIVED_FOLDER, f"error/{date_group_folder}"
        )
        file_util.rename_file(
            extract_data.requested_absence.file_location, new_requested_absence_s3_path
        )
        logger.debug(
            "Moved requested absence file to error folder.",
            extra={
                "source": extract_data.requested_absence.file_location,
                "destination": new_requested_absence_s3_path,
            },
        )

        # We still want to create the reference file, just use the one that is
        # created in the __init__ of the extract data object and set the path.
        # Note that this will not be attached to a payment
        extract_data.reference_file.file_location = file_util.get_directory(new_pei_s3_path)
        self.db_session.add(extract_data.reference_file)
        logger.debug(
            "Updated reference file location for payment extract data.",
            extra={"reference_file_location": extract_data.reference_file.file_location},
        )

        logger.info("Successfully moved payments files to error folder.")

    def process_extract_data(self, download_directory: pathlib.Path) -> None:

        logger.info("Processing payment extract files")

        payments_util.copy_fineos_data_to_archival_bucket(
            self.db_session, expected_file_names, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        )
        data_by_date = payments_util.group_s3_files_by_date(expected_file_names)

        previously_processed_date = set()

        logger.info("Dates in /received folder: %s", ", ".join(data_by_date.keys()))

        if bool(data_by_date):
            latest_date_str = sorted(data_by_date.keys())[-1]

        for date_str, s3_file_locations in data_by_date.items():

            logger.debug(
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
                        self.db_session, date_str, ReferenceFileType.FINEOS_PAYMENT_EXTRACT
                    )
                ):
                    logger.warning(
                        "Found existing ReferenceFile record for date group in /processed folder: %s",
                        date_str,
                        extra={"date_group": date_str},
                    )
                    previously_processed_date.add(date_str)
                    continue

                self.download_and_extract_data(extract_data, download_directory)

                self.process_records_to_db(extract_data)
                self.move_files_from_received_to_processed(extract_data)

                logger.info(
                    "Successfully processed payment extract files in date group: %s",
                    date_str,
                    extra={"date_group": date_str},
                )
                self.db_session.commit()
            except Exception:
                self.db_session.rollback()
                logger.exception(
                    "Error processing payment extract files in date_group: %s",
                    date_str,
                    extra={"date_group": date_str},
                )
                self.move_files_from_received_to_error(extract_data)
                raise

        logger.info("Successfully processed payment extract files")
