#
# Tests for massgov.pfml.payments.manual.payment_voucher.
#

import datetime
import os.path
import random
import re

import freezegun
import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import State, TaxIdentifier
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.payments import fineos_payment_export, fineos_vendor_export
from massgov.pfml.payments.manual import payment_voucher
from tests.helpers.state_log import AdditionalParams, setup_state_log

# every test in here requires real resources
pytestmark = pytest.mark.integration

test_ci_index = fineos_payment_export.CiIndex(c="7326", i="249")
test_pei_csv_row = {
    "C": "7326",
    "I": "249",
    "LASTUPDATEDATE": "2021-01-15 19:18:35",
    "C_OSUSER_UPDATEDBY": "1000",
    "I_OSUSER_UPDATEDBY": "15",
    "ADDRESSLINE1": "47 Washington St",
    "ADDRESSLINE2": "",
    "ADDRESSLINE3": "",
    "ADDRESSLINE4": "Quincy",
    "ADDRESSLINE5": "",
    "ADDRESSLINE6": "MA",
    "ADDRESSLINE7": "",
    "ADVICETOPAY": "true",
    "ADVICETOPAYOV": "Unknown",
    "AMALGAMATIONC": "Fully Certified",
    "AMOUNT_MONAMT": "1600.18",
    "AMOUNT_MONCUR": "33600000",
    "CHECKCUTTING": "Non Check Cutting",
    "CONFIRMEDBYUS": "GeneratePayments1Process",
    "CONFIRMEDUID": "GENERATEPAYMENTS1PROCESS",
    "CONTRACTREF": "",
    "CORRESPCOUNTR": "USA",
    "CURRENCY": "---",
    "DATEINTERFACE": "2021-01-16 23:59:59",
    "DESCRIPTION": "",
    "EMPLOYEECONTR": "100",
    "EVENTEFFECTIV": "2021-01-16 00:00:00",
    "EVENTREASON": "Automatic Main Payment",
    "EVENTTYPE": "PaymentOut",
    "EXTRACTIONDAT": "",
    "GROSSPAYMENTA_MONAMT": "1600.18",
    "GROSSPAYMENTA_MONCUR": "33600000",
    "INSUREDRESIDE": "Unknown",
    "NAMETOPRINTON": "",
    "NOMINATEDPAYE": "Unknown",
    "NOMPAYEECUSTO": "",
    "NOMPAYEEDOB": "",
    "NOMPAYEEFULLN": "",
    "NOMPAYEESOCNU": "",
    "NOTES": "",
    "PAYEEACCOUNTN": "",
    "PAYEEACCOUNTT": "",
    "PAYEEADDRESS": "47 Washington St\nQuincy\nMA\n02169",
    "PAYEEBANKBRAN": "",
    "PAYEEBANKCODE": "",
    "PAYEEBANKINST": "",
    "PAYEEBANKSORT": "",
    "PAYEECORRESPO": "MA",
    "PAYEECUSTOMER": "2629401",
    "PAYEEDOB": "1974-03-15 00:00:00",
    "PAYEEFULLNAME": "Grady Bednar",
    "PAYEEIDENTIFI": "ID",
    "PAYEESOCNUMBE": "999004400",
    "PAYMENTADD": "47 Washington St\nQuincy\nMA\n02169",
    "PAYMENTADD1": "47 Washington St",
    "PAYMENTADD2": "",
    "PAYMENTADD3": "",
    "PAYMENTADD4": "Quincy",
    "PAYMENTADD5": "",
    "PAYMENTADD6": "MA",
    "PAYMENTADD7": "",
    "PAYMENTADDCOU": "USA",
    "PAYMENTCORRST": "MA",
    "PAYMENTDATE": "2021-01-19 00:00:00",
    "PAYMENTFREQUE": "Weekly",
    "PAYMENTMETHOD": "Check",
    "PAYMENTPOSTCO": "02169",
    "PAYMENTPREMIS": "",
    "PAYMENTTRIGGE": "2021-01-16 23:59:59",
    "PAYMENTTYPE": "Recurring",
    "PAYMETHCURREN": "---",
    "POSTCODE": "02169",
    "PREMISESNO": "",
    "SETUPBYUSERID": "GENERATEPAYMENTS1PROCESS",
    "SETUPBYUSERNA": "GeneratePayments1Process",
    "STATUS": "PendingActive",
    "STATUSEFFECTI": "2021-01-16 23:59:59",
    "STATUSREASON": "Standard",
    "STOCKNO": "",
    "SUMMARYEFFECT": "2021-01-15 19:18:34",
    "SUMMARYSTATUS": "PendingActive",
    "TRANSSTATUSDA": "2021-01-16 23:59:59",
}
test_claim_details_csv_row = {
    "C": "7733",
    "I": "249",
    "LASTUPDATEDATE": "2021-01-15 19:18:35",
    "C_OSUSER_UPDATEDBY": "1000",
    "I_OSUSER_UPDATEDBY": "15",
    "ABSENCECASENU": "NTN-308848-ABS-01",
    "BENEFITRIGHTT": "Absence Benefit",
    "CLAIMANTAGE": "0",
    "CLAIMANTCUSTO": "",
    "CLAIMANTDOB": "",
    "CLAIMANTGENDE": "",
    "CLAIMANTNAME": "",
    "CLAIMANTRELTO": "",
    "CLAIMNUMBER": "PL ABS-308849",
    "DIAGCODE2": "",
    "DIAGCODE3": "",
    "DIAGCODE4": "",
    "DIAGCODE5": "",
    "EMPLOYEEID": "",
    "EVENTCAUSE": "Unknown",
    "INCURREDDATE": "2021-01-01 00:00:00",
    "INSUREDADDRES": "47 Washington St\nQuincy\nMA\n02169",
    "INSUREDADDRL1": "47 Washington St",
    "INSUREDADDRL2": "",
    "INSUREDADDRL3": "",
    "INSUREDADDRL4": "Quincy",
    "INSUREDADDRL5": "",
    "INSUREDADDRL6": "MA",
    "INSUREDADDRL7": "",
    "INSUREDAGE": "46",
    "INSUREDCORCOU": "USA",
    "INSUREDCORRES": "MA",
    "INSUREDCUSTOM": "2629401",
    "INSUREDDOB": "1974-03-15 00:00:00",
    "INSUREDEMPLOY": "",
    "INSUREDFULLNA": "Grady Bednar",
    "INSUREDGENDER": "Unknown",
    "INSUREDPOSTCO": "02169",
    "INSUREDPREMIS": "",
    "INSUREDRETIRE": "0",
    "INSUREDSOCNUM": "999004400",
    "LEAVEPLANID": "F5626",
    "LEAVEREQUESTI": "5456",
    "NOTIFIEDDATE": "2021-01-14 12:29:38",
    "PAYEEAGEATINC": "46",
    "PAYEECASEROLE": "Employee",
    "PAYEERELTOINS": "Unknown",
    "PRIMARYDIAGNO": "",
    "PRIMARYMEDICA": "70144000",
    "DIAG2MEDICALC": "70144000",
    "DIAG3MEDICALC": "70144000",
    "DIAG4MEDICALC": "70144000",
    "DIAG5MEDICALC": "70144000",
    "PECLASSID": "7326",
    "PEINDEXID": "249",
    "DATEINTERFACE": "2021-01-16 23:59:59",
}
test_payment_details_csv_row = {
    "C": "7806",
    "I": "401",
    "LASTUPDATEDATE": "2021-01-15 19:18:35",
    "C_OSUSER_UPDATEDBY": "1000",
    "I_OSUSER_UPDATEDBY": "15",
    "BENEFITEFFECT": "2021-01-08 00:00:00",
    "BENEFITFINALP": "2021-02-01 00:00:00",
    "DESCRIPTION_PAYMENTDTLS": "Unknown",
    "PAYMENTENDPER": "2021-01-21 00:00:00",
    "PAYMENTSTARTP": "2021-01-15 00:00:00",
    "BALANCINGAMOU_MONAMT": "800.09",
    "BALANCINGAMOU_MONCUR": "33600000",
    "BUSINESSNETBE_MONAMT": "800.09",
    "BUSINESSNETBE_MONCUR": "33600000",
    "DUETYPE": "ScheduledMain",
    "GROUPID": "",
    "PECLASSID": "7326",
    "PEINDEXID": "249",
    "CLAIMDETAILSCLASSID": "7733",
    "CLAIMDETAILSINDEXID": "249",
    "DATEINTERFACE": "2021-01-16 23:59:59",
}
test_requested_absence_som_csv_row = {
    "NOTIFICATION_CASENUMBER": "NTN-308848",
    "ABSENCE_CASENUMBER": "NTN-308848-ABS-01",
    "ABSENCE_CASETYPENAME": "Absence Case",
    "ABSENCE_CASESTATUS": "Approved",
    "ABSENCE_CASEOWNER": "SaviLinx",
    "ABSENCE_CASECREATIONDATE": "2021-01-14 12:29:38",
    "ABSENCE_CASELASTUPDATEDATE": "2021-01-14 12:30:07",
    "ABSENCE_INTAKESOURCE": "Self-Service",
    "ABSENCE_NOTIFIEDBY": "Employee",
    "EMPLOYEE_CUSTOMERNO": "2629401",
    "EMPLOYEE_MANAGER_CUSTOMERNO": "",
    "EMPLOYEE_ADDTL_MNGR_CUSTOMERNO": "",
    "EMPLOYER_CUSTOMERNO": "2626107",
    "EMPLOYER_NAME": "Revolutionary Empower Schemas Inc",
    "EMPLOYMENT_CLASSID": "14453",
    "EMPLOYMENT_INDEXID": "2357482",
    "LEAVEREQUEST_ID": "5456",
    "LEAVEREQUEST_NOTIFICATIONDATE": "2021-01-14 12:29:38",
    "LEAVEREQUEST_LASTUPDATEDATE": "2021-01-14 12:30:07",
    "LEAVEREQUEST_ORIGINALREQUEST": "1",
    "LEAVEREQUEST_EVIDENCERESULTTYPE": "Satisfied",
    "LEAVEREQUEST_DECISION": "Approved",
    "LEAVEREQUEST_DIAGNOSIS": "",
    "ABSENCEREASON_CLASSID": "14412",
    "ABSENCEREASON_INDEXID": "19",
    "ABSENCEREASON_NAME": "Serious Health Condition - Employee",
    "ABSENCEREASON_QUALIFIER1": "Not Work Related",
    "ABSENCEREASON_QUALIFIER2": "Sickness",
    "ABSENCEREASON_COVERAGE": "Employee",
    "PRIMARY_RELATIONSHIP_NAME": "",
    "PRIMARY_RELATIONSHIP_QUAL1": "",
    "PRIMARY_RELATIONSHIP_QUAL2": "",
    "PRIMARY_RELATIONSHIP_COVER": "Please Select",
    "SECONDARY_RELATIONSHIP_NAME": "",
    "SECONDARY_RELATIONSHIP_QUAL1": "",
    "SECONDARY_RELATIONSHIP_QUAL2": "",
    "SECONDARY_RELATIONSHIP_COVER": "Please Select",
    "ABSENCEPERIOD_CLASSID": "14449",
    "ABSENCEPERIOD_INDEXID": "9477",
    "ABSENCEPERIOD_TYPE": "Time off period",
    "ABSENCEPERIOD_STATUS": "Known",
    "ABSENCEPERIOD_START": "2021-01-01 00:00:00",
    "ABSENCEPERIOD_END": "2021-02-01 00:00:00",
    "EPISODE_FREQUENCY_COUNT": "",
    "EPISODE_FREQUENCY_PERIOD": "",
    "EPISODIC_FREQUENCY_PERIOD_UNIT": "Please Select",
    "EPISODE_DURATION": "",
    "EPISODIC_DURATION_UNIT": "Please Select",
}

