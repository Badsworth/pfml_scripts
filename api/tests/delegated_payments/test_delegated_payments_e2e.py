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
from massgov.pfml.delegated_payments.mock.scenarios import (
    DELAYED_SCENARIO_DESCRIPTORS,
    SCENARIO_DESCRIPTORS,
    ScenarioDescriptor,
    ScenarioName,
)
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
from massgov.pfml.experian.physical_address.client.mock import MockClient

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
                .order_by(Payment.created_at.desc())
                .first()
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

    # ========================================================================
    # Configuration / Setup
    # ========================================================================

    caplog.set_level(logging.ERROR)  # noqa: B1
    setup_common_env_variables(monkeypatch)
    s3_config = payments_config.get_s3_config()
    mock_experian_client = get_mock_address_client()

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    test_dataset = generate_test_dataset(SCENARIO_DESCRIPTORS)
    # Confirm generated DB rows match expectations
    assert len(test_dataset.scenario_dataset) == len(SCENARIO_DESCRIPTORS)

    # ===============================================================================
    # [Day 1 - Between 7:00 - 9:00 PM] Generate FINEOS vendor extract files
    # ===============================================================================

    with freeze_time("2021-05-01 20:00:00", tz_offset=5):
        fineos_timestamp_prefix = get_current_timestamp_prefix()

        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 1 - After 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-01 21:30:00", tz_offset=5):
        # == Run the task
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        # == Validate created rows

        # TODO claimant rows - PUB-165

        # Payments
        payments = test_db_session.query(Payment).all()
        assert len(payments) == len(test_dataset.scenario_dataset)

        # Payment staging tables
        assert len(test_db_session.query(FineosExtractVbiRequestedAbsence).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpei).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiClaimDetails).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiPaymentDetails).all()) == len(payments)

        # == Validate employee state logs
        assert_employee_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,
                # ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                # ScenarioName.PUB_ACH_PRENOTE_RETURN,
                # ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ],
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
                ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID
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
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID,
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
        assert len(audit_report_parsed_csv_rows) == len(
            [
                ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID
            ]
        )

        payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
        )
        assert_csv_content(
            audit_report_parsed_csv_rows,
            {PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: [str(p.payment_id) for p in payments]},
        )

        # Validate reference files
        assert_ref_file(
            f"{s3_config.pfml_fineos_extract_archive_path}processed/{fineos_timestamp_prefix}payment-extract",
            ReferenceFileType.FINEOS_PAYMENT_EXTRACT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_error_reports_archive_path}/sent/{date_folder}/{timestamp_prefix}Payment-Audit-Report.csv",
            ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT,
            test_db_session,
        )

        # == Validate all reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_FINEOS_EXTRACT_REPORTS,
            test_db_session,
        )

        # == Validate metrics
        assert_metrics(test_db_other_session, "StateCleanupStep", {"audit_state_cleanup_count": 0})

        assert_metrics(
            test_db_other_session,
            "ClaimantExtractStep",
            {
                "claim_not_found_count": 0,
                "eft_found_count": 0,
                "eft_rejected_count": 0,
                "employee_feed_record_count": 0,
                "employee_not_found_count": 0,
                "errored_claimant_count": 0,
                "evidence_not_id_proofed_count": 0,
                "new_eft_count": 0,
                "processed_requested_absence_count": 0,
                "valid_claimant_count": 0,
                "vbi_requested_absence_som_record_count": 0,
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentExtractStep",
            {
                "active_payment_error_count": 0,
                "already_active_payment_count": 0,
                "approved_prenote_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "cancellation_count": len([ScenarioName.CANCELLATION_PAYMENT]),
                "claim_details_record_count": len(SCENARIO_DESCRIPTORS),
                "claim_not_found_count": 0,
                "claimant_mismatch_count": 0,
                "eft_found_count": len(
                    [
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "employee_missing_in_db_count": 0,
                "employer_reimbursement_count": len([ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT]),
                "errored_payment_count": len(
                    [
                        ScenarioName.CLAIM_NOT_ID_PROOFED,
                        ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
                        ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "new_eft_count": len([ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE]),
                "not_approved_prenote_count": len(
                    [
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "not_pending_or_approved_leave_request_count": len(
                    [ScenarioName.REJECTED_LEAVE_REQUEST_DECISION]
                ),
                "overpayment_count": len(
                    [
                        ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
                        ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
                        ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
                    ]
                ),
                "payment_details_record_count": len(SCENARIO_DESCRIPTORS),
                "pei_record_count": len(SCENARIO_DESCRIPTORS),
                "prenote_past_waiting_period_approved_count": 0,
                "processed_payment_count": len(SCENARIO_DESCRIPTORS),
                "requested_absence_record_count": len(SCENARIO_DESCRIPTORS),
                "standard_valid_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "tax_identifier_missing_in_db_count": len(
                    [ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB]
                ),
                "zero_dollar_payment_count": len([ScenarioName.ZERO_DOLLAR_PAYMENT]),
            },
        )

        assert_metrics(
            test_db_other_session,
            "AddressValidationStep",
            {
                "invalid_experian_format": 0,
                "invalid_experian_response": 0,
                "multiple_experian_matches": len(
                    [ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN]
                ),
                "no_experian_match_count": len(
                    [
                        ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                    ]
                ),
                "previously_validated_match_count": 0,
                "valid_experian_format": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "validated_address_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "verified_experian_match": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentAuditReportStep",
            {
                "payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "payment_sampled_for_audit_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "sampled_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
            },
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {
                "report_error_count": 0,
                "report_generated_count": len(PROCESS_FINEOS_EXTRACT_REPORTS),
            },
        )

    # ===============================================================================
    # [Day 2 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-02 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset)

    # ==============================================================================================
    # [Day 2 - Between 5:00 - 7:00 PM PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ==============================================================================================

    with freeze_time("2021-05-02 18:00:00", tz_offset=5):
        # == Run the task
        run_process_pub_payments_ecs_task(
            db_session=test_db_session,
            log_entry_db_session=test_db_other_session,
            config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
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
                ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
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

        # Validate reference files
        assert_ref_file(
            f"{s3_config.pfml_payment_rejects_archive_path}/processed/{date_folder}/Payment-Rejects.csv",
            ReferenceFileType.DELEGATED_PAYMENT_REJECTS,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv",
            ReferenceFileType.PUB_EZ_CHECK,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt",
            ReferenceFileType.PUB_POSITIVE_PAYMENT,
            test_db_session,
        )

        assert_ref_file(
            f"{s3_config.pfml_pub_ach_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_NACHA}",
            ReferenceFileType.PUB_NACHA,
            test_db_session,
        )

        # TODO validate content of outgoing files

        # == Writeback
        writeback_folder_path = os.path.join(s3_config.fineos_data_import_path)
        assert_files(writeback_folder_path, ["pei_writeback.csv"], get_current_timestamp_prefix())

        assert_ref_file(
            f"{s3_config.pfml_fineos_writeback_archive_path}sent/{date_folder}/{timestamp_prefix}pei_writeback.csv",
            ReferenceFileType.PEI_WRITEBACK,
            test_db_session,
        )

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            CREATE_PUB_FILES_REPORTS,
            test_db_session,
        )

        # == Metrics
        assert_metrics(
            test_db_other_session,
            "PickupResponseFilesStep",
            {
                "Payment-Audit-Report_file_moved_count": 0,
                "EOLWD-DFML-POSITIVE-PAY_file_moved_count": 0,
                "EOLWD-DFML-NACHA_file_moved_count": 0,
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentRejectsStep",
            {
                "accepted_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "parsed_rows_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "payment_state_log_missing_count": 0,
                "payment_state_log_not_in_audit_response_pending_count": 0,
                "rejected_payment_count": len([ScenarioName.AUDIT_REJECTED]),
                "state_logs_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentMethodsSplitStep",
            {
                "ach_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "check_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
            },
        )

        assert_metrics(
            test_db_other_session,
            "TransactionFileCreatorStep",
            {
                "ach_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "ach_prenote_count": len([ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE]),
            },
        )

        assert_metrics(
            test_db_other_session,
            "FineosPeiWritebackStep",
            {
                "cancelled_payment_count": len([ScenarioName.CANCELLATION_PAYMENT]),
                "check_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,

                    ]
                ),
                "eft_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                    ]
                ),
                "employer_reimbursement_payment_count": len(
                    [ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT]
                ),
                "errored_payment_writeback_items_count": 0,
                "overpayment_count": len(
                    [
                        ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
                        ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
                        ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
                    ]
                ),
                "payment_writeback_two_items_count": 0,
                "writeback_record_count": len(
                    [
                        ScenarioName.CANCELLATION_PAYMENT,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PENDING_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_IN_REVIEW_LEAVE_REQUEST_DECISION,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,
                        ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
                        ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
                        ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
                        ScenarioName.ZERO_DOLLAR_PAYMENT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,

                    ]
                ),
                "zero_dollar_payment_count": len([ScenarioName.ZERO_DOLLAR_PAYMENT]),
            },
        )

        # ReportStep
        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {"report_error_count": 0, "report_generated_count": len(CREATE_PUB_FILES_REPORTS),},
        )

        # TODO file transaction metrics when available

    # ===============================================================================
    # [Day 3 - 9:00 AM] PUB sends ACH and Check response files
    # ===============================================================================

    with freeze_time("2021-05-03 09:00:00", tz_offset=5):
        generate_pub_returns(test_dataset)

    # ==============================================================================================
    # [Day 3 - 11:00 AM] Run the PUB Response ECS task - response, writeback, reports
    # ==============================================================================================

    with freeze_time("2021-05-03 11:00:00", tz_offset=5):

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
        nacha_filenames = [payments_util.Constants.FILE_NAME_PUB_NACHA]
        assert_files(pub_ach_response_processed_folder, nacha_filenames, timestamp_prefix)

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
        positive_pay_filenames = [positive_pay_check_response_file, outstanding_check_response_file]
        assert_files(pub_check_response_processed_folder, positive_pay_filenames, timestamp_prefix)

        # == PubError TODO adjust as metric based scenarios below are added
        assert len(test_db_session.query(PubError).all()) == len(
            [
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND,
            ]
        )

        # == Metrics

        assert_metrics(
            test_db_other_session,
            "PickupResponseFilesStep",
            {
                "Payment-Audit-Report_file_moved_count": 0,
                "EOLWD-DFML-POSITIVE-PAY_file_moved_count": len(positive_pay_filenames),
                "EOLWD-DFML-NACHA_file_moved_count": len(nacha_filenames),
            },
        )

        assert_metrics(
            test_db_other_session,
            "ProcessNachaReturnFileStep",
            {
                "ach_return_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID
                    ]
                ),
                "change_notification_count": len(
                    [
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                    ]
                ),
                # "eft_prenote_already_approved_count": len(
                #     [
                #         ScenarioName.PUB_ACH_PRENOTE_RETURN,
                #         ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                #     ]
                # ),  # TODO validate
                "eft_prenote_count": len(
                    [
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID
                    ]
                ),
                "eft_prenote_id_not_found_count": len([
                    ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID
                ]),
                "eft_prenote_rejected_count": len([
                    ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID
                ]),
                "eft_prenote_unexpected_state_count": 0,
                "payment_already_complete_count": 0,  # TODO add scenario?
                "payment_complete_with_change_count": len(
                    [ScenarioName.PUB_ACH_FAMILY_RETURN, ScenarioName.PUB_ACH_MEDICAL_RETURN,]
                ),  # TODO validate
                "payment_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                    ]
                ),
                "payment_id_not_found_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID
                    ]
                ),
                "payment_already_rejected_count": 0,  # TODO add scenario
                "payment_notification_unexpected_state_count": 0,
                "payment_rejected_count": len(
                    [
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                    ]
                ),
                "payment_unexpected_state_count": 0,
                "unknown_id_format_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_EFT_PRENOTE_ID,
                    ]
                ),
                "warning_count": 0,
            },
        )

        # Outstanding check response
        assert_metrics(
            test_db_other_session,
            "ProcessCheckReturnFileStep",
            {
                "check_number_not_found_count": len(
                    [

                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND
                    ]
                ),
                "check_payment_count": len(
                    [
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                    ]
                ),
                "payment_complete_by_paid_check": 0,
                "payment_failed_by_check": len(
                    [
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                    ]
                ),
                "payment_still_outstanding": len(
                    [
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                    ]
                ),
                "payment_unexpected_state_count": 0,
                "warning_count": 0,
            },
            log_report_index=1,  # second when sorted in start time desc order
            description="Outstanding check responses",
        )

        # Positive pay check response
        assert_metrics(
            test_db_other_session,
            "ProcessCheckReturnFileStep",
            {
                "check_number_not_found_count": len(
                    [
                        ScenarioName.CHECK_PAYMENT_CHECK_NUMBER_NOT_FOUND
                    ]
                ),
                "check_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                    ]
                ),
                "payment_complete_by_paid_check": len(
                    [
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                    ]
                ),
                "payment_failed_by_check": 0,
                "payment_still_outstanding": 0,
                "payment_unexpected_state_count": 0,
                "warning_count": 0,
            },
            log_report_index=0,  # first when sorted by import log id desc order
            description="Positive pay check responses",
        )

        assert_metrics(
            test_db_other_session,
            "FineosPeiWritebackStep",
            {
                "cancelled_payment_count": 0,
                "check_payment_count": 0,
                "eft_payment_count": 0,
                "employer_reimbursement_payment_count": 0,
                "errored_payment_writeback_items_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                    ]
                ),
                "overpayment_count": 0,
                "payment_writeback_two_items_count": len(
                    [
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                    ]
                ),
                "writeback_record_count": len(
                    [
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_PAYMENT_ADDRESS_MULTIPLE_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                    ]
                ),
                "zero_dollar_payment_count": 0,
            },
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {
                "report_error_count": 0,
                "report_generated_count": len([PROCESS_PUB_RESPONSES_REPORTS]),
            },
        )

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_PUB_RESPONSES_REPORTS,
            test_db_session,
        )

    # ===============================================================================
    # [Day 9 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-09 18:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 9 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-09 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.NO_PRIOR_EFT_ACCOUNT_ON_EMPLOYEE,],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        # validate other scenarios that have reached an end state are erroring out
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_happy_path_scenarios,
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )


