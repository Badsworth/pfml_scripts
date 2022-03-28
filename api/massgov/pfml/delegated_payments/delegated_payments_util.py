import os
import re
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import ColumnProperty, class_mapper

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.lookup import LookupTable
from massgov.pfml.db.models import base
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    Address,
    Claim,
    ClaimType,
    Employee,
    Employer,
    ExperianAddressPair,
    LkClaimType,
    LkReferenceFileType,
    Payment,
    PaymentDetails,
    PaymentTransactionType,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.payments import (
    FineosExtractCancelledPayments,
    FineosExtractEmployeeFeed,
    FineosExtractPaymentFullSnapshot,
    FineosExtractReplacedPayments,
    FineosExtractVbi1099DataSom,
    FineosExtractVbiLeavePlanRequestedAbsence,
    FineosExtractVbiRequestedAbsence,
    FineosExtractVbiRequestedAbsenceSom,
    FineosExtractVbiTaskReportSom,
    FineosExtractVPaidLeaveInstruction,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
    FineosExtractVpeiPaymentLine,
    PaymentLine,
    PaymentLog,
)
from massgov.pfml.db.models.state import LkState, State
from massgov.pfml.util.collections.dict import filter_dict, make_keys_lowercase
from massgov.pfml.util.compare import compare_attributes
from massgov.pfml.util.converters.str_to_numeric import str_to_int
from massgov.pfml.util.datetime import date_to_isoformat, get_now_us_eastern
from massgov.pfml.util.routing_number_validation import validate_routing_number

logger = logging.get_logger(__package__)

ExtractTable = Union[
    Type[FineosExtractVpei],
    Type[FineosExtractVpeiClaimDetails],
    Type[FineosExtractVpeiPaymentDetails],
    Type[FineosExtractVpeiPaymentLine],
    Type[FineosExtractVbiRequestedAbsenceSom],
    Type[FineosExtractEmployeeFeed],
    Type[FineosExtractVbiRequestedAbsence],
    Type[FineosExtractCancelledPayments],
    Type[FineosExtractPaymentFullSnapshot],
    Type[FineosExtractReplacedPayments],
    Type[FineosExtractVbiLeavePlanRequestedAbsence],
    Type[FineosExtractVPaidLeaveInstruction],
    Type[FineosExtractVbi1099DataSom],
    Type[FineosExtractVbiTaskReportSom],
]


@dataclass(frozen=True, eq=True)
class FineosExtract:
    file_name: str

    table: ExtractTable = field(compare=False, repr=False)

    # Note field names is simply a list of fields we care about. Extracts will
    # contain many additional fields that we do not use. This is the list of
    # fields that is required to be present, otherwise we throw an exception
    # (see validate_columns_present())
    field_names: List[str] = field(compare=False, repr=False)

    # This allows us to optionally specify filters on fields, in which case we
    # will only process rows that match *all* of these filters.
    # usage is field_filters = {"field_name1": re.compile(r"expression1""), ...}
    field_filters: Dict[str, List[str]] = field(
        default_factory=lambda: {}, compare=False, repr=False
    )


class Constants:
    S3_OUTBOUND_READY_DIR = "ready"
    S3_OUTBOUND_SENT_DIR = "sent"
    S3_OUTBOUND_ERROR_DIR = "error"
    S3_INBOUND_RECEIVED_DIR = "received"
    S3_INBOUND_PROCESSED_DIR = "processed"
    S3_INBOUND_SKIPPED_DIR = "skipped"
    S3_INBOUND_ERROR_DIR = "error"

    FILE_NAME_PUB_NACHA = "EOLWD-DFML-NACHA"
    FILE_NAME_PUB_EZ_CHECK = "EOLWD-DFML-EZ-CHECK"
    FILE_NAME_PUB_POSITIVE_PAY = "EOLWD-DFML-POSITIVE-PAY"
    FILE_NAME_PAYMENT_AUDIT_REPORT = "Payment-Audit-Report"
    FILE_NAME_RAW_PUB_ACH_FILE = "ACD9T136-DFML"
    FILE_NAME_MANUAL_PUB_REJECT = "manual-pub-reject"

    REQUESTED_ABSENCE_SOM_FILE_NAME = "VBI_REQUESTEDABSENCE_SOM.csv"
    EMPLOYEE_FEED_FILE_NAME = "Employee_feed.csv"
    VBI_1099DATA_SOM_FILE_NAME = "VBI_1099DATA_SOM.csv"

    PEI_EXPECTED_FILE_NAME = "vpei.csv"
    PAYMENT_DETAILS_EXPECTED_FILE_NAME = "vpeipaymentdetails.csv"
    PAYMENT_LINE_EXPECTED_FILE_NAME = "vpeipaymentline.csv"
    CLAIM_DETAILS_EXPECTED_FILE_NAME = "vpeiclaimdetails.csv"
    REQUESTED_ABSENCE_FILE_NAME = "VBI_REQUESTEDABSENCE.csv"

    NACHA_FILE_FORMAT = f"%Y-%m-%d-%H-%M-%S-{FILE_NAME_PUB_NACHA}"

    VBI_TASK_REPORT_STATUS_OPEN = "928000"

    # When processing payments, certain states
    # are allowed to be restarted (mainly error states)
    # If we receive a payment record from FINEOS while
    # a payment is in ANY other states, the new payment record should
    # immediately go into the payment error report
    #
    # How do you know if something should go in this list?
    #   1. The payment associated with the state has reached an end state and will never change again
    #   2. The state is an error state and someone will be notified (eg. Program Integrity) via a report
    #   3. The state has a scenario where we want to receive the same payment again unmodified (eg. the issue is
    #      we're missing the employee record)
    #   4. The payment has not already been sent to PUB - even if it's an error state
    #   5. The state is in the DELEGATED_PAYMENT flow
    RESTARTABLE_PAYMENT_STATES = frozenset(
        [
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            State.STATE_WITHHOLDING_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            State.FEDERAL_WITHHOLDING_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            State.STATE_WITHHOLDING_ERROR_RESTARTABLE,
            State.FEDERAL_WITHHOLDING_ERROR_RESTARTABLE,
            State.DELEGATED_PAYMENT_CASCADED_ERROR_RESTARTABLE,
        ]
    )
    RESTARTABLE_PAYMENT_STATE_IDS = frozenset(
        [state.state_id for state in RESTARTABLE_PAYMENT_STATES]
    )

    # States that we wait in while waiting for the reject file
    # If any payments are still in this state when the extract
    # task runs, we'll move them to an error state.
    REJECT_FILE_PENDING_STATES = [
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        State.FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT,
        State.STATE_WITHHOLDING_RELATED_PENDING_AUDIT,
        State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT,
        State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT,
    ]

    # These overpayment transaction types don't have payment details
    # which means in a few places we want to explicitly not expect to see payment details.
    OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS = frozenset(
        [
            PaymentTransactionType.OVERPAYMENT_ACTUAL_RECOVERY,
            PaymentTransactionType.OVERPAYMENT_RECOVERY,
            PaymentTransactionType.OVERPAYMENT_RECOVERY_CANCELLATION,
            PaymentTransactionType.OVERPAYMENT_RECOVERY_REVERSE,
            PaymentTransactionType.OVERPAYMENT_ADJUSTMENT,
            PaymentTransactionType.OVERPAYMENT_ACTUAL_RECOVERY_CANCELLATION,
            PaymentTransactionType.OVERPAYMENT_ADJUSTMENT_CANCELLATION,
        ]
    )
    OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS_IDS = frozenset(
        [
            overpayment_type.payment_transaction_type_id
            for overpayment_type in OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS
        ]
    )

    PAYMENT_SENT_STATES = frozenset(
        [
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
        ]
    )
    PAYMENT_SENT_STATE_IDS = frozenset([state.state_id for state in PAYMENT_SENT_STATES])


