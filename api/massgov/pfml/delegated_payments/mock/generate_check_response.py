import argparse
import datetime
from dataclasses import asdict, dataclass
from random import randint
from typing import List, Optional, Union

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.delegated_payments.mock.scenario_data_generator import ScenarioData
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
    trc_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    account_name: Optional[str] = None
    check_number: Optional[str] = None
    payee_name: Optional[str] = None
    payee_id: Optional[str] = None
    bfc_code: Optional[str] = None


@dataclass
class PaidCheckResponseData(CheckResponseData):
    response_type: Optional[str] = None
    type_detail: Optional[str] = None
    posted_date: Optional[str] = None
    posted_amount: Optional[str] = None


@dataclass
class OutstandingCheckResponseData(CheckResponseData):
    response_type: Optional[str] = None
    type_detail: Optional[str] = None
    issued_date: Optional[str] = None
    issued_amount: Optional[str] = None


CHECK_RESPONSE_DATA_FIELDS = CheckResponseData(
    begin_date="Begin Date",
    end_date="End Date",
    trc_number="TRC Number",
    account_name="Bank Name",
    account_number="Account Number",
    account_type="Account Type",
    bank_name="Account Name",
    bfc_code="BCF Code",
    payee_id="Payee ID",
    check_number="Check Number",
    payee_name="Payee Name",
)

PAID_CHECK_RESPONSE_DATA_FIELDS = PaidCheckResponseData(
    response_type="Type",
    type_detail="Type Detail",
    posted_amount="Posted Amount",
    posted_date="Posted Date",
    **asdict(CHECK_RESPONSE_DATA_FIELDS),
)

OUTSTANDING_CHECK_RESPONSE_DATA_FIELDS = OutstandingCheckResponseData(
    response_type="Type",
    type_detail="Type Detail",
    issued_amount="Issued Amount",
    issued_date="Issued Date",
    **asdict(CHECK_RESPONSE_DATA_FIELDS),
)


class PubCheckResponseGenerator:
    def __init__(self, scenario_dataset: List[ScenarioData], folder_path: str):
        self.scenario_dataset = scenario_dataset
        self.folder_path = folder_path

        self.paid_checks: List[PaidCheckResponseData] = []
        self.outstanding_checks: List[OutstandingCheckResponseData] = []

    def run(self):
        for scenario_data in self.scenario_dataset:
            if scenario_data.scenario_descriptor.payment_method != PaymentMethod.CHECK:
                logger.info("Skipping non check payments")
                continue

            if not scenario_data.scenario_descriptor.pub_check_response:
                logger.warning("Skipping response for check payment")
                continue

            try:
                self.add_check_response_entry(scenario_data)
            except Exception:
                logger.exception(
                    f"Error generating response for scenario: {scenario_data.scenario_descriptor.scenario_name}"
                )

        self.write_files()

    def add_check_response_entry(self, scenario_data: ScenarioData) -> None:
        scenario_descriptor = scenario_data.scenario_descriptor
        payment = scenario_data.payment
        employee = scenario_data.employee

        if payment is None:
            logger.warning(
                "Skipping return because payment is emptry on data for scenario: %s",
                scenario_descriptor.scenario_name,
            )
            return

        # scenario specific
        if (
            scenario_descriptor.pub_check_paid_response
            and scenario_descriptor.pub_check_outstanding_response
        ):
            raise Exception("Invalid check response scenario")

        check_number = (
            "0"
            if scenario_descriptor.pub_check_return_invalid_check_number
            else str(payment.check.check_number)
        )

        check_response_data_common = CheckResponseData(
            begin_date=str(payment.period_start_date.strftime("%m/%d/%Y"))
            if payment.period_start_date
            else None,
            end_date=str(payment.period_end_date.strftime("%m/%d/%Y"))
            if payment.period_end_date
            else None,
            trc_number=str(randint(100000000, 999999999)),
            account_name="Payee Account",
            account_number="123456789",
            account_type="Checking",
            bank_name="PEOPLES UNITED BANK",
            bfc_code="CLMNT",
            payee_id=employee.employee_id,
            check_number=check_number,
            payee_name=_format_employee_name_for_ez_check(employee),
        )

        response_date = (
            payment.payment_date + datetime.timedelta(days=10) if payment.payment_date else None
        )

        if scenario_descriptor.pub_check_paid_response:
            paid_entry = PaidCheckResponseData(
                response_type="Debits",
                type_detail="Check",
                posted_amount=str(payment.amount),
                posted_date=str(response_date.strftime("%m/%d/%Y")) if response_date else None,
                **asdict(check_response_data_common),
            )
            self.paid_checks.append(paid_entry)

        if scenario_descriptor.pub_check_outstanding_response:
            outstanding_entry = OutstandingCheckResponseData(
                response_type="Outstanding",
                type_detail=scenario_descriptor.pub_check_outstanding_response_status.value,
                issued_amount=str(payment.amount),
                issued_date=str(response_date.strftime("%m/%d/%Y")) if response_date else None,
                **asdict(check_response_data_common),
            )
            self.outstanding_checks.append(outstanding_entry)

    def write_files(self) -> None:
        if len(self.paid_checks) > 0:
            self.write_csv(
                self.paid_checks,
                PAID_CHECK_RESPONSE_DATA_FIELDS,
                f"Paid-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}",
            )

        if len(self.outstanding_checks) > 0:
            self.write_csv(
                self.outstanding_checks,
                OUTSTANDING_CHECK_RESPONSE_DATA_FIELDS,
                f"Outstanding-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}",
            )

    def write_csv(
        self,
        entries_list: Union[List[PaidCheckResponseData], List[OutstandingCheckResponseData]],
        fieldnames: Union[PaidCheckResponseData, OutstandingCheckResponseData],
        file_name: str,
    ) -> None:
        fieldname_by_key = {key: value for key, value in asdict(fieldnames).items()}

        response_csv_data = []
        for entry in entries_list:
            _data = asdict(entry)

            data = {}
            for key, value in _data.items():
                fieldname = fieldname_by_key.get(key, None)
                if fieldname:
                    data[fieldname] = value

            response_csv_data.append(data)

        create_csv_from_list(
            data=response_csv_data,
            fieldnames=asdict(fieldnames).values(),
            file_name=file_name,
            folder_path=self.folder_path,
        )