def test_e2e_pub_payments_delayed_scenarios(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
    create_triggers,
):
    # ========================================================================
    # Configuration / Setup
    # ========================================================================

    caplog.set_level(logging.ERROR)  # noqa: B1
    setup_common_env_variables(monkeypatch)
    mock_experian_client = get_mock_address_client()

    # ========================================================================
    # Data Setup - Mirror DOR Import + Claim Application
    # ========================================================================

    test_dataset = generate_test_dataset(DELAYED_SCENARIO_DESCRIPTORS)
    # Confirm generated DB rows match expectations
    assert len(test_dataset.scenario_dataset) == len(DELAYED_SCENARIO_DESCRIPTORS)

    # ===============================================================================
    # [Day 1 - Between 7:00 - 9:00 PM] Generate FINEOS extract files
    # ===============================================================================

    with freeze_time("2021-05-01 20:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 1 - After 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-01 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,],
            end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.INVALID_ADDRESS_FIXED,],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

    # ===============================================================================
    # [Day 2 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-02 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset, round=1)

    # ============================================================================================================
    # [Day 2 - Between 5:00 - 7:00 PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ============================================================================================================

    with freeze_time("2021-05-02 18:00:00", tz_offset=5):
        run_process_pub_payments_ecs_task(
            db_session=test_db_session,
            log_entry_db_session=test_db_other_session,
            config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=test_db_session,
        )

    # ===============================================================================
    # [Day 2 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-02 19:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset, round=2)

    # ===============================================================================
    # [Day 2 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-02 21:00:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
                ScenarioName.INVALID_ADDRESS_FIXED,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

    # ===============================================================================
    # [Day 3 - 9:00 AM] PUB sends ACH and Check response files
    # ===============================================================================

    # with freeze_time("2021-05-03 09:00:00", tz_offset=5):
    #     generate_pub_returns(test_dataset)

    # ==============================================================================================
    # [Day 3 - 11:00 AM] Run the PUB Response ECS task - response, writeback, reports
    # ==============================================================================================

    # with freeze_time("2021-05-03 11:00:00", tz_offset=5):

    #     # == Run the task
    #     run_process_pub_responses_ecs_task(
    #         db_session=test_db_session,
    #         log_entry_db_session=test_db_other_session,
    #         config=ProcessPubResponsesTaskConfiguration(["--steps", "ALL"]),
    #     )

    # ===============================================================================
    # [Day 3 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-03 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset, round=2)

    # ============================================================================================================
    # [Day 3 - Between 5:00 - 7:00 PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ============================================================================================================

    with freeze_time("2021-05-03 18:00:00", tz_offset=5):
        run_process_pub_payments_ecs_task(
            db_session=test_db_session,
            log_entry_db_session=test_db_other_session,
            config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED],
            end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
            db_session=test_db_session,
        )

    # ===============================================================================
    # [Day 3 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-03 18:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 3 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-03 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

    # TODO Scenario: Day 6 Prenote Rejection
    # TODO Scenario: Fix for invalid ach return
    # TODO Scenario: Fix for invalid check return


