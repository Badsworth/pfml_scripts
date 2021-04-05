import os
from typing import Tuple

import pytest
from freezegun import freeze_time

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    ClaimType,
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
from massgov.pfml.delegated_payments.audit.mock.pub_outbound_file_generator import (
    generate_pub_return,
)
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    NachaBatchType,
    add_eft_prenote_to_nacha_file,
    add_payments_to_nacha_file,
    create_nacha_batch,
    create_nacha_file,
    upload_nacha_file_to_s3,
)
from massgov.pfml.delegated_payments.util.ach.nacha import NachaEntry, NachaFile


def test_name_truncation(monkeypatch):
    entry = NachaEntry(
        trans_code="22",
        receiving_dfi_id="23138010",
        dfi_act_num="122424",
        amount=123.00,
        id="1224asdfgasdf",
        name="Smith-Westfield Johnathan",
    )

    assert entry.get_value("name") == "Smith-Westfield Johnat"


@freeze_time("2021-03-17 21:58:00")
def test_generate_nacha_file(monkeypatch, test_db_session):
    file = NachaFile()
    batch = create_nacha_batch(NachaBatchType.MEDICAL_LEAVE)

    entry = NachaEntry(
        trans_code="22",
        receiving_dfi_id="231380104",
        dfi_act_num="122424",
        amount=123.00,
        id="1224asdfgasdf",
        name="Smith John",
    )

    entry2 = NachaEntry(
        trans_code="22",
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


@freeze_time("2021-03-17 21:58:00")
def test_generate_nacha_file_multiple_batches(monkeypatch, test_db_session):
    file = NachaFile()
    batch1 = create_nacha_batch(NachaBatchType.MEDICAL_LEAVE)
    batch2 = create_nacha_batch(NachaBatchType.FAMILY_LEAVE)

    entry = NachaEntry(
        trans_code="22",
        receiving_dfi_id="231380104",
        dfi_act_num="122424",
        amount=123.00,
        id="1224asdfgasdf",
        name="Smith John",
    )

    entry2 = NachaEntry(
        trans_code="22",
        receiving_dfi_id="231380104",
        dfi_act_num="122425",
        amount=129.00,
        id="1224asdfgas23r",
        name="Smith John",
    )

    batch1.add_entry(entry)
    batch2.add_entry(entry2)
    file.add_batch(batch1)
    file.add_batch(batch2)

    ach_output = file.to_bytes()

    expected_output = open(
        os.path.join(os.path.dirname(__file__), "test_files", "expected_payments_multi_batch.ach"),
        "rb",
    ).read()

    assert ach_output == expected_output


def test_nacha_file_prenote_entries():
    nacha_file = create_nacha_file()

    employees_with_eft = []
    for _ in range(5):
        employees_with_eft.append(build_employee_with_eft(PrenoteState.PENDING_PRE_PUB))

    add_eft_prenote_to_nacha_file(nacha_file, employees_with_eft)

    assert len(nacha_file.batches[0].entries) == 5


def test_nacha_file_prenote_entries_errors():
    nacha_file = create_nacha_file()

    employee_with_eft = build_employee_with_eft(PrenoteState.APPROVED)

    with pytest.raises(
        Exception,
        match=f"Found non pending eft trying to add to prenote list: {employee_with_eft[0].employee_id}, eft: {employee_with_eft[1].pub_eft_id}",
    ):
        add_eft_prenote_to_nacha_file(nacha_file, [employee_with_eft])


def test_nacha_file_payment_entries():
    nacha_file = create_nacha_file()

    payments = []
    for _ in range(5):
        payments.append(build_payment(PaymentMethod.ACH, ClaimType.FAMILY_LEAVE))
    for _ in range(5):
        payments.append(build_payment(PaymentMethod.ACH, ClaimType.MEDICAL_LEAVE))

    add_payments_to_nacha_file(nacha_file, payments)

    assert len(nacha_file.batches) == 2
    assert len(nacha_file.batches[0].entries) == 5
    assert len(nacha_file.batches[1].entries) == 5


def test_nacha_file_payment_entries_one_leave_type():
    # Same as above, but only one leave type, only one batch should be added.
    nacha_file = create_nacha_file()

    payments = []
    for _ in range(5):
        payments.append(build_payment(PaymentMethod.ACH, ClaimType.FAMILY_LEAVE))

    add_payments_to_nacha_file(nacha_file, payments)
    assert len(nacha_file.batches[0].entries) == 5


def test_nacha_file_payment_and_prenote_entries():
    nacha_file = create_nacha_file()
    payments = []
    for _ in range(5):
        payments.append(build_payment(PaymentMethod.ACH, ClaimType.FAMILY_LEAVE))
    for _ in range(5):
        payments.append(build_payment(PaymentMethod.ACH, ClaimType.MEDICAL_LEAVE))

    employees_with_eft = []
    for _ in range(7):
        employees_with_eft.append(build_employee_with_eft(PrenoteState.PENDING_PRE_PUB))

    # Add all payments and EFT
    add_payments_to_nacha_file(nacha_file, payments)
    add_eft_prenote_to_nacha_file(nacha_file, employees_with_eft)

    assert len(nacha_file.batches) == 2
    assert len(nacha_file.batches[0].entries) == 12
    assert len(nacha_file.batches[1].entries) == 5


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

    employee_with_eft = build_employee_with_eft(PrenoteState.PENDING_PRE_PUB)
    add_eft_prenote_to_nacha_file(nacha_file, [employee_with_eft])

    payment = build_payment(PaymentMethod.ACH)
    add_payments_to_nacha_file(nacha_file, [payment])

    folder_path = str(tmp_path)
    nacha_file_name = "PUB-NACHA-20210315"
    file_path = os.path.join(folder_path, nacha_file_name)

    upload_nacha_file_to_s3(nacha_file, file_path)

    assert nacha_file_name in file_util.list_files(folder_path)


def build_employee_with_eft(prenote_state: LkPrenoteState) -> Tuple[Employee, PubEft]:
    employee = EmployeeFactory.build()
    pub_eft = PubEftFactory.build(prenote_state_id=prenote_state.prenote_state_id)
    EmployeePubEftPairFactory.build(employee=employee, pub_eft=pub_eft)

    return (employee, pub_eft)


def build_payment(payment_method: LkPaymentMethod, claim_type: ClaimType = ClaimType.FAMILY_LEAVE):
    employee_with_eft = build_employee_with_eft(PrenoteState.PENDING_PRE_PUB)
    employee = employee_with_eft[0]
    pub_eft = employee_with_eft[1]

    claim = ClaimFactory.build(employee=employee, claim_type_id=claim_type.claim_type_id)
    payment = PaymentFactory.build(
        claim=claim, pub_eft=pub_eft, disb_method_id=payment_method.payment_method_id
    )
    return payment


def test_generate_eft_response(initialize_factories_session, test_db_session, tmp_path):

    prenote_scenario_data, ach_scenario_data = generate_pub_return(test_db_session, tmp_path)

    # TODO: read and parse NACHA file, compare to scenarios

    # assert False
    # generated_nacha_file.to_bytes()
