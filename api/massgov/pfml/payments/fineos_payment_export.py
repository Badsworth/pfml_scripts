import csv
import io
import os
import pathlib
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List

import massgov.pfml.db as db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    EFT,
    Address,
    AddressType,
    BankAccountType,
    Claim,
    Employee,
    EmployeeAddress,
    GeoState,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    TaxIdentifier,
)

# Expected file names
PEI_EXPECTED_FILE_NAME = "vpei.csv.zip"
PAYMENT_DETAILS_EXPECTED_FILE_NAME = "vpeipaymentdetails.csv.zip"
CLAIM_DETAILS_EXPECTED_FILE_NAME = "vpeiclaimdetails.csv.zip"

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
    indexed_data: Dict[CiIndex, Dict[str, str]] = None


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

        self.reference_file = ReferenceFile(
            file_location=payments_util.get_s3_config().pfml_fineos_inbound_path,
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

    tin: str
    absence_case_number: str

    address_line_one: str
    address_line_two: str
    city: str
    state: str
    zip_code: str

    raw_payment_method: str
    payment_start_period: str
    payment_end_period: str
    payment_date: str
    payment_amount: str

    routing_nbr: str
    account_nbr: str
    raw_account_type: str

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


def copy_fineos_data_to_archival_bucket() -> Dict[str, str]:
    s3_config = payments_util.get_s3_config()
    return file_util.copy_s3_files(
        s3_config.fineos_data_export_path, s3_config.pfml_fineos_inbound_path, expected_file_names
    )


def download_and_process_data(extract_data: ExtractData, download_directory: pathlib.Path) -> None:
    # To make processing simpler elsewhere, we index each extract file object on a key
    # that will let us join it with the PEI file later.

    # VPEI file
    pei_data = download_and_parse_data(extract_data.pei.file_location, download_directory)
    # This doesn't specifically need to be indexed, but it lets us be consistent
    indexed_pei_data = {}
    for record in pei_data:
        indexed_pei_data[CiIndex(record["C"], record["I"])] = record
    extract_data.pei.indexed_data = indexed_pei_data

    # Payment details file
    payment_details = download_and_parse_data(
        extract_data.payment_details.file_location, download_directory
    )
    # claim details needs to be indexed on PECLASSID and PEINDEXID
    # which point to the vpei.C and vpei.I columns
    indexed_payment_details = {}
    for record in payment_details:
        indexed_payment_details[CiIndex(record["PECLASSID"], record["PEINDEXID"])] = record
    extract_data.payment_details.indexed_data = indexed_payment_details

    # Claim details file
    claim_details = download_and_parse_data(
        extract_data.claim_details.file_location, download_directory
    )
    # claim details needs to be indexed on PECLASSID and PEINDEXID
    # which point to the vpei.C and vpei.I columns
    indexed_claim_details = {}
    for record in claim_details:
        indexed_claim_details[CiIndex(record["PECLASSID"], record["PEINDEXID"])] = record
    extract_data.claim_details.indexed_data = indexed_claim_details


def determine_field_names(zipf: zipfile.ZipFile, file_name: str) -> List[str]:
    field_names = OrderedDict()
    # Read the first line of the file and handle duplicate field names.
    with zipf.open(file_name[:-4]) as extract_file:
        text_wrapper = io.TextIOWrapper(extract_file, encoding="UTF-8")
        reader = csv.reader(text_wrapper, delimiter=",")

        # If duplicates are found, they'll be named
        # field_name_1, field_name_2,..
        for field_name in next(reader):
            if field_name in field_names:
                new_field_name = f"{field_name}_{field_names[field_name]}"
                field_names[field_name] += 1
                field_names[new_field_name] = 1
            else:
                field_names[field_name] = 1

    return field_names.keys()


def download_and_parse_data(s3_path: str, download_directory: pathlib.Path) -> List[Dict[str, str]]:
    file_name = s3_path.split("/")[-1]
    download_location = download_directory / file_name
    file_util.download_from_s3(s3_path, str(download_location))

    raw_extract_data = []

    with zipfile.ZipFile(download_location) as zipf:
        field_names = determine_field_names(zipf, file_name)
        # Open the file within the ZIP file (named the same, without .zip)
        with zipf.open(file_name[:-4]) as extract_file:
            # Need to wrap the file to convert it from bytes to string
            text_wrapper = io.TextIOWrapper(extract_file, encoding="UTF-8")
            dict_reader = csv.DictReader(text_wrapper, delimiter=",", fieldnames=field_names)
            # Each data object represents a row from the CSV as a dictionary
            # The keys are column headers
            # The rows are the corresponding value in the row
            next(dict_reader)  # Because we specify the fieldnames, skip the header row
            raw_extract_data = list(dict_reader)

    return raw_extract_data


def group_s3_files_by_date() -> Dict[str, List[str]]:
    s3_config = payments_util.get_s3_config()
    s3_objects = file_util.list_files(s3_config.pfml_fineos_inbound_path, "/")

    date_to_full_path = {}

    for s3_object in s3_objects:
        for expected_file_name in expected_file_names:
            if s3_object.endswith(expected_file_name):
                # Grab everything that isn't the suffix of the file name
                date = s3_object[: -len(expected_file_name)]
                fixed_date_str = date.rstrip("-")  # eg. 2020-01-01- becomes 2020-01-01

                if not date_to_full_path.get(fixed_date_str):
                    date_to_full_path[fixed_date_str] = []

                full_path = os.path.join(s3_config.pfml_fineos_inbound_path, s3_object)
                date_to_full_path[fixed_date_str].append(full_path)

    return date_to_full_path


def get_employee_and_claim(payment_data: PaymentData, db_session: db.Session) -> (Employee, Claim):
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
        claim = Claim(
            employee_id=employee.employee_id, fineos_absence_id=payment_data.absence_case_number,
        )
        db_session.add(claim)
        db_session.commit()

    return employee, claim


def update_mailing_address(
    payment_data: PaymentData, employee: Employee, db_session: db.Session
) -> None:
    mailing_address = employee.mailing_address
    if not mailing_address:
        mailing_address = Address()
    mailing_address.address_line_one = payment_data.address_line_one
    if payment_data.address_line_two:
        mailing_address.address_line_two = payment_data.address_line_two
    mailing_address.city = payment_data.city
    mailing_address.geo_state_id = GeoState.get_id(payment_data.state)
    mailing_address.zip_code = payment_data.zip_code
    mailing_address.address_type_id = AddressType.MAILING.address_type_id

    db_session.add(mailing_address)
    employee.mailing_address = mailing_address

    # We also want to make sure the address is linked in the EmployeeAddress table
    employee_address = employee.addresses.filter(
        EmployeeAddress.address_id == mailing_address.address_id
    ).one_or_none()
    if not employee_address:
        employee_address = EmployeeAddress(employee=employee, address=mailing_address)
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
    payment.payment_method_id = PaymentMethod.get_id(payment_data.raw_payment_method)
    payment.period_start_date = payment_data.payment_start_period
    payment.period_end_date = payment_data.payment_end_period
    payment.payment_date = payment_data.payment_date
    payment.amount = payment_data.payment_amount
    payment.fineos_pei_c_value = payment_data.c_value
    payment.fineos_pei_i_value = payment_data.i_value

    db_session.add(payment)
    db_session.commit()  # Forces payment_id to be created and available
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

    eft.routing_nbr = payment_data.routing_nbr
    eft.account_nbr = payment_data.account_nbr
    eft.bank_account_type_id = BankAccountType.get_id(payment_data.raw_account_type)

    employee.eft = eft
    db_session.add(eft)


def process_payment_data_record(
    payment_data: PaymentData, reference_file: ReferenceFile, db_session: db.Session
) -> None:
    employee, claim = get_employee_and_claim(payment_data, db_session)

    # We weren't able to find the employee and claim, can't properly associate it
    if payment_data.validation_container.has_validation_issues():
        return

    # Update the mailing address with values from FINEOS
    update_mailing_address(payment_data, employee, db_session)
    # Update the EFT info with values from FINEOS
    update_eft(payment_data, employee, db_session)
    # Create the payment record
    payment = create_or_update_payment(payment_data, claim, db_session)

    # Link the payment object to the payment_reference_file
    payment_reference_file = PaymentReferenceFile(
        payment_id=payment.payment_id, reference_file_id=reference_file.reference_file_id,
    )
    db_session.add(payment_reference_file)
    db_session.commit()


def process_records_to_db(
    extract_data: ExtractData, db_session: db.Session
) -> List[payments_util.ValidationContainer]:
    # Add the files to the DB
    # Note a single payment reference file is used for all files collectively
    db_session.add(extract_data.reference_file)

    validation_issues = []

    for index, record in extract_data.pei.indexed_data.items():
        try:
            # Construct a payment data object for easier organization of the many params
            payment_data = PaymentData(extract_data, index, record)

            # Some required parameter is missing, can't continue processing the record
            if payment_data.validation_container.has_validation_issues():
                validation_issues.append(payment_data.validation_container)
                continue

            process_payment_data_record(payment_data, extract_data.reference_file, db_session)

            # If there were any issues later in the processing, add the validation issue
            if payment_data.validation_container.has_validation_issues():
                validation_issues.append(payment_data.validation_container)
                continue

        except Exception as e:
            # In the case of any error, add the error message to the validation
            # container, or create one and add it.
            if payment_data:
                validation_container = payment_data.validation_container
            else:
                validation_container = payments_util.ValidationContainer(str(index))

            validation_container.add_error_msg(str(e))
            validation_issues.append(payment_data.validation_container)

    db_session.flush()
    db_session.commit()
    return validation_issues


def move_files_from_received_to_processed(
    extract_data: ExtractData, db_session: db.Session
) -> None:
    # Effectively, this method will move a file of path:
    # s3://bucket/path/to/received/2020-01-01-file.csv
    # to
    # s3://bucket/path/to/processed/2020-01-01/2020-01-01-file.csv
    new_pei_s3_path = extract_data.pei.file_location.replace(
        "received", f"processed/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.pei.file_location, new_pei_s3_path)

    new_payment_s3_path = extract_data.payment_details.file_location.replace(
        "received", f"processed/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.payment_details.file_location, new_payment_s3_path)

    new_claim_s3_path = extract_data.claim_details.file_location.replace(
        "received", f"processed/{extract_data.date_str}"
    )
    file_util.rename_file(extract_data.claim_details.file_location, new_claim_s3_path)

    # Update the reference file DB record to point to the new folder for these files
    extract_data.reference_file.file_location = file_util.get_directory(new_pei_s3_path)
    db_session.add(extract_data.reference_file)


def process_extract_data(
    download_directory: pathlib.Path, db_session: db.Session
) -> List[payments_util.ValidationContainer]:
    data_by_date = group_s3_files_by_date()

    validation_issues = []

    for date_str, s3_file_locations in data_by_date.items():
        try:
            extract_data = ExtractData(s3_file_locations, date_str)
            download_and_process_data(extract_data, download_directory)
            issues = process_records_to_db(extract_data, db_session)
            validation_issues.extend(issues)
            move_files_from_received_to_processed(extract_data, db_session)
        except Exception as e:
            # If there was an exception anywhere in the processing, let's
            # add it to the validation error object. The logic that runs
            # this will determine what to do regarding the issue.
            issue = payments_util.ValidationContainer("ProcessingError")
            issue.add_error_msg(str(e))
            validation_issues.append(issue)

    return validation_issues
