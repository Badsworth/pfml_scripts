import decimal
import json
import os

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.db.models.factories import AbsencePeriodFactory
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FineosIAWWData,
    generate_iaww_extract_files,
)
from massgov.pfml.delegated_payments.task.process_iaww_from_fineos import (
    Configuration as IAWWTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_iaww_from_fineos import (
    _process_iaww_from_fineos as run_process_iaww_from_fineos,
)

date_str = "2020-08-01-12-00-00"


def test_iaww_extracts(
    mock_s3_bucket,
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    local_test_db_session,
    local_initialize_factories_session,
    local_test_db_other_session,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_IAWW_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    # Create IAWW extract files
    folder_path = os.path.join(f"s3://{mock_fineos_s3_bucket}", "DT2/dataexports/")
    dataset = [
        FineosIAWWData(aww_value="1331.66"),
        FineosIAWWData(aww_value="1538"),
        FineosIAWWData(aww_value="1700.50"),
        FineosIAWWData(aww_value="XX"),  # invalid amount
        FineosIAWWData(leave_request_id_value=""),  # missing leave request id
        FineosIAWWData(leaveplan_i_value_request=""),  # mistached instruction and request
    ]
    extract_records = generate_iaww_extract_files(dataset, folder_path, f"{date_str}-")

    leave_request_ids = []
    for extract_record in extract_records[
        payments_util.FineosExtractConstants.VBI_LEAVE_PLAN_REQUESTED_ABSENCE.file_name
    ]:
        leave_request_ids.append(extract_record["LEAVEREQUEST_ID"])

    absence_case_1 = AbsencePeriodFactory.create(fineos_leave_request_id=int(leave_request_ids[0]))
    absence_case_2 = AbsencePeriodFactory.create(fineos_leave_request_id=int(leave_request_ids[0]))
    absence_case_3 = AbsencePeriodFactory.create(fineos_leave_request_id=int(leave_request_ids[1]))
    absence_case_4 = AbsencePeriodFactory.create(fineos_leave_request_id=int(leave_request_ids[2]))
    absence_case_5 = AbsencePeriodFactory.create()

    run_process_iaww_from_fineos(
        db_session=local_test_db_session,
        log_entry_db_session=local_test_db_other_session,
        config=IAWWTaskConfiguration(["--steps", "ALL"]),
    )

    assert absence_case_1.fineos_average_weekly_wage == decimal.Decimal("1331.66")
    assert absence_case_2.fineos_average_weekly_wage == decimal.Decimal("1331.66")
    assert absence_case_3.fineos_average_weekly_wage == decimal.Decimal("1538")
    assert absence_case_4.fineos_average_weekly_wage == decimal.Decimal("1700.50")
    assert absence_case_5.fineos_average_weekly_wage is None

    import_logs = (
        local_test_db_other_session.query(ImportLog).order_by(ImportLog.import_log_id.asc()).all()
    )
    assert len(import_logs) == 2
    assert import_logs[0].source == "FineosExtractStep"
    assert import_logs[1].source == "IAWWExtractStep"

    extract_log_report = json.loads(import_logs[0].report)
    assert extract_log_report.get("records_processed_count", None) == 12

    iaww_process_log_report = json.loads(import_logs[1].report)
    assert iaww_process_log_report.get("paid_leave_instruction_record_count", None) == 6
    assert iaww_process_log_report.get("processed_paid_leave_instruction_count", None) == 6
    assert iaww_process_log_report.get("leave_plan_requested_absence_record_count", None) == 4
    assert (
        iaww_process_log_report.get("not_matching_leave_plan_requested_absence_record_count", None)
        == 1
    )
    assert iaww_process_log_report.get("absence_periods_iaww_added", None) == 4
    assert iaww_process_log_report.get("paid_leave_instruction_validation_issue_count", None) == 1
    assert (
        iaww_process_log_report.get(
            "leave_plan_requested_absence_record_validation_issue_count", None
        )
        == 1
    )