test_vbi_requested_absence_csv_row = {
    "ABSENCE_CASENUMBER": "NTN-308848-ABS-01",
    "LEAVEREQUEST_ID": "1234",
    "LEAVEREQUEST_DECISION": "Pending",
}


class MockCSVWriter:
    def __init__(self):
        self.rows = []

    def writerow(self, row):
        self.rows.append(row)


class MockLogEntry:
    def set_metrics(self, **metrics):
        pass

    def increment(self, metric):
        pass


def setup_standard_test_data(
    test_db_session,
    *,
    ci_index=None,
    pei_csv_row=None,
    claim_details_csv_row=None,
    payment_details_csv_row=None,
    requested_absence_som_csv_row=None,
    vbi_requested_absence_csv_row=None
):
    ci_index = ci_index or test_ci_index
    pei_csv_row = pei_csv_row or test_pei_csv_row
    claim_details_csv_row = claim_details_csv_row or test_claim_details_csv_row
    payment_details_csv_row = payment_details_csv_row or test_payment_details_csv_row
    requested_absence_som_csv_row = (
        requested_absence_som_csv_row or test_requested_absence_som_csv_row
    )
    vbi_requested_absence_csv_row = (
        vbi_requested_absence_csv_row or test_vbi_requested_absence_csv_row
    )

    input_files = [
        "s3://bucket/test/2021-01-17-19-14-25-Employee_feed.csv",
        "s3://bucket/test/2021-01-17-19-14-25-LeavePlan_info.csv",
        "s3://bucket/test/2021-01-17-19-14-25-VBI_REQUESTEDABSENCE_SOM.csv",
        "s3://bucket/test/2021-01-17-19-14-25-VBI_REQUESTEDABSENCE.csv",
        "s3://bucket/test/2021-01-17-19-14-25-vpeiclaimdetails.csv",
        "s3://bucket/test/2021-01-17-19-14-25-vpei.csv",
        "s3://bucket/test/2021-01-17-19-14-25-vpeipaymentdetails.csv",
    ]

    # Build a fineos_payment_export.ExtractData object with 1 row of data.
    extract_data = fineos_payment_export.ExtractData(input_files, "manual")
    extract_data.pei.indexed_data[ci_index] = pei_csv_row
    extract_data.claim_details.indexed_data[ci_index] = claim_details_csv_row
    extract_data.payment_details.indexed_data[ci_index] = [payment_details_csv_row]

    # Build a fineos_vendor_export.Extract object with 1 row of data.
    requested_absence_extract = fineos_vendor_export.Extract(
        "s3://bucket/test/2021-01-17-19-14-25-VBI_REQUESTEDABSENCE_SOM.csv"
    )
    requested_absence_extract.indexed_data["NTN-308848-ABS-01"] = requested_absence_som_csv_row

    # Build a custom voucher extract data for data from the VBI_REQUESTEDABSENCE.csv
    # Not to be confused with the similarly named VBI_REQUESTEDABSENCE_SOM.csv
    voucher_extract_data = payment_voucher.VoucherExtractData(input_files)
    voucher_extract_data.vbi_requested_absence.indexed_data[
        "NTN-308848-ABS-01"
    ] = vbi_requested_absence_csv_row

    setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_states=[State.VCM_REPORT_SENT],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            tax_identifier=TaxIdentifier(tax_identifier="999004400"),
            ctr_vendor_customer_code="VC0001230001",
        ),
    )

    return extract_data, requested_absence_extract, voucher_extract_data, ci_index


