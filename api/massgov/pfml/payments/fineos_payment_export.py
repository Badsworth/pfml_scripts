import csv
import decimal
import os
import pathlib
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, cast

from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    EFT,
    Address,
    AddressType,
    BankAccountType,
    Claim,
    CtrAddressPair,
    Employee,
    EmployeeAddress,
    GeoState,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    TaxIdentifier,
)

logger = logging.get_logger(__name__)

# folder constants
RECEIVED_FOLDER = "received"
PROCESSED_FOLDER = "processed"

# Expected file names
PEI_EXPECTED_FILE_NAME = "vpei.csv"
PAYMENT_DETAILS_EXPECTED_FILE_NAME = "vpeipaymentdetails.csv"
CLAIM_DETAILS_EXPECTED_FILE_NAME = "vpeiclaimdetails.csv"

expected_file_names = [
    PEI_EXPECTED_FILE_NAME,
    PAYMENT_DETAILS_EXPECTED_FILE_NAME,
    CLAIM_DETAILS_EXPECTED_FILE_NAME,
]


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

        self.date_str = date_str

        file_location = os.path.join(
            payments_config.get_s3_config().pfml_fineos_inbound_path, RECEIVED_FOLDER, self.date_str
        )
        self.reference_file = ReferenceFile(
            file_location=file_location,
            reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        logger.debug("Intialized extract data: %s", self.reference_file.file_location)


class PaymentData:
    """A class for containing any and all payment data. Handles validation and
       pulling values out of the various types

       All values are pulled from the CSV as-is and as strings. Values prefixed with raw_ need
       to be converted from the FINEOS value to one of our DB values (usually a lookup enum)
    """

    validation_container: payments_util.ValidationContainer

    c_value: str
    i_value: str
    fineos_employee_customer_number: str

    tin: Optional[str]
    absence_case_number: Optional[str] = None

    full_name: Optional[str]

    address_line_one: Optional[str]
    address_line_two: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]

    raw_payment_method: Optional[str]
    payment_start_period: Optional[str]
    payment_end_period: Optional[str]
    payment_date: Optional[str]
    payment_amount: Optional[str]
    payment_event_type: Optional[str]
    leave_request_id: Optional[str] = None

    routing_nbr: Optional[str]
    account_nbr: Optional[str]
    raw_account_type: Optional[str]

    amalgamationc: Optional[str]

    def __init__(self, extract_data: ExtractData, index: CiIndex, pei_record: Dict[str, str]):
        self.validation_container = payments_util.ValidationContainer(str(index))
        self.c_value = index.c
        self.i_value = index.i

        # Grab every value we might need out of the main vpei dataset.
        self.tin = payments_util.validate_csv_input(
            "PAYEESOCNUMBE", pei_record, self.validation_container, True
        )

        # Validate and set the FINEOS customer number. This value is directly passed
        # through to the Payment Voucher and SHOULD NOT be saved to the PFML database
        # without first discussing and determining if there will be any unexpected
        # negative side effects.
        self.fineos_customer_number_employee = payments_util.validate_csv_input(
            "PAYEECUSTOMER", pei_record, self.validation_container, True
        )

        self.full_name = payments_util.validate_csv_input(
            "PAYEEFULLNAME", pei_record, self.validation_container, False
        )

        self.address_line_one = payments_util.validate_csv_input(
            "PAYMENTADD1", pei_record, self.validation_container, True
        )
        self.address_line_two = payments_util.validate_csv_input(
            "PAYMENTADD2", pei_record, self.validation_container, False
        )
        self.city = payments_util.validate_csv_input(
            "PAYMENTADD4", pei_record, self.validation_container, True
        )
        self.state = payments_util.validate_csv_input(
            "PAYMENTADD6",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(GeoState),
        )
        self.zip_code = payments_util.validate_csv_input(
            "PAYMENTPOSTCO",
            pei_record,
            self.validation_container,
            True,
            min_length=5,
            max_length=10,
        )

        self.raw_payment_method = payments_util.validate_csv_input(
            "PAYMENTMETHOD",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(
                PaymentMethod,
                disallowed_lookup_values=[PaymentMethod.DEBIT.payment_method_description],
            ),
        )

        self.payment_date = payments_util.validate_csv_input(
            "PAYMENTDATE",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=payment_period_date_validator,
        )

        self.payment_amount = payments_util.validate_csv_input(
            "AMOUNT_MONAMT",
            pei_record,
            self.validation_container,
            True,
            custom_validator_func=self.amount_validator,
        )

        self.payment_event_type = payments_util.validate_csv_input(
            "EVENTTYPE", pei_record, self.validation_container, True
        )

        # These are only required if payment_method is for EFT
        eft_required = self.raw_payment_method == PaymentMethod.ACH.payment_method_description
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

        self.amalgamationc = payments_util.validate_csv_input(
            "AMALGAMATIONC", pei_record, self.validation_container, False
        )

        # Find the record in the other datasets.
        payment_details = extract_data.payment_details.indexed_data.get(index)
        if not payment_details:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "payment_details"
            )
        else:
            self.aggregate_payment_details(payment_details)

        claim_details = extract_data.claim_details.indexed_data.get(index)
        if not claim_details:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "claim_details"
            )
        else:
            self.absence_case_number = payments_util.validate_csv_input(
                "ABSENCECASENU", claim_details, self.validation_container, True
            )

            self.leave_request_id = payments_util.validate_csv_input(
                "LEAVEREQUESTI", claim_details, self.validation_container, True
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
                True,
                custom_validator_func=payment_period_date_validator,
            )
            row_end_period = payments_util.validate_csv_input(
                "PAYMENTENDPER",
                payment_detail_row,
                self.validation_container,
                True,
                custom_validator_func=payment_period_date_validator,
            )
            if row_start_period is not None:
                start_periods.append(row_start_period)
            if row_end_period is not None:
                end_periods.append(row_end_period)
        if start_periods:
            self.payment_start_period = min(start_periods)
        if end_periods:
            self.payment_end_period = max(end_periods)

    def amount_validator(self, amount_str: str) -> Optional[payments_util.ValidationReason]:
        amount = float(amount_str)
        if amount <= 0:
            return payments_util.ValidationReason.INVALID_VALUE
        return None

    def get_traceable_details(self) -> Dict[str, Optional[str]]:
        # For logging purposes, this returns useful, traceable details
        # about a payment that isn't PII. Recommended usage is as:
        # logger.info("...", extra=payment_data.get_traceable_details())
        return {
            "c_value": self.c_value,
            "i_value": self.i_value,
            "absence_case_number": self.absence_case_number,
        }


