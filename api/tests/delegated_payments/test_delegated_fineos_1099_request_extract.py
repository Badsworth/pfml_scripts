import pytest

import massgov.pfml.delegated_payments.delegated_fineos_1099_extract as request_1099_extract
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import Employee, ReferenceFileType
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    ImportLogFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.db.models.payments import FineosExtractVbi1099DataSom, Pfml1099Request
from massgov.pfml.delegated_payments.mock.fineos_extract_data import FineosPaymentData
from massgov.pfml.util.batch.log import LogEntry


@pytest.fixture
def request_1099_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return request_1099_extract.Data1099ExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def local_request_1099_extract_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return request_1099_extract.Data1099ExtractStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def get_xml_type_one() -> str:
    xml_1099_packed_data1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                <EnumObject>
                    <name>ENUM</name>
                    <prompt>Provide the reason for the 1099G reissue</prompt>
                    <value>512512001</value>
                    <radiobutton>false</radiobutton>
                </EnumObject>
            </ns2:DataSet>"""
    return xml_1099_packed_data1


def get_xml_type_three() -> str:
    xml_1099_packed_data1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                <EnumObject>
                    <name>ENUM</name>
                    <prompt>Provide the reason for the 1099G reissue</prompt>
                    <value>512512003</value>
                    <radiobutton>false</radiobutton>
                </EnumObject>
            </ns2:DataSet>"""
    return xml_1099_packed_data1


