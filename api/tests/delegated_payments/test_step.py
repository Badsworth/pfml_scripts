import json
from datetime import datetime

import pytest
from freezegun.api import freeze_time

from massgov.pfml import db
from massgov.pfml.db.models.factories import ImportLogFactory
from massgov.pfml.delegated_payments.pub import process_files_in_path_step
from massgov.pfml.delegated_payments.pub.process_check_return_step import ProcessCheckReturnFileStep
from massgov.pfml.delegated_payments.pub.process_nacha_return_step import ProcessNachaReturnFileStep


@pytest.mark.parametrize(
    "return_file_step,metric",
    [
        (ProcessNachaReturnFileStep, ProcessNachaReturnFileStep.Metrics.PROCESSED_ACH_FILE),
        (ProcessCheckReturnFileStep, ProcessCheckReturnFileStep.Metrics.PROCESSED_CHECKS_PAID_FILE),
        (
            ProcessCheckReturnFileStep,
            ProcessCheckReturnFileStep.Metrics.PROCESSED_CHECKS_OUTSTANDING_FILE,
        ),
    ],
)
@freeze_time("2021-12-28")  # Tue
@pytest.mark.parametrize(
    "business_days,created_at,found_log",
    [
        (1, datetime(2021, 12, 28), True),  # Tue
        (2, datetime(2021, 12, 27), True),  # Mon
        (2, datetime(2021, 12, 24), True),  # Mon
        (3, datetime(2021, 12, 23), True),  # Thu
        (4, datetime(2021, 12, 22), True),  # Wed
        (4, datetime(2021, 12, 21), False),  # Tue
        (4, datetime(2021, 12, 20), False),  # Mon
    ],
)
def test_check_if_processed_within_x_days(
    test_db_session: db.Session,
    initialize_factories_session,
    return_file_step: process_files_in_path_step.ProcessFilesInPathStep,
    metric: str,
    business_days: int,
    created_at: datetime,
    found_log: bool,
):
    import_type = return_file_step.__name__
    metrics = {metric: 1}
    report_str = json.dumps(metrics, indent=2)
    ImportLogFactory.create(import_type=import_type, report=report_str, created_at=created_at)

    # Create dummy logs with utcnow
    for _ in range(5):
        metrics = {metric: 0}
        report_str = json.dumps(metrics, indent=2)
        ImportLogFactory.create(
            import_type=import_type, report=report_str, created_at=datetime.utcnow()
        )

    was_processed_within_x_days = return_file_step.check_if_processed_within_x_days(
        test_db_session, metric, business_days
    )

    assert was_processed_within_x_days == found_log