def payment_period_date_validator(
    payment_period_date_str: str,
) -> Optional[payments_util.ValidationReason]:
    now = payments_util.get_now()
    payment_period_date = datetime.strptime(payment_period_date_str, "%Y-%m-%d %H:%M:%S")
    if payment_period_date.date() > now.date():
        return payments_util.ValidationReason.INVALID_VALUE
    return None


# TODO move to payments_util
def download_and_process_data(extract_data: ExtractData, download_directory: pathlib.Path) -> None:
    logger.info(
        "Downloading and indexing payment extract data files.",
        extra={
            "pei_file": extract_data.pei.file_location,
            "payment_details_file": extract_data.payment_details.file_location,
            "claim_details_file": extract_data.claim_details.file_location,
        },
    )
    # To make processing simpler elsewhere, we index each extract file object on a key
    # that will let us join it with the PEI file later.

    # VPEI file
    pei_data = download_and_parse_data(extract_data.pei.file_location, download_directory)
    # This doesn't specifically need to be indexed, but it lets us be consistent
    for record in pei_data:
        extract_data.pei.indexed_data[CiIndex(record["C"], record["I"])] = record
        logger.debug("indexed pei file row with CI: %s, %s", record["C"], record["I"])

    # Payment details file
    payment_details = download_and_parse_data(
        extract_data.payment_details.file_location, download_directory
    )
    # claim details needs to be indexed on PECLASSID and PEINDEXID
    # which point to the vpei.C and vpei.I columns
    for record in payment_details:
        index = CiIndex(record["PECLASSID"], record["PEINDEXID"])
        if index not in extract_data.payment_details.indexed_data:
            extract_data.payment_details.indexed_data[index] = []
        extract_data.payment_details.indexed_data[index].append(record)
        logger.debug(
            "indexed payment details file row with CI: %s, %s",
            record["PECLASSID"],
            record["PEINDEXID"],
        )

    # Claim details file
    claim_details = download_and_parse_data(
        extract_data.claim_details.file_location, download_directory
    )
    # claim details needs to be indexed on PECLASSID and PEINDEXID
    # which point to the vpei.C and vpei.I columns
    for record in claim_details:
        extract_data.claim_details.indexed_data[
            CiIndex(record["PECLASSID"], record["PEINDEXID"])
        ] = record
        logger.debug(
            "indexed claim details file row with CI: %s, %s",
            record["PECLASSID"],
            record["PEINDEXID"],
        )

    logger.info("Successfully downloaded and indexed payment extract data files.")