CANCELLED_OR_REPLACED_EXTRACT_FIELD_NAMES = [
    "C",
    "I",
    "STATUSREASON",
    "GROSSAMOUNT",
    "ADDEDBY",
    "ISSUEDATE",
    "CANCELLATIONDATE",
    "TRANSACTIONSTATUSDATE",
    "TRANSACTIONSTATUS",
    "EXTRACTIONDATE",
    "STOCKNUMBER",
    "CLAIMNUMBER",
    "BENEFITCASENUMBER",
]


@dataclass
class FineosExtractConstants:
    # FINEOS Claimant Extract Files
    VBI_REQUESTED_ABSENCE_SOM = FineosExtract(
        file_name="VBI_REQUESTEDABSENCE_SOM.csv",
        table=FineosExtractVbiRequestedAbsenceSom,
        field_names=[
            "ABSENCEPERIOD_CLASSID",
            "ABSENCEPERIOD_INDEXID",
            "ABSENCEREASON_COVERAGE",
            "ABSENCE_CASENUMBER",
            "NOTIFICATION_CASENUMBER",
            "ABSENCE_CASESTATUS",
            "ABSENCEPERIOD_START",
            "ABSENCEPERIOD_END",
            "LEAVEREQUEST_EVIDENCERESULTTYPE",
            "EMPLOYEE_CUSTOMERNO",
            "EMPLOYER_CUSTOMERNO",
            "LEAVEREQUEST_ID",
            "ORGUNIT_NAME",
        ],
    )

    EMPLOYEE_FEED = FineosExtract(
        file_name="Employee_feed.csv",
        table=FineosExtractEmployeeFeed,
        field_names=[
            "C",
            "I",
            "DEFPAYMENTPREF",
            "CUSTOMERNO",
            "NATINSNO",
            "DATEOFBIRTH",
            "PAYMENTMETHOD",
            "ADDRESS1",
            "ADDRESS2",
            "ADDRESS4",
            "ADDRESS6",
            "POSTCODE",
            "SORTCODE",
            "ACCOUNTNO",
            "ACCOUNTTYPE",
            "FIRSTNAMES",
            "INITIALS",
            "LASTNAME",
        ],
    )
    VBI_1099DATA_SOM = FineosExtract(
        file_name="VBI_1099DATA_SOM.csv",
        table=FineosExtractVbi1099DataSom,
        field_names=["FIRSTNAMES", "LASTNAME", "CUSTOMERNO", "PACKEDDATA", "DOCUMENTTYPE", "C"],
    )
    VPEI = FineosExtract(
        file_name="vpei.csv",
        table=FineosExtractVpei,
        field_names=[
            "C",
            "I",
            "PAYEESOCNUMBE",
            "PAYMENTADD1",
            "PAYMENTADD2",
            "PAYMENTADD4",
            "PAYMENTADD6",
            "PAYMENTPOSTCO",
            "PAYMENTMETHOD",
            "PAYMENTDATE",
            "AMOUNT_MONAMT",
            "PAYEEBANKSORT",
            "PAYEEACCOUNTN",
            "PAYEEACCOUNTT",
            "EVENTTYPE",
            "PAYEEIDENTIFI",
            "PAYEEFULLNAME",
            "EVENTREASON",
            "AMALGAMATIONC",
            "PAYMENTTYPE",
        ],
    )

    PAYMENT_DETAILS = FineosExtract(
        file_name="vpeipaymentdetails.csv",
        table=FineosExtractVpeiPaymentDetails,
        field_names=[
            "C",
            "I",
            "PECLASSID",
            "PEINDEXID",
            "PAYMENTSTARTP",
            "PAYMENTENDPER",
            "BALANCINGAMOU_MONAMT",
            "BUSINESSNETBE_MONAMT",
        ],
    )

    PAYMENT_LINE = FineosExtract(
        file_name="vpeipaymentline.csv",
        table=FineosExtractVpeiPaymentLine,
        field_names=[
            "C",
            "I",
            "AMOUNT_MONAMT",
            "LINETYPE",
            "PAYMENTDETAILCLASSID",
            "PAYMENTDETAILINDEXID",
            "C_PYMNTEIF_PAYMENTLINES",
            "I_PYMNTEIF_PAYMENTLINES",
        ],
    )

    CLAIM_DETAILS = FineosExtract(
        file_name="vpeiclaimdetails.csv",
        table=FineosExtractVpeiClaimDetails,
        field_names=["PECLASSID", "PEINDEXID", "ABSENCECASENU", "LEAVEREQUESTI"],
    )

    # Note this is the one used in the payment extract
    # do not confuse it with the similar _SOM one in the claimant extract
    VBI_REQUESTED_ABSENCE = FineosExtract(
        file_name="VBI_REQUESTEDABSENCE.csv",
        table=FineosExtractVbiRequestedAbsence,
        field_names=[
            "ABSENCEPERIOD_CLASSID",
            "ABSENCEPERIOD_INDEXID",
            "LEAVEREQUEST_DECISION",
            "LEAVEREQUEST_ID",
            "ABSENCEREASON_COVERAGE",
            "ABSENCE_CASECREATIONDATE",
            "ABSENCEPERIOD_TYPE",
            "ABSENCEREASON_QUALIFIER1",
            "ABSENCEREASON_QUALIFIER2",
            "ABSENCEREASON_NAME",
        ],
    )

    PAYMENT_FULL_SNAPSHOT = FineosExtract(
        file_name="Automated-Adhoc-Extract-SOM_PEI_Fullextract.csv",
        table=FineosExtractPaymentFullSnapshot,
        field_names=[
            "C",
            "I",
            "FLAGS",
            "PARTITIONID",
            "LASTUPDATEDATE",
            "BOEVERSION",
            "C_OSUSER_UPDATEDBY",
            "I_OSUSER_UPDATEDBY",
            "ADDRESSLINE1",
            "ADDRESSLINE2",
            "ADDRESSLINE3",
            "ADDRESSLINE4",
            "ADDRESSLINE5",
            "ADDRESSLINE6",
            "ADDRESSLINE7",
            "ADVICETOPAY",
            "ADVICETOPAYOV",
            "AMALGAMATIONC",
            "PAYMENTTYPE",
            "AMOUNT_MONAMT",
            "AMOUNT_MONCUR",
            "CHECKCUTTING",
            "CONFIRMEDBYUS",
            "CONFIRMEDUID",
            "CONTRACTREF",
            "CORRESPCOUNTR",
            "CURRENCY",
            "DATEINTERFACE",
            "DATELASTPROCE",
            "DESCRIPTION",
            "EMPLOYEECONTR",
            "EVENTEFFECTIV",
            "EVENTREASON",
            "EVENTTYPE",
            "EXTRACTIONDAT",
            "GROSSPAYMENTA_MONAMT",
            "GROSSPAYMENTA_MONCUR",
            "INSUREDRESIDE",
            "NAMETOPRINTON",
            "NOMINATEDPAYE",
            "NOMPAYEECUSTO",
            "NOMPAYEEDOB",
            "NOMPAYEEFULLN",
            "NOMPAYEESOCNU",
            "NOTES",
            "PAYEEACCOUNTN",
            "PAYEEACCOUNTT",
            "PAYEEADDRESS",
            "PAYEEBANKBRAN",
            "PAYEEBANKCODE",
            "PAYEEBANKINST",
            "PAYEEBANKSORT",
            "PAYEECORRESPO",
            "PAYEECUSTOMER",
            "PAYEEDOB",
            "PAYEEFULLNAME",
            "PAYEEIDENTIFI",
            "PAYEESOCNUMBE",
            "PAYMENTADD",
            "PAYMENTADD1",
            "PAYMENTADD2",
            "PAYMENTADD3",
            "PAYMENTADD4",
            "PAYMENTADD5",
            "PAYMENTADD6",
            "PAYMENTADD7",
            "PAYMENTADDCOU",
            "PAYMENTCORRST",
            "PAYMENTDATE",
            "PAYMENTFREQUE",
            "PAYMENTMETHOD",
            "PAYMENTPOSTCO",
            "PAYMENTPREMIS",
            "PAYMENTTRIGGE",
            "PAYMENTTYPE",
            "PAYMETHCURREN",
            "PERCENTTAXABL",
            "POSTCODE",
            "PREMISESNO",
            "SETUPBYUSERID",
            "SETUPBYUSERNA",
            "STATUS",
            "STATUSEFFECTI",
            "STATUSREASON",
            "STOCKNO",
            "SUMMARYEFFECT",
            "SUMMARYSTATUS",
            "TAXOVERRIDE",
            "TAXWAGEAMOUNT_MONAMT",
            "TAXWAGEAMOUNT_MONCUR",
            "TRANSACTIONNO",
            "TRANSACTIONST",
            "TRANSSTATUSDA",
        ],
    )

    CANCELLED_PAYMENTS_EXTRACT = FineosExtract(
        file_name="Automated-Adhoc-Extract-SOM_PEI_CancelledRecords.csv",
        table=FineosExtractCancelledPayments,
        field_names=CANCELLED_OR_REPLACED_EXTRACT_FIELD_NAMES,
    )

    REPLACED_PAYMENTS_EXTRACT = FineosExtract(
        file_name="Automated-Adhoc-Extract-SOM_PEI_ReplacedRecords.csv",
        table=FineosExtractReplacedPayments,
        field_names=CANCELLED_OR_REPLACED_EXTRACT_FIELD_NAMES,
    )

    VBI_LEAVE_PLAN_REQUESTED_ABSENCE = FineosExtract(
        file_name="VBI_LEAVEPLANREQUESTEDABSENCE.csv",
        table=FineosExtractVbiLeavePlanRequestedAbsence,
        field_names=["SELECTEDPLAN_CLASSID", "SELECTEDPLAN_INDEXID", "LEAVEREQUEST_ID"],
    )

    PAID_LEAVE_INSTRUCTION = FineosExtract(
        file_name="vpaidleaveinstruction.csv",
        table=FineosExtractVPaidLeaveInstruction,
        field_names=[
            "C",
            "I",
            "AVERAGEWEEKLYWAGE_MONAMT",
            "C_SELECTEDLEAVEPLAN",
            "I_SELECTEDLEAVEPLAN",
        ],
    )

    VBI_TASKREPORT_SOM = FineosExtract(
        file_name="VBI_TASKREPORT_SOM.csv",
        table=FineosExtractVbiTaskReportSom,
        field_names=[
            "TASKID",
            "TASKTABLEID",
            "CREATIONDATE",
            "STARTDATE",
            "CLOSEDDATE",
            "ONHOLDUNTILDATE",
            "STATUS",
            "TASKTYPENAME",
            "CASETYPE",
            "NOTIFICATIONNUMBER",
            "CASENUMBER",
        ],
        field_filters={
            "STATUS": ["928000"],
            "TASKTYPENAME": [
                "Employee Reported Other Income",
                "Escalate Employer Reported Other Income",
                "Escalate employer reported accrued paid leave (PTO)",
                "Employee reported accrued paid leave (PTO)",
                "Employee Reported Other Leave",
            ],
        },
    )


