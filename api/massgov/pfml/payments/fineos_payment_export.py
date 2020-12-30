import csv
import decimal
import os
import pathlib
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
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


class ExtractData:
    pei: Extract
    payment_details: Extract
    claim_details: Extract

    date_str: str

    reference_file: ReferenceFile

    def __init__(self, s3_locations: List[str], date_str: str):
        for s3_location in s3_locations:
            if s3_location.endswith(PEI_EXPECTED_FILE_NAME):
                self.pei = Extract(s3_location)
            elif s3_location.endswith(PAYMENT_DETAILS_EXPECTED_FILE_NAME):
                self.payment_details = Extract(s3_location)
            elif s3_location.endswith(CLAIM_DETAILS_EXPECTED_FILE_NAME):
                self.claim_details = Extract(s3_location)

        self.date_str = date_str

        file_location = os.path.join(
            payments_util.get_s3_config().pfml_fineos_inbound_path, RECEIVED_FOLDER, self.date_str
        )
        self.reference_file = ReferenceFile(
            file_location=file_location,
            reference_file_type_id=ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
        )


class PaymentData:
    """A class for containing any and all payment data. Handles validation and
       pulling values out of the various types

       All values are pulled from the CSV as-is and as strings. Values prefixed with raw_ need
       to be converted from the FINEOS value to one of our DB values (usually a lookup enum)
    """

    validation_container: payments_util.ValidationContainer

    c_value: str
    i_value: str
    customer_no: str

    tin: Optional[str]
    absence_case_number: Optional[str]

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

    routing_nbr: Optional[str]
    account_nbr: Optional[str]
    raw_account_type: Optional[str]

    def __init__(self, extract_data: ExtractData, index: CiIndex, pei_record: Dict[str, str]):
        self.validation_container = payments_util.ValidationContainer(str(index))
        self.c_value = index.c
        self.i_value = index.i

        # Find the record in the other datasets.
        payment_details = extract_data.payment_details.indexed_data.get(index)
        claim_details = extract_data.claim_details.indexed_data.get(index)
        if not payment_details:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "payment_details"
            )
        if not claim_details:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_DATASET, "claim_details"
            )

        if self.validation_container.has_validation_issues():
            return
        # Cast these to non-optional values as we've validated them above (for linting)
        payment_details = cast(Dict[str, str], payment_details)
        claim_details = cast(Dict[str, str], claim_details)

        # Grab every value we might need out of the datasets
        self.tin = payments_util.validate_csv_input(
            "PAYEESOCNUMBE", pei_record, self.validation_container, True
        )
        self.absence_case_number = payments_util.validate_csv_input(
            "ABSENCECASENU", claim_details, self.validation_container, True
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
            custom_validator_func=payments_util.lookup_validator(PaymentMethod),
        )
        self.payment_start_period = payments_util.validate_csv_input(
            "PAYMENTSTARTP", payment_details, self.validation_container, True
        )
        self.payment_end_period = payments_util.validate_csv_input(
            "PAYMENTENDPER", payment_details, self.validation_container, True
        )
        self.payment_date = payments_util.validate_csv_input(
            "PAYMENTDATE", pei_record, self.validation_container, True
        )
        self.payment_amount = payments_util.validate_csv_input(
            "AMOUNT_MONAMT", pei_record, self.validation_container, True
        )

        # These are only required if payment_method is for EFT
        eft_required = self.raw_payment_method == PaymentMethod.ACH.payment_method_description
        self.routing_nbr = payments_util.validate_csv_input(
            "PAYEEBANKCODE",
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


def copy_fineos_data_to_archival_bucket(db_session: db.Session) -> Dict[str, Dict[str, str]]:
    # stage source and destination folders
    s3_config = payments_util.get_s3_config()
    source_folder = s3_config.fineos_data_export_path
    destination_folder = os.path.join(s3_config.pfml_fineos_inbound_path, RECEIVED_FOLDER)

    # copy all previously unprocessed files to the received folder
    # keep a mapping of expected to mapped files grouped by date
    copied_file_mapping_by_date: Dict[str, Dict[str, str]] = {}

    def copy_files(files, folder, check_already_processed=False):
        previously_processed_date_group = set()

        for file_path in files:
            date_str = get_date_group_str_from_path(file_path)
            for expected_file_name in expected_file_names:
                if file_path.endswith(expected_file_name) and date_str is not None:
                    source_file = os.path.join(source_folder, folder, file_path)

                    if check_already_processed and (
                        date_str in previously_processed_date_group
                        or reference_file_exists(db_session, date_str)
                    ):
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
                            f"Duplicate files found for {expected_file_name}: {existing_expected_file} and {source_file}"
                        )

                    file_util.copy_file(source_file, destination_file)
                    copied_file_mapping_by_date[date_str][expected_file_name] = destination_file

    # process top level files
    top_level_files = file_util.list_files(source_folder)
    copy_files(top_level_files, folder="", check_already_processed=True)

    # check archive folders for unprocessed dates
    date_folders = file_util.list_folders(source_folder)
    for date_folder in date_folders:
        if not reference_file_exists(db_session, date_folder):
            subfolder_path = os.path.join(source_folder, date_folder)
            subfolder_files = file_util.list_files(subfolder_path)
            copy_files(subfolder_files, folder=date_folder, check_already_processed=False)

    # check for missing files in each group
    missing_files = []
    for date_str, copied_file_mapping in copied_file_mapping_by_date.items():
        for expected_file_name, destination in copied_file_mapping.items():
            if not destination:
                missing_files.append(f"{date_str}-{expected_file_name}")

    if missing_files:
        raise Exception(f"The following files were not found in S3 {','.join(missing_files)}")

    return copied_file_mapping_by_date


