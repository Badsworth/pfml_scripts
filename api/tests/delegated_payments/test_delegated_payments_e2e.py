# See workflow here: https://lucid.app/lucidchart/edf54a33-1a3f-432d-82b7-157cf02667a4/edit?page=T9dnksYTkKxE#
# See implementation design here: https://lwd.atlassian.net/wiki/spaces/API/pages/1478918156/Local+E2E+Test+Suite

import csv
import json
import logging  # noqa: B1
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from unittest import mock

from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Flow,
    ImportLog,
    LkFlow,
    LkState,
    Payment,
    PubError,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.payments import (
    FineosExtractVbiRequestedAbsence,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
)
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import CiIndex
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FINEOS_PAYMENT_EXTRACT_FILES,
    generate_payment_extract_files,
)
from massgov.pfml.delegated_payments.mock.generate_check_response import PubCheckResponseGenerator
from massgov.pfml.delegated_payments.mock.pub_ach_response_generator import PubACHResponseGenerator
from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    ScenarioData,
    ScenarioDataConfig,
    ScenarioNameWithCount,
    generate_scenario_dataset,
    get_mock_address_client,
)
from massgov.pfml.delegated_payments.mock.scenarios import SCENARIO_DESCRIPTORS, ScenarioName
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    CREATE_PUB_FILES_REPORTS,
    PROCESS_FINEOS_EXTRACT_REPORTS,
    PROCESS_PUB_RESPONSES_REPORTS,
    ReportName,
    get_report_by_name,
)
from massgov.pfml.delegated_payments.task.process_fineos_extracts import (
    Configuration as FineosTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_fineos_extracts import (
    _process_fineos_extracts as run_fineos_ecs_task,
)
from massgov.pfml.delegated_payments.task.process_pub_payments import (
    Configuration as ProcessPubPaymentsTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_pub_payments import (
    _process_pub_payments as run_process_pub_payments_ecs_task,
)
from massgov.pfml.delegated_payments.task.process_pub_responses import (
    Configuration as ProcessPubResponsesTaskConfiguration,
)
from massgov.pfml.delegated_payments.task.process_pub_responses import (
    _process_pub_responses as run_process_pub_responses_ecs_task,
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
        return self.scenario_dataset_map.get(scenario_name, None)

    def get_scenario_data_by_payment_ci(self, c_value: str, i_value: str) -> Optional[ScenarioData]:
        for scenario_data in self.scenario_dataset:
            if CiIndex(c=scenario_data.payment_c_value, i=scenario_data.payment_i_value) == CiIndex(
                c=c_value, i=i_value
            ):
                return scenario_data
        return None

    def populate_scenario_data_payments(self, db_session) -> None:
        for scenario_data in self.scenario_dataset:
            payment = (
                db_session.query(Payment)
                .filter(
                    Payment.fineos_pei_c_value == scenario_data.payment_c_value,
                    Payment.fineos_pei_i_value == scenario_data.payment_i_value,
                )
                .one_or_none()
            )
            scenario_data.payment = payment


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
    # TODO make metric count numbers more readable (use variables etc), check diffs in state

    # ========================================================================
    # Configuration / Setup
    # ========================================================================
    caplog.set_level(logging.ERROR)  # noqa: B1

    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")

    monkeypatch.setenv("DFML_PUB_ACCOUNT_NUMBER", "123456789")
    monkeypatch.setenv("DFML_PUB_ROUTING_NUMBER", "234567890")
    monkeypatch.setenv("PUB_PAYMENT_STARTING_CHECK_NUMBER", "100")

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

        # TODO generate claimant extract files - PUB-165

        generate_payment_extract_files(
            scenario_dataset, fineos_data_export_path, payments_util.get_now()
        )

        # TODO Confirm expected claimant files were generated - PUB-165

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

        test_dataset.populate_scenario_data_payments(test_db_session)

        # == Validate created rows

        assert_ref_file(
            f"{s3_config.pfml_fineos_extract_archive_path}processed/2021-05-01-08-00-00-payment-extract",
            ReferenceFileType.FINEOS_PAYMENT_EXTRACT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_error_reports_archive_path}/sent/2021-05-01/2021-05-01-15-00-00-Payment-Audit-Report.csv",
            ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_error_reports_archive_path}/sent/2021-05-01/2021-05-01-15-00-00-claimant-extract-error-report.csv",
            ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_error_reports_archive_path}/sent/2021-05-01/2021-05-01-15-00-00-payment-extract-error-report.csv",
            ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_error_reports_archive_path}/sent/2021-05-01/2021-05-01-15-00-00-address-error-report.csv",
            ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE,
            test_db_session,
        )
        # TODO claimant rows - PUB-165

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

        # TODO claimant file related state log assertions - PUB-165

        # == Validate payments state logs
        stage_1_happy_path_scenarios = [
            ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
            ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
            ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
        ]
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_happy_path_scenarios,
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.AUDIT_REJECTED,
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
                ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
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

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN],
            end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.CLAIM_NOT_ID_PROOFED,
                ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
                ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
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

        assert len(audit_report_parsed_csv_rows) == (
            len(stage_1_happy_path_scenarios) + 1 + 5 + 3 + 1 + 1
        )  # happy path + audit_rejected + non_prenote_pub_returns + outstanding_rejected_checks + invalid prenote ID + invalid payment ID

        payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
        )
        assert_csv_content(
            audit_report_parsed_csv_rows,
            {PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: [str(p.payment_id) for p in payments]},
        )

        # == Validate all reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_FINEOS_EXTRACT_REPORTS,
        )

        # == Validate metrics
        assert_metrics(
            test_db_other_session,
            "PaymentExtractStep",
            {
                "processed_payment_count": len(SCENARIO_DESCRIPTORS),
                "not_pending_or_approved_leave_request_count": 1,
                "approved_prenote_count": 12,
                "zero_dollar_payment_count": 1,
                "cancellation_count": 1,
                "overpayment_count": 3,
                "employer_reimbursement_count": 1,
                "errored_payment_count": 8,  # See DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT state check above
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentAuditReportStep",
            {
                "payment_sampled_for_audit_count": (
                    len(stage_1_happy_path_scenarios) + 1 + 5 + 3 + 1 + 1
                ),  # happy path + audit_rejected + non_prenote_pub_returns + outstanding_rejected_checks + check_not_found + invalid_payment_id
            },
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {"report_generated_count": len(PROCESS_FINEOS_EXTRACT_REPORTS)},
        )

        # TODO validate metrics for other steps when available

    # ===============================================================================
    # [Day 2 - 12:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-02 12:00:00"):
        rejects_file_received_path = os.path.join(
            s3_config.pfml_payment_rejects_archive_path,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            "Payment-Rejects.csv",
        )
        generate_rejects_file(test_dataset, audit_report_file_path, rejects_file_received_path)

    # ==============================================================================================
    # [Day 2 - 2:00 PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ==============================================================================================

    with freeze_time("2021-05-02 14:00:00"):
        # == Run the task
        run_process_pub_payments_ecs_task(
            db_session=test_db_session,
            log_entry_db_session=test_db_other_session,
            config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
        )

        assert_ref_file(
            f"{s3_config.pfml_payment_rejects_archive_path}/processed/2021-05-02/Payment-Rejects.csv",
            ReferenceFileType.DELEGATED_PAYMENT_REJECTS,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/2021-05-02/2021-05-02-10-00-00-EOLWD-DFML-EZ-CHECK.csv",
            ReferenceFileType.PUB_EZ_CHECK,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/2021-05-02/2021-05-02-10-00-00-EOLWD-DFML-POSITIVE-PAY.txt",
            ReferenceFileType.PUB_POSITIVE_PAYMENT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_ach_archive_path}/sent/2021-05-02/2021-05-02-10-00-00-EOLWD-DFML-NACHA",
            ReferenceFileType.PUB_NACHA,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_fineos_writeback_archive_path}sent/2021-05-02/2021-05-02-10-00-00-pei_writeback.csv",
            ReferenceFileType.PEI_WRITEBACK,
            test_db_session,
        )

        for report_name in CREATE_PUB_FILES_REPORTS:
            assert_ref_file(
                f"{s3_config.pfml_error_reports_archive_path}/sent/2021-05-02/2021-05-02-10-00-00-{report_name.value}.csv",
                ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE,
                test_db_session,
            )

        # == Validate payments state logs

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
            ],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.ZERO_DOLLAR_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CANCELLATION_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
                ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
                ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
            ],
            end_state=State.DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_PAYMENT_FINEOS_WRITEBACK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=test_db_session,
        )

        # == Rejects processed
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        rejects_file_received_path = os.path.join(
            s3_config.pfml_payment_rejects_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        assert_files(rejects_file_received_path, ["Payment-Rejects.csv"])

        # == Transaction Files
        pub_folder_path = os.path.join(s3_config.pub_moveit_outbound_path)
        pub_check_archive_folder_path = os.path.join(
            s3_config.pfml_pub_check_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            date_folder,
        )
        pub_ach_archive_folder_path = os.path.join(
            s3_config.pfml_pub_ach_archive_path,
            payments_util.Constants.S3_OUTBOUND_SENT_DIR,
            date_folder,
        )
        dfml_report_outbound_path = os.path.join(s3_config.dfml_report_outbound_path)

        assert_files(
            dfml_report_outbound_path, [f"{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"]
        )
        assert_files(
            pub_check_archive_folder_path,
            [f"{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"],
            timestamp_prefix,
        )

        assert_files(pub_folder_path, [f"{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt"])
        assert_files(
            pub_check_archive_folder_path,
            [f"{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt"],
            timestamp_prefix,
        )

        assert_files(pub_folder_path, [payments_util.Constants.FILE_NAME_PUB_NACHA])
        assert_files(
            pub_ach_archive_folder_path,
            [payments_util.Constants.FILE_NAME_PUB_NACHA],
            timestamp_prefix,
        )

        # TODO validate content of outgoing files

        # == Writeback
        writeback_folder_path = os.path.join(s3_config.fineos_data_import_path)
        assert_files(writeback_folder_path, ["pei_writeback.csv"], get_current_timestamp_prefix())

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            CREATE_PUB_FILES_REPORTS,
        )

        # == Metrics
        assert_metrics(
            test_db_other_session,
            "PaymentRejectsStep",
            {"rejected_payment_count": 1, "accepted_payment_count": 20},
        )

        assert_metrics(
            test_db_other_session,
            "PaymentMethodsSplitStep",
            {"ach_payment_count": 11, "check_payment_count": 9},
        )

        assert_metrics(
            test_db_other_session, "FineosPeiWritebackStep", {"writeback_record_count": 26,},
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {"report_generated_count": len(CREATE_PUB_FILES_REPORTS)},
        )

        # TODO file transaction metrics when available

    # ===============================================================================
    # [Day 3 - 7:00 AM] PUB sends ACH and Check response files
    # ===============================================================================

    with freeze_time("2021-05-03 07:00:00"):
        pub_response_folder = os.path.join(s3_config.pub_moveit_inbound_path)
        pub_ach_response_generator = PubACHResponseGenerator(
            test_dataset.scenario_dataset, pub_response_folder
        )
        pub_ach_response_generator.run()

        pub_check_response_generator = PubCheckResponseGenerator(
            test_dataset.scenario_dataset, pub_response_folder
        )
        pub_check_response_generator.run()

    # ==============================================================================================
    # [Day 3 - 9:00 AM] Run the PUB Response ECS task - response, writeback, reports
    # ==============================================================================================

    with freeze_time("2021-05-03 09:00:00"):

        # == Run the task
        run_process_pub_responses_ecs_task(
            db_session=test_db_session,
            log_entry_db_session=test_db_other_session,
            config=ProcessPubResponsesTaskConfiguration(["--steps", "ALL"]),
        )

        # == Validate payment states

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ],
            end_state=State.DELEGATED_PAYMENT_COMPLETE,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ],
            end_state=State.ERRORED_PEI_WRITEBACK_SENT,
            db_session=test_db_session,
        )

        # Unchanged
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
            db_session=test_db_session,
        )

        # Unchanged
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
            ],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_SENT_CHECK,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ],
            end_state=State.ERRORED_PEI_WRITEBACK_SENT,
            db_session=test_db_session,
        )

        # == Assert files

        # processed ach return files
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        pub_ach_response_processed_folder = os.path.join(
            s3_config.pfml_pub_ach_archive_path,
            date_folder,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
        assert_files(
            pub_ach_response_processed_folder,
            [payments_util.Constants.FILE_NAME_PUB_NACHA],
            timestamp_prefix,
        )

        # processed check return files
        pub_check_response_processed_folder = os.path.join(
            s3_config.pfml_pub_check_archive_path,
            date_folder,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
        positive_pay_check_response_file = (
            f"Paid-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.csv"
        )
        outstanding_check_response_file = (
            f"Outstanding-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.csv"
        )
        assert_files(
            pub_check_response_processed_folder,
            [positive_pay_check_response_file, outstanding_check_response_file],
            timestamp_prefix,
        )

        # == PubError TODO adjust as metric based scenarios below are added
        assert len(test_db_session.query(PubError).all()) == (
            2 + 2 + 2 + 3 + 1 + 1 + 1 + 1
        )  # eft_prenote_unexpected_state_count + payment_complete_with_change_count + payment_rejected_count + payment_failed_by_check + unknown_id_format_count + invalid_check_number + invalid_eft_id

        # == Metrics
        assert_metrics(
            test_db_other_session,
            "ProcessNachaReturnFileStep",
            {
                "warning_count": 0,
                "ach_return_count": 6,
                "change_notification_count": 3,
                "eft_prenote_count": 3,
                "payment_count": 5,
                "unknown_id_format_count": 1,
                "eft_prenote_id_not_found_count": 1,
                "eft_prenote_unexpected_state_count": 1,
                "eft_prenote_already_approved_count": 1,
                "eft_prenote_rejected_count": 0,  # TODO add scenario
                "payment_id_not_found_count": 1,
                "payment_rejected_count": 2,  # Both prenotes
                "payment_already_rejected_count": 0,
                "payment_unexpected_state_count": 0,
                "payment_complete_with_change_count": 2,  # TODO validate
                "payment_already_complete_count": 0,  # TODO add scenario?
                "payment_notification_unexpected_state_count": 0,  # TODO add scenario
            },
        )

        # Outstanding check response
        assert_metrics(
            test_db_other_session,
            "ProcessCheckReturnFileStep",
            {
                "warning_count": 0,
                "check_payment_count": 5,
                "payment_complete_by_paid_check": 0,
                "payment_still_outstanding": 2,
                "payment_failed_by_check": 3,
                "check_number_not_found_count": 0,
                "payment_unexpected_state_count": 0,  # TODO add scenario
            },
            log_report_index=1,  # second when sorted in start time desc order
            description="Outstanding check responses",
        )

        # Positive pay check response
        assert_metrics(
            test_db_other_session,
            "ProcessCheckReturnFileStep",
            {
                "warning_count": 0,
                "check_payment_count": 4,
                "payment_complete_by_paid_check": 3,
                "payment_still_outstanding": 0,
                "payment_failed_by_check": 0,
                "check_number_not_found_count": 1,
                "payment_unexpected_state_count": 0,
            },
            log_report_index=0,  # first when sorted by import log id desc order
            description="Positive pay check responses",
        )

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_PUB_RESPONSES_REPORTS,
        )

    # == Day 4
    # TODO new extract to work with same payments (maybe reuse the same extract with name updated)
    # - prenotes should move along
    # - all others should error since they are already processed


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
            payment = scenario_data.payment

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


def assert_reports(
    reports_folder_path: str, reports_archive_folder_path: str, report_names: List[ReportName],
):
    date_folder = get_current_date_folder()
    timestamp_prefix = get_current_timestamp_prefix()

    for report_name in report_names:
        report = get_report_by_name(report_name)
        file_name = f"{report.report_name.value}.csv"

        outbound_folder = reports_folder_path
        sent_folder = os.path.join(
            reports_archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder,
        )

        assert_files(outbound_folder, [file_name])
        assert_files(sent_folder, [file_name], timestamp_prefix)


def assert_metrics(
    log_report_db_session: db.Session,
    log_report_name: str,
    metrics_expected_values: Dict[str, Any],
    description: str = "",
    log_report_index: int = 0,  # we may have more than one report for a step
):
    log_reports = (
        log_report_db_session.query(ImportLog)
        .filter(ImportLog.source == log_report_name)
        .order_by(ImportLog.import_log_id.desc())
        .all()
    )

    log_report = log_reports[log_report_index]
    log_report = json.loads(log_report.report)

    assertion_errors = []
    for metric_key, expected_value in metrics_expected_values.items():
        value = log_report.get(metric_key, None)
        if value != expected_value:
            assertion_errors.append(
                f"metric: {metric_key}, expected: {expected_value}, found: {value}\n"
            )

    errors = "".join(assertion_errors)
    assert (
        len(assertion_errors) == 0
    ), f"Unexpected metric value(s) in log report '{log_report_name}', description: {description}\n{errors}"


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


def generate_rejects_file(test_dataset: TestDataSet, audit_file_path: str, rejects_file_path: str):
    parsed_audit_rows = parse_csv(audit_file_path)

    csv_file = file_util.write_file(rejects_file_path)
    csv_output = csv.DictWriter(
        csv_file,
        fieldnames=asdict(PAYMENT_AUDIT_CSV_HEADERS).values(),
        lineterminator="\n",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    )
    csv_output.writeheader()

    for parsed_audit_row in parsed_audit_rows:
        c_value = parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.c_value]
        i_value = parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.i_value]

        scenario_data = test_dataset.get_scenario_data_by_payment_ci(c_value, i_value)
        assert scenario_data, f"Can not find scenario data with c: {c_value}, i:{i_value}"

        if not scenario_data.scenario_descriptor.is_audit_approved:
            parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity] = "Y"

    csv_output.writerows(parsed_audit_rows)
    csv_file.close()


def assert_ref_file(file_path: str, ref_file_type: ReferenceFileType, db_session: db.Session):
    found = (
        db_session.query(ReferenceFile)
        .filter(ReferenceFile.file_location == file_path)
        .filter(ReferenceFile.reference_file_type_id == ref_file_type.reference_file_type_id)
        .one_or_none()
    )

    assert found is not None
