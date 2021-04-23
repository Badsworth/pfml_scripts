import argparse
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from random import randint
from typing import Dict, List, Optional

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Payment, PaymentCheck
from massgov.pfml.db.models.factories import PaymentFactory, PubEftFactory
from massgov.pfml.delegated_payments.mock.scenarios import ScenarioDescriptor, ScenarioName
from massgov.pfml.delegated_payments.pub.pub_check import _format_employee_name_for_ez_check
from massgov.pfml.util.files import create_csv_from_list

logger = logging.get_logger(__name__)

# Setup command line generator args
parser = argparse.ArgumentParser(description="Generate fake check response files and data")
parser.add_argument(
    "--folder", type=str, default="check_files", help="Output folder for generated files"
)
parser.add_argument("--count", type=str, default=100, help="Number of rows for generated files")


@dataclass
class CheckResponseData:
    begin_date: Optional[str] = None
    end_date: Optional[str] = None
    posted_date: Optional[str] = None
    issued_date: Optional[str] = None
    trc_number: Optional[int] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    account_name: Optional[str] = None
    type: Optional[str] = None
    check_number: Optional[int] = None
    payee_name: Optional[str] = None
    payee_id: Optional[str] = None
    bfc_code: Optional[str] = None
    type_detail: Optional[str] = None
    posted_amount: Optional[Decimal] = None
    issued_amount: Optional[Decimal] = None


class Constants:
    BEGIN_DATE = "Begin Date"
    END_DATE = "End Date"
    TRC_Number = "TRC Number"
    BANK_NAME = "Bank Name"
    ACCOUNT_NUMBER = "Account Number"
    ACCOUNT_TYPE = "Account Type"
    ACCOUNT_NAME = "Account Name"
    TYPE = "Type"
    TYPE_DETAIL = "Type Detail"
    POSTED_DATE = "Posted Date"
    POSTED_AMOUNT = "Posted Amount"
    CHECK_NUMBER = "Check Number"
    ISSUED_DATE = "Issued Date"
    ISSUED_AMOUNT = "Issued Amount"
    PAYEE_NAME = "Payee Name"
    PAYEE_ID = "Payee ID"
    BFC_CODE = "BCF Code"

    OUTSTANDING_FTP_CSV_HEADER = [
        BEGIN_DATE,
        END_DATE,
        TRC_Number,
        BANK_NAME,
        ACCOUNT_NUMBER,
        ACCOUNT_TYPE,
        ACCOUNT_NAME,
        TYPE,
        TYPE_DETAIL,
        CHECK_NUMBER,
        ISSUED_DATE,
        ISSUED_AMOUNT,
        PAYEE_NAME,
        PAYEE_ID,
        BFC_CODE,
    ]

    PAID_FTP_CSV_HEADER = [
        BEGIN_DATE,
        END_DATE,
        TRC_Number,
        BANK_NAME,
        ACCOUNT_NUMBER,
        ACCOUNT_TYPE,
        ACCOUNT_NAME,
        TYPE,
        TYPE_DETAIL,
        CHECK_NUMBER,
        POSTED_DATE,
        POSTED_AMOUNT,
        PAYEE_NAME,
        PAYEE_ID,
        BFC_CODE,
    ]


