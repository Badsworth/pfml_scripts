import os
from dataclasses import dataclass
from enum import Enum
from typing import List

import massgov.pfml.db.config as db_config
from massgov.pfml.util.strings import split_str


class RMVCheckBehavior(Enum):
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
    cognito_user_pool_client_id: str
    cognito_user_pool_keys_url: str
    enable_employee_endpoints: bool
    # TODO: Remove this after rollout https://lwd.atlassian.net/browse/EMPLOYER-962
    enforce_verification: bool
    rmv_check_behavior: RMVCheckBehavior
    rmv_check_mock_success: bool
    enable_application_fraud_check: bool
    dashboard_password: str


def get_config() -> AppConfig:
    return AppConfig(
        environment=str(os.environ.get("ENVIRONMENT")),
        port=int(os.environ.get("PORT", 1550)),
        enable_full_error_logs=os.environ.get("ENABLE_FULL_ERROR_LOGS", "0") == "1",
        cors_origins=split_str(os.environ.get("CORS_ORIGINS")),
        db=db_config.get_config(),
        cognito_user_pool_client_id=os.environ.get("COGNITO_USER_POOL_CLIENT_ID", ""),
        cognito_user_pool_keys_url=os.environ.get("COGNITO_USER_POOL_KEYS_URL", ""),
        enable_employee_endpoints=os.environ.get("ENABLE_EMPLOYEE_ENDPOINTS", "0") == "1",
        enforce_verification=os.environ.get("ENFORCE_LEAVE_ADMIN_VERIFICATION", "0") == "1",
        rmv_check_behavior=RMVCheckBehavior(
            os.environ.get("RMV_CHECK_BEHAVIOR", RMVCheckBehavior.MOCK.value)
        ),
        # "1" always passes id proofing, "0" always fails id proofing
        rmv_check_mock_success=os.environ.get("RMV_CHECK_MOCK_SUCCESS", "1") == "1",
        enable_application_fraud_check=os.environ.get("ENABLE_APPLICATION_FRAUD_CHECK", "0") == "1",
        dashboard_password=os.environ.get("DASHBOARD_PASSWORD", ""),
    )