def download_and_process_data(extract_data: ExtractData, download_directory: pathlib.Path) -> None:
    # To make processing simpler elsewhere, we index each extract file object on a key
    # that will let us join it with the PEI file later.

    # VPEI file
    pei_data = download_and_parse_data(extract_data.pei.file_location, download_directory)
    # This doesn't specifically need to be indexed, but it lets us be consistent
    for record in pei_data:
        extract_data.pei.indexed_data[CiIndex(record["C"], record["I"])] = record

    # Payment details file
    payment_details = download_and_parse_data(
        extract_data.payment_details.file_location, download_directory
    )
    # claim details needs to be indexed on PECLASSID and PEINDEXID
    # which point to the vpei.C and vpei.I columns
    for record in payment_details:
        extract_data.payment_details.indexed_data[
            CiIndex(record["PECLASSID"], record["PEINDEXID"])
        ] = record

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
    file_util.download_from_s3(s3_path, str(download_location))

    raw_extract_data = []

    field_names = determine_field_names(download_location)
    with open(download_location) as extract_file:
        dict_reader = csv.DictReader(extract_file, delimiter=",", fieldnames=field_names)
        # Each data object represents a row from the CSV as a dictionary
        # The keys are column headers
        # The rows are the corresponding value in the row
        next(dict_reader)  # Because we specify the fieldnames, skip the header row
        raw_extract_data = list(dict_reader)

    return raw_extract_data


def get_date_group_str_from_path(path: str) -> Optional[str]:
    # E.g. For a file path s3://bucket/folder/2020-12-01-file-name.csv return 2020-12-01
    match = re.search("\\d{4}-\\d{2}-\\d{2}-\\d{2}-\\d{2}-\\d{2}", path)
    date_group_str = match[0] if match else None

    return date_group_str


def reference_file_exists(db_session, date_str):
    path = os.path.join(
        payments_util.get_s3_config().pfml_fineos_inbound_path, PROCESSED_FOLDER, date_str
    )
    reference_file = (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location == path,
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id,
        )
        .first()
    )

    return reference_file is not None


def group_s3_files_by_date() -> Dict[str, List[str]]:
    s3_config = payments_util.get_s3_config()
    source_folder = os.path.join(s3_config.pfml_fineos_inbound_path, RECEIVED_FOLDER)
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