def generate_check_response_files():
    logging.init(__name__)

    logger.info("Generating check response files.")

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder
    count = args.count

    payments: List[Payment] = []
    for _ in range(count):
        pub_eft = PubEftFactory.create()
        payment = PaymentFactory.create(pub_eft=pub_eft)
        check = PaymentCheck(check_number=randint(1, 100000))
        payment.check = check
        payments.append(payment)

    paid_ftp_scenario: List[CheckResponseData] = generate_paid_ftp_data(
        scenario_descriptor=ScenarioDescriptor(
            scenario_name=ScenarioName.HAPPY_PATH_CHECK_RESPONSE_PAID_FTP
        ),
        payments=payments,
    )

    outstanding_ftp_scenario: List[CheckResponseData] = generate_outstanding_ftp_data(
        scenario_descriptor=ScenarioDescriptor(
            scenario_name=ScenarioName.HAPPY_PATH_CHECK_RESPONSE_OUTSTANDING_FTP
        ),
        payments=payments,
    )

    # generate Paid FTP File
    file_name = "Paid FTP"
    csv_header = Constants.PAID_FTP_CSV_HEADER
    generate_check_response_file(paid_ftp_scenario, csv_header, file_name, folder_path)

    # generate Outstanding FTP File
    file_name = "Outstanding FTP"
    csv_header = Constants.OUTSTANDING_FTP_CSV_HEADER
    generate_check_response_file(outstanding_ftp_scenario, csv_header, file_name, folder_path)

    logger.info("Done generating check response files.")


def generate_paid_ftp_data(
    scenario_descriptor: ScenarioDescriptor, payments: List[Payment],
) -> List[CheckResponseData]:
    check_response_data: List[CheckResponseData] = []

    for payment in payments:
        check_response_data.append(
            CheckResponseData(
                begin_date=str(payment.period_start_date.strftime("%m/%d/%Y"))
                if payment.period_start_date
                else None,
                end_date=str(payment.period_end_date.strftime("%m/%d/%Y"))
                if payment.period_end_date
                else None,
                trc_number=randint(100000000, 999999999),
                account_name=str(payment.pub_eft.bank_account_type.bank_account_type_description),
                account_number=str(payment.pub_eft.account_nbr),
                account_type=payment.pub_eft.bank_account_type.bank_account_type_description,
                bank_name="PEOPLES UNITED BANK",
                type="Debits",
                type_detail="Check",
                bfc_code="CLMNT",
                payee_id=payment.claim.employee.employee_id,
                check_number=payment.check.check_number,
                payee_name=_format_employee_name_for_ez_check(payment.claim.employee),
                posted_amount=payment.amount,
                posted_date=str(payment.payment_date.strftime("%m/%d/%Y"))
                if payment.payment_date
                else None,
            )
        )

    return check_response_data


def generate_outstanding_ftp_data(
    scenario_descriptor: ScenarioDescriptor, payments: List[Payment],
) -> List[CheckResponseData]:
    check_response_data: List[CheckResponseData] = []
    for payment in payments:
        check_response_data.append(
            CheckResponseData(
                begin_date=str(payment.period_start_date.strftime("%m/%d/%Y"))
                if payment.period_start_date
                else None,
                end_date=str(payment.period_end_date.strftime("%m/%d/%Y"))
                if payment.period_end_date
                else None,
                trc_number=randint(100000000, 999999999),
                bank_name="PEOPLES UNITED BANK",
                account_name=payment.pub_eft.bank_account_type.bank_account_type_description,
                account_number=payment.pub_eft.account_nbr,
                account_type=payment.pub_eft.bank_account_type.bank_account_type_description,
                type="Outstanding",
                type_detail="Outstanding",
                bfc_code="CLMNT",
                payee_id=payment.claim.employee.employee_id,
                check_number=payment.check.check_number,
                payee_name=_format_employee_name_for_ez_check(payment.claim.employee),
                issued_amount=payment.amount,
                issued_date=str(payment.payment_date.strftime("%m/%d/%Y"))
                if payment.payment_date
                else None,
            )
        )

    return check_response_data


def generate_check_response_file(
    check_response_data: List[CheckResponseData],
    csv_header: List[str],
    file_name: str,
    folder_path: str,
) -> List[CheckResponseData]:
    check_response_data_set: List[Dict] = []

    for d in check_response_data:
        _data = asdict(d)
        data = {}
        for key, value in _data.items():
            k = key.replace("_", " ").title()
            if value is not None and k in csv_header:
                data[k] = value

        check_response_data_set.append(data)

    create_csv_from_list(
        data=check_response_data_set,
        fieldnames=csv_header,
        file_name=file_name,
        folder_path=Path(folder_path),
    )

    return check_response_data
