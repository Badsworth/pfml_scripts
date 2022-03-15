import boto3
import moto
import pytest

import massgov.pfml.dor.pending_filing.pending_filing_submission as pending_filing_submission
import massgov.pfml.util.files as file_utils


@pytest.fixture
def test_input_path(tmp_path):
    test_folder = tmp_path / "dfml"
    test_folder.mkdir()
    received_folder = test_folder / "received"
    received_folder.mkdir()
    test_file = received_folder / "CompaniesReturningToStatePlan_20211228_1009.csv"
    test_file.write_text(get_input_file_content())

    return test_folder


def get_input_file_content():
    submission_file_header = (
        "FEIN,'Organization Name','MedicalExemption,'Family Exemption',"
        "'Effective date with State','First Requested Quarter'"
    )
    submission_file_line_one = "987987987,OAR Enterprises Corp.,No,No,1/1/2022,9/30/2021"
    submission_file_line_two = "654654654,ACME LLC,No,No,1/1/2022,9/30/2021"
    content = "{}\n{}\n{}".format(
        submission_file_header, submission_file_line_one, submission_file_line_two
    )
    return content


@pytest.fixture
def test_output_path(tmp_path):
    return tmp_path / "dor"


@pytest.fixture
def test_output_file(test_output_path):
    test_output_path.mkdir(exist_ok=True)
    output_folder = test_output_path / "send"
    output_folder.mkdir(exist_ok=True)
    output_file_name = f"{pending_filing_submission.SUBMISSION_FILE_NAME}_20211228_100900"
    output_path = "{}/{}".format(output_folder, output_file_name)
    return file_utils.write_file(output_path, "w")


def test_get_file_to_process(monkeypatch, test_input_path):
    monkeypatch.setenv("INPUT_FOLDER_PATH", test_input_path)
    file_to_process = pending_filing_submission.get_file_to_process()
    assert file_to_process.__contains__("CompaniesReturningToStatePlan")


def test_write_to_submission_file(test_output_file):
    pending_filing_submission.write_to_submission_file("987987987", "20210930", test_output_file)
    test_output_file.close()

    output_lines = file_utils.read_file_lines(str(test_output_file.name))
    output_list = list(output_lines)

    assert output_list[0] == "FEIN      987987987     20210930"


def test_process_pending_filing_employers(monkeypatch, test_input_path, test_output_path):
    monkeypatch.setenv("INPUT_FOLDER_PATH", test_input_path)
    monkeypatch.setenv("OUTPUT_FOLDER_PATH", test_output_path)

    report = pending_filing_submission.process_pending_filing_employers()
    assert report.total_employers_written_count == 2

    output_path = f"{str(test_output_path)}/send"

    file_list = file_utils.list_files(output_path)

    output_files = []
    for output_file in file_list:
        if output_file.startswith(pending_filing_submission.SUBMISSION_FILE_NAME):
            output_files.append(output_file)

    file_name = f"{output_path}/{output_files[0]}"
    output_lines = file_utils.read_file_lines(file_name)
    output_list = list(output_lines)

    assert output_list[0] == "FEIN      987987987     20210930"
    assert output_list[1] == "FEIN      654654654     20210930"


@moto.mock_ssm()
@moto.mock_sts()
@moto.mock_s3()
def test_main_success_s3_location(
    local_test_db_session, monkeypatch, logging_fix, reset_aws_env_vars
):
    monkeypatch.setattr(pending_filing_submission, "make_db_session", lambda: local_test_db_session)

    # Not exact match to actual S3 buckets but just to
    # simulate separate locations for input and output.
    mock_bucket_name_dfml = "agency-transfer-dfml"
    mock_bucket_name_dor = "agency-transfer-dor"

    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket=mock_bucket_name_dfml)
    s3_client.create_bucket(Bucket=mock_bucket_name_dor)

    s3_client.put_object(
        Bucket=f"{mock_bucket_name_dfml}",
        Key="received/CompaniesReturningToStatePlan_20211228_1009.csv",
        Body=get_input_file_content(),
    )

    monkeypatch.setenv("INPUT_FOLDER_PATH", f"s3://{mock_bucket_name_dfml}")
    monkeypatch.setenv("OUTPUT_FOLDER_PATH", f"s3://{mock_bucket_name_dor}")

    report = pending_filing_submission.handler_with_return()

    object_list = s3_client.list_objects(Bucket=f"{mock_bucket_name_dor}")["Contents"]
    output_file_reference = None
    for output_file in object_list:
        if output_file["Key"].__contains__(
            f"send/{pending_filing_submission.SUBMISSION_FILE_NAME}"
        ):
            output_file_reference = output_file

    assert output_file_reference
    output_file_object = s3_client.get_object(
        Bucket=f"{mock_bucket_name_dor}", Key=output_file_reference["Key"]
    )

    # smart_open defaults to multipart S3 uploads. This causes the ETag header
    # for the files in S3 to have the upload part number on the end (e.g.,
    # `-1`), rather than just an MD5.
    #
    # This breaks the (incorrect) validation the DOR system tries to run when
    # picking up the file.
    #
    # Solution is to not use the multipart upload for these files DOR needs to
    # fetch.
    etag = output_file_object["ResponseMetadata"]["HTTPHeaders"]["etag"]
    assert not etag.endswith('-1"')
    assert report.start
    assert report.end
    assert report.total_employers_received_count == 2
    assert report.total_employers_written_count == 2
