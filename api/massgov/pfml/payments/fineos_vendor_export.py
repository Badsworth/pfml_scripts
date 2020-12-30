import os
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, cast

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    EFT,
    AbsenceStatus,
    Address,
    BankAccountType,
    Claim,
    ClaimType,
    CtrAddressPair,
    Employee,
    EmployeeAddress,
    EmployeeReferenceFile,
    GeoState,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
    TaxIdentifier,
)
from massgov.pfml.verification.generate_verification_codes import CSVSourceWrapper

logger = logging.get_logger(__name__)

# folder constants
RECEIVED_FOLDER = "received"
PROCESSED_FOLDER = "processed"
ERRORED_FOLDER = "errored"

REQUESTED_ABSENCES_FILE_NAME = "VBI_REQUESTEDABSENCE_SOM.csv"
EMPLOYEE_FEED_FILE_NAME = "Employee_feed.csv"
LEAVE_PLAN_INFO_FILE_NAME = "LeavePlan_info.csv"

expected_file_names = [
    REQUESTED_ABSENCES_FILE_NAME,
    EMPLOYEE_FEED_FILE_NAME,
    LEAVE_PLAN_INFO_FILE_NAME,
]

ELECTRONIC_FUNDS_TRANSFER = 1


@dataclass
class Extract:
    file_location: str
    indexed_data: Dict[str, Dict[str, str]] = field(default_factory=dict)


class ExtractData:
    requested_absence_info: Extract
    employee_feed: Extract
    leave_plan_info: Extract

    date_str: str

    reference_file: ReferenceFile

    def __init__(self, s3_locations: List[str], date_str: str):
        for s3_location in s3_locations:
            if s3_location.endswith(REQUESTED_ABSENCES_FILE_NAME):
                self.requested_absence_info = Extract(s3_location)
            elif s3_location.endswith(EMPLOYEE_FEED_FILE_NAME):
                self.employee_feed = Extract(s3_location)
            elif s3_location.endswith(LEAVE_PLAN_INFO_FILE_NAME):
                self.leave_plan_info = Extract(s3_location)

        self.date_str = date_str

        self.reference_file = ReferenceFile(
            file_location=os.path.join(
                payments_config.get_s3_config().pfml_fineos_inbound_path, "received", self.date_str
            ),
            reference_file_type_id=ReferenceFileType.VENDOR_CLAIM_EXTRACT.reference_file_type_id,
            reference_file_id=uuid.uuid4().__str__(),
        )


def process_vendor_extract_data(db_session: db.Session) -> None:
    payments_util.copy_fineos_data_to_archival_bucket(expected_file_names)
    data_by_date = payments_util.group_s3_files_by_date(expected_file_names)
    download_directory = tempfile.mkdtemp().__str__()

    for date_str, s3_file_locations in data_by_date.items():
        try:
            extract_data = ExtractData(s3_file_locations, date_str)
            download_and_index_data(extract_data, download_directory)
            process_records_to_db(extract_data, db_session)
            move_files_from_received_to_processed(extract_data, db_session)
            db_session.commit()
        except Exception as e:
            # If there was a file-level exception anywhere in the processing,
            # we move the file from received to error
            # Add this function:
            db_session.rollback()
            logger.exception(e)
            move_files_from_received_to_error(extract_data)