def determine_field_names(download_location: pathlib.Path) -> List[str]:
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


def download_and_parse_data(s3_path: str, download_directory: pathlib.Path) -> List[Dict[str, str]]:
    file_name = s3_path.split("/")[-1]
    download_location = download_directory / file_name
    logger.info("download %s to %s", s3_path, download_location)
    if s3_path.startswith("s3:/"):
        file_util.download_from_s3(s3_path, str(download_location))
    else:
        file_util.copy_file(s3_path, str(download_location))

    raw_extract_data = []

    field_names = determine_field_names(download_location)
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
    payment_data: PaymentData, db_session: db.Session
) -> Tuple[Optional[Employee], Optional[Claim]]:
    # Get the TIN, employee and claim associated with the payment to be made
    try:
        tax_identifier = (
            db_session.query(TaxIdentifier).filter_by(tax_identifier=payment_data.tin).one_or_none()
        )
        if not tax_identifier:
            payment_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB, "tax_identifier"
            )
            return None, None

        employee = db_session.query(Employee).filter_by(tax_identifier=tax_identifier).one_or_none()
        if not employee:
            payment_data.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_IN_DB, "employee"
            )
            return None, None

        claim = (
            db_session.query(Claim)
            .filter_by(
                fineos_absence_id=payment_data.absence_case_number, employee_id=employee.employee_id
            )
            .one_or_none()
        )
    except SQLAlchemyError as e:
        logger.exception(
            "Unexpected error %s with one_or_none when querying for tin/employee/claim",
            type(e),
            extra=payment_data.get_traceable_details(),
        )
        raise

    # claim might not exist because the employee used the call center, if so, create the claim now
    if not claim:
        claim = Claim(
            claim_id=uuid.uuid4(),
            employee=employee,
            fineos_absence_id=payment_data.absence_case_number,
        )
        db_session.add(claim)

    return employee, claim


def update_ctr_address_pair_fineos_address(
    payment_data: PaymentData, employee: Employee, db_session: db.Session
) -> bool:
    """Create or update the employee's EFT record

    Returns:
        bool: True if payment_data has address updates; False otherwise
    """
    # Construct an Address from the payment_data
    payment_data_address = Address(
        address_id=uuid.uuid4(),
        address_line_one=payment_data.address_line_one,
        address_line_two=payment_data.address_line_two if payment_data.address_line_two else None,
        city=payment_data.city,
        geo_state_id=GeoState.get_id(payment_data.state),
        zip_code=payment_data.zip_code,
        address_type_id=AddressType.MAILING.address_type_id,
    )

    # If ctr_address_pair exists, compare the existing fineos_address with the payment_data address
    #   If they're the same, nothing needs to be done, so we can return
    #   If they're different or if no ctr_address_pair exists, create a new CtrAddressPair
    ctr_address_pair = employee.ctr_address_pair
    if ctr_address_pair:
        if payments_util.is_same_address(ctr_address_pair.fineos_address, payment_data_address):
            return False

    new_ctr_address_pair = CtrAddressPair(fineos_address=payment_data_address)
    employee.ctr_address_pair = new_ctr_address_pair
    db_session.add(payment_data_address)
    db_session.add(new_ctr_address_pair)
    db_session.add(employee)

    # We also want to make sure the address is linked in the EmployeeAddress table
    employee_address = EmployeeAddress(employee=employee, address=payment_data_address)
    db_session.add(employee_address)
    return True


