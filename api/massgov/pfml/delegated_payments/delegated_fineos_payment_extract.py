import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
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
    LatestStateLog,
    LkPaymentRelevantParty,
    LkPaymentTransactionType,
    Payment,
    PaymentDetails,
    PaymentMethod,
    PaymentReferenceFile,
    PaymentRelevantParty,
    PaymentTransactionType,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.geo import GeoState
from massgov.pfml.db.models.payments import (
    ACTIVE_WRITEBACK_RECORD_STATUS,
    FineosExtractVbiRequestedAbsence,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
    FineosExtractVpeiPaymentLine,
    FineosWritebackTransactionStatus,
    LkFineosWritebackTransactionStatus,
    LkPaymentEventType,
    PaymentEventType,
    PaymentLine,
)
from massgov.pfml.db.models.state import Flow, LkState, State
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    stage_payment_fineos_writeback,
)
from massgov.pfml.util.converters.str_to_numeric import str_to_int
from massgov.pfml.util.datetime import datetime_str_to_date, get_now_us_eastern

logger = logging.get_logger(__name__)

# waiting period for pending prenote
PRENOTE_PRENDING_WAITING_PERIOD = 5

# folder constants
RECEIVED_FOLDER = "received"
PROCESSED_FOLDER = "processed"
SKIPPED_FOLDER = "skipped"

CANCELLATION_PAYMENT_TRANSACTION_TYPE = "PaymentOut Cancellation"

STATE_TAX_WITHHOLDING_TIN = "SITPAYEE001"
FEDERAL_TAX_WITHHOLDING_TIN = "FITAMOUNTPAYEE001"

# There are multiple types of overpayments
OVERPAYMENT_PAYMENT_TRANSACTION_TYPES = [
    PaymentTransactionType.OVERPAYMENT,
    PaymentTransactionType.OVERPAYMENT_ACTUAL_RECOVERY,
    PaymentTransactionType.OVERPAYMENT_RECOVERY,
    PaymentTransactionType.OVERPAYMENT_ADJUSTMENT,
    PaymentTransactionType.OVERPAYMENT_RECOVERY_REVERSE,
    PaymentTransactionType.OVERPAYMENT_RECOVERY_CANCELLATION,
    PaymentTransactionType.OVERPAYMENT_ACTUAL_RECOVERY_CANCELLATION,
    PaymentTransactionType.OVERPAYMENT_ADJUSTMENT_CANCELLATION,
]

PAYMENT_EVENT_TYPES = [
    PaymentEventType.PAYMENT_OUT,
    PaymentEventType.PAYMENT_OUT_CANCELLATIONS,
    PaymentEventType.OVERPAYMENT,
    PaymentEventType.OVERPAYMENT_ADJUSTMENT,
    PaymentEventType.OVERPAYMENT_ADJUSTMENT_CANCELLATION,
    PaymentEventType.OVERPAYMENT_ACTUAL_RECOVERY,
    PaymentEventType.OVERPAYMENT_RECOVERY_CANCELLATION,
    PaymentEventType.OVERPAYMENT_ACTUAL_RECOVERY_CANCELLATION,
    PaymentEventType.OVERPAYMENT_RECOVERY_REVERSE,
]

OVERPAYMENT_PAYMENT_TRANSACTION_TYPE_IDS = set(
    [
        overpayment_transaction_type.payment_transaction_type_id
        for overpayment_transaction_type in OVERPAYMENT_PAYMENT_TRANSACTION_TYPES
    ]
)
PAYMENT_OUT_TRANSACTION_TYPE = "PaymentOut"
AUTO_ALT_EVENT_REASON = "Automatic Alternate Payment"

TAX_IDENTIFICATION_NUMBER = "Tax Identification Number"

# TASKTYPENAME of VBI Task Report Som for other income-related tasks
OTHER_INCOME_TASKTYPENAMES = [
    "Employee Reported Other Income",
    "Escalate Employer Reported Other Income",
    "Escalate employer reported accrued paid leave (PTO)",
    "Employee reported accrued paid leave (PTO)",
    "Employee Reported Other Leave",
]