def download_and_index_data(extract_data: ExtractData, download_directory: str) -> None:
    downloaded_employee_feed_file = download_file(
        extract_data.employee_feed.file_location, download_directory
    )

    # Index employee file for easy search.
    employee_indexed_data: Dict[str, Dict[str, str]] = {}
    employee_rows = CSVSourceWrapper(downloaded_employee_feed_file)
    for row in employee_rows:
        default_payment_flag = row.get("DEFPAYMENTPREF")
        if default_payment_flag is not None and default_payment_flag == "Y":
            employee_indexed_data[str(row.get("CUSTOMERNO"))] = row

    extract_data.employee_feed.indexed_data = employee_indexed_data

    downloaded_leave_plan_info_file = download_file(
        extract_data.leave_plan_info.file_location, download_directory
    )

    # Index leave plan info for easy search.
    leave_plan_info_indexed_data: Dict[str, Dict[str, str]] = {}
    leave_plan_info_rows = CSVSourceWrapper(downloaded_leave_plan_info_file)
    for row in leave_plan_info_rows:
        leave_plan_info_indexed_data[str(row.get("ABSENCE_CASENUMBER"))] = row

    extract_data.leave_plan_info.indexed_data = leave_plan_info_indexed_data

    downloaded_requested_absence_file = download_file(
        extract_data.requested_absence_info.file_location, download_directory
    )

    requested_absence_indexed_data: Dict[str, Dict[str, str]] = {}
    requested_absence_rows = CSVSourceWrapper(downloaded_requested_absence_file)
    for row in requested_absence_rows:
        requested_absence_indexed_data[str(row.get("ABSENCE_CASENUMBER"))] = row

    extract_data.requested_absence_info.indexed_data = requested_absence_indexed_data


def download_file(s3_path: str, download_directory: str) -> str:
    file_name = os.path.basename(s3_path)
    download_location = os.path.join(download_directory, file_name)
    try:
        file_util.download_from_s3(s3_path, download_location)
    except Exception as e:
        logger.exception(e)
        raise e

    return download_location


def process_records_to_db(extract_data: ExtractData, db_session: db.Session) -> None:
    requested_absences = extract_data.requested_absence_info.indexed_data.values()

    for requested_absence in requested_absences:
        evidence_result_type = requested_absence.get("LEAVEREQUEST_EVIDENCERESULTTYPE")
        if evidence_result_type is None or evidence_result_type != "Satisfied":
            continue

        # Add / update entry on claim table
        validation_container = create_or_update_claim(db_session, extract_data, requested_absence)

        # Update employee info
        employee_pfml_entry = update_employee_info(
            db_session, extract_data, requested_absence, validation_container
        )

        if employee_pfml_entry is not None:
            generate_employee_reference_file(
                db_session, extract_data, employee_pfml_entry, validation_container
            )


def create_or_update_claim(
    db_session: db.Session, extract_data: ExtractData, requested_absence: Dict[str, str]
) -> payments_util.ValidationContainer:
    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(absence_case_id)

    claim_pfml: Optional[Claim] = db_session.query(Claim).filter(
        Claim.fineos_absence_id == absence_case_id
    ).one_or_none()

    if claim_pfml is None:
        claim_pfml = Claim()
        claim_pfml.fineos_absence_id = absence_case_id

    # Update, or finish formatting new,  claim row.
    claim_pfml.fineos_notification_id = requested_absence.get("NOTIFICATION_CASENUMBER")

    leave_plan = extract_data.leave_plan_info.indexed_data.get(absence_case_id)

    if leave_plan is None:
        error_msg = f"Leave Plan Info not found for Requested Absence {absence_case_id}"
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_DATASET, error_msg,
        )
    else:
        leave_type = payments_util.validate_csv_input(
            "LEAVETYPE",
            leave_plan,
            validation_container,
            True,
            custom_validator_func=payments_util.lookup_validator(ClaimType),
        )

        if leave_type is not None:
            try:
                claim_pfml.claim_type_id = ClaimType.get_id(leave_type)
            except KeyError:
                # validate_csv_input already recorded the key does not exist
                # but doesn't signal back.
                pass

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
        claim_pfml.absence_period_end_date = payments_util.datetime_str_to_date(absence_end_date)

    evidence_result_type = requested_absence.get("LEAVEREQUEST_EVIDENCERESULTTYPE")
    claim_pfml.is_id_proofed = evidence_result_type == "Satisfied"

    db_session.add(claim_pfml)

    return validation_container


