import boto3
import moto
import pydantic
import pytest

from massgov.pfml.db.models.factories import WagesAndContributionsFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


@moto.mock_ssm()
def test_main_requires_non_empty_env_vars(
    test_db_session, monkeypatch, logging_fix, reset_aws_env_vars
):
    import massgov.pfml.fineos.eligibility_feed_export.eligibility_export as main

    main.db_session_raw = test_db_session

    # check that error is raised if none of the environment variables are set
    with pytest.raises(pydantic.ValidationError):
        main.handler({}, {})

    # and also check that they are required to be non-empty
    monkeypatch.setenv("OUTPUT_DIRECTORY_PATH", "")
    monkeypatch.setenv("FINEOS_AWS_IAM_ROLE_ARN", "")
    monkeypatch.setenv("FINEOS_AWS_IAM_ROLE_EXTERNAL_ID", "")

    with pytest.raises(pydantic.ValidationError):
        main.handler({}, {})


@moto.mock_ssm()
@moto.mock_sts()
@moto.mock_s3()
def test_main_success_fineos_location(
    test_db_session, initialize_factories_session, monkeypatch, logging_fix, reset_aws_env_vars,
):
    import massgov.pfml.fineos.eligibility_feed_export.eligibility_export as main

    main.db_session_raw = test_db_session

    mock_fineos_bucket_name = "fin-som-foo"

    s3_client = boto3.resource("s3")
    s3_client.create_bucket(Bucket=mock_fineos_bucket_name)

    WagesAndContributionsFactory.create()

    monkeypatch.setenv("OUTPUT_DIRECTORY_PATH", f"s3://{mock_fineos_bucket_name}/test-output-dir")
    monkeypatch.setenv(
        "FINEOS_AWS_IAM_ROLE_ARN",
        "arn:aws:iam::000000000000:role/sompre-IAMRoles-CustomerAccountAccessRole-foobar",
    )
    monkeypatch.setenv("FINEOS_AWS_IAM_ROLE_EXTERNAL_ID", "123")

    response = main.handler({}, {})

    assert response["started_at"]
    assert response["completed_at"]
    assert response["employers_total_count"] == 1
    assert response["employers_success_count"] == 1
    assert response["employers_error_count"] == 0
    assert response["employers_skipped_count"] == 0
    assert response["employee_and_employer_pairs_total_count"] == 1


@moto.mock_ssm()
def test_main_success_non_fineos_location(
    test_db_session,
    initialize_factories_session,
    monkeypatch,
    logging_fix,
    reset_aws_env_vars,
    tmp_path,
):
    import massgov.pfml.fineos.eligibility_feed_export.eligibility_export as main

    main.db_session_raw = test_db_session

    WagesAndContributionsFactory.create()

    batch_output_dir = tmp_path / "batch1"
    batch_output_dir.mkdir()

    monkeypatch.setenv("OUTPUT_DIRECTORY_PATH", str(tmp_path))
    monkeypatch.setenv(
        "FINEOS_AWS_IAM_ROLE_ARN",
        "arn:aws:iam::000000000000:role/sompre-IAMRoles-CustomerAccountAccessRole-foobar",
    )
    monkeypatch.setenv("FINEOS_AWS_IAM_ROLE_EXTERNAL_ID", "123")

    response = main.handler({}, {})

    assert response["started_at"]
    assert response["completed_at"]
    assert response["employers_total_count"] == 1
    assert response["employers_success_count"] == 1
    assert response["employers_error_count"] == 0
    assert response["employers_skipped_count"] == 0
    assert response["employee_and_employer_pairs_total_count"] == 1