# == Common E2E Workflow Segments ==


def generate_test_dataset(scenario_descriptors: List[ScenarioDescriptor]) -> TestDataSet:
    config = ScenarioDataConfig(
        scenarios_with_count=[
            ScenarioNameWithCount(scenario_name=scenario_descriptor.scenario_name, count=1)
            for scenario_descriptor in scenario_descriptors
        ]
    )
    scenario_dataset = generate_scenario_dataset(config=config)
    return TestDataSet(scenario_dataset)


def generate_fineos_extract_files(scenario_dataset: List[ScenarioData], round: int = 1):
    s3_config = payments_config.get_s3_config()

    fineos_data_export_path = s3_config.fineos_data_export_path

    # TODO generate claimant extract files - PUB-165

    generate_payment_extract_files(
        scenario_dataset, fineos_data_export_path, payments_util.get_now(), round=round
    )

    # TODO Confirm expected claimant files were generated - PUB-165

    # Confirm expected payment files were generated
    fineos_extract_date_prefix = get_current_timestamp_prefix()
    assert_files(fineos_data_export_path, FINEOS_PAYMENT_EXTRACT_FILES, fineos_extract_date_prefix)


def generate_rejects_file(test_dataset: TestDataSet, round: int = 1):
    s3_config = payments_config.get_s3_config()

    rejects_file_received_path = os.path.join(
        s3_config.pfml_payment_rejects_archive_path,
        payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
        "Payment-Rejects.csv",
    )

    audit_report_file_path = os.path.join(
        s3_config.dfml_report_outbound_path, "Payment-Audit-Report.csv"
    )

    parsed_audit_rows = parse_csv(audit_report_file_path)

    csv_file = file_util.write_file(rejects_file_received_path)
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
            rejected_value = "Y"
            if scenario_data.scenario_descriptor.is_audit_approved_delayed and round > 1:
                rejected_value = "N"
            parsed_audit_row[
                PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity
            ] = rejected_value

    csv_output.writerows(parsed_audit_rows)
    csv_file.close()


