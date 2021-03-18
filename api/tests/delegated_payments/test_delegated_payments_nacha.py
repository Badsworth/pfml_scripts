import decimal
import os
from datetime import datetime
from typing import List

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import ClaimType, Payment, PaymentMethod, State
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
)
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    create_nacha_file,
    upload_nacha_file_to_s3,
)
from massgov.pfml.delegated_payments.util.ach.nacha import NachaBatch, NachaEntry, NachaFile
from tests.helpers.state_log import AdditionalParams, setup_state_log

# every test in here requires real resources
pytestmark = pytest.mark.integration


def get_payment(
    fineos_absence_id: str,
    claim_type_id: int,
    ctr_vendor_code: str,
    amount: decimal.Decimal,
    payment_date: datetime.date,
    start_date: datetime.date,
    end_date: datetime.date,
    payment_method_id: int,
    fineos_pei_i_value: str,
) -> Payment:
    employee = EmployeeFactory(
        ctr_vendor_customer_code=ctr_vendor_code, payment_method_id=payment_method_id
    )
    employer = EmployerFactory()

    return PaymentFactory(
        payment_date=payment_date,
        period_start_date=start_date,
        period_end_date=end_date,
        amount=amount,
        fineos_pei_i_value=fineos_pei_i_value,
        claim=ClaimFactory(
            employee=employee,
            employer_id=employer.employer_id,
            claim_type_id=claim_type_id,
            fineos_absence_id=fineos_absence_id,
        ),
    )


def get_payments() -> List[Payment]:
    return [
        get_payment(
            fineos_absence_id="NTN-1234-ABS-01",
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            ctr_vendor_code="abc1234",
            amount=decimal.Decimal("1200.00"),
            payment_date=datetime(2020, 7, 1).date(),
            start_date=datetime(2020, 8, 1).date(),
            end_date=datetime(2020, 12, 1).date(),
            payment_method_id=PaymentMethod.CHECK.payment_method_id,
            fineos_pei_i_value="1",
        ),
        get_payment(
            fineos_absence_id="NTN-1234-ABS-02",
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            ctr_vendor_code="12345678",
            amount=decimal.Decimal("1300.00"),
            payment_date=datetime(2020, 1, 15).date(),
            start_date=datetime(2020, 2, 15).date(),
            end_date=datetime(2020, 4, 15).date(),
            payment_method_id=PaymentMethod.ACH.payment_method_id,
            fineos_pei_i_value="2",
        ),
    ]


def create_add_to_pub_state_log_for_payment(payment: Payment, db_session: db.Session) -> None:
    state_log_util.create_finished_state_log(
        end_state=State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=db_session,
    )


def test_copy_nacha_files_to_s3(
    initialize_factories_session, test_db_session, mock_s3_bucket, monkeypatch
):
    s3_bucket_uri = f"s3://{mock_s3_bucket}"
    source_directory_path = "payments/pub/outbound"
    test_pub_outbound_path = os.path.join(s3_bucket_uri, source_directory_path)

    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("PFML_PUB_OUTBOUND_PATH", test_pub_outbound_path)

    additional_params = AdditionalParams()
    additional_params.add_eft = True

    setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_states=[State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT],
        test_db_session=test_db_session,
        additional_params=additional_params,
    )

    real_nacha_file = create_nacha_file(test_db_session)
    real_filepath = upload_nacha_file_to_s3(test_db_session, real_nacha_file)

    formatted_now = payments_util.get_now().strftime("%Y%m%d")
    path = os.path.join(s3_bucket_uri, source_directory_path, f"ready/PUB-NACHA-{formatted_now}")

    assert real_filepath == path


def test_name_truncation(monkeypatch):
    entry = NachaEntry(
        receiving_dfi_id="23138010",
        dfi_act_num="122424",
        amount=123.00,
        id="1224asdfgasdf",
        name="Johnathan Smith-Westfield Westinghouse III",
    )

    assert entry.get_value("name") == "Johnathan Smith-Westfi"


@freeze_time("2021-03-17 21:58:00")
def test_generate_nacha_file(monkeypatch, test_db_session):
    effective_date = datetime.now()
    today = datetime.today()

    file = NachaFile()
    batch = NachaBatch(effective_date, today)

    entry = NachaEntry(
        receiving_dfi_id="231380104",
        dfi_act_num="122424",
        amount=123.00,
        id="1224asdfgasdf",
        name="John Smith",
    )

    entry2 = NachaEntry(
        receiving_dfi_id="231380104",
        dfi_act_num="122425",
        amount=129.00,
        id="1224asdfgas23r",
        name="John Smith12",
    )

    batch.add_entry(entry)
    batch.add_entry(entry2)

    file.add_batch(batch)

    ach_output = file.to_bytes()

    expected_output = open(
        os.path.join(os.path.dirname(__file__), "test_files", "expected_payments.ach"), "rb"
    ).read()

    assert ach_output == expected_output


@pytest.mark.integration
def test_build_nacha_files_raise_error_no_payments_error(
    initialize_factories_session, test_db_session, mock_s3_bucket
):
    # The only eligible payment will raise an error.
    payments = get_payments()
    invalid_payment_record = payments[0]
    invalid_payment_record.amount = decimal.Decimal("00.00")
    create_add_to_pub_state_log_for_payment(invalid_payment_record, test_db_session)

    with pytest.raises(Exception):
        create_nacha_file(test_db_session)