def update_employee_info(
    db_session: db.Session,
    extract_data: ExtractData,
    requested_absence: Dict[str, str],
    validation_container: payments_util.ValidationContainer,
) -> Optional[Employee]:
    employee_customer_nbr = payments_util.validate_csv_input(
        "EMPLOYEE_CUSTOMERNO", requested_absence, validation_container, True
    )

    if employee_customer_nbr is None:
        employee_feed_entry = None
    else:
        employee_feed_entry = extract_data.employee_feed.indexed_data.get(employee_customer_nbr)

    # As we filter out all employee feed entries that do not have the default payment flag
    # set to Y this may be a possible condition: employee exists in FINEOS but has no
    # payment address set properly.
    if employee_feed_entry is None:
        absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
        error_msg = (
            f"Employee in VBI_REQUESTEDABSENCE_SOM with absence id {absence_case_id} and customer nbr {employee_customer_nbr} "
            "not found in employee feed file with default payment flag set to Y."
        )
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_DATASET, error_msg
        )
        return None

    employee_tax_identifier = payments_util.validate_csv_input(
        "NATINSNO", employee_feed_entry, validation_container, True
    )

    employee_pfml_entry = None

    if employee_tax_identifier is not None:
        tax_identifier_id = (
            db_session.query(TaxIdentifier.tax_identifier_id)
            .filter(TaxIdentifier.tax_identifier == employee_tax_identifier)
            .one_or_none()
        )
        if tax_identifier_id is not None:
            employee_pfml_entry = (
                db_session.query(Employee)
                .filter(Employee.tax_identifier_id == tax_identifier_id)
                .one_or_none()
            )

    # Assumption is we should not be creating employees in the PFML DB through this extract.
    if employee_pfml_entry is None:
        error_msg = f"Employee in employee file with customer nbr {employee_customer_nbr} not found in PFML DB."
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_IN_DB, error_msg
        )
        return None

    # Use employee feed entry to update PFML DB
    date_of_birth = payments_util.validate_csv_input(
        "DATEOFBIRTH", employee_feed_entry, validation_container, True
    )

    if date_of_birth is not None:
        employee_pfml_entry.date_of_birth = payments_util.datetime_str_to_date(date_of_birth)

    update_mailing_address(
        db_session, employee_feed_entry, employee_pfml_entry, validation_container
    )

    payment_method = payments_util.validate_csv_input(
        "PAYMENTMETHOD",
        employee_feed_entry,
        validation_container,
        True,
        custom_validator_func=payments_util.lookup_validator(PaymentMethod),
    )

    if payment_method is not None:
        try:
            employee_pfml_entry.payment_method_id = PaymentMethod.get_id(payment_method)
        except KeyError:
            pass

    update_eft_info(db_session, employee_feed_entry, employee_pfml_entry, validation_container)

    customer_nbr = payments_util.validate_csv_input(
        "CUSTOMERNO", employee_feed_entry, validation_container, True
    )

    if customer_nbr is not None:
        employee_pfml_entry.fineos_customer_number = customer_nbr

    db_session.add(employee_pfml_entry)

    return employee_pfml_entry


def update_mailing_address(
    db_session: db.Session,
    employee_feed_entry: Dict[str, str],
    employee_pfml_entry: Employee,
    validation_container: payments_util.ValidationContainer,
) -> None:
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
        "POSTCODE", employee_feed_entry, validation_container, True, min_length=5, max_length=10,
    )

    if nbr_of_validation_errors == len(validation_container.validation_issues):
        mailing_address = Address(
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
                return

        new_ctr_address_pair = CtrAddressPair(fineos_address=mailing_address)
        employee_pfml_entry.ctr_address_pair = new_ctr_address_pair
        db_session.add(mailing_address)
        db_session.add(new_ctr_address_pair)
        db_session.add(employee_pfml_entry)

        # We also want to make sure the address is linked in the EmployeeAddress table
        employee_address = EmployeeAddress(employee=employee_pfml_entry, address=mailing_address)
        db_session.add(employee_address)


def update_eft_info(
    db_session: db.Session,
    employee_feed_entry: Dict[str, str],
    employee_pfml_entry: Employee,
    validation_container: payments_util.ValidationContainer,
) -> None:
    nbr_of_validation_errors = len(validation_container.validation_issues)
    eft_required = employee_pfml_entry.payment_method_id == ELECTRONIC_FUNDS_TRANSFER

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
        True,
        custom_validator_func=payments_util.lookup_validator(BankAccountType),
    )

    if nbr_of_validation_errors == len(validation_container.validation_issues):
        eft = employee_pfml_entry.eft
        if not eft:
            eft = EFT()
        # Cast is to satisfy picky linting
        eft.routing_nbr = int(cast(str, routing_nbr))
        eft.account_nbr = int(cast(str, account_nbr))
        eft.bank_account_type_id = BankAccountType.get_id(account_type)
        db_session.add(eft)
        employee_pfml_entry.eft = eft