def get_xml_type_invalid() -> str:
    xml_1099_packed_data1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                <EnumObject>
                    <name>ENUM</name>
                    <prompt>Provide the reason for the 1099G reissue</prompt>
                    <value>512512004</value>
                    <radiobutton>false</radiobutton>
                </EnumObject>
            </ns2:DataSet>"""
    return xml_1099_packed_data1


def stage_data(records, db_session, reference_file=None, import_log=None):
    if not reference_file:
        reference_file = ReferenceFileFactory.create(
            reference_file_type_id=ReferenceFileType.FINEOS_1099_DATA_EXTRACT.reference_file_type_id
        )
    if not import_log:
        import_log = ImportLogFactory.create()

    for record in records:
        instance = payments_util.create_staging_table_instance(
            record.get_vbi_1099_data_record(),
            FineosExtractVbi1099DataSom,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)

    db_session.commit()


def create_employee_record(custno, ssn) -> Employee:
    employee = EmployeeFactory.create(
        fineos_customer_number=custno,
        tax_identifier=TaxIdentifierFactory.create(tax_identifier=ssn),
        fineos_employee_first_name="Original-FINEOS-First",
        fineos_employee_last_name="Original-FINEOS-Last",
    )
    return employee


def make_1099_data_from_fineos_vbi_data(db_session):
    xml_data = get_xml_type_one()
    req_1099_data_1 = FineosPaymentData(packed_data_1099=xml_data)
    emp = create_employee_record(req_1099_data_1.customer_number, req_1099_data_1.ssn)
    stage_data([req_1099_data_1], db_session)
    vbi_1099 = db_session.query(FineosExtractVbi1099DataSom).first()
    with LogEntry(db_session, "test log entry") as log_entry:
        return request_1099_extract.Data1099(
            vbi_1099.vbi_1099_data_som_id,
            emp.employee_id,
            vbi_1099,
            vbi_1099.packeddata,
            log_entry.increment,
        )


def make_invalid_1099_data_from_fineos_vbi_data(db_session):
    xml_data = get_xml_type_invalid()
    req_1099_data_1 = FineosPaymentData(packed_data_1099=xml_data)
    emp = create_employee_record(req_1099_data_1.customer_number, req_1099_data_1.ssn)
    stage_data([req_1099_data_1], db_session)
    vbi_1099 = db_session.query(FineosExtractVbi1099DataSom).first()
    with LogEntry(db_session, "test log entry") as log_entry:
        return request_1099_extract.Data1099(
            vbi_1099.vbi_1099_data_som_id,
            emp.employee_id,
            vbi_1099,
            vbi_1099.packeddata,
            log_entry.increment,
        )


def test_process_1099_records(request_1099_extract_step, test_db_session):
    xml_data = get_xml_type_one()
    req_1099_data_1 = FineosPaymentData(packed_data_1099=xml_data)
    emp = create_employee_record(req_1099_data_1.customer_number, req_1099_data_1.ssn)
    stage_data([req_1099_data_1], test_db_session)
    request_1099_extract_step.process_1099_records()
    vbi_1099 = test_db_session.query(FineosExtractVbi1099DataSom).all()
    pfml_request_1099 = test_db_session.query(Pfml1099Request).all()
    assert len(vbi_1099) == 1
    assert len(pfml_request_1099) == 1
    assert pfml_request_1099[0].employee_id == emp.employee_id
    assert pfml_request_1099[0].correction_ind is False


def test_parse_packed_data_info(initialize_factories_session, test_db_session):
    data1099 = make_1099_data_from_fineos_vbi_data(test_db_session)
    res = data1099.parse_packed_data_info()
    assert res == "512512001"
    data1099.packed_data_validator()
    assert len(data1099.validation_container.validation_issues) == 0


def test_packed_data_validator_invalid_case(initialize_factories_session, test_db_session):
    data1099 = make_invalid_1099_data_from_fineos_vbi_data(test_db_session)
    data1099.packed_data_validator()
    assert len(data1099.validation_container.validation_issues) > 0


def test_process_1099_records_no_xml_data(request_1099_extract_step, test_db_session):
    req_1099_data_1 = FineosPaymentData(packed_data_1099=None)
    create_employee_record(req_1099_data_1.customer_number, req_1099_data_1.ssn)
    stage_data([req_1099_data_1], test_db_session)
    request_1099_extract_step.process_1099_records()
    vbi_1099 = test_db_session.query(FineosExtractVbi1099DataSom).all()
    pfml_request_1099 = test_db_session.query(Pfml1099Request).all()
    assert len(vbi_1099) == 1
    assert len(pfml_request_1099) == 0


def test_run_step_happy_path(local_request_1099_extract_step, local_test_db_session):
    # create data with reasons to request 1099 data

    xml_data_three = get_xml_type_three()
    req_1099_data_3 = FineosPaymentData(packed_data_1099=xml_data_three)
    emp = create_employee_record(req_1099_data_3.customer_number, req_1099_data_3.ssn)
    stage_data([req_1099_data_3], local_test_db_session)

    local_request_1099_extract_step.run()
    vbi_1099 = local_test_db_session.query(FineosExtractVbi1099DataSom).all()
    assert len(vbi_1099) == 1
    pfml_request_1099 = local_test_db_session.query(Pfml1099Request).all()
    emp = (
        local_test_db_session.query(Employee)
        .filter(Employee.fineos_customer_number == req_1099_data_3.customer_number)
        .first()
    )
    assert len(pfml_request_1099) == 1
    pfml_requestn = (
        local_test_db_session.query(Pfml1099Request)
        .filter(Pfml1099Request.employee_id == emp.employee_id)
        .first()
    )
    assert pfml_requestn.correction_ind is True


def test_map_request_type(request_1099_extract_step):
    REQUEST_TYPE_ONE = "512512001"
    REQUEST_TYPE_TWO = "512512002"
    REQUEST_TYPE_THREE = "512512003"

    assert request_1099_extract_step.map_request_type(REQUEST_TYPE_ONE) is False
    assert request_1099_extract_step.map_request_type(REQUEST_TYPE_TWO) is True
    assert request_1099_extract_step.map_request_type(REQUEST_TYPE_THREE) is True


def test_create_update_record(request_1099_extract_step):

    employee_id = "a9c98c3f-eaaf-4f68-9a03-13561537c023"
    correction_ind = True
    result = request_1099_extract_step.create_update_record(employee_id, correction_ind, None)
    assert result == 1