def standard_output_row(*, doc_id):
    return {
        "absence_case_number": "NTN-308848-ABS-01",
        "activity_code": "7247",
        "address_code": "AD010",
        "address_line_1": "47 Washington St",
        "address_line_2": "",
        "c_value": "7326",
        "city": "Quincy",
        "description": "PFML Payment NTN-308848-ABS-01 [01/15/2021-01/21/2021]",
        "doc_id": doc_id,
        "event_type": "AP01",
        "first_last_name": "Grady Bednar",
        "i_value": "249",
        "leave_type": "PFMLMEDIFY2170030632",
        "mmars_vendor_code": "VC0001230001",
        "payment_amount": "1600.18",
        "payment_doc_id_code": "GAX",
        "payment_doc_id_dept": "EOL",
        "payment_period_end_date": "2021-01-21",
        "payment_period_start_date": "2021-01-15",
        "payment_preference": "Check",
        "scheduled_payment_date": "2021-01-18",
        "state": "MA",
        "vendor_invoice_date": "2021-01-22",
        "vendor_invoice_line": "1",
        "vendor_invoice_number": "NTN-308848-ABS-01_249",
        "vendor_single_payment": "Yes",
        "zip": "02169",
        "case_status": "Approved",
        "employer_id": "2626107",
        "leave_request_id": "1234",
        "leave_request_decision": "Pending",
        "vcm_flag": "Yes",
        "claimants_that_have_zero_or_credit_value": "",
        "good_to_pay_from_prior_batch": "",
        "had_a_payment_in_a_prior_batch_by_vc_code": "",
        "inv": "",
        "payments_offset_to_zero": "",
        "is_exempt": "",
        "leave_decision_not_approved": "",
        "has_a_check_preference_with_an_adl2_issue": "",
        "adl2_corrected": "",
        "removed_or_added_after_audit_of_info": "",
        "to_be_removed_from_file": "",
        "notes": "",
    }