CLAIMANT_EXTRACT_FILES = [
    FineosExtractConstants.VBI_REQUESTED_ABSENCE_SOM,
    FineosExtractConstants.EMPLOYEE_FEED,
    FineosExtractConstants.VBI_REQUESTED_ABSENCE,
]

CLAIMANT_EXTRACT_FILE_NAMES = [extract_file.file_name for extract_file in CLAIMANT_EXTRACT_FILES]

PAYMENT_EXTRACT_FILES = [
    FineosExtractConstants.VPEI,
    FineosExtractConstants.CLAIM_DETAILS,
    FineosExtractConstants.PAYMENT_DETAILS,
    FineosExtractConstants.PAYMENT_LINE,
]
PAYMENT_EXTRACT_FILE_NAMES = [extract_file.file_name for extract_file in PAYMENT_EXTRACT_FILES]

PAYMENT_RECONCILIATION_EXTRACT_FILES = [
    FineosExtractConstants.PAYMENT_FULL_SNAPSHOT,
    FineosExtractConstants.CANCELLED_PAYMENTS_EXTRACT,
    FineosExtractConstants.REPLACED_PAYMENTS_EXTRACT,
]
PAYMENT_RECONCILIATION_EXTRACT_FILE_NAMES = [
    extract_file.file_name for extract_file in PAYMENT_RECONCILIATION_EXTRACT_FILES
]

IAWW_EXTRACT_FILES = [
    FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE,
    FineosExtractConstants.PAID_LEAVE_INSTRUCTION,
]
IAWW_EXTRACT_FILES_NAMES = [extract_file.file_name for extract_file in IAWW_EXTRACT_FILES]

REQUEST_1099_EXTRACT_FILES = [FineosExtractConstants.VBI_1099DATA_SOM]

REQUEST_1099_EXTRACT_FILES_NAMES = [
    extract_file.file_name for extract_file in REQUEST_1099_EXTRACT_FILES
]

VBI_TASKREPORT_SOM_EXTRACT_FILES = [FineosExtractConstants.VBI_TASKREPORT_SOM]
VBI_TASKREPORT_SOM_EXTRACT_FILE_NAMES = [
    extract_file.file_name for extract_file in VBI_TASKREPORT_SOM_EXTRACT_FILES
]


class Regexes:
    MONETARY_AMOUNT = (
        r"^\d*\.\d\d$"  # Decimal fields must include 2 digits following the decimal point.
    )
    STATE_ABBREVIATION = r"^[A-Z]{2}$"  # State abbreviations should be exactly 2 uppercase letters.
    COUNTRY_ABBREVIATION = (
        r"^[A-Z]{2}$"  # Country abbreviations should be exactly 2 uppercase letters.
    )
    ZIP_CODE = r"^\d{5}(-\d{4})?$"  # Zip codes must contain 5 digits and may contain +4 identifier.