def generate_pub_returns(test_dataset: TestDataSet):
    s3_config = payments_config.get_s3_config()

    pub_response_folder = os.path.join(s3_config.pub_moveit_inbound_path)
    pub_ach_response_generator = PubACHResponseGenerator(
        test_dataset.scenario_dataset, pub_response_folder
    )
    pub_ach_response_generator.run()

    pub_check_response_generator = PubCheckResponseGenerator(
        test_dataset.scenario_dataset, pub_response_folder
    )
    pub_check_response_generator.run()


def process_fineos_extracts(
    test_dataset: TestDataSet,
    mock_experian_client: MockClient,
    db_session: db.Session,
    log_entry_db_session: db.Session,
):
    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_client",
        return_value=mock_experian_client,
    ):
        run_fineos_ecs_task(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            config=FineosTaskConfiguration(["--steps", "ALL"]),
        )

    test_dataset.populate_scenario_data_payments(db_session)


def setup_common_env_variables(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")

    monkeypatch.setenv("DFML_PUB_ACCOUNT_NUMBER", "123456789")
    monkeypatch.setenv("DFML_PUB_ROUTING_NUMBER", "234567890")
    monkeypatch.setenv("PUB_PAYMENT_STARTING_CHECK_NUMBER", "100")


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

            assert (
                state_log is not None
            ), f"No employee state log found for scenario: {scenario_name}"
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
    reports_folder_path: str,
    reports_archive_folder_path: str,
    report_names: List[ReportName],
    db_session: db.Session,
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

        assert_ref_file(
            f"{reports_archive_folder_path}/sent/{date_folder}/{timestamp_prefix}{file_name}",
            ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE,
            db_session,
        )


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


def assert_ref_file(file_path: str, ref_file_type: ReferenceFileType, db_session: db.Session):
    found = (
        db_session.query(ReferenceFile)
        .filter(ReferenceFile.file_location == file_path)
        .filter(ReferenceFile.reference_file_type_id == ref_file_type.reference_file_type_id)
        .one_or_none()
    )

    assert (
        found is not None
    ), f"No reference file found for type: {ref_file_type.reference_file_type_description}, file path: {file_path}"