class PaymentData:
    """A class for containing any and all payment data. Handles validation and
    pulling values out of the various types

    All values are pulled from the CSV as-is and as strings. Values prefixed with raw_ need
    to be converted from the FINEOS value to one of our DB values (usually a lookup enum)
    """

    validation_container: payments_util.ValidationContainer

    pei_record: FineosExtractVpei

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
    absence_case_creation_date: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    amalgamation_c: Optional[str] = None
    payment_type: Optional[str] = None

    claim_type_raw: Optional[str] = None

    routing_nbr: Optional[str] = None
    account_nbr: Optional[str] = None
    raw_account_type: Optional[str] = None

    payment_detail_records: List[PaymentDetails]
    payment_line_records: List[PaymentLine]

    payment_transaction_type: LkPaymentTransactionType
    payment_relevant_party: LkPaymentRelevantParty
    is_standard_payment: bool
    is_employee_required: bool
    is_employer_reimbursement: bool
    is_employer_reimbursement_enabled: bool
    is_payment_intended_for_pub: bool
    is_payment_detail_expected: bool

    def __init__(
        self,
        c_value: str,
        i_value: str,
        pei_record: FineosExtractVpei,
        payment_details: List[FineosExtractVpeiPaymentDetails],
        payment_lines: List[FineosExtractVpeiPaymentLine],
        claim_details: Optional[FineosExtractVpeiClaimDetails],
        requested_absence_record: Optional[FineosExtractVbiRequestedAbsence],
        count_incrementer: Optional[Callable[[str], None]] = None,
    ):
        self.validation_container = payments_util.ValidationContainer(
            str(f"C={c_value},I={i_value}")
        )
        self.c_value = c_value
        self.i_value = i_value
        self.pei_record = pei_record

        self.payment_detail_records = []
        self.payment_line_records = []

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS ALWAYS REQUIRED FOR ALL PAYMENTS
        #######################################

        # Grab every value we might need out of the datasets
        self.tin = payments_util.validate_db_input(
            "PAYEESOCNUMBE", pei_record, self.validation_container, True
        )

        self.payee_identifier = payments_util.validate_db_input(
            "PAYEEIDENTIFI", pei_record, self.validation_container, True
        )

        self.event_type = payments_util.validate_db_input(
            "EVENTTYPE", pei_record, self.validation_container, True
        )

        # Not required as some valid scenarios won't set this (Overpayments)
        self.event_reason = payments_util.validate_db_input(
            "EVENTREASON", pei_record, self.validation_container, False
        )

        # Not required, only care if it's set and a specific value
        self.amalgamation_c = payments_util.validate_db_input(
            "AMALGAMATIONC", pei_record, self.validation_container, False
        )

        self.payment_type = payments_util.validate_db_input(
            "PAYMENTTYPE", pei_record, self.validation_container, False
        )

        self.payment_date = payments_util.validate_db_input(
            "PAYMENTDATE",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=self.payment_period_date_validator,
        )

        self.payment_amount = self.get_payment_amount(pei_record)

        self.payment_relevant_party = self.get_relevant_party()

        self.payment_transaction_type = self.get_payment_transaction_type()

        # Overpayment recoveries (of several different types) do not
        # have payment detail records as they don't have pay periods
        self.is_payment_detail_expected = (
            self.payment_transaction_type.payment_transaction_type_id
            not in payments_util.Constants.OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS_IDS
        )

        # Process the payment details records in order to get specific
        # pay-period information for payments.
        if not payment_details and self.is_payment_detail_expected:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "payment_details", "payment_details"
            )

        if payment_details:
            self.aggregate_payment_details(payment_details)

        # We always expect payment lines, except for zero dollar tax withholdings
        # which don't end up with payment line records for whatever reason
        is_tax_withholding = self.payment_relevant_party.payment_relevant_party_id in [
            PaymentRelevantParty.FEDERAL_TAX.payment_relevant_party_id,
            PaymentRelevantParty.STATE_TAX.payment_relevant_party_id,
        ]
        is_zero_dollar = (
            self.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
        )
        if not payment_lines and not (is_tax_withholding and is_zero_dollar):
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "payment_lines", "payment_lines"
            )

        if payment_lines:
            self.aggregate_payment_lines(payment_lines)

        # We only want to do specific checks if it is a standard payment
        # There is no need to error a cancellation/overpayment/etc. if the payment
        # is missing EFT or address info that we are never going to use.
        self.is_standard_payment = (
            self.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.STANDARD.payment_transaction_type_id
        )

        self.is_employer_reimbursement = (
            self.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        )

        self.is_employer_reimbursement_enabled = (
            payments_util.is_employer_reimbursement_payments_enabled()
        )

        self.is_payment_intended_for_pub = self.is_standard_payment or (
            self.is_employer_reimbursement and self.is_employer_reimbursement_enabled
        )

        # We only want to check for an employee in certain scenarios
        # Employer Reimbursements will not map to an Employee,
        # and nor will payments associated with tax withholdings
        # We are not checking against transaction type here because
        # cancelled tax withholdings will be "Cancellations" not tax withholdings.
        if self.is_employer_reimbursement_enabled:
            self.is_employee_required = (
                self.tin != STATE_TAX_WITHHOLDING_TIN and self.tin != FEDERAL_TAX_WITHHOLDING_TIN
            )
        else:
            self.is_employee_required = (
                self.payment_transaction_type.payment_transaction_type_id
                != PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
                and self.tin != STATE_TAX_WITHHOLDING_TIN
                and self.tin != FEDERAL_TAX_WITHHOLDING_TIN
            )

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS ALWAYS REQUIRED FOR STANDARD PAYMENTS
        #######################################

        # Find the record in the other datasets.
        if not claim_details and self.is_payment_intended_for_pub:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "claim_details"
            )

        if claim_details:
            self.process_claim_details(claim_details, requested_absence_record, count_incrementer)
        elif self.is_payment_intended_for_pub:
            # We require the absence case number, if claim details doesn't exist
            # we want to set the validation issue manually here
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_FIELD, "ABSENCECASENU"
            )

        disallowed_lookup_values = [PaymentMethod.DEBIT.payment_method_description]
        # Employer reimbursements are check only
        if self.is_employer_reimbursement:
            disallowed_lookup_values.append(PaymentMethod.ACH.payment_method_description)
        self.raw_payment_method = payments_util.validate_db_input(
            "PAYMENTMETHOD",
            pei_record,
            self.validation_container,
            self.is_payment_intended_for_pub,
            custom_validator_func=payments_util.lookup_validator(
                PaymentMethod,
                disallowed_lookup_values=disallowed_lookup_values,
            ),
        )

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS REQUIRED FOR CHECKS + STANDARD PAYMENT
        #######################################

        # Address values are only required if we are paying by check
        address_required = (
            self.raw_payment_method == PaymentMethod.CHECK.payment_method_description
            and self.is_payment_intended_for_pub
        )
        self.address_line_one = payments_util.validate_db_input(
            "PAYMENTADD1", pei_record, self.validation_container, address_required
        )
        self.address_line_two = payments_util.validate_db_input(
            "PAYMENTADD2",
            pei_record,
            self.validation_container,
            False,  # Address line two always optional
        )
        self.city = payments_util.validate_db_input(
            "PAYMENTADD4", pei_record, self.validation_container, address_required
        )
        self.state = payments_util.validate_db_input(
            "PAYMENTADD6",
            pei_record,
            self.validation_container,
            address_required,
            custom_validator_func=payments_util.lookup_validator(GeoState),
        )

        self.zip_code = payments_util.validate_db_input(
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
        self.routing_nbr = payments_util.validate_db_input(
            "PAYEEBANKSORT",
            pei_record,
            self.validation_container,
            eft_required,
            min_length=9,
            max_length=9,
            custom_validator_func=payments_util.routing_number_validator,
        )
        self.account_nbr = payments_util.validate_db_input(
            "PAYEEACCOUNTN", pei_record, self.validation_container, eft_required, max_length=17
        )
        self.raw_account_type = payments_util.validate_db_input(
            "PAYEEACCOUNTT",
            pei_record,
            self.validation_container,
            eft_required,
            custom_validator_func=payments_util.lookup_validator(BankAccountType),
        )

        #######################################
        # BEGIN - VALIDATION OF PARAMETERS REQUIRED FOR CHECKS + EMPLOYER REIMBURSEMENT PAYMENT
        #######################################
        if (
            self.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        ):
            self.full_name = payments_util.validate_db_input(
                "PAYEEFULLNAME",
                pei_record,
                self.validation_container,
                self.is_employer_reimbursement,
            )

    def get_payment_amount(self, pei_record: FineosExtractVpei) -> Optional[Decimal]:
        raw_payment_amount = payments_util.validate_db_input(
            "AMOUNT_MONAMT",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=payments_util.amount_validator,
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
        # Cancellations
        if self.event_type == CANCELLATION_PAYMENT_TRANSACTION_TYPE:
            return PaymentTransactionType.CANCELLATION

        # Zero dollar payments overrule all other payment types
        if self.payment_amount == Decimal("0"):
            return PaymentTransactionType.ZERO_DOLLAR

        # Note that Overpayments can be positive or negative amounts
        overpayment_transaction_type = self.get_transaction_type_if_overpayment()
        if overpayment_transaction_type:
            return overpayment_transaction_type

        party_to_type = {
            PaymentRelevantParty.STATE_TAX.payment_relevant_party_id: PaymentTransactionType.STATE_TAX_WITHHOLDING,
            PaymentRelevantParty.FEDERAL_TAX.payment_relevant_party_id: PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
            PaymentRelevantParty.REIMBURSED_EMPLOYER.payment_relevant_party_id: PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
            PaymentRelevantParty.CLAIMANT.payment_relevant_party_id: PaymentTransactionType.STANDARD,
        }
        if (
            self.event_type == PAYMENT_OUT_TRANSACTION_TYPE
            and self.payment_amount
            and self.payment_amount > Decimal("0")
            and self.payment_relevant_party.payment_relevant_party_id in party_to_type
        ):
            return party_to_type[self.payment_relevant_party.payment_relevant_party_id]

        self.validation_container.add_validation_issue(
            payments_util.ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
            f"Unknown payment scenario encountered. Payment Amount: {self.payment_amount}, Event Type: {self.event_type}, Event Reason: {self.event_reason}",
        )
        return PaymentTransactionType.UNKNOWN

    def get_transaction_type_if_overpayment(self) -> Optional[LkPaymentTransactionType]:
        for overpayment_transaction_type in OVERPAYMENT_PAYMENT_TRANSACTION_TYPES:
            if self.event_type == overpayment_transaction_type.payment_transaction_type_description:
                return overpayment_transaction_type
        return None

    def get_payment_event_type(self) -> Optional[LkPaymentEventType]:
        for payment_event_type in PAYMENT_EVENT_TYPES:
            if self.event_type == payment_event_type.payment_event_type_description:
                return payment_event_type
        return None

    def get_relevant_party(self) -> LkPaymentRelevantParty:
        """
        Determine the relevant party for the payment. Payment transaction type
        on its own doesn't determine this; for example, a zero dollar payment
        might be issued to a claimant or as part of federal tax withholding.
        """

        if self.tin == STATE_TAX_WITHHOLDING_TIN:
            return PaymentRelevantParty.STATE_TAX

        if self.tin == FEDERAL_TAX_WITHHOLDING_TIN:
            return PaymentRelevantParty.FEDERAL_TAX

        if (
            self.event_reason == AUTO_ALT_EVENT_REASON
            and self.get_payment_event_type()
            and self.payee_identifier == TAX_IDENTIFICATION_NUMBER
        ):
            return PaymentRelevantParty.REIMBURSED_EMPLOYER

        # All other scenarios should be claimants
        return PaymentRelevantParty.CLAIMANT

    def process_claim_details(
        self,
        claim_details: FineosExtractVpeiClaimDetails,
        requested_absence: Optional[FineosExtractVbiRequestedAbsence],
        count_incrementer: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.absence_case_number = payments_util.validate_db_input(
            "ABSENCECASENU", claim_details, self.validation_container, self.is_standard_payment
        )

        self.leave_request_id = payments_util.validate_db_input(
            "LEAVEREQUESTI",
            claim_details,
            self.validation_container,
            self.is_payment_intended_for_pub,
            custom_validator_func=payments_util.leave_request_id_validator,
        )

        if requested_absence:

            def leave_request_decision_validator_closure(
                is_adhoc_payment: bool,
            ) -> Callable[[str], Optional[payments_util.ValidationReason]]:
                def leave_request_decision_validator(
                    leave_request_decision: str,
                ) -> Optional[payments_util.ValidationReason]:
                    if leave_request_decision == "In Review":
                        if is_adhoc_payment:
                            return None
                        if count_incrementer is not None:
                            count_incrementer(
                                PaymentExtractStep.Metrics.IN_REVIEW_LEAVE_REQUEST_COUNT
                            )
                        return payments_util.ValidationReason.LEAVE_REQUEST_IN_REVIEW
                    if leave_request_decision != "Approved":
                        if count_incrementer is not None:
                            count_incrementer(
                                PaymentExtractStep.Metrics.NOT_APPROVED_LEAVE_REQUEST_COUNT
                            )
                        return payments_util.ValidationReason.INVALID_VALUE
                    return None

                return leave_request_decision_validator

            self.leave_request_decision = payments_util.validate_db_input(
                "LEAVEREQUEST_DECISION",
                requested_absence,
                self.validation_container,
                self.is_payment_intended_for_pub,
                custom_validator_func=leave_request_decision_validator_closure(
                    self.is_adhoc_payment()
                ),
            )

            self.claim_type_raw = payments_util.validate_db_input(
                "ABSENCEREASON_COVERAGE", requested_absence, self.validation_container, True
            )

            self.absence_case_creation_date = payments_util.validate_db_input(
                "ABSENCE_CASECREATIONDATE",
                requested_absence,
                self.validation_container,
                True,
                custom_validator_func=self.payment_period_date_validator,
            )

        elif self.is_payment_intended_for_pub:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET,
                f"Payment leave request ID not found in requested absence file: {self.leave_request_id}",
            )

    def aggregate_payment_details(
        self, payment_details: List[FineosExtractVpeiPaymentDetails]
    ) -> None:
        """Aggregate payment period dates across all the payment details for this payment.

        Pseudocode:
           payment_start_period = min(payment_detail[1..N].PAYMENTSTARTP)
           payment_end_period = max(payment_detail[1..N].PAYMENTENDP)
        """
        start_periods = []
        end_periods = []
        for payment_detail_row in payment_details:
            payment_details_c_value = payments_util.validate_db_input(
                "C",
                payment_detail_row,
                self.validation_container,
                True,
            )

            payment_details_i_value = payments_util.validate_db_input(
                "I",
                payment_detail_row,
                self.validation_container,
                True,
            )

            row_start_period = payments_util.validate_db_input(
                "PAYMENTSTARTP",
                payment_detail_row,
                self.validation_container,
                True,
                custom_validator_func=self.payment_period_date_validator,
            )
            row_end_period = payments_util.validate_db_input(
                "PAYMENTENDPER",
                payment_detail_row,
                self.validation_container,
                True,
                custom_validator_func=self.payment_period_date_validator,
            )

            # This amount will sum to the amount we pay the claimant
            # across all of the payment periods of a payment
            row_amount_post_tax = payments_util.validate_db_input(
                "BALANCINGAMOU_MONAMT",
                payment_detail_row,
                self.validation_container,
                True,
                custom_validator_func=payments_util.amount_validator,
            )

            # This amount is prior to taxes being taken out and
            # also includes overpayments that have been paid back in some scenarios
            business_net_amount = payments_util.validate_db_input(
                "BUSINESSNETBE_MONAMT",
                payment_detail_row,
                self.validation_container,
                True,
                custom_validator_func=payments_util.amount_validator,
            )

            if row_start_period is not None:
                start_periods.append(row_start_period)
            if row_end_period is not None:
                end_periods.append(row_end_period)

            if all(
                field is not None
                for field in [
                    payment_details_c_value,
                    payment_details_i_value,
                    row_start_period,
                    row_end_period,
                    row_amount_post_tax,
                    business_net_amount,
                ]
            ):
                self.payment_detail_records.append(
                    PaymentDetails(
                        payment_details_id=uuid.uuid4(),
                        vpei_payment_details_id=payment_detail_row.vpei_payment_details_id,
                        payment_details_c_value=payment_details_c_value,
                        payment_details_i_value=payment_details_i_value,
                        period_start_date=datetime_str_to_date(row_start_period),
                        period_end_date=datetime_str_to_date(row_end_period),
                        amount=Decimal(cast(str, row_amount_post_tax)),
                        business_net_amount=Decimal(cast(str, business_net_amount)),
                    )
                )

        if start_periods:
            self.payment_start_period = min(start_periods)
        if end_periods:
            self.payment_end_period = max(end_periods)

    def aggregate_payment_lines(self, payment_lines: List[FineosExtractVpeiPaymentLine]) -> None:
        """
        Iterate over the list of payment lines and validate
        their values. If valid, create a payment line record
        in the DB.

        Also connects the payment line to the payment detail
        record that it is associated with at the same time.
        """
        # Create a mapping for payment detail C/I value
        # as we'll reference it below
        payment_detail_mapping = {}
        for payment_detail in self.payment_detail_records:
            key = (payment_detail.payment_details_c_value, payment_detail.payment_details_i_value)
            payment_detail_mapping[key] = payment_detail

        for payment_line in payment_lines:
            payment_line_c_value = payments_util.validate_db_input(
                "C",
                payment_line,
                self.validation_container,
                True,
            )

            payment_line_i_value = payments_util.validate_db_input(
                "I",
                payment_line,
                self.validation_container,
                True,
            )

            amount = payments_util.validate_db_input(
                "AMOUNT_MONAMT",
                payment_line,
                self.validation_container,
                True,
                custom_validator_func=payments_util.amount_validator,
            )

            line_type = payments_util.validate_db_input(
                "LINETYPE",
                payment_line,
                self.validation_container,
                True,
            )

            payment_detail_class_id = payments_util.validate_db_input(
                "PAYMENTDETAILCLASSID",
                payment_line,
                self.validation_container,
                self.is_payment_detail_expected,
            )
            payment_detail_index_id = payments_util.validate_db_input(
                "PAYMENTDETAILINDEXID",
                payment_line,
                self.validation_container,
                self.is_payment_detail_expected,
            )

            related_payment_detail: Optional[PaymentDetails] = payment_detail_mapping.get(
                (payment_detail_class_id, payment_detail_index_id), None
            )
            if not related_payment_detail and self.is_payment_detail_expected:
                self.validation_container.add_validation_issue(
                    payments_util.ValidationReason.MISSING_DATASET,
                    f"Payment detail with C={payment_detail_class_id},I={payment_detail_index_id} not found for payment line",
                    "payment_detail",
                )

            if all(
                field is not None
                for field in [
                    payment_line_c_value,
                    payment_line_i_value,
                    amount,
                    line_type,
                ]
            ):

                self.payment_line_records.append(
                    PaymentLine(
                        vpei_payment_line_id=payment_line.vpei_payment_line_id,
                        # Payment ID gets set after we create the payment
                        payment_details_id=related_payment_detail.payment_details_id
                        if related_payment_detail
                        else None,
                        payment_line_c_value=cast(str, payment_line_c_value),
                        payment_line_i_value=cast(str, payment_line_i_value),
                        amount=Decimal(cast(str, amount)),
                        line_type=cast(str, line_type),
                    )
                )

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
            "absence_case_id": self.absence_case_number,
            "period_start_date": self.payment_start_period,
            "period_end_date": self.payment_end_period,
            "payment_transaction_type": self.payment_transaction_type.payment_transaction_type_description,
            "payment_relevant_party": self.payment_relevant_party.payment_relevant_party_description,
            "is_for_standard_payment": self.is_employee_required,
        }

    def get_payment_message_str(self) -> str:
        return f"[C={self.c_value},I={self.i_value},absence_case_id={self.absence_case_number}]"

    def is_adhoc_payment(self) -> bool:
        # In past iteration self.amalgamation_c was used to determine this field,
        # but was switched to payment_type to future proof against fineos
        # changing amalgamation_c field again.
        # See: https://lwd.atlassian.net/browse/API-2235 for more details
        return self.payment_type == "Adhoc"


class PaymentExtractStep(Step):
    class Metrics(str, enum.Enum):
        EXTRACT_PATH = "extract_path"
        ACTIVE_PAYMENT_ERROR_COUNT = "active_payment_error_count"
        ALREADY_ACTIVE_PAYMENT_COUNT = "already_active_payment_count"
        APPROVED_PRENOTE_COUNT = "approved_prenote_count"
        CANCELLATION_COUNT = "cancellation_count"
        CLAIM_DETAILS_RECORD_COUNT = "claim_details_record_count"
        CLAIM_NOT_FOUND_COUNT = "claim_not_found_count"
        CLAIMANT_MISMATCH_COUNT = "claimant_mismatch_count"
        EFT_FOUND_COUNT = "eft_found_count"
        EMPLOYEE_MISSING_IN_DB_COUNT = "employee_in_payment_extract_missing_in_db_count"
        EMPLOYEE_FINEOS_NAME_MISSING = "employee_fineos_name_missing"
        EMPLOYER_REIMBURSEMENT_COUNT = "employer_reimbursement_count"
        ERRORED_PAYMENT_COUNT = "errored_payment_count"
        NEW_EFT_COUNT = "new_eft_count"
        NOT_APPROVED_PRENOTE_COUNT = "not_approved_prenote_count"
        NOT_APPROVED_LEAVE_REQUEST_COUNT = "not_approved_leave_request_count"
        IN_REVIEW_LEAVE_REQUEST_COUNT = "in_review_leave_request_count"
        OVERPAYMENT_COUNT = "overpayment_count"
        PAYMENT_DETAILS_RECORD_COUNT = "payment_details_record_count"
        PAYMENT_LINE_RECORD_COUNT = "payment_line_record_count"
        PEI_RECORD_COUNT = "pei_record_count"
        PRENOTE_PAST_WAITING_PERIOD_APPROVED_COUNT = "prenote_past_waiting_period_approved_count"
        PROCESSED_PAYMENT_COUNT = "processed_payment_count"
        REQUESTED_ABSENCE_RECORD_COUNT = "requested_absence_record_count"
        STANDARD_VALID_PAYMENT_COUNT = "standard_valid_payment_count"
        TAX_IDENTIFIER_MISSING_IN_DB_COUNT = "tax_identifier_missing_in_db_count"
        ZERO_DOLLAR_PAYMENT_COUNT = "zero_dollar_payment_count"
        ADHOC_PAYMENT_COUNT = "adhoc_payment_count"
        MULTIPLE_CLAIM_DETAILS_ERROR_COUNT = "multiple_claim_details_error_count"
        FEDERAL_WITHHOLDING_PAYMENT_COUNT = "federal_withholding_payment_count"
        STATE_WITHHOLDING_PAYMENT_COUNT = "state_withholding_payment_count"
        EXEMPT_EMPLOYER_COUNT = "exempt_employer_count"

    def run_step(self):
        logger.info("Processing payment extract data")
        self.process_records()
        logger.info("Successfully processed payment extract data")

    def get_active_payment_state(self, payment: Payment) -> Optional[LkState]:
        """For the given payment, determine if the payment is being processed or complete
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
                Payment.exclude_from_payment_status != True,  # noqa: E712
                StateLog.end_state_id.notin_(payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS),
                LkState.flow_id == Flow.DELEGATED_PAYMENT.flow_id,
            )
            .first()
        )

        if active_state:
            # If you are seeing this error, the writebacks are not working
            # properly. We need to verify that we have been correctly sending
            # the writebacks, and that FINEOS has been properly consuming them.
            logger.error(
                "Payment received from FINEOS is already in active state: [%s] - active payment ID: %s",
                active_state.end_state.state_description,
                active_state.payment.payment_id,
                extra=payments_util.get_traceable_payment_details(payment),
            )
            self.increment(self.Metrics.ALREADY_ACTIVE_PAYMENT_COUNT)
            return active_state.end_state

        return None

    def get_employee_and_claim(
        self, payment_data: PaymentData
    ) -> Tuple[Optional[Employee], Optional[Claim]]:

        # Get the TIN, employee and claim associated with the payment to be made
        employee, claim = None, None
        try:
            claim = (
                self.db_session.query(Claim)
                .filter_by(fineos_absence_id=payment_data.absence_case_number)
                .one_or_none()
            )
            # If the employee is required and should be validated, do so
            # Otherwise, we know we aren't going to find an employee, so don't look
            if payment_data.is_employee_required:
                if (
                    payment_data.payment_relevant_party.payment_relevant_party_id
                    == PaymentRelevantParty.REIMBURSED_EMPLOYER.payment_relevant_party_id
                    and payment_data.is_employer_reimbursement_enabled
                ):
                    employee = claim.employee if claim is not None else None
                    if not employee:
                        self.increment(self.Metrics.EMPLOYEE_MISSING_IN_DB_COUNT)
                        payment_data.validation_container.add_validation_issue(
                            payments_util.ValidationReason.MISSING_IN_DB,
                            payment_data.tin,
                            "employee",
                        )
                else:
                    tax_identifier = (
                        self.db_session.query(TaxIdentifier)
                        .filter_by(tax_identifier=payment_data.tin)
                        .one_or_none()
                    )
                    if not tax_identifier:
                        self.increment(self.Metrics.TAX_IDENTIFIER_MISSING_IN_DB_COUNT)
                        payment_data.validation_container.add_validation_issue(
                            payments_util.ValidationReason.MISSING_IN_DB,
                            payment_data.tin,
                            "tax_identifier",
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
                                payment_data.tin,
                                "employee",
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
        if not claim and payment_data.is_payment_intended_for_pub:
            payment_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB,
                payment_data.absence_case_number,
                "claim",
            )
            self.increment(self.Metrics.CLAIM_NOT_FOUND_COUNT)
            return None, None

        # Perform various validations on the claim. We require
        # A claim to be ID Proofed
        # A claim to have an attached employer
        # A claim to have a claim type
        # The employee we fetched above to already be connected to the claim
        if claim:
            if not claim.is_id_proofed:
                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.CLAIM_NOT_ID_PROOFED,
                    f"Claim {payment_data.absence_case_number} has not been ID proofed",
                )

            if payment_data.is_payment_intended_for_pub and not claim.employer_id:
                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.MISSING_IN_DB,
                    f"Claim {payment_data.absence_case_number} does not have an employer associated with it",
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
        if payment_data.is_standard_payment:
            employee_address = EmployeeAddress(employee=employee, address=payment_data_address)
            self.db_session.add(employee_address)

        return new_experian_address_pair, True

    def create_payment(
        self,
        payment_data: PaymentData,
        claim: Optional[Claim],
        employee: Optional[Employee],
        validation_container: payments_util.ValidationContainer,
    ) -> Payment:
        # We always create a new payment record. This may be completely new
        # or a payment might have been created before. We'll check that later.

        logger.info("Creating payment record in DB", extra=payment_data.get_traceable_details())
        payment = Payment(payment_id=uuid.uuid4(), vpei_id=payment_data.pei_record.vpei_id)

        # set the payment method
        if payment_data.raw_payment_method:
            payment.disb_method_id = PaymentMethod.get_id(payment_data.raw_payment_method)

        # Note that these values may have validation issues and not be set
        # that is fine as it will get moved to an error state
        if payment_data.leave_request_id:
            payment.fineos_leave_request_id = str_to_int(payment_data.leave_request_id)
        if claim:
            payment.claim = claim
        if employee:
            payment.employee = employee
        payment.period_start_date = datetime_str_to_date(payment_data.payment_start_period)
        payment.period_end_date = datetime_str_to_date(payment_data.payment_end_period)
        payment.payment_date = datetime_str_to_date(payment_data.payment_date)
        payment.absence_case_creation_date = datetime_str_to_date(
            payment_data.absence_case_creation_date
        )

        payment.payment_relevant_party_id = (
            payment_data.payment_relevant_party.payment_relevant_party_id
        )

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
        payment.fineos_extraction_date = get_now_us_eastern().date()
        payment.fineos_extract_import_log_id = self.get_import_log_id()
        payment.leave_request_decision = payment_data.leave_request_decision

        # Set the payee name.
        # For payments that are not paid to the claimant (e.g. - employer reimbursements), we use this name.
        # For claimant payments will use other fields for the claimant name.
        payment.payee_name = payment_data.full_name

        # This is used later in the post-processing step to filter out
        # adhoc payments from the weekly maximum check.
        payment.is_adhoc_payment = payment_data.is_adhoc_payment()

        if payment.is_adhoc_payment:
            self.increment(self.Metrics.ADHOC_PAYMENT_COUNT)

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
            payment.exclude_from_payment_status = True

        self.db_session.add(payment)

        for payment_detail in payment_data.payment_detail_records:
            payment_detail.payment = payment
            self.db_session.add(payment_detail)

        for payment_line in payment_data.payment_line_records:
            payment_line.payment = payment
            self.db_session.add(payment_line)

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
        if existing_eft:
            extra |= payments_util.get_traceable_pub_eft_details(existing_eft, employee)
            self.increment(self.Metrics.EFT_FOUND_COUNT)
            logger.info("Found existing EFT info for claimant associated with payment", extra=extra)

            if PrenoteState.APPROVED.prenote_state_id == existing_eft.prenote_state_id:
                self.increment(self.Metrics.APPROVED_PRENOTE_COUNT)
            elif (
                (PrenoteState.PENDING_WITH_PUB.prenote_state_id == existing_eft.prenote_state_id)
                and existing_eft.prenote_sent_at
                and (get_now_us_eastern() - existing_eft.prenote_sent_at).days
                >= PRENOTE_PRENDING_WAITING_PERIOD
            ):
                # Set prenote to approved
                existing_eft.prenote_state_id = PrenoteState.APPROVED.prenote_state_id
                existing_eft.prenote_approved_at = get_now_us_eastern()

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

            extra |= payments_util.get_traceable_pub_eft_details(
                new_eft, employee, state=State.DELEGATED_EFT_SEND_PRENOTE
            )
            logger.info(
                "Starting DELEGATED_EFT prenote flow for employee associated with payment",
                extra=extra,
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
            if payment_data.is_payment_intended_for_pub:
                address_pair, has_address_update = self.update_experian_address_pair_fineos_address(
                    payment_data, employee
                )

            # Update the EFT info with values from FINEOS
            payment_eft, has_eft_update = self.update_eft(payment_data, employee)

        # Create the payment record
        payment = self.create_payment(
            payment_data, claim, employee, payment_data.validation_container
        )

        # Capture the fineos provided employee name for the payment
        if employee:
            if (
                employee.fineos_employee_first_name is None
                or employee.fineos_employee_last_name is None
            ):
                self.increment(self.Metrics.EMPLOYEE_FINEOS_NAME_MISSING)
                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.MISSING_FINEOS_NAME,
                    f"Missing name from FINEOS on employee {employee.employee_id}",
                )
            else:
                payment.fineos_employee_first_name = employee.fineos_employee_first_name
                payment.fineos_employee_middle_name = employee.fineos_employee_middle_name
                payment.fineos_employee_last_name = employee.fineos_employee_last_name

        # Check whether the employer is exempt from payments
        # Only for standard payments
        if payment_data.is_standard_payment and payment and claim and claim.employer:
            is_employer_exempt_for_payment = payments_util.is_employer_exempt_for_payment(
                payment, claim, claim.employer
            )
            if is_employer_exempt_for_payment:
                self.increment(self.Metrics.EXEMPT_EMPLOYER_COUNT)
                employer = claim.employer
                message = f"Employer {employer.fineos_employer_id} is exempt for dates {employer.exemption_commence_date} - {employer.exemption_cease_date}"
                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.EMPLOYER_EXEMPT, message
                )

        # If it is not an adhoc payment and it has certain kinds of open
        # tasks, we reject it and add it to the error report
        if (
            not payment.is_adhoc_payment
            and payment_data.is_payment_intended_for_pub
            and payment_data.absence_case_number is not None
        ):
            open_other_income_tasks = payments_util.get_open_tasks(
                self.db_session, payment_data.absence_case_number, OTHER_INCOME_TASKTYPENAMES
            )
            if len(open_other_income_tasks) > 0:
                payment_data.validation_container.add_validation_issue(
                    payments_util.ValidationReason.OPEN_OTHER_INCOME_TASKS,
                    f"TASKTYPENAMES: {[task.tasktypename for task in open_other_income_tasks]}",
                )

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
            payment=payment, reference_file=reference_file
        )
        self.db_session.add(payment_reference_file)

        return payment

    def process_payment_data_record(
        self, payment_data: PaymentData, reference_file: ReferenceFile
    ) -> Payment:
        employee, claim = self.get_employee_and_claim(payment_data)
        payment = self.add_records_to_db(payment_data, employee, claim, reference_file)

        return payment

    def _setup_state_log(self, payment: Payment, payment_data: PaymentData) -> None:
        transaction_status = None

        # If it has an active payment issue, we do not want
        # to update the transaction status, the writebacks
        # are probably not working, and we'd prefer the payment
        # keep whatever its original status was.
        if payment.exclude_from_payment_status:
            message = "Active Payment Error - Contact FINEOS"
            end_state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
            self.increment(self.Metrics.ERRORED_PAYMENT_COUNT)

        # https://lwd.atlassian.net/wiki/spaces/API/pages/1336901700/Types+of+Payments
        # Does the payment have validation issues
        # If so, add to that error state
        elif payment_data.validation_container.has_validation_issues():
            message = "Error processing payment record"

            # https://lwd.atlassian.net/wiki/spaces/API/pages/1319272855/Payment+Transaction+Scenarios
            # We want to determine what kind of PEI writeback we'd do if it has errors
            transaction_status = self._determine_pei_transaction_status(payment_data)
            self._manage_pei_writeback_state(payment, transaction_status, payment_data)

            # Payments in an active state go to the general error report state
            if transaction_status.writeback_record_status == ACTIVE_WRITEBACK_RECORD_STATUS:
                end_state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
            else:  # Otherwise they go to the restartable error report state
                end_state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE

            self.increment(self.Metrics.ERRORED_PAYMENT_COUNT)

        # Employer reimbursements are added to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        ):
            if payments_util.is_employer_reimbursement_payments_enabled():
                end_state = State.PAYMENT_READY_FOR_ADDRESS_VALIDATION
                message = "Success"
            else:
                end_state = State.DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_RESTARTABLE
                message = "Employer reimbursement payment processed"
            self.increment(self.Metrics.EMPLOYER_REIMBURSEMENT_COUNT)

        # Zero dollar payments are added to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
        ):
            end_state = State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
            message = "Zero dollar payment processed"
            self._manage_pei_writeback_state(
                payment, FineosWritebackTransactionStatus.PROCESSED, payment_data
            )
            self.increment(self.Metrics.ZERO_DOLLAR_PAYMENT_COUNT)

        # Overpayments are added to to the FINEOS writeback + a report
        elif payment.payment_transaction_type_id in OVERPAYMENT_PAYMENT_TRANSACTION_TYPE_IDS:
            end_state = State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
            message = "Overpayment payment processed"
            self._manage_pei_writeback_state(
                payment, FineosWritebackTransactionStatus.PROCESSED, payment_data
            )
            self.increment(self.Metrics.OVERPAYMENT_COUNT)

        # Cancellations are added to the FINEOS writeback + a report
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
        ):
            end_state = State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION
            message = "Cancellation payment processed"
            self._manage_pei_writeback_state(
                payment, FineosWritebackTransactionStatus.PROCESSED, payment_data
            )
            self.increment(self.Metrics.CANCELLATION_COUNT)

        # set status FEDERAL_WITHHOLDING_READY_FOR_PROCESSING
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id
        ):
            end_state = State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING
            message = "Federal Withholding payment processed"
            self.increment(self.Metrics.FEDERAL_WITHHOLDING_PAYMENT_COUNT)

        # set status  STATE_WITHHOLDING_READY_FOR_PROCESSING
        elif (
            payment.payment_transaction_type_id
            == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
        ):
            end_state = State.STATE_WITHHOLDING_READY_FOR_PROCESSING
            message = "State Withholding payment processed"
            self.increment(self.Metrics.STATE_WITHHOLDING_PAYMENT_COUNT)

        else:
            end_state = State.PAYMENT_READY_FOR_ADDRESS_VALIDATION
            message = "Success"
            self.increment(self.Metrics.STANDARD_VALID_PAYMENT_COUNT)

        # TODO Move call to _manage_pei_writeback_state here

        state_log_util.create_finished_state_log(
            end_state=end_state,
            outcome=state_log_util.build_outcome(message, payment_data.validation_container),
            associated_model=payment,
            db_session=self.db_session,
        )
        extra = payments_util.get_traceable_payment_details(payment, end_state)
        extra["is_for_standard_payment"] = payment_data.is_employee_required

        # Keep track of stale payments
        earliest_matching_payment = payments_util.get_earliest_matching_payment(
            self.db_session, payment_data.c_value, payment_data.i_value
        )
        if earliest_matching_payment:
            extra["days_since_payment_first_seen"] = (
                datetime.utcnow().date() - earliest_matching_payment.created_at.date()
            ).days + 1
            extra["day_payment_first_seen"] = str(earliest_matching_payment.created_at.date())

        logger.info(
            "After consuming extracts and performing initial validation, payment added to state",
            extra=extra,
        )
        # For the payments that failed validation, log their reason codes
        # and field names so that we can collect metrics on the most common error types
        for reason, field_name in payment_data.validation_container.get_reasons_with_field_names():
            # Replaced each iteration
            extra["validation_reason"] = str(reason)
            extra["field_name"] = field_name
            logger.info("Payment failed validation", extra=extra)

    def _manage_pei_writeback_state(
        self,
        payment: Payment,
        transaction_status: LkFineosWritebackTransactionStatus,
        payment_data: PaymentData,
    ) -> None:
        """If the payment had any validation issues, we want to writeback to FINEOS
        so that the particular error can be shown in the UI.

        Note that some of these states also mark the payment as
        Active (they only end up in extracts when PendingActive)
        This is deliberate as some payments need to be marked as Active
        so they can be fixed and reissued (an extracted payment can't be modified)
        """

        message = f"Payment added to DELEGATED_PEI_WRITEBACK flow with transaction status {transaction_status.transaction_status_description}"

        stage_payment_fineos_writeback(
            payment=payment,
            writeback_transaction_status=transaction_status,
            outcome=state_log_util.build_outcome(message, payment_data.validation_container),
            db_session=self.db_session,
            import_log_id=self.get_import_log_id(),
        )
        logger.info(message, extra=payment_data.get_traceable_details())

    def _determine_pei_transaction_status(
        self, payment_data: PaymentData
    ) -> LkFineosWritebackTransactionStatus:
        # https://lwd.atlassian.net/wiki/spaces/API/pages/1319272855/Payment+Transaction+Scenarios
        validation_reasons = payment_data.validation_container.get_reasons()
        has_other_issues = False
        has_system_issue = False
        has_exempt_employer = False
        has_leave_request_in_review = False
        has_pending_prenote = False
        has_rejected_prenote = False
        has_open_other_income_tasks = False

        for reason in validation_reasons:
            # Some issues are either due to the data setup in our system
            # or issues with the extracts themselves (records entirely missing)
            # If that's the case, we don't want to block the payment from being
            # processed again, we want to keep receiving it until we/FINEOS fix the issue
            # ID Proofing is included in this list, as we shouldn't receive non-ID proofed
            # records in the extract
            if reason in [
                payments_util.ValidationReason.MISSING_IN_DB,
                payments_util.ValidationReason.MISSING_FINEOS_NAME,
                payments_util.ValidationReason.CLAIM_NOT_ID_PROOFED,
                payments_util.ValidationReason.MISSING_DATASET,
                payments_util.ValidationReason.CLAIMANT_MISMATCH,
                payments_util.ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
            ]:
                has_system_issue = True

            # Employers exempt from leave entirely block the payment, will
            # write back as Active
            elif reason == payments_util.ValidationReason.EMPLOYER_EXEMPT:
                has_exempt_employer = True

            # Reject any payments with leave request ???In Review???, allowing for
            # retries each day in case the status changes to ???Approved??? or ???Completed???
            elif reason == payments_util.ValidationReason.LEAVE_REQUEST_IN_REVIEW:
                has_leave_request_in_review = True

            # Pending prenotes will also be put in PendingActive as we are just
            # waiting to get the payment
            elif reason == payments_util.ValidationReason.EFT_PRENOTE_PENDING:
                has_pending_prenote = True

            # Rejected prenotes will get set to Active as the payment information
            # needs to be fixed as we can't even attempt to pay them
            elif reason == payments_util.ValidationReason.EFT_PRENOTE_REJECTED:
                has_rejected_prenote = True

            elif reason == payments_util.ValidationReason.OPEN_OTHER_INCOME_TASKS:
                has_open_other_income_tasks = True

            # Otherwise the issue is any of the other validation reasons
            # which all will set the payment to Active so the payment can
            # be fixed and reissued.
            else:
                has_other_issues = True

        # This always takes precendence as there is something
        # that requires a correction
        if has_other_issues:
            return FineosWritebackTransactionStatus.FAILED_AUTOMATED_VALIDATION

        # Issues in our system take next precendence as a payment
        # would be blocked due to this until manual engineering effort
        # investigates and fixes the issue
        if has_system_issue:
            return FineosWritebackTransactionStatus.DATA_ISSUE_IN_SYSTEM

        # Exempt employer would block payment, so later scenarios irrelevant
        if has_exempt_employer:
            return FineosWritebackTransactionStatus.EXEMPT_EMPLOYER

        if has_open_other_income_tasks:
            return FineosWritebackTransactionStatus.SELF_REPORTED_ADDITIONAL_INCOME

        # Leave requests in review take next precendence
        if has_leave_request_in_review:
            return FineosWritebackTransactionStatus.LEAVE_IN_REVIEW

        # Pending and rejected can't happen at the same time, so ordering
        # won't matter
        if has_pending_prenote:
            return FineosWritebackTransactionStatus.PENDING_PRENOTE

        if has_rejected_prenote:
            return FineosWritebackTransactionStatus.PRENOTE_ERROR

        # This should be impossible
        raise Exception(
            "Unknown scenario encountered when attempting to figure out the transaction status for payment. Got reasons %s"
            % validation_reasons
        )

    def process_payment_record(
        self,
        raw_payment_record: FineosExtractVpei,
        reference_file: ReferenceFile,
        latest_claimant_extract_reference_file: ReferenceFile,
    ) -> None:
        self.increment(self.Metrics.PROCESSED_PAYMENT_COUNT)

        try:
            c_value, i_value = cast(str, raw_payment_record.c), cast(str, raw_payment_record.i)

            # Fetch the records associated with the payment from other tables
            # We fetch all records even when we expect only one. The PaymentData
            # validation will handle cases where that's unexpected

            # We expect multiple payment detail records
            # joined on the C/I value. Each of these represents
            # a pay period within a payment (although most payments will have exactly 1)
            payment_details_records = (
                self.db_session.query(FineosExtractVpeiPaymentDetails)
                .filter(
                    FineosExtractVpeiPaymentDetails.peclassid == c_value,
                    FineosExtractVpeiPaymentDetails.peindexid == i_value,
                    FineosExtractVpeiPaymentDetails.reference_file_id
                    == reference_file.reference_file_id,
                )
                .all()
            )
            self.increment(self.Metrics.PAYMENT_DETAILS_RECORD_COUNT, len(payment_details_records))

            # We expect multiple payment line records for each payment
            # joined on the C/I value. Each of these represents
            # a specific amount+type that makes up the payment
            # eg. $500 for base benefit, or -$50 removed for tax
            payment_line_records = (
                self.db_session.query(FineosExtractVpeiPaymentLine)
                .filter(
                    FineosExtractVpeiPaymentLine.c_pymnteif_paymentlines == c_value,
                    FineosExtractVpeiPaymentLine.i_pymnteif_paymentlines == i_value,
                    FineosExtractVpeiPaymentLine.reference_file_id
                    == reference_file.reference_file_id,
                )
                .all()
            )
            self.increment(self.Metrics.PAYMENT_LINE_RECORD_COUNT, len(payment_line_records))

            # We expect only one claim details record
            # joined on the C/I value
            claim_details_records = (
                self.db_session.query(FineosExtractVpeiClaimDetails)
                .filter(
                    FineosExtractVpeiClaimDetails.peclassid == c_value,
                    FineosExtractVpeiClaimDetails.peindexid == i_value,
                    FineosExtractVpeiClaimDetails.reference_file_id
                    == reference_file.reference_file_id,
                )
                .all()
            )
            self.increment(self.Metrics.CLAIM_DETAILS_RECORD_COUNT, len(claim_details_records))

            claim_details_record = None
            if len(claim_details_records) > 0:
                claim_details_record = claim_details_records[0]
                # From testing and validation, we shouldn't ever get more than
                # a single claim details record. If we do, log an error, but continue
                if len(claim_details_records) > 1:
                    # If you are seeing this error, please investigate and check with FINEOS
                    # We should also verify that there is nothing different between the claim details records
                    logger.error(
                        "Payment with C/I value %s/%s has multiple claim details records present.",
                        c_value,
                        i_value,
                    )
                    self.increment(self.Metrics.MULTIPLE_CLAIM_DETAILS_ERROR_COUNT)

            # To get the requested absence record, we need
            # to use a claim detail record to know the leave request ID.
            requested_absence_record = None
            if claim_details_record:
                leave_request_id = claim_details_record.leaverequesti

                # Realistically, we can get more than one of these
                # as multiple absence periods within a claim can cause
                # multiple records. However, the only fields that differ
                # are the absence period start/end dates (which we do not use)
                # Fetch all of them, we'll filter it to one and log a message
                # just in case it ever matters.
                requested_absence_records = (
                    self.db_session.query(FineosExtractVbiRequestedAbsence)
                    .filter(
                        FineosExtractVbiRequestedAbsence.leaverequest_id == leave_request_id,
                        FineosExtractVbiRequestedAbsence.reference_file_id
                        == latest_claimant_extract_reference_file.reference_file_id,
                    )
                    .all()
                )
                self.increment(
                    self.Metrics.REQUESTED_ABSENCE_RECORD_COUNT, len(requested_absence_records)
                )
                if len(requested_absence_records) > 0:
                    if len(requested_absence_records) > 1:
                        logger.warning(
                            "Found more than one requested absence record for payment with C/I %s/%s and leave request ID %s",
                            c_value,
                            i_value,
                            leave_request_id,
                        )
                    requested_absence_record = requested_absence_records[0]

            # Construct a payment data object for easier organization of the many params
            payment_data = PaymentData(
                c_value,
                i_value,
                raw_payment_record,
                payment_details_records,
                payment_line_records,
                claim_details_record,
                requested_absence_record,
                count_incrementer=self.increment,
            )

            logger.info(
                "Processing extract data for payment record",
                extra=payment_data.get_traceable_details(),
            )

            payment = self.process_payment_data_record(payment_data, reference_file)

            # Create and finish the state log. If there were any issues, this'll set the
            # record to an error state which'll send out a report to address it, otherwise
            # it will move onto the next step in processing
            self._setup_state_log(payment, payment_data)

        except Exception:
            # An exception during processing would indicate
            # either a bug or a scenario that we believe invalidates
            # an entire file and warrants investigating
            logger.exception(
                "An error occurred while processing payment for CI: %s, %s", c_value, i_value
            )
            raise

        return None

    def process_records(self) -> None:
        # Grab the latest payment extract reference file
        reference_file = (
            self.db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
            )
            .order_by(ReferenceFile.created_at.desc())
            .first()
        )
        if not reference_file:
            raise Exception(
                "No payment extracts consumed. This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
            )
        if reference_file.processed_import_log_id:
            logger.warning(
                "Already processed the most recent extracts for %s in import run %s",
                reference_file.file_location,
                reference_file.processed_import_log_id,
            )
            return

        # We also want the latest claimant extract reference
        # file as we'll need it for the requested absence file
        # that we are going to lookup. Don't care if it's processed
        # already as it's just a lookup file
        latest_claimant_extract_reference_file = (
            self.db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
            )
            .order_by(ReferenceFile.created_at.desc())
            .first()
        )
        if not latest_claimant_extract_reference_file:
            raise Exception(
                "No claimant extracts consumed. This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
            )

        raw_payment_records = (
            self.db_session.query(FineosExtractVpei)
            .filter(FineosExtractVpei.reference_file_id == reference_file.reference_file_id)
            .all()
        )
        for raw_payment_record in raw_payment_records:
            self.increment(self.Metrics.PEI_RECORD_COUNT)
            self.process_payment_record(
                raw_payment_record,
                reference_file,
                latest_claimant_extract_reference_file,
            )

        reference_file.processed_import_log_id = self.get_import_log_id()