def get_employee_and_claim(
    payment_data: PaymentData, db_session: db.Session
) -> Tuple[Optional[Employee], Optional[Claim]]:
    # Get the TIN, employee and claim associated with the payment to be made
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
    # claim might not exist because the employee used the call center, if so, create the claim now
    if not claim:
        claim = Claim(employee=employee, fineos_absence_id=payment_data.absence_case_number,)
        db_session.add(claim)

    # Update the payment method ID of the employee
    employee.payment_method_id = PaymentMethod.get_id(payment_data.raw_payment_method)

    return employee, claim


def update_ctr_address_pair_fineos_address(
    payment_data: PaymentData, employee: Employee, db_session: db.Session
) -> None:
    # Construct an Address from the payment_data
    payment_data_address = Address(
        address_line_one=payment_data.address_line_one,
        address_line_two=payment_data.address_line_two if payment_data.address_line_two else None,
        city=payment_data.city,
        geo_state_id=GeoState.get_id(payment_data.state),
        zip_code=payment_data.zip_code,
        address_type_id=AddressType.MAILING.address_type_id,
    )

    # If ctr_address_pair exists, compare the exisiting fineos_address with the payment_data address
    #   If they're the same, nothing needs to be done, so we can return
    #   If they're different or if no ctr_address_pair exists, create a new CtrAddressPair
    ctr_address_pair = employee.ctr_address_pair
    if ctr_address_pair:
        if payments_util.is_same_address(ctr_address_pair.fineos_address, payment_data_address):
            return

    new_ctr_address_pair = CtrAddressPair(fineos_address=payment_data_address)
    employee.ctr_address_pair = new_ctr_address_pair
    db_session.add(payment_data_address)
    db_session.add(new_ctr_address_pair)
    db_session.add(employee)

    # We also want to make sure the address is linked in the EmployeeAddress table
    employee_address = EmployeeAddress(employee=employee, address=payment_data_address)
    db_session.add(employee_address)


def create_or_update_payment(
    payment_data: PaymentData, claim: Claim, db_session: db.Session
) -> Payment:
    # First check if a payment already exists
    payment = (
        db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .one_or_none()
    )

    if not payment:
        payment = Payment()

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


def update_eft(payment_data: PaymentData, employee: Employee, db_session: db.Session) -> None:
    # Only update if the employee is using ACH for payments
    if payment_data.raw_payment_method != PaymentMethod.ACH.payment_method_description:
        # We deliberately do not delete an EFT record in the case they switched from
        # EFT to Check for payment method. In the event they switch back, we'll update accordingly later.
        return

    eft = employee.eft

    if not eft:
        eft = EFT()

    # Need to cast these values as str rather than Optional[str]
    # as we've already validated they're not None
    # for linting, but then make them ints for actually assigning them
    eft.routing_nbr = int(cast(str, payment_data.routing_nbr))
    eft.account_nbr = int(cast(str, payment_data.account_nbr))
    eft.bank_account_type_id = BankAccountType.get_id(payment_data.raw_account_type)

    employee.eft = eft
    db_session.add(eft)


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

    # Update the mailing address with values from FINEOS
    update_ctr_address_pair_fineos_address(payment_data, employee, db_session)
    # Update the EFT info with values from FINEOS
    update_eft(payment_data, employee, db_session)
    # Create the payment record
    payment = create_or_update_payment(payment_data, claim, db_session)

    # Link the payment object to the payment_reference_file
    payment_reference_file = PaymentReferenceFile(payment=payment, reference_file=reference_file,)
    db_session.add(payment_reference_file)

    return payment


