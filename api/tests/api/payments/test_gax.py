import decimal
import xml.dom.minidom as minidom
from datetime import datetime
from typing import List

import defusedxml.ElementTree as ET
import pytest
import smart_open
from freezegun import freeze_time
from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.payments.gax as gax
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import (
    ClaimType,
    CtrDocumentIdentifier,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
)
from tests.api.payments import validate_attributes, validate_elements


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


def create_add_to_gax_state_log_for_payment(payment: Payment, db_session: db.Session) -> None:
    state_log_util.create_finished_state_log(
        end_state=State.ADD_TO_GAX,
        outcome=state_log_util.build_outcome("success"),
        associated_model=payment,
        db_session=db_session,
    )


def test_get_fiscal_year():
    # Fiscal year matches calendar year for first six months
    assert gax.get_fiscal_year(datetime(2020, 1, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 2, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 3, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 4, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 5, 1)) == 2020
    assert gax.get_fiscal_year(datetime(2020, 6, 1)) == 2020
    # And then is incremented by 1 starting in July
    assert gax.get_fiscal_year(datetime(2020, 7, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 8, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 9, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 10, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 11, 1)) == 2021
    assert gax.get_fiscal_year(datetime(2020, 12, 1)) == 2021


def test_get_fiscal_month():
    # Fiscal month is 6 months ahead
    assert gax.get_fiscal_month(datetime(2020, 1, 1)) == 7
    assert gax.get_fiscal_month(datetime(2020, 2, 1)) == 8
    assert gax.get_fiscal_month(datetime(2020, 3, 1)) == 9
    assert gax.get_fiscal_month(datetime(2020, 4, 1)) == 10
    assert gax.get_fiscal_month(datetime(2020, 5, 1)) == 11
    assert gax.get_fiscal_month(datetime(2020, 6, 1)) == 12
    assert gax.get_fiscal_month(datetime(2020, 7, 1)) == 1
    assert gax.get_fiscal_month(datetime(2020, 8, 1)) == 2
    assert gax.get_fiscal_month(datetime(2020, 9, 1)) == 3
    assert gax.get_fiscal_month(datetime(2020, 10, 1)) == 4
    assert gax.get_fiscal_month(datetime(2020, 11, 1)) == 5
    assert gax.get_fiscal_month(datetime(2020, 12, 1)) == 6


def test_get_disbursement_format():
    assert gax.get_disbursement_format(PaymentMethod.ACH) is None
    assert gax.get_disbursement_format(PaymentMethod.CHECK) == "REGW"


def test_gax_doc_id():
    doc_id = gax.get_doc_id()
    assert doc_id[:8] == "INTFDFML"
    assert len(doc_id) == 20


@pytest.mark.integration
def test_build_individual_gax_document(initialize_factories_session, test_db_session):
    xml_document = minidom.Document()
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    payment = get_payment(
        fineos_absence_id="NTN-1234-ABS-01",
        payment_date=datetime(2020, 7, 1).date(),
        ctr_vendor_code="abc1234",
        amount=decimal.Decimal("1200.00"),
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        start_date=datetime(2020, 8, 1).date(),
        end_date=datetime(2020, 12, 1).date(),
        payment_method_id=PaymentMethod.ACH.payment_method_id,
        fineos_pei_i_value="1",
    )
    test_db_session.add(payment)
    test_db_session.commit()

    document = gax.build_individual_gax_document(xml_document, payment, payments_util.get_now())

    # Doc ID is generated randomly every run, but appears in many sub values.
    doc_id = document._attrs["DOC_ID"].value
    assert doc_id

    # Verify the root of the document
    assert document.tagName == "AMS_DOCUMENT"
    expected_doc_attributes = {"DOC_ID": doc_id}
    expected_doc_attributes.update(gax.ams_doc_attributes.copy())
    expected_doc_attributes.update(gax.generic_attributes.copy())
    validate_attributes(document, expected_doc_attributes)
    assert len(document.childNodes) == 3

    # Validate the ABS_DOC_HDR section
    abs_doc_hdr = document.childNodes[0]
    assert abs_doc_hdr.tagName == "ABS_DOC_HDR"
    validate_attributes(abs_doc_hdr, {"AMSDataObject": "Y"})

    expected_hdr_subelements = {
        "DOC_ID": doc_id,
        "DOC_BFY": "2021",
        "DOC_FY_DC": "2021",
        "DOC_PER_DC": "1",
    }
    expected_hdr_subelements.update(gax.generic_attributes.copy())
    validate_elements(abs_doc_hdr, expected_hdr_subelements)

    # Validate the ABS_DOC_VEND section
    abs_doc_vend = document.childNodes[1]

    assert abs_doc_vend.tagName == "ABS_DOC_VEND"
    validate_attributes(abs_doc_vend, {"AMSDataObject": "Y"})

    expected_vend_subelements = {
        "DOC_ID": doc_id,
        "VEND_CUST_CD": "ABC1234",
        "AD_ID": "AD010",
        "DFLT_DISB_FRMT": "null",  # for ACH
    }
    expected_vend_subelements.update(gax.generic_attributes.copy())
    expected_vend_subelements.update(gax.abs_doc_vend_attributes.copy())
    validate_elements(abs_doc_vend, expected_vend_subelements)

    # Validate the ABS_DOC_ACTG section
    abs_doc_actg = document.childNodes[2]
    assert abs_doc_actg.tagName == "ABS_DOC_ACTG"
    validate_attributes(abs_doc_actg, {"AMSDataObject": "Y"})

    expected_actg_subelements = {
        "DOC_ID": doc_id,
        "EVNT_TYP_ID": "7246",
        "LN_AM": "1200.00",
        "BFY": "2021",
        "FY_DC": "2021",
        "PER_DC": "1",
        "VEND_INV_NO": "NTN-1234-ABS-01_1",
        "VEND_INV_DT": "2020-12-02",
        "CHK_DSCR": "PFML PAYMENT NTN-1234-ABS-01 [08/01/2020-12/01/2020]",
        "RFED_DOC_ID": "PFMLFAMLFY2170030632",
        "ACTV_CD": "7246",
        "SVC_FRM_DT": "2020-08-01",
        "SVC_TO_DT": "2020-12-01",
    }
    expected_actg_subelements.update(gax.generic_attributes.copy())
    expected_actg_subelements.update(gax.abs_doc_actg_attributes.copy())
    validate_elements(abs_doc_actg, expected_actg_subelements)


