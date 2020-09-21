import json
from datetime import datetime, timedelta

import boto3
from moto import mock_s3

import massgov.pfml.formstack.importer.import_formstack as import_formstack
from massgov.pfml.formstack.formstack_client import Submission, SubmissionKeyValuePair


class MockFormstackClient:
    def get_forms(self):
        return [{"id": "fake_id"}, {"id": "fake_id_2"}]

    def get_submissions(self, form_id, start_time, end_time):
        submission1 = SubmissionKeyValuePair(**{"field": "fake_field_1", "value": "fake_value_1"})
        submission2 = SubmissionKeyValuePair(**{"field": "fake_field_2", "value": "fake_value_2"})

        return [
            Submission(**{"submission_id": "111", "data": [submission1]}),
            Submission(**{"submission_id": "222", "data": [submission2]}),
        ]


def test_get_form_ids():
    client = MockFormstackClient()
    forms = import_formstack.get_form_ids(client)

    assert len(forms) == 2
    assert forms[0] == "fake_id"
    assert forms[1] == "fake_id_2"

    forms = import_formstack.get_form_ids(client, "fake_passed_form_id")

    assert len(forms) == 1
    assert forms[0] == "fake_passed_form_id"


def test_process_submissions(monkeypatch):
    def mock_write_to_s3(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "massgov.pfml.formstack.importer.import_formstack.write_to_s3", mock_write_to_s3
    )

    client = MockFormstackClient()
    end_time = datetime.now()
    start_time = datetime.now() - timedelta(hours=24)
    form_ids = ["123", "456"]

    submissions_by_form = import_formstack.process_submissions(
        client, form_ids, start_time, end_time
    )

    assert submissions_by_form[0]["form_id"] == "123"
    assert submissions_by_form[0]["total_submissions"] == 2
    assert submissions_by_form[1]["form_id"] == "456"
    assert submissions_by_form[1]["total_submissions"] == 2


@mock_s3
def test_write_to_s3(monkeypatch):
    def mock_get_secret_from_env(*args, **kwargs):
        return "test-bucket"

    monkeypatch.setattr(
        "massgov.pfml.formstack.importer.import_formstack.get_secret_from_env",
        mock_get_secret_from_env,
    )
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-bucket")

    fake_data_to_write = [{"test": "data"}]
    fake_form_id = "123"
    end_time = datetime.now().isoformat()
    start_time = (datetime.now() - timedelta(hours=24)).isoformat()
    key = f"{fake_form_id}_{start_time.replace(' ', '_')}_{end_time.replace(' ', '_')}.json"

    import_formstack.write_to_s3(fake_data_to_write, fake_form_id, start_time, end_time)

    file_body = json.loads(conn.Object("test-bucket", key).get()["Body"].read().decode("utf-8"))

    assert file_body == fake_data_to_write


def test_write_to_import_log(monkeypatch, test_db_session):
    import_start_time = datetime.now()
    query_start_time = datetime.now() - timedelta(hours=24)
    query_end_time = datetime.now()
    report_status = "success"
    source = "fake_test_source"

    submissions_by_form = [{"form_id": "123", "total_submissions": 1}]

    report_log_entry = import_formstack.write_to_import_log(
        test_db_session,
        submissions_by_form,
        source,
        import_start_time,
        query_start_time,
        query_end_time,
        report_status,
    )
    assert report_log_entry.import_log_id is not None