def _setup_state_log(
    payment: Optional[Payment],
    was_successful: bool,
    validation_container: payments_util.ValidationContainer,
    db_session: db.Session,
) -> None:
    if payment:
        new_state_log = state_log_util.create_state_log(
            start_state=State.PAYMENT_PROCESS_INITIATED,
            associated_model=payment,
            db_session=db_session,
            commit=False,
        )
    else:
        # In the most problematic cases, the state log
        # needs to be created before we've got a payment
        # object to associate it with. Associate the type with payment
        # but no actual payment.
        new_state_log = state_log_util.create_state_log_without_associated_model(
            start_state=State.PAYMENT_PROCESS_INITIATED,
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            db_session=db_session,
            commit=False,
        )

    # Immediately end the state log entry
    # but don't add/commit it quite yet, only if all records can be processed
    end_state = (
        State.MARK_AS_EXTRACTED_IN_FINEOS
        if was_successful
        else State.ADD_TO_PAYMENT_EXPORT_ERROR_REPORT
    )
    message = "Success" if was_successful else "Error processing payment record"
    state_log_util.finish_state_log(
        state_log=new_state_log,
        end_state=end_state,
        db_session=db_session,
        outcome=state_log_util.build_outcome(message, validation_container),
        commit=False,
    )


def process_records_to_db(extract_data: ExtractData, db_session: db.Session) -> None:
    # Add the files to the DB
    # Note a single payment reference file is used for all files collectively
    db_session.add(extract_data.reference_file)

    for index, record in extract_data.pei.indexed_data.items():
        try:
            # Construct a payment data object for easier organization of the many params
            payment_data = PaymentData(extract_data, index, record)

            # Some required parameter is missing, can't continue processing the record
            if payment_data.validation_container.has_validation_issues():
                _setup_state_log(None, False, payment_data.validation_container, db_session)
                continue

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
        except Exception as e:
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


def move_files_from_received_to_processed(
    extract_data: ExtractData, db_session: db.Session
) -> None:
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-file.csv
    # to
    # s3://bucket/path/to/processed/2020-01-01/2020-01-01-file.csv
    new_pei_s3_path = extract_data.pei.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)

    new_payment_s3_path = extract_data.payment_details.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.payment_details.file_location, new_payment_s3_path)

    new_claim_s3_path = extract_data.claim_details.file_location.replace(
        RECEIVED_FOLDER, f"{PROCESSED_FOLDER}/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)

    # Update the reference file DB record to point to the new folder for these files
    extract_data.reference_file.file_location = extract_data.reference_file.file_location.replace(
        RECEIVED_FOLDER, PROCESSED_FOLDER
    )
    db_session.add(extract_data.reference_file)


def move_files_from_received_to_error(
    extract_data: Optional[ExtractData], db_session: db.Session
) -> None:
    if not extract_data:
        logger.error("Cannot move files to error directory, as path is not known")
        return
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-file.csv
    # to
    # s3://bucket/path/to/error/2020-01-01/2020-01-01-file.csv
    new_pei_s3_path = extract_data.pei.file_location.replace(
        "received", f"error/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)

    new_payment_s3_path = extract_data.payment_details.file_location.replace(
        "received", f"error/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.payment_details.file_location, new_payment_s3_path)

    new_claim_s3_path = extract_data.claim_details.file_location.replace(
        "received", f"error/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)

    # We still want to create the reference file, just use the one that is
    # created in the __init__ of the extract data object and set the path.
    # Note that this will not be attached to a payment
    extract_data.reference_file.file_location = file_util.get_directory(new_pei_s3_path)
    db_session.add(extract_data.reference_file)


def process_extract_data(download_directory: pathlib.Path, db_session: db.Session) -> None:
    data_by_date = group_s3_files_by_date()
    copy_fineos_data_to_archival_bucket(db_session)
    data_by_date = group_s3_files_by_date()

    previously_processed_date = set()

    for date_str, s3_file_locations in data_by_date.items():
        try:
            if date_str in previously_processed_date or reference_file_exists(db_session, date_str):
                logger.warning(
                    "Found previously processed file(s) for date group still in received folder: %s",
                    date_str,
                )
                previously_processed_date.add(date_str)
                continue

            extract_data = ExtractData(s3_file_locations, date_str)
            download_and_process_data(extract_data, download_directory)
            process_records_to_db(extract_data, db_session)
            move_files_from_received_to_processed(extract_data, db_session)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.exception("Error processing FINEOS payment export")
            move_files_from_received_to_error(extract_data, db_session)
            raise e