def generate_employee_reference_file(
    db_session: db.Session,
    extract_data: ExtractData,
    employee_pfml_entry: Employee,
    validation_container: payments_util.ValidationContainer,
) -> None:
    db_session.add(extract_data.reference_file)
    employee_reference_file = EmployeeReferenceFile(
        employee_id=employee_pfml_entry.employee_id,
        reference_file_id=extract_data.reference_file.reference_file_id,
    )
    db_session.add(employee_reference_file)
    validation_container.record_key = employee_pfml_entry.employee_id
    if validation_container.has_validation_issues():
        state_log = state_log_util.create_state_log(
            start_state=State.VENDOR_CHECK_INITIATED_BY_VENDOR_EXPORT,
            associated_model=employee_pfml_entry,
            db_session=db_session,
            commit=False,
        )
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT,
            outcome=state_log_util.build_outcome(
                f"Employee {employee_pfml_entry.employee_id} had validation issues in FINEOS vendor export {extract_data.date_str}",
                validation_container,
            ),
            db_session=db_session,
            commit=False,
        )
    else:
        state_log = state_log_util.create_state_log(
            start_state=State.VENDOR_CHECK_INITIATED_BY_VENDOR_EXPORT,
            associated_model=employee_pfml_entry,
            db_session=db_session,
            commit=False,
        )
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.IDENTIFY_MMARS_STATUS,
            outcome=state_log_util.build_outcome(
                f"Employee {employee_pfml_entry.employee_id} successfully extracted from FINEOS vendor export {extract_data.date_str}"
            ),
            db_session=db_session,
            commit=False,
        )

        # If payment method is EFT, then we also need a state log entry that starts in EFT_DETECTED_IN_VENDOR_EXPORT and ends in EFT_REQUEST_RECEIVED


def move_files_from_received_to_processed(
    extract_data: ExtractData, db_session: db.Session
) -> None:
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-file.csv
    # to
    # s3://bucket/path/to/processed/2020-01-01/2020-01-01-file.csv
    new_requested_absence_info_s3_path = extract_data.requested_absence_info.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(
        extract_data.requested_absence_info.file_location, new_requested_absence_info_s3_path
    )

    new_employee_feed_s3_path = extract_data.employee_feed.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.employee_feed.file_location, new_employee_feed_s3_path)

    new_leave_plan_info_s3_path = extract_data.leave_plan_info.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.leave_plan_info.file_location, new_leave_plan_info_s3_path)

    # Update the reference file DB record to point to the new folder for these files
    extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
        RECEIVED_FOLDER, PROCESSED_FOLDER
    )
    db_session.add(extract_data.reference_file)


def move_files_from_received_to_error(extract_data: ExtractData) -> None:
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-file.csv
    # to
    # s3://bucket/path/to/errored/2020-01-01/2020-01-01-file.csv
    new_requested_absence_info_s3_path = extract_data.requested_absence_info.file_location.replace(
        RECEIVED_FOLDER, f"{ERRORED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(
        extract_data.requested_absence_info.file_location, new_requested_absence_info_s3_path
    )

    new_employee_feed_s3_path = extract_data.employee_feed.file_location.replace(
        RECEIVED_FOLDER, f"{ERRORED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.employee_feed.file_location, new_employee_feed_s3_path)

    new_leave_plan_info_s3_path = extract_data.leave_plan_info.file_location.replace(
        RECEIVED_FOLDER, f"{ERRORED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.leave_plan_info.file_location, new_leave_plan_info_s3_path)
