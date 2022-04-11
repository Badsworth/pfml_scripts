import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List

import massgov.pfml.db.config as db_config
from massgov.pfml.util.strings import split_str


class RMVAPIBehavior(Enum):
    # Fully mocked endpoint
    MOCK = "fully_mocked"
    # Partially mocked endpoint, will call the RMV API when called with certain records. Mocked responses otherwise.
    PARTIAL_MOCK = "partially_mocked"
    # All requests hit RMV API
    NO_MOCK = "not_mocked"


@dataclass
class AppConfig:
    environment: str
    port: int
    enable_full_error_logs: bool
    cors_origins: List[str]
    db: db_config.DbConfig
    cognito_user_pool_id: str
    cognito_user_pool_client_id: str
    cognito_user_pool_keys_url: str
    enable_employee_endpoints: bool
    limit_ssn_fein_max_attempts: int
    rmv_api_behavior: RMVAPIBehavior
    rmv_check_mock_success: bool
    enable_application_fraud_check: bool
    dashboard_password: str
    new_plan_proofs_active_at: datetime
    enable_generate_1099_pdf: bool
    generate_1099_max_files: int
    enable_merge_1099_pdf: bool
    enable_upload_1099_pdf: bool
    upload_max_files_to_fineos: int
    enable_document_multipart_upload: bool
    enable_1099_testfile_generation: bool
    disable_sending_emails: bool
    enable_response_validation: bool
    enable_full_check_solution: bool


def get_config() -> AppConfig:
    return AppConfig(
        environment=str(os.environ.get("ENVIRONMENT")),
        port=int(os.environ.get("PORT", 1550)),
        enable_full_error_logs=os.environ.get("ENABLE_FULL_ERROR_LOGS", "0") == "1",
        cors_origins=split_str(os.environ.get("CORS_ORIGINS")),
        db=db_config.get_config(),
        cognito_user_pool_id=os.environ.get("COGNITO_USER_POOL_ID", ""),
        cognito_user_pool_client_id=os.environ.get("COGNITO_USER_POOL_CLIENT_ID", ""),
        cognito_user_pool_keys_url=os.environ.get("COGNITO_USER_POOL_KEYS_URL", ""),
        enable_employee_endpoints=os.environ.get("ENABLE_EMPLOYEE_ENDPOINTS", "0") == "1",
        limit_ssn_fein_max_attempts=int(os.environ.get("LIMIT_SSN_FEIN_MAX_ATTEMPTS", 5)),
        rmv_api_behavior=RMVAPIBehavior(
            os.environ.get("RMV_API_BEHAVIOR", RMVAPIBehavior.MOCK.value)
        ),
        # "1" always passes id proofing, "0" always fails id proofing
        rmv_check_mock_success=os.environ.get("RMV_CHECK_MOCK_SUCCESS", "1") == "1",
        enable_application_fraud_check=os.environ.get("ENABLE_APPLICATION_FRAUD_CHECK", "0") == "1",
        dashboard_password=os.environ.get("DASHBOARD_PASSWORD", ""),
        new_plan_proofs_active_at=datetime.fromisoformat(
            os.environ.get("NEW_PLAN_PROOFS_ACTIVE_AT", "2021-06-26 00:00:00+00:00")
        ),
        enable_generate_1099_pdf=os.environ.get("ENABLE_GENERATE_1099_PDF", "0") == "1",
        generate_1099_max_files=int(os.environ.get("GENERATE_1099_MAX_FILES", 1000)),
        enable_merge_1099_pdf=os.environ.get("ENABLE_MERGE_1099_PDF", "0") == "1",
        enable_upload_1099_pdf=os.environ.get("ENABLE_UPLOAD_1099_PDF", "0") == "1",
        upload_max_files_to_fineos=int(os.environ.get("UPLOAD_MAX_FILES_TO_FINEOS", 10)),
        enable_document_multipart_upload=os.environ.get("ENABLE_DOCUMENT_MULTIPART_UPLOAD", "0")
        == "1",
        enable_1099_testfile_generation=os.environ.get("TEST_FILE_GENERATION_1099", "0") == "1",
        # Sending emails is enabled by default. It must be disabled explicitly if
        # desired eg for local development
        disable_sending_emails=os.environ.get("DISABLE_SENDING_EMAILS", "0") == "1",
        enable_response_validation=os.environ.get("ENABLE_RESPONSE_VALIDATION", "0") == "1",
        enable_full_check_solution=os.environ.get("ENABLE_FULL_CHECK_SOLUTION", "0") == "1",
    )
