import os
from datetime import datetime
from typing import Tuple

import pytest
from freezegun import freeze_time

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Employee,
    LkPaymentMethod,
    LkPrenoteState,
    PaymentMethod,
    PrenoteState,
    PubEft,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    PaymentFactory,
    PubEftFactory,
)
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    add_eft_prenote_to_nacha_file,
    add_payments_to_nacha_file,
    create_nacha_file,
    upload_nacha_file_to_s3,
)
from massgov.pfml.delegated_payments.util.ach.nacha import NachaBatch, NachaEntry, NachaFile


def test_name_truncation(monkeypatch):
    entry = NachaEntry(
        receiving_dfi_id="23138010",
        dfi_act_num="122424",
        amount=123.00,
        id="1224asdfgasdf",
        name="Smith-Westfield Johnathan",
    )

    assert entry.get_value("name") == "Smith-Westfield Johnat"


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
        name="Smith John",
    )

    entry2 = NachaEntry(
        receiving_dfi_id="231380104",
        dfi_act_num="122425",
        amount=129.00,
        id="1224asdfgas23r",
        name="Smith John",
    )

    batch.add_entry(entry)
    batch.add_entry(entry2)

    file.add_batch(batch)

    ach_output = file.to_bytes()

    expected_output = open(
        os.path.join(os.path.dirname(__file__), "test_files", "expected_payments.ach"), "rb"
    ).read()

    assert ach_output == expected_output


def test_nacha_file_prenote_entries():
    nacha_file = create_nacha_file()

    employees_with_eft = []
    for _ in range(5):
        employees_with_eft.append(
            build_employee_with_eft(PaymentMethod.ACH, PrenoteState.PENDING_PRE_PUB)
        )

    add_eft_prenote_to_nacha_file(nacha_file, employees_with_eft)

    assert len(nacha_file.batches[0].entries) == 5


def test_nacha_file_prenote_entries_errors():
    nacha_file = create_nacha_file()

    employee_with_eft = build_employee_with_eft(PaymentMethod.ACH, PrenoteState.APPROVED)

    with pytest.raises(
        Exception,
        match=f"Found non pending eft trying to add to prenote list: {employee_with_eft[0].employee_id}, eft: {employee_with_eft[1].pub_eft_id}",
    ):
        add_eft_prenote_to_nacha_file(nacha_file, [employee_with_eft])


def test_nacha_file_payment_entries():
    nacha_file = create_nacha_file()

    payments = []
    for _ in range(5):
        payments.append(build_payment(PaymentMethod.ACH))

    add_payments_to_nacha_file(nacha_file, payments)

    assert len(nacha_file.batches[0].entries) == 5


# TODO check payment method https://lwd.atlassian.net/browse/PUB-106
# def test_nacha_file_payment_entries_errors():
#     valid_payment = build_payment(PaymentMethod.ACH)
#     invalid_payment_record = build_payment(PaymentMethod.CHECK)

#     payments = [valid_payment, invalid_payment_record]

#     nacha_file = create_nacha_file()

#     with pytest.raises(
#         Exception,
#         match=f"Non-ACH payment method for payment: {invalid_payment_record.payment_id}",
#     ):
#         add_payments_to_nacha_file(nacha_file, payments)


# TODO After PUB-40 and PUB-42 are complete
# parse and validate and contents of generated nacha file for ach and pre note fields


def test_nacha_file_upload(tmp_path):
    nacha_file = create_nacha_file()

    employee_with_eft = build_employee_with_eft(PaymentMethod.ACH, PrenoteState.PENDING_PRE_PUB)
    add_eft_prenote_to_nacha_file(nacha_file, [employee_with_eft])

    payment = build_payment(PaymentMethod.ACH)
    add_payments_to_nacha_file(nacha_file, [payment])

    folder_path = str(tmp_path)
    nacha_file_name = "PUB-NACHA-20210315"
    file_path = os.path.join(folder_path, nacha_file_name)

    upload_nacha_file_to_s3(nacha_file, file_path)

    assert nacha_file_name in file_util.list_files(folder_path)


def build_employee_with_eft(
    payment_method: LkPaymentMethod, prenote_state: LkPrenoteState
) -> Tuple[Employee, PubEft]:
    employee = EmployeeFactory.build(payment_method_id=payment_method.payment_method_id)
    pub_eft = PubEftFactory.build(prenote_state_id=prenote_state.prenote_state_id)
    EmployeePubEftPairFactory.build(employee=employee, pub_eft=pub_eft)

    return (employee, pub_eft)


def build_payment(payment_method: LkPaymentMethod):
    employee_with_eft = build_employee_with_eft(payment_method, PrenoteState.PENDING_PRE_PUB)
    employee = employee_with_eft[0]
    pub_eft = employee_with_eft[1]

    claim = ClaimFactory.build(employee=employee)
    payment = PaymentFactory.build(claim=claim, pub_eft=pub_eft)
    return payment