@pytest.mark.integration
@freeze_time("2021-01-01 12:00:00")
def test_build_gax_files(
    initialize_factories_session, test_db_session, mock_s3_bucket, set_exporter_env_vars, mock_ses
):
    payments = get_payments()
    for payment in payments:
        create_add_to_gax_state_log_for_payment(payment, test_db_session)

    ctr_outbound_path = f"s3://{mock_s3_bucket}/path/to/dir"
    (dat_filepath, inf_filepath) = gax.build_gax_files(test_db_session, ctr_outbound_path)

    # Confirm that we created a database row for each payment we created a document for.
    assert test_db_session.query(
        func.count(CtrDocumentIdentifier.ctr_document_identifier_id)
    ).scalar() == len(payments)
    assert test_db_session.query(
        func.count(PaymentReferenceFile.ctr_document_identifier_id)
    ).scalar() == len(payments)

    # Confirm we created StateLog records for both payments
    assert test_db_session.query(
        func.count(StateLog.state_log_id).filter(StateLog.end_state_id == State.GAX_SENT.state_id)
    ).scalar() == len(payments)

    # Confirm that we created a single GAX record.
    ref_files = (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id == ReferenceFileType.GAX.reference_file_type_id
        )
        .all()
    )
    assert len(ref_files) == 1

    # Confirm that the ReferenceFile is correctly associated with Payment models through the
    # PaymentReferenceFile table.
    ref_file = ref_files[0]
    assert len(ref_file.payments) == len(payments)

    # Confirm that the INF data is being saved to the database properly.
    assert ref_file.ctr_batch_identifier.inf_data.get("NewMmarsTransCode") == "GAX"

    with smart_open.open(inf_filepath) as inf_file:
        assert inf_filepath.split("/")[-1] == "EOL20210101GAX10.INF"
        inf_file_contents = "".join(line for line in inf_file)
        assert inf_file_contents == (
            "NewMmarsBatchID = EOL0101GAX10;\n"
            "NewMmarsBatchDeptCode = EOL;\n"
            "NewMmarsUnitCode = 8770;\n"
            "NewMmarsImportDate = 2021-01-01;\n"
            "NewMmarsTransCode = GAX;\n"
            "NewMmarsTableName = ;\n"
            "NewMmarsTransCount = 2;\n"
            "NewMmarsTransDollarAmount = 2500.00;\n"
        )

    with smart_open.open(dat_filepath) as dat_file:
        assert dat_filepath.split("/")[-1] == "EOL20210101GAX10.DAT"
        dat_file_contents = "".join(line for line in dat_file)

        # This bit doesn't get parsed into the XML objects
        assert dat_file_contents.startswith('<?xml version="1.0" encoding="ISO-8859-1"?>')

        # Make sure cdata fields weren't mistakenly escaped
        assert "&lt;" not in dat_file_contents
        assert "&gt;" not in dat_file_contents
        # Make sure cdata fields were created properly by looking for one
        assert '<BFY Attribute="Y"><![CDATA[2021]]></BFY>' in dat_file_contents

        # We use ET for parsing instead of minidom as minidom makes odd decisions
        # when creating objects (new lines are child nodes?) that is complex.
        # Note that this parser removes the CDATA tags when parsing.
        root = ET.fromstring(dat_file_contents)

        # For the two documents passed in
        assert len(root) == 2
        assert len(root) == int(ref_file.ctr_batch_identifier.inf_data.get("NewMmarsTransCount"))

        for document in root:
            # Doc ID is generated randomly every run, but appears in many sub values.
            doc_id = document.attrib["DOC_ID"]
            assert doc_id

            assert document.tag == "AMS_DOCUMENT"
            expected_doc_attributes = {"DOC_ID": doc_id}
            expected_doc_attributes.update(gax.ams_doc_attributes.copy())
            expected_doc_attributes.update(gax.generic_attributes.copy())
            assert document.attrib == expected_doc_attributes
            assert len(document) == 3  # len of an element gives number of subelements

            abs_doc_hdr = document[0]
            assert abs_doc_hdr.tag == "ABS_DOC_HDR"
            assert abs_doc_hdr.attrib == {"AMSDataObject": "Y"}

            abs_doc_vend = document[1]
            assert abs_doc_vend.tag == "ABS_DOC_VEND"
            assert abs_doc_vend.attrib == {"AMSDataObject": "Y"}

            abs_doc_actg = document[2]
            assert abs_doc_actg.tag == "ABS_DOC_ACTG"
            assert abs_doc_actg.attrib == {"AMSDataObject": "Y"}