def standard_writeback_row():
    return {
        "c_value": "7326",
        "i_value": "249",
        "status": "Active",
        "stock_no": "",
        "transaction_status": "",
        "trans_status_date": "2021-01-15",
    }


@freezegun.freeze_time("2021-01-15 08:00:00", tz_offset=0)
def test_process_payment_record(test_db_session, initialize_factories_session):
    (
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
    ) = setup_standard_test_data(test_db_session)

    output_csv = MockCSVWriter()
    writeback_csv = MockCSVWriter()

    payment_voucher.process_payment_record(
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
        test_pei_csv_row,
        output_csv,
        writeback_csv,
        datetime.date(2021, 1, 18),
        test_db_session,
        MockLogEntry(),
    )

    assert len(output_csv.rows) == 1
    doc_id = output_csv.rows[0]["doc_id"]
    assert re.match("^GAXMDFMLAAAA........$", doc_id)
    expected_output_row = standard_output_row(doc_id=doc_id)
    assert output_csv.rows[0] == expected_output_row

    assert len(writeback_csv.rows) == 1
    assert writeback_csv.rows[0] == standard_writeback_row()


@freezegun.freeze_time("2021-01-15 08:00:00", tz_offset=0)
def test_process_payment_record_multiple_details(test_db_session, initialize_factories_session):
    input_files = [
        "s3://bucket/test/2021-01-17-19-14-25-Employee_feed.csv",
        "s3://bucket/test/2021-01-17-19-14-25-LeavePlan_info.csv",
        "s3://bucket/test/2021-01-17-19-14-25-VBI_REQUESTEDABSENCE_SOM.csv",
        "s3://bucket/test/2021-01-17-19-14-25-VBI_REQUESTEDABSENCE.csv",
        "s3://bucket/test/2021-01-17-19-14-25-vpeiclaimdetails.csv",
        "s3://bucket/test/2021-01-17-19-14-25-vpei.csv",
        "s3://bucket/test/2021-01-17-19-14-25-vpeipaymentdetails.csv",
    ]

    # Build a fineos_payment_export.ExtractData object with 1 row of data.
    extract_data = fineos_payment_export.ExtractData(input_files, "manual")
    extract_data.pei.indexed_data[test_ci_index] = test_pei_csv_row
    extract_data.claim_details.indexed_data[test_ci_index] = test_claim_details_csv_row

    # Multiple rows for this payment in payment_details.
    test_payment_details_csv_row_2 = test_payment_details_csv_row.copy()
    test_payment_details_csv_row_2["PAYMENTSTARTP"] = "2021-01-22 00:00:00"
    test_payment_details_csv_row_2["PAYMENTENDPER"] = "2021-01-28 00:00:00"
    test_payment_details_csv_row_3 = test_payment_details_csv_row.copy()
    test_payment_details_csv_row_3["PAYMENTSTARTP"] = "2021-01-29 00:00:00"
    test_payment_details_csv_row_3["PAYMENTENDPER"] = "2021-02-04 00:00:00"
    extract_data.payment_details.indexed_data[test_ci_index] = [
        test_payment_details_csv_row,
        test_payment_details_csv_row_3,
        test_payment_details_csv_row_2,
    ]

    # Build a fineos_vendor_export.Extract object with 1 row of data.
    requested_absence_extract = fineos_vendor_export.Extract(
        "s3://bucket/test/2021-01-17-19-14-25-VBI_REQUESTEDABSENCE_SOM.csv"
    )
    requested_absence_extract.indexed_data["NTN-308848-ABS-01"] = test_requested_absence_som_csv_row

    # Build a custom voucher extract data for data from the VBI_REQUESTEDABSENCE.csv
    # Not to be confused with the similarly named VBI_REQUESTEDABSENCE_SOM.csv
    voucher_extract_data = payment_voucher.VoucherExtractData(input_files)
    voucher_extract_data.vbi_requested_absence.indexed_data[
        "NTN-308848-ABS-01"
    ] = test_vbi_requested_absence_csv_row

    test_db_session.add(
        EmployeeFactory(
            tax_identifier=TaxIdentifier(tax_identifier="999004400"),
            ctr_vendor_customer_code="VC0001230001",
        )
    )

    output_csv = MockCSVWriter()
    writeback_csv = MockCSVWriter()

    payment_voucher.process_payment_record(
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        test_ci_index,
        test_pei_csv_row,
        output_csv,
        writeback_csv,
        datetime.date(2021, 1, 18),
        test_db_session,
        MockLogEntry(),
    )

    assert len(output_csv.rows) == 1
    doc_id = output_csv.rows[0]["doc_id"]
    assert re.match("^GAXMDFMLAAAA........$", doc_id)

    expected_output_row = standard_output_row(doc_id=doc_id)
    expected_output_row["description"] = "PFML Payment NTN-308848-ABS-01 [01/15/2021-02/04/2021]"
    expected_output_row["payment_period_end_date"] = "2021-02-04"
    expected_output_row["vcm_flag"] = "Missing State"
    expected_output_row["vendor_invoice_date"] = "2021-02-05"
    assert output_csv.rows[0] == expected_output_row

    assert len(writeback_csv.rows) == 1
    assert writeback_csv.rows[0] == standard_writeback_row()