class ValidationReason(str, Enum):
    MISSING_FIELD = "MissingField"
    MISSING_DATASET = "MissingDataset"
    TOO_MANY_DATASETS = "TooManyDatasets"
    MISSING_IN_DB = "MissingInDB"
    MISSING_FINEOS_NAME = "MissingFineosName"
    FIELD_TOO_SHORT = "FieldTooShort"
    FIELD_TOO_LONG = "FieldTooLong"
    INVALID_LOOKUP_VALUE = "InvalidLookupValue"
    INVALID_VALUE = "InvalidValue"
    INVALID_TYPE = "InvalidType"
    RECEIVED_PAYMENT_CURRENTLY_BEING_PROCESSED = "ReceivedPaymentCurrentlyBeingProcessed"
    UNEXPECTED_PAYMENT_TRANSACTION_TYPE = "UnexpectedPaymentTransactionType"
    EFT_PRENOTE_PENDING = "EFTPending"
    EFT_PRENOTE_REJECTED = "EFTRejected"
    CLAIMANT_MISMATCH = "ClaimantMismatch"
    CLAIM_NOT_ID_PROOFED = "ClaimNotIdProofed"
    PAYMENT_EXCEEDS_PAY_PERIOD_CAP = "PaymentExceedsPayPeriodCap"
    ROUTING_NUMBER_FAILS_CHECKSUM = "RoutingNumberFailsChecksum"
    LEAVE_REQUEST_IN_REVIEW = "LeaveRequestInReview"
    UNEXPECTED_RECORD_VARIANCE = "UnexpectedRecordVariance"
    EMPLOYER_EXEMPT = "EmployerExempt"
    OPEN_OTHER_INCOME_TASKS = "OpenOtherIncomeTasks"


@dataclass(frozen=True, eq=True)
class ValidationIssue:
    reason: ValidationReason
    details: Optional[str] = ""
    field_name: Optional[str] = None

    def to_dict(self):
        output = asdict(self)
        if self.field_name is None:
            del output["field_name"]
        return output


@dataclass
class ValidationContainer:
    # Keeping this simple for now, will likely be expanded in the future.
    record_key: str
    validation_issues: List[ValidationIssue] = field(default_factory=list)

    def add_validation_issue(
        self, reason: ValidationReason, details: Optional[str], field_name: Optional[str] = None
    ) -> None:
        self.validation_issues.append(ValidationIssue(reason, details, field_name))

    def has_validation_issues(self) -> bool:
        return len(self.validation_issues) != 0

    def get_reasons(self) -> List[ValidationReason]:
        return [validation_issue.reason for validation_issue in self.validation_issues]

    def get_reasons_with_field_names(self) -> List[Tuple[ValidationReason, Optional[str]]]:
        return [
            (validation_issue.reason, validation_issue.field_name)
            for validation_issue in self.validation_issues
        ]

    def to_dict(self):
        output = asdict(self)
        output["validation_issues"] = [issue.to_dict() for issue in self.validation_issues]
        return output


class ValidationIssueException(Exception):
    __slots__ = ["issues", "message"]

    def __init__(self, issues: List[ValidationIssue], message: str):
        self.issues = issues
        self.message = message


def get_date_folder(current_time: Optional[datetime] = None) -> str:
    if not current_time:
        current_time = get_now_us_eastern()

    return current_time.strftime("%Y-%m-%d")


def build_archive_path(
    prefix: str, file_status: str, file_name: str, current_time: Optional[datetime] = None
) -> str:
    """
    Construct the path to a file. In the format: prefix / file_status / current_time as date / file_name
    If no current_time specified, will use get_now_us_eastern() method.
    For example:

    build_archive_path("s3://bucket/path/archive", Constants.S3_INBOUND_RECEIVED_DIR,
      "2021-01-01-12-00-00-example-file.csv", datetime.datetime(2021, 1, 1, 12, 0, 0))
    produces
    "s3://bucket/path/archive/received/2021-01-01/2021-01-01-12-00-00-example-file.csv"

    Parameters
    -----------
    prefix: str
      The beginning of the path, likely based on a s3 path configured by an env var
    file_status: str
      The state the file is in, should be one of constants defined above that start with S3_INBOUND or S3_OUTBOUND
    file_name: str
      name of the file - will not be modified
    current_time: Optional[datetime]
      An optional datetime for use in the path, will be formatted as %Y-%m-%d
    """

    return os.path.join(prefix, file_status, get_date_folder(current_time), file_name)


def lookup_validator(
    lookup_table_clazz: Type[LookupTable], disallowed_lookup_values: Optional[List[str]] = None
) -> Callable[[str], Optional[ValidationReason]]:
    def validator_func(raw_value: str) -> Optional[ValidationReason]:
        # In certain scenarios, a value might be in our lookup table, but not be
        # valid for a particular scenario, this lets you skip those scenarios
        if disallowed_lookup_values and raw_value in disallowed_lookup_values:
            return ValidationReason.INVALID_LOOKUP_VALUE

        # description_to_db_instance is used by the get_id method
        # If the value passed into this method is set as a key in that, it's valid
        if raw_value not in lookup_table_clazz.description_to_db_instance:
            return ValidationReason.INVALID_LOOKUP_VALUE
        return None

    return validator_func


def zip_code_validator(zip_code: str) -> Optional[ValidationReason]:
    if not re.match(Regexes.ZIP_CODE, zip_code):
        return ValidationReason.INVALID_VALUE
    return None


def routing_number_validator(routing_number: str) -> Optional[ValidationReason]:
    if not validate_routing_number(routing_number):
        return ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM

    return None


def leave_request_id_validator(leave_request_id: str) -> Optional[ValidationReason]:
    parsed_leave_request_id = str_to_int(leave_request_id)
    if parsed_leave_request_id is None:
        return ValidationReason.INVALID_TYPE
    return None


def amount_validator(amount_str: str) -> Optional[ValidationReason]:
    try:
        Decimal(amount_str)
    except (InvalidOperation, TypeError):  # Amount is not numeric
        return ValidationReason.INVALID_VALUE
    return None


def validate_db_input(
    key: str,
    data: Any,
    errors: ValidationContainer,
    required: Optional[bool] = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    custom_validator_func: Optional[Callable[[str], Optional[ValidationReason]]] = None,
) -> Optional[str]:
    value = getattr(data, key.lower(), None)
    if value == "Unknown":
        value = None  # Effectively treating "" and "Unknown" the same

    if required and not value:
        errors.add_validation_issue(ValidationReason.MISSING_FIELD, key, field_name=key)
        return None

    validation_issues = []
    # Check the length only if it is defined/not empty
    if value:
        if min_length and len(value) < min_length:
            validation_issues.append(ValidationReason.FIELD_TOO_SHORT)
        if max_length and len(value) > max_length:
            validation_issues.append(ValidationReason.FIELD_TOO_LONG)

        # Also only bother with custom validation if the value exists
        if custom_validator_func:
            reason = custom_validator_func(value)
            if reason:
                validation_issues.append(reason)

    if required:

        for validation_issue in validation_issues:
            # Any non-missing error types add the value to the error details
            # Note that this means these reports will contain PII data
            errors.add_validation_issue(validation_issue, f"{key}: {value}", key)

    # If any of the specific validations hit an error, don't return the value
    # This is true even if the field is not required as we may still use the field.
    if len(validation_issues) > 0:
        return None

    return value


def get_date_group_str_from_path(path: str) -> Optional[str]:
    # E.g. For a file path s3://bucket/folder/2020-12-01-file-name.csv return 2020-12-01
    match = re.search("\\d{4}-\\d{2}-\\d{2}-\\d{2}-\\d{2}-\\d{2}", path)
    date_group_str = match[0] if match else None

    return date_group_str