@pytest.mark.integration
@freeze_time("2021-01-01 12:00:00")
def test_build_gax_files_previously_processed(
    initialize_factories_session, test_db_session, mock_s3_bucket, set_exporter_env_vars, mock_ses
):
    payments = get_payments()
    # The first payment will have been previously processed based on the state log
    previously_processed_payment = payments[0]
    state_log_util.create_finished_state_log(
        end_state=State.GAX_SENT,  # Any payment with this is sent to an error state
        outcome=state_log_util.build_outcome("success"),
        associated_model=previously_processed_payment,
        db_session=test_db_session,
    )

    # Need to add the ADD_TO_GAX state second so it's the latest
    for payment in payments:
        create_add_to_gax_state_log_for_payment(payment, test_db_session)

    ctr_outbound_path = f"s3://{mock_s3_bucket}/path/to/dir"
    (dat_filepath, inf_filepath) = gax.build_gax_files(test_db_session, ctr_outbound_path)

    # Only the one payment errors here
    errored_state_log = (
        test_db_session.query(StateLog)
        .filter(StateLog.end_state_id == State.ADD_TO_GAX_ERROR_REPORT.state_id)
        .one_or_none()
    )
    assert errored_state_log.payment.payment_id == previously_processed_payment.payment_id

    # Not validating everything, but verify that only one record was added
    with smart_open.open(inf_filepath) as inf_file:
        assert inf_filepath.split("/")[-1] == "EOL20210101GAX10.INF"
        inf_file_contents = "".join(line for line in inf_file)
        assert "NewMmarsTransCount = 1;" in inf_file_contents


@pytest.mark.integration
def test_build_gax_files_no_eligible_payments(test_db_session, mock_s3_bucket):
    ctr_outbound_path = f"s3://{mock_s3_bucket}/path/to/dir"
    assert gax.build_gax_files(test_db_session, ctr_outbound_path) == (
        payments_util.Constants.MMARS_FILE_SKIPPED,
        payments_util.Constants.MMARS_FILE_SKIPPED,
    )


@pytest.mark.integration
def test_build_gax_files_skip_payment_record_errors(
    initialize_factories_session, test_db_session, mock_s3_bucket, set_exporter_env_vars, mock_ses
):
    payments = get_payments()
    valid_payment_record = payments[0]
    create_add_to_gax_state_log_for_payment(valid_payment_record, test_db_session)

    invalid_payment_record = payments[1]
    invalid_payment_record.amount = decimal.Decimal("00.00")
    create_add_to_gax_state_log_for_payment(invalid_payment_record, test_db_session)

    ctr_outbound_path = f"s3://{mock_s3_bucket}/path/to/dir"
    dat_filepath, inf_filepath = gax.build_gax_files(test_db_session, ctr_outbound_path)

    # Confirm that we created a single GAX record.
    ref_files = (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id == ReferenceFileType.GAX.reference_file_type_id
        )
        .all()
    )
    assert len(ref_files) == 1

    # Confirm we only created a StateLog record for the valid payment record
    assert (
        test_db_session.query(
            func.count(StateLog.state_log_id).filter(
                StateLog.end_state_id == State.GAX_SENT.state_id
            )
        ).scalar()
        == 1
    )

    # Confirm that we only added a single payment to the GAX file.
    ref_file = ref_files[0]
    assert len(ref_file.payments) == 1
    assert ref_file.ctr_batch_identifier.inf_data.get("NewMmarsTransCount") == "1"


@pytest.mark.integration
def test_build_gax_files_raise_error_all_rows_error(
    initialize_factories_session, test_db_session, mock_s3_bucket
):
    # The only eligible payment will raise an error.
    payments = get_payments()
    invalid_payment_record = payments[0]
    invalid_payment_record.amount = decimal.Decimal("00.00")
    create_add_to_gax_state_log_for_payment(invalid_payment_record, test_db_session)

    ctr_outbound_path = f"s3://{mock_s3_bucket}/path/to/dir"
    with pytest.raises(Exception, match="No Payment records added to GAX"):
        gax.build_gax_files(test_db_session, ctr_outbound_path)