def create_or_update_payment(
    payment_data: PaymentData, claim: Claim, db_session: db.Session
) -> Payment:
    # First check if a payment already exists
    try:
        payment = (
            db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == payment_data.c_value,
                Payment.fineos_pei_i_value == payment_data.i_value,
            )
            .one_or_none()
        )
    except SQLAlchemyError as e:
        logger.exception(
            "Unexpected error %s with one_or_none when querying for payment",
            type(e),
            extra=payment_data.get_traceable_details(),
        )
        raise

    if not payment:
        logger.info(
            "Creating new payment for CI: %s, %s",
            payment_data.c_value,
            payment_data.i_value,
            extra=payment_data.get_traceable_details(),
        )
        payment = Payment(payment_id=uuid.uuid4())

    payment.claim = claim
    payment.period_start_date = payments_util.datetime_str_to_date(
        payment_data.payment_start_period
    )
    payment.period_end_date = payments_util.datetime_str_to_date(payment_data.payment_end_period)
    payment.payment_date = payments_util.datetime_str_to_date(payment_data.payment_date)
    payment.amount = decimal.Decimal(cast(str, payment_data.payment_amount))
    payment.fineos_pei_c_value = payment_data.c_value
    payment.fineos_pei_i_value = payment_data.i_value
    payment.fineos_extraction_date = payments_util.get_now().date()

    db_session.add(payment)
    return payment


def update_eft(payment_data: PaymentData, employee: Employee, db_session: db.Session) -> bool:
    """Create or update the employee's EFT record

    Returns:
        bool: True if the payment_data includes EFT updates; False otherwise
    """

    # Only update if the employee is using ACH for payments
    if payment_data.raw_payment_method != PaymentMethod.ACH.payment_method_description:
        # We deliberately do not delete an EFT record in the case they switched from
        # EFT to Check for payment method. In the event they switch back, we'll update accordingly later.
        return False

    # Need to cast these values as str rather than Optional[str] as we've
    # already validated they're not None for linting
    routing_nbr = cast(str, payment_data.routing_nbr)
    account_nbr = cast(str, payment_data.account_nbr)
    bank_account_type_id = BankAccountType.get_id(payment_data.raw_account_type)

    # Construct an EFT object.
    new_eft = EFT(
        eft_id=uuid.uuid4(),
        routing_nbr=routing_nbr,
        account_nbr=account_nbr,
        bank_account_type_id=bank_account_type_id,
    )

    # Retrieve the employee's existing EFT data, if any
    existing_eft = employee.eft

    # If the employee has no existing EFT data, set it to the new data
    if not existing_eft:
        employee.eft = new_eft
        db_session.add(new_eft)
        return True

    # If the employee's existing EFT data is the same as the new data, then
    # do nothing
    elif payments_util.is_same_eft(existing_eft, new_eft):
        return False

    # If the employee's existing EFT data is NOT the same as the new data,
    # then overwrite the old data
    else:
        existing_eft.routing_nbr = routing_nbr
        existing_eft.account_nbr = account_nbr
        existing_eft.bank_account_type_id = bank_account_type_id
        db_session.add(existing_eft)
        return True


def process_payment_data_record(
    payment_data: PaymentData, reference_file: ReferenceFile, db_session: db.Session
) -> Optional[Payment]:
    employee, claim = get_employee_and_claim(payment_data, db_session)

    # We weren't able to find the employee and claim, can't properly associate it
    if payment_data.validation_container.has_validation_issues():
        return None
    # cast the types here so the linter doesn't think these are potentially None below
    employee = cast(Employee, employee)
    claim = cast(Claim, claim)

    with fineos_log_tables_util.update_entity_and_remove_log_entry(
        db_session, employee, commit=False
    ):
        # Update the payment method ID of the employee
        employee.payment_method_id = PaymentMethod.get_id(payment_data.raw_payment_method)

        # Update the mailing address with values from FINEOS
        has_address_update = update_ctr_address_pair_fineos_address(
            payment_data, employee, db_session
        )

        # Update the EFT info with values from FINEOS
        has_eft_update = update_eft(payment_data, employee, db_session)

        # Create the payment record
        payment = create_or_update_payment(payment_data, claim, db_session)

        # Specify whether the Payment has an EFT update
        # This gets used later in the pipeline (such as during the PEI Writeback
        # step)
        payment.has_address_update = has_address_update

        # Specify whether the Payment has an EFT update
        # This gets used later in the pipeline (such as during the PEI Writeback
        # step)
        payment.has_eft_update = has_eft_update

        # Link the payment object to the payment_reference_file
        payment_reference_file = PaymentReferenceFile(
            payment=payment, reference_file=reference_file,
        )
        db_session.add(payment_reference_file)

    return payment