@freezegun.freeze_time("2021-01-15 08:00:00", tz_offset=0)
def test_process_payment_record_zero_amount(test_db_session, initialize_factories_session):
    test_pei_csv_row_zero_amount = {**test_pei_csv_row, **{"AMOUNT_MONAMT": "0"}}

    (
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
    ) = setup_standard_test_data(test_db_session, pei_csv_row=test_pei_csv_row_zero_amount)

    output_csv = MockCSVWriter()
    writeback_csv = MockCSVWriter()

    payment_voucher.process_payment_record(
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
        test_pei_csv_row_zero_amount,
        output_csv,
        writeback_csv,
        datetime.date(2021, 1, 18),
        test_db_session,
        MockLogEntry(),
    )

    assert len(output_csv.rows) == 1
    doc_id = output_csv.rows[0]["doc_id"]
    assert re.match("^GAXMDFMLAAAA........$", doc_id)

    expected_output_row = standard_output_row(doc_id=doc_id)
    expected_output_row["payment_amount"] = "0"
    expected_output_row["claimants_that_have_zero_or_credit_value"] = "1"
    assert output_csv.rows[0] == expected_output_row

    assert len(writeback_csv.rows) == 1
    assert writeback_csv.rows[0] == standard_writeback_row()


@freezegun.freeze_time("2021-01-15 08:00:00", tz_offset=0)
def test_process_payment_record_negative_amount(test_db_session, initialize_factories_session):
    test_pei_csv_row_negative_amount = {**test_pei_csv_row, **{"AMOUNT_MONAMT": "-42.0"}}

    (
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
    ) = setup_standard_test_data(test_db_session, pei_csv_row=test_pei_csv_row_negative_amount)

    output_csv = MockCSVWriter()
    writeback_csv = MockCSVWriter()

    payment_voucher.process_payment_record(
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
        test_pei_csv_row_negative_amount,
        output_csv,
        writeback_csv,
        datetime.date(2021, 1, 18),
        test_db_session,
        MockLogEntry(),
    )

    assert len(output_csv.rows) == 1
    doc_id = output_csv.rows[0]["doc_id"]
    assert re.match("^GAXMDFMLAAAA........$", doc_id)

    expected_output_row = standard_output_row(doc_id=doc_id)
    expected_output_row["payment_amount"] = "-42.0"
    expected_output_row["claimants_that_have_zero_or_credit_value"] = "1"
    assert output_csv.rows[0] == expected_output_row

    assert len(writeback_csv.rows) == 1
    assert writeback_csv.rows[0] == standard_writeback_row()


