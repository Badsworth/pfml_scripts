import xml.dom.minidom as minidom

import boto3

import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util


def test_create_vcc_files_in_s3(mock_s3_bucket):
    bucket_path = f"s3://{mock_s3_bucket}"
    filename = "example_filename"
    dat_xml_document = minidom.Document()
    inf_dict = {"NewMmarsBatchDeptCode": payments_util.Constants.COMPTROLLER_DEPT_CODE}

    payments_util.write_vcc_files(bucket_path, filename, dat_xml_document, inf_dict)

    # Expect the files to have been uploaded to S3.
    files_in_mock_s3_bucket = file_util.list_files(bucket_path)
    expected_filename_extensions = [".DAT", ".INF"]
    for filename_extension in expected_filename_extensions:
        assert f"{filename}{filename_extension}" in files_in_mock_s3_bucket

    # Expect the files to have the proper contents.
    #
    # Testing only the INF file here because it is simpler (does not involve XML formatting) and
    # the DAT file should follow a similar pattern.
    s3 = boto3.client("s3")
    inf_file = s3.get_object(Bucket=mock_s3_bucket, Key=f"{filename}.INF")
    assert inf_file["Body"].read() == b"NewMmarsBatchDeptCode = EOL;\n"
