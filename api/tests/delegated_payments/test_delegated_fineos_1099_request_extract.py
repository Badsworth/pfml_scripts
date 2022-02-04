import pytest

import massgov.pfml.delegated_payments.delegated_fineos_1099_extract as request_1099_extract
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import ReferenceFileType
from massgov.pfml.db.models.factories import ImportLogFactory, ReferenceFileFactory
from massgov.pfml.db.models.payments import FineosExtractVbi1099DataSom
from massgov.pfml.delegated_payments.mock.fineos_extract_data import FineosPaymentData


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


def stage_data(
    records, db_session, reference_file=None, import_log=None,
):
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


def test_run_step_happy_path(
    local_request_1099_extract_step, local_test_db_session,
):
    # create data with reasons to request 1099 data

    xml_1099_packed_data1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                <EnumObject>
                    <name>ENUM</name>
                    <prompt>Provide the reason for the 1099G reissue</prompt>
                    <value>512512001</value>
                    <radiobutton>false</radiobutton>
                </EnumObject>
            </ns2:DataSet>"""

    xml_1099_packed_data2 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                <EnumObject>
                    <name>ENUM</name>
                    <prompt>Provide the reason for the 1099G reissue</prompt>
                    <value>512512002</value>
                    <radiobutton>false</radiobutton>
                </EnumObject>
            </ns2:DataSet>"""

    xml_1099_packed_data3 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <ns2:DataSet xmlns:ns2="http://www.fineos.com/ta/common/external">
                <EnumObject>
                    <name>ENUM</name>
                    <prompt>Provide the reason for the 1099G reissue</prompt>
                    <value>512512003</value>
                    <radiobutton>false</radiobutton>
                </EnumObject>
            </ns2:DataSet>"""

    req_1099_data_1 = FineosPaymentData(packed_data_1099=xml_1099_packed_data1)
    req_1099_data_2 = FineosPaymentData(packed_data_1099=xml_1099_packed_data2)
    req_1099_data_3 = FineosPaymentData(packed_data_1099=xml_1099_packed_data3)
    stage_data([req_1099_data_1, req_1099_data_2, req_1099_data_3], local_test_db_session)

    local_request_1099_extract_step.run()


def test_map_request_type(
    request_1099_extract_step, local_test_db_session,
):
    REQUEST_TYPE_ONE = "512512001"
    REQUEST_TYPE_TWO = "512512002"
    REQUEST_TYPE_THREE = "512512003"

    assert request_1099_extract_step.map_request_type(REQUEST_TYPE_ONE) is False
    assert request_1099_extract_step.map_request_type(REQUEST_TYPE_TWO) is True
    assert request_1099_extract_step.map_request_type(REQUEST_TYPE_THREE) is True


def test_create_update_record(request_1099_extract_step, local_test_db_session):

    employee_id = "a9c98c3f-eaaf-4f68-9a03-13561537c023"
    correction_ind = True
    result = request_1099_extract_step.create_update_record(employee_id, correction_ind, None)
    assert result == 1