@freezegun.freeze_time("2021-01-15 08:00:00", tz_offset=0)
def test_process_payment_record_no_amount(test_db_session, initialize_factories_session):
    test_pei_csv_row_no_amount = {**test_pei_csv_row, **{"AMOUNT_MONAMT": ""}}

    (
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
    ) = setup_standard_test_data(test_db_session, pei_csv_row=test_pei_csv_row_no_amount)

    output_csv = MockCSVWriter()
    writeback_csv = MockCSVWriter()

    payment_voucher.process_payment_record(
        extract_data,
        requested_absence_extract,
        voucher_extract_data,
        ci_index,
        test_pei_csv_row_no_amount,
        output_csv,
        writeback_csv,
        datetime.date(2021, 1, 18),
        test_db_session,
        MockLogEntry(),
    )

    assert len(output_csv.rows) == 1
    doc_id = output_csv.rows[0]["doc_id"]
    assert re.match("^GAXMDFMLAAAA........$", doc_id)

    expected_output_row = standard_output_row(doc_id=doc_id)
    expected_output_row["payment_amount"] = None
    expected_output_row["claimants_that_have_zero_or_credit_value"] = ""
    assert output_csv.rows[0] == expected_output_row

    assert len(writeback_csv.rows) == 1
    assert writeback_csv.rows[0] == standard_writeback_row()