def get_date_group_folder_name(date_group: str, reference_file_type: LkReferenceFileType) -> str:
    if (
        not reference_file_type.reference_file_type_description
    ):  # TODO remove when lookup descriptions are non nullable
        return ""

    reference_file_type_folder_postfix = (
        reference_file_type.reference_file_type_description.lower().replace(" ", "-")
    )

    date_group_folder = f"{date_group}-{reference_file_type_folder_postfix}"
    return date_group_folder


def payment_extract_reference_file_exists_by_date_group(
    db_session: db.Session, date_group: str, export_type: LkReferenceFileType
) -> bool:
    processed_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        Constants.S3_INBOUND_PROCESSED_DIR,
        get_date_group_folder_name(date_group, export_type),
    )

    skipped_path = os.path.join(
        payments_config.get_s3_config().pfml_fineos_extract_archive_path,
        Constants.S3_INBOUND_SKIPPED_DIR,
        get_date_group_folder_name(date_group, export_type),
    )
    reference_file = (
        db_session.query(ReferenceFile)
        .filter(ReferenceFile.reference_file_type_id == export_type.reference_file_type_id)
        .filter(
            (ReferenceFile.file_location == processed_path)
            | (ReferenceFile.file_location == skipped_path)
        )
        .first()
    )
    return reference_file is not None