def _setup_state_log(
    payment: Optional[Payment],
    was_successful: bool,
    validation_container: payments_util.ValidationContainer,
    db_session: db.Session,
) -> None:

    if payment:
        # If a payment has already been in a GAX, we do not want to
        # send it again (ideally we should never receive duplicate payments, but it is possible)
        # We do not want to consider these successful regardless of the
        # validation and want to send them in the error report to alert
        # someone that duplicate payments are coming through.
        was_previously_in_gax = state_log_util.has_been_in_end_state(
            payment, db_session, State.GAX_SENT
        )

        # All error scenarios end up in ADD_TO_PAYMENT_EXPORT_ERROR_REPORT
        if was_successful and not was_previously_in_gax:
            end_state = State.MARK_AS_EXTRACTED_IN_FINEOS
        else:
            end_state = State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT

        if was_previously_in_gax:
            # Useful IDs will be added during the error report generation.
            message = "Received a duplicate payment record from FINEOS"
            # Unset the validation container issues to keep
            # the error message simple in the report
            # Don't set the whole container to None as we want
            # the CI Value key added still.
            validation_container.validation_issues = []
        elif not was_successful:
            message = "Error processing payment record"
        else:
            message = "Success"

        state_log_util.create_finished_state_log(
            end_state=end_state,
            outcome=state_log_util.build_outcome(message, validation_container),
            associated_model=payment,
            db_session=db_session,
        )

        if was_successful and payment.has_eft_update and payment.claim and payment.claim.employee:
            employee = payment.claim.employee
            state_log_util.create_finished_state_log(
                end_state=State.EFT_REQUEST_RECEIVED,
                associated_model=employee,
                outcome=state_log_util.build_outcome(
                    f"Initiated VENDOR_EFT flow for Employee {employee.employee_id} from FINEOS payment export"
                ),
                db_session=db_session,
            )

    else:
        # In the most problematic cases, the state log
        # needs to be created before we've got a payment
        # object to associate it with. Associate the type with payment
        # but no actual payment.
        # TODO save with employee id and claim for traceability
        state_log_util.create_state_log_without_associated_model(
            end_state=State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT,
            outcome=state_log_util.build_outcome(
                "Error processing payment record", validation_container
            ),
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            db_session=db_session,
        )


def process_records_to_db(extract_data: ExtractData, db_session: db.Session) -> None:
    logger.info("Processing payment extract data into db: %s", extract_data.date_str)

    # Add the files to the DB
    # Note a single payment reference file is used for all files collectively
    db_session.add(extract_data.reference_file)

    for index, record in extract_data.pei.indexed_data.items():
        try:
            # Construct a payment data object for easier organization of the many params
            payment_data = PaymentData(extract_data, index, record)
            logger.debug("Constructed payment data for extract with CI: %s, %s", index.c, index.i)

            # Some required parameter is missing, can't continue processing the record
            if payment_data.validation_container.has_validation_issues():
                _setup_state_log(None, False, payment_data.validation_container, db_session)
                continue

            logger.info(
                f"Processing payment record - absence case number: {payment_data.absence_case_number}",
                extra=payment_data.get_traceable_details(),
            )

            payment = process_payment_data_record(
                payment_data, extract_data.reference_file, db_session
            )

            # Create and finish the state log. If there were any issues, this'll set the
            # record to an error state which'll send out a report to address it, otherwise
            # it will move onto the next step in processing
            _setup_state_log(
                payment,
                not payment_data.validation_container.has_validation_issues(),
                payment_data.validation_container,
                db_session,
            )

            logger.info(
                f"Done processing payment record - absence case number: {payment_data.absence_case_number}",
                extra=payment_data.get_traceable_details(),
            )
        except Exception as e:
            logger.exception("Validation error while processing payments %s", e)

            # In the case of any error, add the error message to the validation
            # container, or create one and add it.
            if payment_data:
                validation_container = payment_data.validation_container
            else:
                validation_container = payments_util.ValidationContainer(str(index))

            validation_container.add_validation_issue(
                payments_util.ValidationReason.EXCEPTION_OCCURRED, str(e)
            )

            # Note if this errors, the whole process fails, if adding a DB record fails, that's probably desirable
            _setup_state_log(payment, False, validation_container, db_session)

    logger.info("Successfully processed payment extract into db: %s", extract_data.date_str)
    return None