@freezegun.freeze_time("2021-01-21 08:00:00", tz_offset=0)
def test_process_extracts_to_payment_voucher(
    test_db_session, initialize_factories_session, tmp_path
):
    input_path = os.path.join(os.path.dirname(__file__), "test_files")

    for ssn in (
        "390666954",
        "235702221",
        "158786713",
        "037408790",
        "135407982",
        "003061455",
        "066360920",
    ):
        setup_state_log(
            associated_class=state_log_util.AssociatedClass.EMPLOYEE,
            end_states=[State.IDENTIFY_MMARS_STATUS],
            test_db_session=test_db_session,
            additional_params=AdditionalParams(
                tax_identifier=TaxIdentifier(tax_identifier=ssn),
                ctr_vendor_customer_code="VC00012300" + ssn[-2:],
            ),
        )

    test_db_session.add(
        EmployeeFactory(
            tax_identifier=TaxIdentifier(tax_identifier="375563922"), ctr_vendor_customer_code=None,
        )
    )

    # DOC ID in output is randomized so seed to get reproducible output.
    random.seed(1)

    payment_voucher.process_extracts_to_payment_voucher(
        input_path, tmp_path, None, None, test_db_session, MockLogEntry()
    )

    csv_output = open(os.path.join(tmp_path, "20210121_080000_payment_voucher.csv")).readlines()
    expected_output = open(os.path.join(input_path, "expected_payment_voucher.csv")).readlines()

    assert csv_output == expected_output

    writeback = open(os.path.join(tmp_path, "20210121_080000_writeback.csv")).readlines()
    expected_writeback = open(os.path.join(input_path, "expected_writeback.csv")).readlines()

    assert writeback == expected_writeback