def get_fineos_max_history_date(export_type: LkReferenceFileType) -> datetime:
    """Returns a max history datetime for a given ReferenceFileType

    Only accepts:
        - ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
        - ReferenceFileType.FINEOS_PAYMENT_EXTRACT
        - ReferenceFileType.FINEOS_PAYMENT_RECONCILIATION_EXTRACT
        - ReferenceFileType.FINEOS_IAWW_EXTRACT

    Raises:
        ValueError: An unacceptable ReferenceFileType or a bad datestring was
                    provided by get_date_config()
    """
    date_config = payments_config.get_date_config()

    if (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_claimant_extract_max_history_date

    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_payment_extract_max_history_date
    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_PAYMENT_RECONCILIATION_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_payment_reconciliation_extract_max_history_date
    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_IAWW_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_iaww_extract_max_history_date
    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_1099_DATA_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_1099_data_extract_max_history_date
    elif (
        export_type.reference_file_type_id
        == ReferenceFileType.FINEOS_VBI_TASKREPORT_SOM_EXTRACT.reference_file_type_id
    ):
        datestring = date_config.fineos_vbi_taskreport_som_extract_max_history_date

    else:
        raise ValueError(f"Incorrect export_type {export_type} provided")

    return datetime.strptime(datestring, "%Y-%m-%d")  # This may raise a ValueError


# TODO: This function should probably get broken down into smaller functions
def copy_fineos_data_to_archival_bucket(
    db_session: db.Session,
    expected_file_names: List[str],
    export_type: LkReferenceFileType,
    source_folder_s3_config_key: str = "fineos_data_export_path",
    allow_missing: bool = False,
) -> Dict[str, Dict[str, str]]:
    # stage source and destination folders
    s3_config = payments_config.get_s3_config()
    source_folder = getattr(s3_config, source_folder_s3_config_key)
    destination_folder = os.path.join(
        s3_config.pfml_fineos_extract_archive_path, Constants.S3_INBOUND_RECEIVED_DIR
    )

    # If get_fineos_max_history_date() raises a ValueError, we have
    # a big problem and it should propagate up.
    max_history_date = get_fineos_max_history_date(export_type)
    max_history_date_str = max_history_date.strftime("%Y-%m-%d")

    logger.debug(
        "Copying expected files from FINEOS folder: %s (%s)",
        ", ".join(expected_file_names),
        export_type.reference_file_type_description,
        extra={
            "src": source_folder,
            "destination": destination_folder,
            "max_history_date": max_history_date_str,
        },
    )

    logger.info(
        f"Copying fineos extract files to pfml received folder starting at {max_history_date}",
        extra={"max_history_date": max_history_date},
    )

    # copy all previously unprocessed files to the received folder
    # keep a mapping of expected to mapped files grouped by date
    copied_file_mapping_by_date: Dict[str, Dict[str, str]] = {}

    def copy_files(files, folder, check_already_processed=False):
        previously_processed_date_group = set()

        logger.debug("Copying files from folder: %s", folder)

        for file_path in files:
            date_str = get_date_group_str_from_path(file_path)
            # Only copy folders that are newer than a given date
            # Folders are formatted as 2020-12-17-00-00-00; we just care about the day portion
            try:
                # Cast is for picky linter that doesn't want to index an Optional[str]
                # TODO: Better is to refactor get_date_group_str_from_path() to return
                #       str and raise an error if there's an issue
                date_str_str = cast(str, date_str)
                date_of_folder = datetime.strptime(date_str_str[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                # There are non-timestamped folders that we don't want to
                # process, so we skip ahead
                logger.warning(
                    "Skipping: FINEOS extract folder named %s is not a parseable date", date_str
                )
                continue

            # If the date of the folder is older than the max_history_date,
            # we skip ahead
            if date_of_folder < max_history_date:
                logger.info(
                    "Skipping: FINEOS extract folder dated %s is prior to max_history_date %s",
                    date_str,
                    max_history_date_str,
                )
                continue

            for expected_file_name in expected_file_names:
                if file_path.endswith(expected_file_name) and date_str is not None:
                    source_file = os.path.join(source_folder, folder, file_path)

                    if check_already_processed and (
                        date_str in previously_processed_date_group
                        or payment_extract_reference_file_exists_by_date_group(
                            db_session, date_str, export_type
                        )
                    ):
                        logger.info(
                            f"Skipping: FINEOS extract folder dated {date_str} was previously processed"
                        )
                        previously_processed_date_group.add(date_str)
                        continue

                    file_name = file_util.get_file_name(file_path)
                    destination_file = os.path.join(destination_folder, file_name)

                    if copied_file_mapping_by_date.get(date_str) is None:
                        copied_file_mapping_by_date[date_str] = dict.fromkeys(
                            expected_file_names, ""
                        )

                    # We found two files which end the same, error
                    existing_expected_file = copied_file_mapping_by_date[date_str].get(
                        expected_file_name
                    )
                    if existing_expected_file and existing_expected_file != source_file:
                        raise RuntimeError(
                            f"Error while copying fineos extracts - duplicate files found for {expected_file_name}: {existing_expected_file} and {source_file}"
                        )

                    file_util.copy_file(source_file, destination_file)
                    copied_file_mapping_by_date[date_str][expected_file_name] = destination_file

    # process top level files
    top_level_files = file_util.list_files(source_folder)
    copy_files(top_level_files, folder="", check_already_processed=True)

    # check archive folders for unprocessed dates
    date_folders = file_util.list_folders(source_folder)
    for date_folder in date_folders:
        # We never want to process anything from before 2020-12-17 in any environment
        # Add a hardcoded-check here to exclude data that is that old
        # Folders are formatted as 2020-12-17-00-00-00, we just care about the day portion
        try:
            date_of_folder = datetime.strptime(date_folder[:10], "%Y-%m-%d")
            if date_of_folder < max_history_date:
                logger.info(
                    "Skipping FINEOS extract folder dated %s as it is prior to %s",
                    date_folder,
                    max_history_date_str,
                )
                continue
        except ValueError:
            # There are folders named config and logs that we don't want to process
            logger.warning(
                "Skipping FINEOS extract folder named %s as it is not a parseable date", date_folder
            )
            continue

        if payment_extract_reference_file_exists_by_date_group(
            db_session, date_folder, export_type
        ):
            logger.info(
                f"Skipping: FINEOS extract folder dated {date_folder} was previously processed"
            )
            continue

        subfolder_path = os.path.join(source_folder, date_folder)
        subfolder_files = file_util.list_files(subfolder_path)
        copy_files(subfolder_files, folder=date_folder, check_already_processed=False)

    # check for missing files in each group
    missing_files = []
    for date_str, copied_file_mapping in copied_file_mapping_by_date.items():
        for expected_file_name, destination in copied_file_mapping.items():
            if not destination:
                missing_files.append(f"{date_str}-{expected_file_name}")

    if missing_files and not allow_missing:
        message = f"Error while copying fineos extracts - The following expected files were not found {','.join(missing_files)}"
        logger.info(message)
        raise Exception(message)

    logger.debug(
        "Successfully copied expected files from FINEOS folder: %s (%s)",
        expected_file_names,
        export_type.reference_file_type_description,
        extra={
            "src": source_folder,
            "destination": destination_folder,
            "max_history_date": max_history_date_str,
            "copied_files": copied_file_mapping_by_date,
        },
    )

    return copied_file_mapping_by_date


def group_s3_files_by_date(expected_file_names: List[str]) -> Dict[str, List[str]]:
    s3_config = payments_config.get_s3_config()
    source_folder = os.path.join(
        s3_config.pfml_fineos_extract_archive_path, Constants.S3_INBOUND_RECEIVED_DIR
    )
    logger.info("Grouping files by date in path: %s", source_folder)

    s3_objects = file_util.list_files(source_folder)
    s3_objects.sort()

    date_to_full_path: Dict[str, List[str]] = OrderedDict()

    for s3_object in s3_objects:
        fixed_date_str = get_date_group_str_from_path(s3_object)
        for expected_file_name in expected_file_names:
            if s3_object.endswith(expected_file_name) and fixed_date_str is not None:
                if not date_to_full_path.get(fixed_date_str):
                    date_to_full_path[fixed_date_str] = []

                full_path = os.path.join(source_folder, s3_object)
                date_to_full_path[fixed_date_str].append(full_path)

    return date_to_full_path


def is_same_address(first: Address, second: Address) -> bool:
    if (
        compare_attributes(first, second, "address_line_one")
        and compare_attributes(first, second, "city")
        and compare_attributes(first, second, "zip_code")
        and compare_attributes(first, second, "geo_state_id")
        and compare_attributes(first, second, "country_id")
        and compare_attributes(first, second, "address_line_two")
    ):
        return True
    else:
        return False


def find_existing_address_pair(
    employee: Optional[Employee], new_address: Address, db_session: db.Session
) -> Optional[ExperianAddressPair]:
    if not employee:
        return None

    subquery = (
        db_session.query(Payment.payment_id)
        .join(Claim)
        .filter(Claim.employee_id == employee.employee_id)
    )
    experian_address_pairs = (
        db_session.query(ExperianAddressPair)
        .join(Payment, Payment.experian_address_pair_id == ExperianAddressPair.fineos_address_id)
        .filter(Payment.payment_id.in_(subquery))
        .all()
    )

    # For each address associated with prior payments for the claimant
    # see if either the address from FINEOS matches or the one returned
    # by Experian matches (in case FINEOS is updated to the more correct one)
    for experian_address_pair in experian_address_pairs:

        existing_fineos_address = experian_address_pair.fineos_address
        existing_experian_address = experian_address_pair.experian_address

        if existing_fineos_address and is_same_address(new_address, existing_fineos_address):
            return experian_address_pair

        if existing_experian_address and is_same_address(new_address, existing_experian_address):
            return experian_address_pair

    return None


def is_same_eft(first: PubEft, second: PubEft) -> bool:
    """Returns true if all EFT fields match"""
    if (
        first.routing_nbr == second.routing_nbr
        and first.account_nbr == second.account_nbr
        and first.bank_account_type_id == second.bank_account_type_id
    ):
        return True
    else:
        return False


def find_existing_eft(employee: Optional[Employee], new_eft: PubEft) -> Optional[PubEft]:
    if not employee:
        return None

    for pub_eft_pair in employee.pub_efts.all():
        if is_same_eft(pub_eft_pair.pub_eft, new_eft):
            return pub_eft_pair.pub_eft

    return None


def move_file_and_update_ref_file(
    db_session: db.Session, destination: str, ref_file: ReferenceFile
) -> None:
    file_util.rename_file(ref_file.file_location, destination)
    ref_file.file_location = destination


def get_mapped_claim_type(claim_type_str: str) -> LkClaimType:
    """Given a string from a Vendor Extract, return a LkClaimType

    Raises:
        ValueError: if the string does not match an existing LkClaimType
    """
    if claim_type_str == "Family":
        return ClaimType.FAMILY_LEAVE
    elif claim_type_str == "Employee":
        return ClaimType.MEDICAL_LEAVE
    else:
        raise ValueError("Unknown claim type")


def move_reference_file(
    db_session: db.Session, ref_file: ReferenceFile, src_dir: str, dest_dir: str
) -> None:
    """Moves a ReferenceFile

    Renames the actual S3 file (copies and deletes) and updates the reference_file.file_location
    """
    if ref_file.file_location is None:
        raise ValueError(f"ReferenceFile {ref_file.reference_file_id} is missing a file_location")

    old_location = ref_file.file_location

    # Verify that the file_locations contains the src directory. Ex: Constants.S3_INBOUND_RECEIVED_DIR
    # This will raise a ValueError if the src directory is not found
    old_location.rindex(src_dir)

    # Replace src directory with the dest directory. Ex: Constants.S3_INBOUND_ERROR_DIR
    new_location = old_location.replace(src_dir, dest_dir)

    # Rename the file
    # This may raise S3-related errors
    file_util.rename_file(old_location, new_location)

    # Update reference_file.file_location
    try:
        ref_file.file_location = new_location
        db_session.add(ref_file)
        db_session.commit()
        logger.info(
            "Successfully moved Reference File",
            extra={
                "file_location": ref_file.file_location,
                "src_dir": src_dir,
                "dest_dir": dest_dir,
            },
        )
    except SQLAlchemyError:
        # Rollback the database transaction
        db_session.rollback()
        # Rollback the file move
        file_util.rename_file(new_location, old_location)
        # Log the exception
        logger.exception(
            "Unable to move ReferenceFile",
            extra={
                "file_location": ref_file.file_location,
                "src_dir": src_dir,
                "dest_dir": dest_dir,
            },
        )
        raise


def get_attribute_names(cls):
    return [
        prop.key
        for prop in class_mapper(cls).iterate_properties
        if isinstance(prop, ColumnProperty)
    ]


def create_staging_table_instance(
    data: Dict,
    db_cls: ExtractTable,
    ref_file: ReferenceFile,
    fineos_extract_import_log_id: Optional[int] = None,
    ignore_properties: Optional[List[Any]] = None,
) -> base.Base:
    """We return an instance of cls, with matching properties from data and cls. If there are any
    properties from the data that don't have a match in staging model db_cls, we discard them and log it.
    Eg:
        class VbiRequestedAbsenceSom(Base):
            __tablename__ = "a"
            absence_casenumber = Column(Text)
            absence_casestatus = Column(Text)

        data = {'absence_casenumber': '123', 'absence_casestatus': 'active','new_column': 'testtest'}

        We will return an instance of class VbiRequestedAbsenceSom, with properties absence_casenumber and
        absence_casestatus. If new_column is not in ignore_properties, we will log a warning stating
        property new_column is not included in model class VbiRequestedAbsenceSom.
    """
    ignore_properties = [] if ignore_properties is None else ignore_properties

    lower_data = make_keys_lowercase(data)

    # discard any properties (if they're even present) that we've been told to ignore
    [lower_data.pop(prop) for prop in ignore_properties if prop in lower_data]

    # check if extracted data types match our db model properties
    # if there are extra properties, log them
    unconfigured_columns = get_unconfigured_fineos_columns(lower_data, db_cls)
    if len(unconfigured_columns) > 0:
        logger.warning(
            "Unconfigured columns in FINEOS extract after first record.",
            extra={"db_cls.__name__": db_cls.__name__, "fields": ",".join(unconfigured_columns)},
        )
    [lower_data.pop(column) for column in unconfigured_columns]

    return db_cls(
        **lower_data,
        reference_file=ref_file,
        fineos_extract_import_log_id=fineos_extract_import_log_id,
    )


def get_traceable_payment_details(
    payment: Payment, state: Optional[LkState] = None
) -> Dict[str, Optional[Any]]:
    # For logging purposes, this returns useful, traceable details
    # about a payment and related fields if they exist.
    #
    # DO NOT PUT PII IN THE RETURN OF THIS METHOD, IT'S MEANT FOR LOGGING
    #

    claim = payment.claim
    employee = payment.employee
    employer = payment.claim.employer if payment.claim else None

    return {
        "payment_id": payment.payment_id,
        "c_value": payment.fineos_pei_c_value,
        "i_value": payment.fineos_pei_i_value,
        "period_start_date": date_to_isoformat(payment.period_start_date),
        "period_end_date": date_to_isoformat(payment.period_end_date),
        "payment_date": date_to_isoformat(payment.payment_date),
        "payment_amount": str(payment.amount),
        "payment_method": payment.disb_method.payment_method_description
        if payment.disb_method
        else None,
        "pub_individual_id": payment.pub_individual_id,
        "payment_transaction_type": payment.payment_transaction_type.payment_transaction_type_description
        if payment.payment_transaction_type
        else None,
        "is_adhoc": payment.is_adhoc_payment,
        "fineos_extract_import_log_id": payment.fineos_extract_import_log_id,
        # Leave
        "leave_request_decision": payment.leave_request_decision,
        "claim_type": payment.claim_type.claim_type_description if payment.claim_type else None,
        "fineos_leave_request_id": payment.fineos_leave_request_id,
        # Claim
        "claim_id": claim.claim_id if claim else None,
        "absence_case_id": claim.fineos_absence_id if claim else None,
        # Employee
        "employee_id": employee.employee_id if employee else None,
        "fineos_customer_number": employee.fineos_customer_number if employee else None,
        # Employer
        "employer_id": employer.employer_id if employer else None,
        "fineos_employer_id": employer.fineos_employer_id if employer else None,
        # Misc
        "current_state": state.state_description if state else None,
        "relevant_party": payment.payment_relevant_party.payment_relevant_party_description
        if payment.payment_relevant_party
        else None,
    }


def get_traceable_payment_period_details(
    payment_detail: PaymentDetails,
) -> Dict[str, Optional[Any]]:
    # For logging purposes, this returns useful, traceable details
    # about a payment detail.
    #
    # DO NOT PUT PII IN THE RETURN OF THIS METHOD, IT'S MEANT FOR LOGGING
    #

    return {
        "payment_details_id": payment_detail.payment_details_id,
        "payment_details_c_value": payment_detail.payment_details_c_value,
        "payment_details_i_value": payment_detail.payment_details_i_value,
        "payment_details_period_start_date": date_to_isoformat(payment_detail.period_start_date),
        "payment_details_period_end_date": date_to_isoformat(payment_detail.period_end_date),
        "payment_details_balancing_amount": str(payment_detail.amount),
        "payment_details_net_amount": str(payment_detail.business_net_amount),
        "payment_details_payment_id": payment_detail.payment_id,
    }


def get_traceable_payment_line_details(payment_line: PaymentLine) -> Dict[str, Optional[Any]]:
    # For logging purposes, this returns useful, traceable details
    # about a payment line.
    #
    # DO NOT PUT PII IN THE RETURN OF THIS METHOD, IT'S MEANT FOR LOGGING
    #

    return {
        "payment_line_id": payment_line.payment_line_id,
        "payment_line_payment_id": payment_line.payment_id,
        "payment_line_payment_details_id": payment_line.payment_details_id,
        "payment_line_c_value": payment_line.payment_line_c_value,
        "payment_line_i_value": payment_line.payment_line_i_value,
        "payment_line_amount": payment_line.amount,
        "payment_line_type": payment_line.line_type,
    }


def get_traceable_pub_eft_details(
    pub_eft: PubEft,
    employee: Optional[Employee] = None,
    payment: Optional[Payment] = None,
    state: Optional[LkState] = None,
) -> Dict[str, Any]:
    # For logging purposes, this returns useful, traceable details
    # about an EFT record and related fields
    #
    # DO NOT PUT PII IN THE RETURN OF THIS METHOD, IT'S MEANT FOR LOGGING
    #

    details = {}
    if payment:
        details = get_traceable_payment_details(payment)

    details["pub_eft_id"] = pub_eft.pub_eft_id
    details["pub_eft_individual_id"] = pub_eft.pub_individual_id
    details["pub_eft_prenote_state"] = (
        pub_eft.prenote_state.prenote_state_description if pub_eft.prenote_state else None
    )
    if employee:
        details["employee_id"] = employee.employee_id
        details["fineos_customer_number"] = employee.fineos_customer_number

    details["current_state"] = state.state_description if state else None

    return details


def get_transaction_status_date(payment: Payment) -> date:
    # Check payments that have a check posted date should use
    # that for the transaction status date as that indicates
    # from PUB when the check was actually posted
    if payment.check and payment.check.check_posted_date:
        return payment.check.check_posted_date

    # Otherwise the transaction status date is calculated using the current time.
    return get_now_us_eastern().date()


employee_audit_log_keys = {
    "employee_id",
    "tax_identifier_id",
    "first_name",
    "last_name",
    "date_of_birth",
    "fineos_customer_number",
    "latest_import_log_id",
    "created_at",
    "updated_at",
}
employer_audit_log_keys = {
    "employer_id",
    "employer_fein",
    "employer_name",
    "dor_updated_date",
    "latest_import_log_id",
    "fineos_employer_id",
    "created_at",
    "updated_at",
}


def create_payment_log(
    payment: Payment,
    import_log_id: Optional[int],
    db_session: db.Session,
    additional_details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Create a log in the DB for information about a payment at a particular point
    in the processing. Automatically adds a snapshot of
    employee/employer/claim/absence period/payment check
    """
    absence_period = payment.leave_request

    snapshot = {}
    if absence_period:
        snapshot["absence_period"] = absence_period.for_json()
    # When we refactor claim to be fetched from absence period, change this
    # to be in the above if statement
    claim = payment.claim
    if claim:
        snapshot["claim"] = claim.for_json()

        employee = claim.employee
        if employee:
            employee_json = employee.for_json()
            snapshot["employee"] = filter_dict(employee_json, employee_audit_log_keys)

        employer = claim.employer
        if employer:
            employer_json = employer.for_json()
            snapshot["employer"] = filter_dict(employer_json, employer_audit_log_keys)

    payment_details = payment.payment_details
    if payment_details:
        payment_details_info = []
        for payment_detail in payment_details:
            payment_details_info.append(payment_detail.for_json())
        snapshot["payment_details"] = payment_details_info

    check_details = payment.check
    if check_details:
        snapshot["payment_check"] = check_details.for_json()

    audit_details = {"snapshot": snapshot}
    if additional_details:
        audit_details.update(additional_details)

    payment_log = PaymentLog(payment=payment, import_log_id=import_log_id, details=audit_details)
    db_session.add(payment_log)


def create_success_file(start_time: datetime, process_name: str) -> None:
    """
    Create a file that indicates the ECS process was successful. Will
    be put in a folder for the date the processing started, but
    the file will be timestamped with the time it completed.

    s3://bucket/reports/processed/{start_date}/{completion_timestamp}-{process_name}.SUCCESS
    """
    s3_config = payments_config.get_s3_config()

    end_time = get_now_us_eastern()
    timestamp_prefix = end_time.strftime("%Y-%m-%d-%H-%M-%S")
    success_file_name = f"{timestamp_prefix}-{process_name}.SUCCESS"

    archive_path = s3_config.pfml_error_reports_archive_path
    output_path = build_archive_path(
        archive_path, Constants.S3_INBOUND_PROCESSED_DIR, success_file_name, current_time=start_time
    )

    # What is the easiest way to create an empty file to upload?
    with file_util.write_file(output_path) as success_file:
        success_file.write("SUCCESS")

    logger.info("Creating success file at %s", output_path)


def validate_columns_present(record: Dict[str, Any], fineos_extract: FineosExtract) -> None:
    missing_columns = []

    for required_column in fineos_extract.field_names:
        if required_column.lower() not in record:
            missing_columns.append(required_column)

    if len(missing_columns) > 0:
        raise Exception(
            "FINEOS extract %s is missing required fields: %s - found only %s"
            % (fineos_extract.file_name, missing_columns, list(record.keys()))
        )


def get_unconfigured_fineos_columns(record: Dict[str, Any], db_cls: ExtractTable) -> List[Any]:
    class_properties = get_attribute_names(db_cls)
    unconfigured_columns = [column for column in record if column not in class_properties]
    return unconfigured_columns


def matches_all_filters(record: Dict[str, Any], extract: FineosExtract) -> bool:
    for field_name, allowed_values in extract.field_filters.items():
        field_value = record[field_name.lower()]
        if field_value not in allowed_values:
            return False
    return True


def is_employer_exempt_for_payment(payment: Payment, claim: Claim, employer: Employer) -> bool:
    # Adhoc payments always skip the exempt employer check
    if payment.is_adhoc_payment:
        return False

    # See if exemptions are even set for the employer
    # + make the linter happy that we're not comparing nulls
    if (
        not employer.exemption_commence_date
        or not employer.exemption_cease_date
        or not claim.absence_period_start_date
    ):
        return False

    # Check if the employer is exempt for the claim type
    # associated with the payment record
    if (
        payment.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id and employer.family_exemption
    ) or (
        payment.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id
        and employer.medical_exemption
    ):
        # Then check if the start of the claim
        # fell within the exempt dates of the employer
        if (
            employer.exemption_commence_date
            <= claim.absence_period_start_date
            <= employer.exemption_cease_date
        ):
            extra = get_traceable_payment_details(
                payment
            )  # Adds the basics about the employer/claim/payment
            extra["employer_is_exempt_family"] = employer.family_exemption
            extra["employer_is_exempt_medical"] = employer.medical_exemption
            extra["employer_exemption_commence_date"] = employer.exemption_commence_date.isoformat()
            extra["employer_exemption_cease_date"] = employer.exemption_cease_date.isoformat()
            logger.info("Payment failed exempt employer validation check", extra=extra)
            return True

    return False


def is_employer_reimbursement_payments_enabled() -> bool:
    return os.environ.get("ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS", "0") == "1"


def get_earliest_absence_period_for_payment_leave_request(
    db_session: db.Session, payment: Payment
) -> Optional[AbsencePeriod]:
    """
    Get the earliest absence period associated with a payment
    Note that this does not mean the payment is necessarily in
    the absence period. It just means it's the first absence period
    of the paid leave request connected to the payment.

    Claim
        * Paid Leave 1
            * Absence Period A
                * Payment I
                * Payment II
            * Absence Period B
                * Payment III
                * Payment IV
        * Paid Leave 2
            * Absence Period C
                * Payment V
                * Payment VI
            * Absence Period D
                * Payment VII
            * Absence Period E
                * Payment VIII

    For the above example:
    Payments I -> IV would return Absence Period A
    Payments V -> VIII would return Absence Period C

    Nothing would ever return Absence Periods B, D, or E
    """
    return (
        db_session.query(AbsencePeriod)
        .filter(AbsencePeriod.fineos_leave_request_id == payment.fineos_leave_request_id)
        .filter(AbsencePeriod.claim_id == payment.claim_id)
        .order_by(AbsencePeriod.absence_period_start_date.asc())
        .first()
    )


def get_open_tasks(
    db_session: db.Session, absence_case_number: str, tasknames: list[str]
) -> List[FineosExtractVbiTaskReportSom]:
    open_tasks = []

    latest_vbi_task_report_extract_reference_file = (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.FINEOS_VBI_TASKREPORT_SOM_EXTRACT.reference_file_type_id
        )
        .order_by(ReferenceFile.created_at.desc())
        .first()
    )

    if latest_vbi_task_report_extract_reference_file:
        open_tasks = (
            db_session.query(FineosExtractVbiTaskReportSom)
            .filter(
                FineosExtractVbiTaskReportSom.status == Constants.VBI_TASK_REPORT_STATUS_OPEN,
                FineosExtractVbiTaskReportSom.casenumber == absence_case_number,
                FineosExtractVbiTaskReportSom.reference_file_id
                == latest_vbi_task_report_extract_reference_file.reference_file_id,
                FineosExtractVbiTaskReportSom.tasktypename.in_(tasknames),
            )
            .all()
        )
    else:
        raise Exception(
            "No VBI Task Report Som files consumed. This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
        )

    return open_tasks


def get_earliest_matching_payment(
    db_session: db.Session, fineos_pei_c_value: str, fineos_pei_i_value: str
) -> Optional[Payment]:
    """
    Get the earliest payment associated with C/I values
    """
    return (
        db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == fineos_pei_c_value,
            Payment.fineos_pei_i_value == fineos_pei_i_value,
        )
        .order_by(Payment.created_at.asc())
        .first()
    )


def get_payment_transaction_type_id(payment: Payment) -> int:
    transaction_type_id = (
        payment.payment_transaction_type_id
        if payment.payment_transaction_type_id is not None
        else 0
    )
    return transaction_type_id