# TODO move to payments_util
def move_files_from_received_to_processed(
    extract_data: ExtractData, db_session: db.Session
) -> None:
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
    # to
    # s3://bucket/path/to/processed/2020-01-01-11-30-00-payment-export/2020-01-01-11-30-00-file.csv
    date_group_folder = payments_util.get_date_group_folder_name(
        extract_data.date_str, ReferenceFileType.PAYMENT_EXTRACT
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

    # Update the reference file DB record to point to the new folder for these files
    extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}"
    )
    extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
        extract_data.date_str, date_group_folder
    )
    db_session.add(extract_data.reference_file)
    logger.debug(
        "Updated reference file location for payment extract data.",
        extra={"reference_file_location": extract_data.reference_file.file_location},
    )

    logger.info("Successfully moved payments files to processed folder.")


# TODO move to payments_util
def move_files_from_received_to_error(
    extract_data: Optional[ExtractData], db_session: db.Session
) -> None:
    if not extract_data:
        logger.error("Cannot move files to error directory, as path is not known")
        return
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
    # to
    # s3://bucket/path/to/error/2020-01-01-11-30-00-payment-export/2020-01-01-file.csv
    date_group_folder = payments_util.get_date_group_folder_name(
        extract_data.date_str, ReferenceFileType.PAYMENT_EXTRACT
    )
    new_pei_s3_path = extract_data.pei.file_location.replace(
        "received", f"error/{date_group_folder}"
    )
    file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)
    logger.debug(
        "Moved PEI file to error folder.",
        extra={"source": extract_data.pei.file_location, "destination": new_pei_s3_path},
    )

    new_payment_s3_path = extract_data.payment_details.file_location.replace(
        "received", f"error/{date_group_folder}"
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
        "received", f"error/{date_group_folder}"
    )
    file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)
    logger.debug(
        "Moved claim details file to error folder.",
        extra={
            "source": extract_data.claim_details.file_location,
            "destination": new_claim_s3_path,
        },
    )

    # We still want to create the reference file, just use the one that is
    # created in the __init__ of the extract data object and set the path.
    # Note that this will not be attached to a payment
    extract_data.reference_file.file_location = file_util.get_directory(new_pei_s3_path)
    db_session.add(extract_data.reference_file)
    logger.debug(
        "Updated reference file location for payment extract data.",
        extra={"reference_file_location": extract_data.reference_file.file_location},
    )

    logger.info("Successfully moved payments files to error folder.")


def process_extract_data(download_directory: pathlib.Path, db_session: db.Session) -> None:

    logger.info("Processing payment extract files")

    payments_util.copy_fineos_data_to_archival_bucket(
        db_session, expected_file_names, ReferenceFileType.PAYMENT_EXTRACT
    )
    data_by_date = payments_util.group_s3_files_by_date(expected_file_names)

    previously_processed_date = set()

    logger.info("Dates in /received folder: %s", ", ".join(data_by_date.keys()))

    for date_str, s3_file_locations in data_by_date.items():

        logger.debug("Processing files in date group: %s", date_str, extra={"date_group": date_str})

        try:
            if (
                date_str in previously_processed_date
                or payments_util.payment_extract_reference_file_exists_by_date_group(
                    db_session, date_str, ReferenceFileType.PAYMENT_EXTRACT
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
            download_and_process_data(extract_data, download_directory)

            process_records_to_db(extract_data, db_session)
            move_files_from_received_to_processed(extract_data, db_session)
            logger.info(
                "Successfully processed payment extract files in date group: %s",
                date_str,
                extra={"date_group": date_str},
            )
            db_session.commit()
        except Exception:
            db_session.rollback()
            logger.exception(
                "Error processing payment extract files in date_group: %s",
                date_str,
                extra={"date_group": date_str},
            )
            move_files_from_received_to_error(extract_data, db_session)
            raise

    logger.info("Successfully processed payment extract files")
