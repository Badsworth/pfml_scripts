# See workflow here: https://lucid.app/lucidchart/edf54a33-1a3f-432d-82b7-157cf02667a4/edit?page=T9dnksYTkKxE#
# See implementation design here: https://lwd.atlassian.net/wiki/spaces/API/pages/1478918156/Local+E2E+Test+Suite

import csv
import json
import logging  # noqa: B1
import os
from typing import Any, Dict, List, Optional
from unittest import mock

from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import Flow, ImportLog, LkFlow, LkState, Payment, State
from massgov.pfml.db.models.payments import (
    FineosExtractVbiRequestedAbsence,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FINEOS_PAYMENT_EXTRACT_FILES,
    generate_payment_extract_files,
)
from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    ScenarioData,
    ScenarioDataConfig,
    ScenarioNameWithCount,
    generate_scenario_dataset,
    get_mock_address_client,
)
from massgov.pfml.delegated_payments.mock.scenarios import SCENARIO_DESCRIPTORS, ScenarioName
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_FINEOS_EXTRACT_REPORTS,
    get_report_by_name,
)
from massgov.pfml.delegated_payments.task.process_fineos_extracts import (
    Configuration as FineosTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_fineos_extracts import (
    _process_fineos_extracts as run_fineos_ecs_task,
)

# == Data Structures ==


class TestDataSet:
    def __init__(self, scenario_dataset: List[ScenarioData]):
        self.scenario_dataset = scenario_dataset
        self.scenario_dataset_map: Dict[ScenarioName, List[ScenarioData]] = {}

        for scenario_data in scenario_dataset:
            scenario_name: ScenarioName = scenario_data.scenario_descriptor.scenario_name

            if self.scenario_dataset_map.get(scenario_name) is None:
                self.scenario_dataset_map[scenario_name] = []
            self.scenario_dataset_map[scenario_name].append(scenario_data)

    def get_scenario_data_by_name(
        self, scenario_name: ScenarioName
    ) -> Optional[List[ScenarioData]]:
        return self.scenario_dataset_map[scenario_name]


# == The E2E Test ==


def test_e2e_pub_payments(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
    create_triggers,
):
    # TODO Validate error and warning logs
    # TODO Validate reference files

    # ========================================================================
    # Configuration / Setup
    # ========================================================================
    caplog.set_level(logging.INFO)  # noqa: B1

    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")

    s3_config = payments_config.get_s3_config()

    mock_experian_client = get_mock_address_client()

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    config = ScenarioDataConfig(
        scenarios_with_count=[
            ScenarioNameWithCount(scenario_name=scenario_descriptor.scenario_name, count=1)
            for scenario_descriptor in SCENARIO_DESCRIPTORS
        ]
    )
    scenario_dataset = generate_scenario_dataset(config=config)
    test_dataset = TestDataSet(scenario_dataset)

    # Confirm generated DB rows match expectations
    assert len(scenario_dataset) == len(SCENARIO_DESCRIPTORS)

    # ===============================================================================
    # [Day 1 - 12:00 PM] Generate FINEOS vendor extract files
    # ===============================================================================

    with freeze_time("2021-05-01 12:00:00"):
        fineos_data_export_path = s3_config.fineos_data_export_path

        # TODO generate claimant extract files

        generate_payment_extract_files(
            scenario_dataset, fineos_data_export_path, payments_util.get_now()
        )

        # TODO Confirm expected claimant files were generated

        # Confirm expected payment files were generated
        fineos_extract_date_prefix = get_current_timestamp_prefix()
        assert_files(
            fineos_data_export_path, FINEOS_PAYMENT_EXTRACT_FILES, fineos_extract_date_prefix
        )

    # ===============================================================================
    # [Day 1 - 7:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-01 19:00:00"):

        # == Run the task
        with mock.patch(
            "massgov.pfml.delegated_payments.address_validation._get_experian_client",
            return_value=mock_experian_client,
        ):
            run_fineos_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=FineosTaskConfiguration(["--steps", "ALL"]),
            )

        # == Validate created rows

        # TODO claimant rows

        # Payments
        payments = test_db_session.query(Payment).all()
        assert len(payments) == len(scenario_dataset)

        # Payment staging tables
        assert len(test_db_session.query(FineosExtractVbiRequestedAbsence).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpei).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiClaimDetails).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiPaymentDetails).all()) == len(payments)

        # == Validate employee state logs
        assert_employee_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,],
            end_state=State.DELEGATED_EFT_SEND_PRENOTE,
            flow=Flow.DELEGATED_EFT,
            db_session=test_db_session,
        )

        # TODO claimant file related state log assertions

        # == Validate payments state logs
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.ZERO_DOLLAR_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CANCELLATION_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
                ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
            ],
            end_state=State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_EMPLOYER_REIMBURSEMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN],
            end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PENDING_LEAVE_REQUEST_DECISION,
                ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
            ],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # == Validate audit report
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        payment_audit_report_outbound_folder_path = os.path.join(
            s3_config.dfml_report_outbound_path
        )

        payment_audit_report_sent_folder_path = os.path.join(
            s3_config.pfml_error_reports_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            date_folder,
        )

        audit_report_file_name = "Payment-Audit-Report.csv"

        assert_files(payment_audit_report_outbound_folder_path, [audit_report_file_name])
        assert_files(
            payment_audit_report_sent_folder_path, [audit_report_file_name], timestamp_prefix
        )

        audit_report_file_path = os.path.join(
            payment_audit_report_outbound_folder_path, audit_report_file_name
        )

        audit_report_parsed_csv_rows = parse_csv(audit_report_file_path)

        assert (
            len(audit_report_parsed_csv_rows) == 4
        )  # See DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT validation above

        payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
        )
        assert_csv_content(
            audit_report_parsed_csv_rows,
            {PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: [str(p.payment_id) for p in payments]},
        )

        # == Validate all reports
        for report_name in PROCESS_FINEOS_EXTRACT_REPORTS:
            report = get_report_by_name(report_name)
            file_name = f"{report.report_name.value}.csv"

            outbound_folder = os.path.join(s3_config.dfml_report_outbound_path)
            sent_folder = os.path.join(
                s3_config.pfml_error_reports_archive_path,
                payments_util.Constants.S3_OUTBOUND_SENT_DIR,
                date_folder,
            )

            assert_files(outbound_folder, [file_name])
            assert_files(sent_folder, [file_name], timestamp_prefix)

        # Validate metrics
        assert_metrics(
            test_db_other_session,
            "PaymentExtractStep",
            {
                "processed_payment_count": len(SCENARIO_DESCRIPTORS),
                "unapproved_leave_request_count": 1,
                "approved_prenote_count": 2,
                "zero_dollar_payment_count": 1,
                "cancellation_count": 1,
                "overpayment_count": 2,
                "employer_reimbursement_count": 1,
                "errored_payment_count": 4,  # See DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT state check above
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentAuditReportStep",
            {
                "payment_sampled_for_audit_count": 4,  # See DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT state check above
            },
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {"report_generated_count": len(PROCESS_FINEOS_EXTRACT_REPORTS)},
        )

        # TODO validate metrics for other steps when available

    # TODO - Day 2 PUB Processing ECS Task

    # TODO - Day 3 PUB Returns ECS Task


# == Assertion Helpers ==


def assert_files(folder_path, expected_files, file_prefix=""):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert (
            f"{file_prefix}{expected_file}" in files_in_folder
        ), f"Can not find {file_prefix}{expected_file} under path: {folder_path}, found files: {files_in_folder}"


def assert_payment_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: LkState,
    db_session: db.Session,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            payment = (
                db_session.query(Payment)
                .filter(
                    Payment.fineos_pei_c_value == scenario_data.payment_c_value,
                    Payment.fineos_pei_i_value == scenario_data.payment_i_value,
                )
                .one_or_none()
            )

            assert payment is not None

            state_log = state_log_util.get_latest_state_log_in_flow(
                payment, Flow.DELEGATED_PAYMENT, db_session
            )

            assert state_log is not None
            assert (
                state_log.end_state_id == end_state.state_id
            ), f"Unexpected payment state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}"


def assert_employee_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: LkState,
    flow: LkFlow,
    db_session: db.Session,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            employee = scenario_data.employee

            state_log = state_log_util.get_latest_state_log_in_flow(employee, flow, db_session)

            assert state_log is not None
            assert (
                state_log.end_state_id == end_state.state_id
            ), f"Unexpected employee state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}"


def assert_csv_content(rows: Dict[str, str], column_to_expected_values: Dict[str, List[str]]):
    def csv_has_column_value(column, expected_value):
        for row in rows:
            value = row.get(column, None)
            if value is not None and value == expected_value:
                return True

        return False

    for column, expected_values in column_to_expected_values.items():
        for expected_value in expected_values:
            assert csv_has_column_value(
                column, expected_value
            ), f"Expected csv column value not found - column: {column}, expected value: {expected_value}"


def assert_metrics(
    log_report_db_session: db.Session, log_report_name: str, metrics_expected_values: Dict[str, Any]
):
    log_report = (
        log_report_db_session.query(ImportLog)
        .filter(ImportLog.source == log_report_name)
        .order_by(ImportLog.start.desc())
        .first()
    )

    log_report = json.loads(log_report.report)
    for metric_key, expected_value in metrics_expected_values.items():
        value = log_report.get(metric_key, None)
        assert (
            value == expected_value
        ), f"Unexpected metric value in log report '{log_report_name}' - metric: {metric_key}, expected: {expected_value}, found: {value}"


# == Utility Helpers ==


def parse_csv(csv_file_path: str):
    parsed_csv = csv.DictReader(file_util.open_stream(csv_file_path))
    return list(parsed_csv)


def get_payments_in_end_state(db_session: db.Session, end_state: LkState) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=end_state,
        db_session=db_session,
    )

    return [state_log.payment for state_log in state_logs]


def get_current_date_folder():
    return payments_util.get_now().strftime("%Y-%m-%d")


def get_current_timestamp_prefix():
    return payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S-")
