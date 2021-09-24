# See workflow here: https://lucid.app/lucidchart/edf54a33-1a3f-432d-82b7-157cf02667a4/edit?page=T9dnksYTkKxE#
# See implementation design here: https://lwd.atlassian.net/wiki/spaces/API/pages/1478918156/Local+E2E+Test+Suite

import csv
import json
import logging  # noqa: B1
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.experian.address_validate_soap.client as soap_api
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Claim,
    Flow,
    ImportLog,
    LkFlow,
    LkState,
    Payment,
    PaymentMethod,
    PrenoteState,
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
    FineosWritebackDetails,
    LkFineosWritebackTransactionStatus,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
)
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import CiIndex
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    generate_claimant_data_files,
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

    def get_scenario_names(self, scenarios_to_filter: Optional[List[str]] = None) -> List[str]:
        filter_set = set()
        if scenarios_to_filter:
            filter_set.update(scenarios_to_filter)
        return [
            sd.scenario_descriptor.scenario_name
            for sd in self.scenario_dataset
            if sd.scenario_descriptor.scenario_name not in filter_set
        ]

    def get_scenario_data_by_name(
        self, scenario_name: ScenarioName
    ) -> Optional[List[ScenarioData]]:
        return self.scenario_dataset_map.get(scenario_name, None)

    def get_scenario_payments_by_name(self, scenario_name: ScenarioName) -> List[Payment]:
        scenario_data_items = self.get_scenario_data_by_name(scenario_name)

        payments = []
        if scenario_data_items is not None:
            for scenario_data in scenario_data_items:
                payment = scenario_data.additional_payment or scenario_data.payment
                if payment is not None:
                    payments.append(payment)

        return payments

    def get_scenario_data_by_payment_ci(self, c_value: str, i_value: str) -> Optional[ScenarioData]:
        for scenario_data in self.scenario_dataset:
            if CiIndex(c=scenario_data.payment_c_value, i=scenario_data.payment_i_value) == CiIndex(
                c=c_value, i=i_value
            ):
                return scenario_data

            elif CiIndex(
                c=scenario_data.additional_payment_c_value,
                i=scenario_data.additional_payment_i_value,
            ) == CiIndex(c=c_value, i=i_value):
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

            # If it has an additional payment expected, query for it too
            if scenario_data.additional_payment_c_value:
                additional_payment = (
                    db_session.query(Payment)
                    .filter(
                        Payment.fineos_pei_c_value == scenario_data.additional_payment_c_value,
                        Payment.fineos_pei_i_value == scenario_data.additional_payment_i_value,
                    )
                    .order_by(Payment.created_at.desc())
                    .first()
                )
                scenario_data.additional_payment = additional_payment

    def populate_scenario_dataset_claims(self, db_session) -> None:
        for scenario_data in self.scenario_dataset:
            if scenario_data.claim:
                continue

            scenario_data.claim = (
                db_session.query(Claim)
                .filter(Claim.fineos_absence_id == scenario_data.absence_case_id)
                .first()
            )


# == The E2E Test ==


def test_e2e_pub_payments(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
    local_create_triggers,
):
    test_db_session = local_test_db_session
    test_db_other_session = local_test_db_other_session

    # TODO Validate error and warning logs - PUB-171

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

    test_dataset = generate_test_dataset(SCENARIO_DESCRIPTORS, test_db_session)
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
        claims = test_db_session.query(Claim).all()
        # Each scenario will have a claim created even if it doesn't start with one
        assert len(claims) == len(test_dataset.scenario_dataset)

        # Payments
        payments = test_db_session.query(Payment).all()
        missing_payment = list(
            filter(
                lambda sd: not sd.scenario_descriptor.create_payment, test_dataset.scenario_dataset
            )
        )
        assert len(payments) == len(test_dataset.scenario_dataset) - len(missing_payment)

        # Payment staging tables
        assert len(test_db_session.query(FineosExtractVbiRequestedAbsence).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpei).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiClaimDetails).all()) == len(payments)
        assert len(test_db_session.query(FineosExtractVpeiPaymentDetails).all()) == len(payments)

        # == Validate employee state logs
        assert_employee_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ],
            end_state=State.DELEGATED_EFT_SEND_PRENOTE,
            flow=Flow.DELEGATED_EFT,
            db_session=test_db_session,
        )

        # == Validate payments state logs
        stage_1_happy_path_scenarios = [
            ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
            ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
        ]

        stage_1_non_standard_payments = [
            ScenarioName.ZERO_DOLLAR_PAYMENT,
            ScenarioName.CANCELLATION_PAYMENT,
            ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,
        ]

        stage_1_overpayment_scenarios = [
            ScenarioName.OVERPAYMENT_PAYMENT_POSITIVE,
            ScenarioName.OVERPAYMENT_PAYMENT_NEGATIVE,
            ScenarioName.OVERPAYMENT_MISSING_NON_VPEI_RECORDS,
        ]

        stage_1_non_standard_payments.extend(stage_1_overpayment_scenarios)

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
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.AUDIT_SKIPPED,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.ZERO_DOLLAR_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CANCELLATION_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_overpayment_scenarios,
            end_state=State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT,],
            end_state=State.DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT,
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
                ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION,
            ],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        state_1_invalid_payment_scenarios = [
            ScenarioName.CLAIM_NOT_ID_PROOFED,
            ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
            ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
            ScenarioName.PUB_ACH_PRENOTE_RETURN,
            ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
            ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=state_1_invalid_payment_scenarios,
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
            db_session=test_db_session,
        )

        # == Validate claim state
        invalid_claim_scenarios = [
            ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
            ScenarioName.CLAIM_NOT_ID_PROOFED,
        ]
        valid_claim_scenarios = test_dataset.get_scenario_names(
            scenarios_to_filter=invalid_claim_scenarios
        )

        assert_claim_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=valid_claim_scenarios,
            end_state=State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
            db_session=test_db_session,
        )
        assert_claim_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=invalid_claim_scenarios,
            end_state=State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # == Validate prenote states
        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.AUDIT_SKIPPED,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ],
            expected_prenote_state=PrenoteState.APPROVED,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ],
            expected_prenote_state=PrenoteState.PENDING_PRE_PUB,
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
                ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.AUDIT_REJECTED,
                ScenarioName.AUDIT_SKIPPED,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
            ]
        )

        payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT
        )
        assert_csv_content(
            audit_report_parsed_csv_rows,
            [
                {
                    PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: str(p.payment_id),
                    PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity: "",
                }
                for p in payments
            ],
        )

        # == Writeback
        stage_1_generic_flow_writeback_scenarios = []
        stage_1_generic_flow_writeback_scenarios.extend(stage_1_non_standard_payments)
        stage_1_generic_flow_writeback_scenarios.extend(state_1_invalid_payment_scenarios)
        stage_1_generic_flow_writeback_scenarios.extend(
            [
                ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION,
            ]
        )
        stage_1_generic_flow_writeback_scenarios.append(
            ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN
        )

        assert_writeback_for_stage(
            test_dataset, [], stage_1_generic_flow_writeback_scenarios, test_db_session,
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

        ach_payments = list(
            filter(
                lambda sd: sd.scenario_descriptor.payment_method.payment_method_id
                == PaymentMethod.ACH.payment_method_id,
                test_dataset.scenario_dataset,
            )
        )
        assert_metrics(
            test_db_other_session,
            "ClaimantExtractStep",
            {
                "claim_not_found_count": len([ScenarioName.CLAIM_NOT_ID_PROOFED]),
                "claim_processed_count": len(SCENARIO_DESCRIPTORS),
                "eft_found_count": len(ach_payments)
                - len(
                    [
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
                    ]
                ),
                "eft_rejected_count": 0,
                "employee_feed_record_count": len(SCENARIO_DESCRIPTORS),
                "employee_not_found_in_feed_count": 0,
                "tax_identifier_missing_in_db_count": len(
                    [ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT]
                ),
                "employee_not_found_in_database_count": 0,
                "employee_processed_multiple_times": 0,
                "errored_claim_count": len(
                    [
                        ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
                        ScenarioName.CLAIM_NOT_ID_PROOFED,
                    ]
                ),
                "errored_claimant_count": 0,
                "evidence_not_id_proofed_count": len([ScenarioName.CLAIM_NOT_ID_PROOFED]),
                "new_eft_count": len(
                    [
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                    ]
                ),
                "processed_employee_count": len(SCENARIO_DESCRIPTORS),
                "processed_requested_absence_count": len(SCENARIO_DESCRIPTORS),
                "valid_claim_count": len(SCENARIO_DESCRIPTORS)
                - len(
                    [
                        ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
                        ScenarioName.CLAIM_NOT_ID_PROOFED,
                    ]
                ),
                "vbi_requested_absence_som_record_count": len(SCENARIO_DESCRIPTORS),
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
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "cancellation_count": len([ScenarioName.CANCELLATION_PAYMENT]),
                "claim_details_record_count": len(SCENARIO_DESCRIPTORS)
                - len([ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED]),
                "claim_not_found_count": 0,
                "claimant_mismatch_count": len(
                    [ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT]
                ),
                "eft_found_count": len(
                    [
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "employee_in_payment_extract_missing_in_db_count": 0,
                "employer_reimbursement_count": len([ScenarioName.EMPLOYER_REIMBURSEMENT_PAYMENT]),
                "errored_payment_count": len(
                    [
                        ScenarioName.CLAIM_NOT_ID_PROOFED,
                        ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
                        ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                        ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION,
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
                    ]
                ),
                "new_eft_count": 0,
                "not_approved_prenote_count": len(
                    [
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                    ]
                ),
                "in_review_leave_request_count": len(
                    [ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION]
                ),
                "not_approved_leave_request_count": len(
                    [
                        ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                        ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "overpayment_count": len(stage_1_overpayment_scenarios),
                "payment_details_record_count": len(SCENARIO_DESCRIPTORS)
                - len([ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED]),
                "pei_record_count": len(SCENARIO_DESCRIPTORS)
                - len([ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED]),
                "prenote_past_waiting_period_approved_count": 0,
                "processed_payment_count": len(SCENARIO_DESCRIPTORS)
                - len([ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED]),
                "requested_absence_record_count": len(SCENARIO_DESCRIPTORS)
                - len([ScenarioName.CLAIMANT_PRENOTED_NO_PAYMENT_RECEIVED]),
                "standard_valid_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
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
                "experian_search_exception_count": 0,
                "invalid_experian_format": 0,
                "invalid_experian_response": 0,
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
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "validated_address_count": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "verified_experian_match": len(
                    [
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
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
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "payment_sampled_for_audit_count": len(
                    [
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "sampled_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                        ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
                        ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                        ScenarioName.AUDIT_REJECTED,
                        ScenarioName.AUDIT_SKIPPED,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                        ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
                        ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
                    ]
                ),
            },
        )

        assert_metrics(
            test_db_other_session,
            "FineosPeiWritebackStep",
            {
                "errored_writeback_record_during_file_creation_count": 0,
                "errored_writeback_record_during_file_transfer_count": 0,
                "successful_writeback_record_count": len(stage_1_generic_flow_writeback_scenarios),
                "writeback_record_count": len(stage_1_generic_flow_writeback_scenarios),
                "generic_flow_writeback_items_count": len(stage_1_generic_flow_writeback_scenarios),
                "address_validation_error_writeback_transaction_status_count": len(
                    [ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN]
                ),
                "payment_system_error_writeback_transaction_status_count": len(
                    [
                        ScenarioName.CLAIM_NOT_ID_PROOFED,
                        ScenarioName.PAYMENT_EXTRACT_EMPLOYEE_MISSING_IN_DB,
                        ScenarioName.CLAIM_UNABLE_TO_SET_EMPLOYEE_FROM_EXTRACT,
                    ]
                ),
                "eft_pending_bank_validation_writeback_transaction_status_count": len(
                    [
                        ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                        ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                    ]
                ),
                "payment_validation_error_writeback_transaction_status_count": len(
                    [
                        ScenarioName.REJECTED_LEAVE_REQUEST_DECISION,
                        ScenarioName.UNKNOWN_LEAVE_REQUEST_DECISION,
                    ]
                ),
                "processed_writeback_transaction_status_count": len(stage_1_non_standard_payments),
            },
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {
                "processed_report_count": len(PROCESS_FINEOS_EXTRACT_REPORTS),
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
        process_pub_payments(test_db_session, test_db_other_session)

        # == Validate file contents
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        positive_pay_ez_check_payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )
        ez_check_file_contents = file_util.read_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_EZ_CHECK}.csv"
        )

        for payment in positive_pay_ez_check_payments:
            assert ez_check_file_contents.index(payment.claim.fineos_absence_id) != -1

        positive_pay_file_contents = file_util.read_file(
            f"{s3_config.pfml_pub_check_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.txt",
        )

        for payment in positive_pay_ez_check_payments:
            assert positive_pay_file_contents.index(str(payment.check.check_number)) != -1

        ach_file_contents = file_util.read_file(
            f"{s3_config.pfml_pub_ach_archive_path}/sent/{date_folder}/{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_NACHA}",
        )

        ach_payments = get_payments_in_end_state(
            test_db_session, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT
        )

        for payment in ach_payments:
            assert ach_file_contents.index(payment.pub_eft.account_nbr) != -1

        # == Validate payments state logs

        # End State
        stage_2_ach_scenarios = [
            ScenarioName.HAPPY_PATH_MEDICAL_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_FAMILY_ACH_PRENOTED,
            ScenarioName.HAPPY_PATH_ACH_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN,
            ScenarioName.PUB_ACH_FAMILY_RETURN,
            ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ScenarioName.HAPPY_PATH_CLAIM_MISSING_EMPLOYEE,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_2_ach_scenarios,
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=test_db_session,
        )

        # End State
        stage_2_check_scenarios = [
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
        ]

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_2_check_scenarios,
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_SKIPPED,
                ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
            ],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            db_session=test_db_session,
        )

        # == Validate prenote states
        stage_2_prenote_scenarios = [
            ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
            ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
            ScenarioName.PUB_ACH_PRENOTE_RETURN,
            ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
            ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
        ]

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=stage_2_prenote_scenarios,
            expected_prenote_state=PrenoteState.PENDING_WITH_PUB,
        )

        # == Rejects processed
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        rejects_file_received_path = os.path.join(
            s3_config.pfml_payment_rejects_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        assert_files(
            rejects_file_received_path, ["Payment-Audit-Report-Response.csv"], timestamp_prefix
        )

        rejects_file_path = os.path.join(
            rejects_file_received_path, f"{timestamp_prefix}Payment-Audit-Report-Response.csv"
        )
        rejects_file_parsed_rows = parse_csv(rejects_file_path)

        rejected_scenario_data_payments = test_dataset.get_scenario_payments_by_name(
            ScenarioName.AUDIT_REJECTED
        )

        skipped_scenario_data_payments = test_dataset.get_scenario_payments_by_name(
            ScenarioName.AUDIT_SKIPPED
        )

        assert_csv_content(
            rejects_file_parsed_rows,
            [
                {
                    PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: str(p.payment_id),
                    PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity: "Y",
                    PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity: "",
                }
                for p in rejected_scenario_data_payments
            ],
        )

        assert_csv_content(
            rejects_file_parsed_rows,
            [
                {
                    PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id: str(p.payment_id),
                    PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity: "",
                    PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity: "Y",
                }
                for p in skipped_scenario_data_payments
            ],
        )

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
            f"{s3_config.pfml_payment_rejects_archive_path}/processed/{date_folder}/{timestamp_prefix}Payment-Audit-Report-Response.csv",
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

        # == Writeback
        stage_2_legacy_writeback_scenario_names = []

        stage_2_generic_flow_writeback_scenarios = [
            ScenarioName.AUDIT_REJECTED,
            ScenarioName.AUDIT_SKIPPED,
            ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION,
        ]
        stage_2_generic_flow_writeback_scenarios.extend(stage_2_ach_scenarios)
        stage_2_generic_flow_writeback_scenarios.extend(stage_2_check_scenarios)

        assert_writeback_for_stage(
            test_dataset,
            stage_2_legacy_writeback_scenario_names,
            stage_2_generic_flow_writeback_scenarios,
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
                "Payment-Audit-Report_file_moved_count": 1,
                "EOLWD-DFML-POSITIVE-PAY_file_moved_count": 0,
                "EOLWD-DFML-NACHA_file_moved_count": 0,
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentRejectsStep",
            {
                "accepted_payment_count": len(stage_2_ach_scenarios) + len(stage_2_check_scenarios),
                "parsed_rows_count": len(stage_2_generic_flow_writeback_scenarios),
                "payment_state_log_missing_count": 0,
                "payment_state_log_not_in_audit_response_pending_count": 0,
                "rejected_payment_count": len([ScenarioName.AUDIT_REJECTED]),
                "skipped_payment_count": len(
                    [ScenarioName.AUDIT_SKIPPED, ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION]
                ),
                "state_logs_count": len(stage_2_generic_flow_writeback_scenarios),
            },
        )

        assert_metrics(
            test_db_other_session,
            "PaymentMethodsSplitStep",
            {
                "ach_payment_count": len(stage_2_ach_scenarios),
                "check_payment_count": len(stage_2_check_scenarios),
                "payment_count": len(stage_2_ach_scenarios) + len(stage_2_check_scenarios),
            },
        )

        assert_metrics(
            test_db_other_session,
            "TransactionFileCreatorStep",
            {
                "ach_payment_count": len(stage_2_ach_scenarios),
                "ach_prenote_count": len(stage_2_prenote_scenarios),
                "check_payment_count": len(stage_2_check_scenarios),
                "failed_to_add_transaction_count": 0,
                "successful_add_to_transaction_count": len(stage_2_prenote_scenarios)
                + len(stage_2_ach_scenarios)
                + len(stage_2_check_scenarios),
                "transaction_files_sent_count": 3,  # EzCheck, NACHA, and positive pay files.
            },
        )

        assert_metrics(
            test_db_other_session,
            "FineosPeiWritebackStep",
            {
                "errored_writeback_record_during_file_creation_count": 0,
                "errored_writeback_record_during_file_transfer_count": 0,
                "successful_writeback_record_count": len(stage_2_legacy_writeback_scenario_names)
                + len(stage_2_generic_flow_writeback_scenarios),
                "writeback_record_count": len(stage_2_legacy_writeback_scenario_names)
                + len(stage_2_generic_flow_writeback_scenarios),
                "generic_flow_writeback_items_count": len(stage_2_generic_flow_writeback_scenarios),
                "payment_audit_error_writeback_transaction_status_count": len(
                    [ScenarioName.AUDIT_REJECTED]
                ),
                "pending_payment_audit_writeback_transaction_status_count": len(
                    [ScenarioName.AUDIT_SKIPPED]
                ),
                "leave_plan_in_review_writeback_transaction_status_count": len(
                    [ScenarioName.IN_REVIEW_LEAVE_REQUEST_DECISION]
                ),
                "paid_writeback_transaction_status_count": len(stage_2_ach_scenarios)
                + len(stage_2_check_scenarios),
            },
        )

        # ReportStep
        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {
                "processed_report_count": len(CREATE_PUB_FILES_REPORTS),
                "report_error_count": 0,
                "report_generated_count": len(CREATE_PUB_FILES_REPORTS),
            },
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
        process_pub_responses(test_db_session, test_db_other_session)

        # == Validate payment states

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
            ],
            end_state=State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ],
            end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            db_session=test_db_session,
        )

        # Unchanged
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=test_db_session,
        )

        # Unchanged
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_OUTSTANDING,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_FUTURE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            db_session=test_db_session,
        )

        # End State
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ],
            end_state=State.DELEGATED_PAYMENT_COMPLETE,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
            ],
            end_state=State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            db_session=test_db_session,
        )

        # == Validate prenote states
        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
            ],
            expected_prenote_state=PrenoteState.PENDING_WITH_PUB,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,],
            expected_prenote_state=PrenoteState.APPROVED,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_RETURN,],
            expected_prenote_state=PrenoteState.REJECTED,
        )

        # == Assert files

        # processed ach return files
        date_folder = get_current_date_folder()
        timestamp_prefix = get_current_timestamp_prefix()

        pub_ach_response_processed_folder = os.path.join(
            s3_config.pfml_pub_ach_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        nacha_filenames = [payments_util.Constants.FILE_NAME_PUB_NACHA]
        assert_files(pub_ach_response_processed_folder, nacha_filenames, timestamp_prefix)

        # check content of the ach response file
        nacha_response_file_contents = file_util.read_file(
            os.path.join(
                pub_ach_response_processed_folder,
                f"{timestamp_prefix}{payments_util.Constants.FILE_NAME_PUB_NACHA}",
            )
        )

        for scenario_data in test_dataset.scenario_dataset:
            scenario_descriptor = scenario_data.scenario_descriptor
            scenario_name = scenario_descriptor.scenario_name

            if scenario_descriptor.payment_method != PaymentMethod.ACH or not (
                scenario_descriptor.pub_ach_response_return
                or scenario_descriptor.pub_ach_response_change_notification
            ):
                continue

            payment = scenario_data.additional_payment or scenario_data.payment

            assert payment is not None, f"No Payment found: {scenario_name}"

            pub_eft = payment.pub_eft

            assert pub_eft is not None, f"No PubEft found: {scenario_name}"

            routing_number = pub_eft.routing_nbr
            account_number = pub_eft.account_nbr
            nacha_id_prefix = "P" if scenario_descriptor.prenoted else "E"
            pub_individual_id = (
                payment.pub_individual_id
                if scenario_descriptor.prenoted
                else pub_eft.pub_individual_id
            )
            nacha_id = f"{nacha_id_prefix}{pub_individual_id}"

            assert (
                nacha_id in nacha_response_file_contents
            ), f"Could not find nacha_id: {nacha_id} - {scenario_name}"
            assert (
                routing_number in nacha_response_file_contents
            ), f"Could not find routing_number: {routing_number} - {scenario_name}"
            assert (
                account_number in nacha_response_file_contents
            ), f"Could not find account_number: {account_number} - {scenario_name}"

        # processed check return files
        pub_check_response_processed_folder = os.path.join(
            s3_config.pfml_pub_check_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            date_folder,
        )
        positive_pay_check_response_file = (
            f"Paid-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.csv"
        )
        outstanding_check_response_file = (
            f"Outstanding-{payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY}.csv"
        )
        positive_pay_filenames = [positive_pay_check_response_file, outstanding_check_response_file]
        assert_files(pub_check_response_processed_folder, positive_pay_filenames, timestamp_prefix)

        # check content of the check response files
        positive_pay_check_response_file_contents = file_util.read_file(
            os.path.join(
                pub_check_response_processed_folder,
                f"{timestamp_prefix}{positive_pay_check_response_file}",
            )
        )
        outstanding_check_response_file_contents = file_util.read_file(
            os.path.join(
                pub_check_response_processed_folder,
                f"{timestamp_prefix}{outstanding_check_response_file}",
            )
        )

        for scenario_data in test_dataset.scenario_dataset:
            scenario_descriptor = scenario_data.scenario_descriptor
            scenario_name = scenario_descriptor.scenario_name

            if (
                scenario_descriptor.payment_method != PaymentMethod.CHECK
                or not scenario_descriptor.pub_check_response
            ):
                continue

            employee = scenario_data.employee

            if scenario_descriptor.pub_check_paid_response:
                assert (
                    str(employee.employee_id) in positive_pay_check_response_file_contents
                ), f"Employee id not found in positive pay file for {scenario_name}"
            else:
                assert (
                    str(employee.employee_id) in outstanding_check_response_file_contents
                ), f"Employee id not found in oustanding file for {scenario_name}"

        # == PubError adjust as metric based scenarios below are added
        assert len(test_db_session.query(PubError).all()) == len(
            [
                ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                ScenarioName.PUB_ACH_FAMILY_RETURN,
                ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                ScenarioName.PUB_ACH_MEDICAL_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_ACH_PRENOTE_RETURN,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
                ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
            ]
        )

        # == Writeback
        stage_3_errored_writeback_scenarios = [
            ScenarioName.PUB_ACH_FAMILY_RETURN,
            ScenarioName.PUB_ACH_MEDICAL_RETURN,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_VOID,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STALE,
            ScenarioName.PUB_CHECK_FAMILY_RETURN_STOP,
        ]
        stage_3_successful_writeback_scenarios = [
            ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
            ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
            ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
            ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
        ]

        stage_3_all_writeback_scenarios = (
            stage_3_errored_writeback_scenarios + stage_3_successful_writeback_scenarios
        )

        assert_writeback_for_stage(
            test_dataset, [], stage_3_all_writeback_scenarios, test_db_session,
        )

        # == Reports
        assert_reports(
            s3_config.dfml_report_outbound_path,
            s3_config.pfml_error_reports_archive_path,
            PROCESS_PUB_RESPONSES_REPORTS,
            test_db_session,
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
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                    ]
                ),
                "change_notification_count": len(
                    [
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                    ]
                ),
                "eft_prenote_already_rejected_count": 0,
                "eft_prenote_count": len(
                    [
                        ScenarioName.PUB_ACH_PRENOTE_RETURN,
                        ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
                        ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                    ]
                ),
                "eft_prenote_id_not_found_count": len(
                    [ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,]
                ),
                "eft_prenote_change_notification_count": len(
                    [ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION]
                ),
                "eft_prenote_rejected_count": len([ScenarioName.PUB_ACH_PRENOTE_RETURN]),
                "eft_prenote_unexpected_state_count": 0,
                "payment_already_complete_count": 0,
                "payment_complete_with_change_count": len(
                    [
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                    ]
                ),
                "payment_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_RETURN,
                        ScenarioName.PUB_ACH_MEDICAL_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_NOTIFICATION,
                        ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND,
                    ]
                ),
                "payment_id_not_found_count": len(
                    [ScenarioName.PUB_ACH_FAMILY_RETURN_PAYMENT_ID_NOT_FOUND]
                ),
                "payment_already_rejected_count": 0,  # TODO add scenario or check this on later days
                "payment_notification_unexpected_state_count": 0,
                "payment_rejected_count": len(
                    [ScenarioName.PUB_ACH_MEDICAL_RETURN, ScenarioName.PUB_ACH_FAMILY_RETURN,]
                ),
                "payment_unexpected_state_count": 0,
                "unknown_id_format_count": len(
                    [
                        ScenarioName.PUB_ACH_FAMILY_RETURN_INVALID_PAYMENT_ID_FORMAT,
                        ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
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
                "check_number_not_found_count": 0,
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
                    [ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND]
                ),
                "check_payment_count": len(
                    [
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
                        ScenarioName.HAPPY_PATH_CHECK_FAMILY_RETURN_PAID,
                        ScenarioName.PUB_CHECK_FAMILY_RETURN_CHECK_NUMBER_NOT_FOUND,
                    ]
                ),
                "payment_complete_by_paid_check": len(
                    [
                        ScenarioName.HAPPY_PATH_FAMILY_CHECK_PRENOTED,
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
                "errored_writeback_record_during_file_creation_count": 0,
                "errored_writeback_record_during_file_transfer_count": 0,
                "successful_writeback_record_count": len(stage_3_all_writeback_scenarios),
                "writeback_record_count": len(stage_3_all_writeback_scenarios),
                "bank_processing_error_writeback_transaction_status_count": len(
                    stage_3_errored_writeback_scenarios
                ),
                "posted_writeback_transaction_status_count": len(
                    stage_3_successful_writeback_scenarios
                ),
            },
        )

        assert_metrics(
            test_db_other_session,
            "ReportStep",
            {
                "processed_report_count": len([PROCESS_PUB_RESPONSES_REPORTS]),
                "report_error_count": 0,
                "report_generated_count": len([PROCESS_PUB_RESPONSES_REPORTS]),
            },
        )

    # ===============================================================================
    # [Day 7 - 7:00 PM] Generate FINEOS extract files
    # ===============================================================================
    with freeze_time("2021-05-07 18:00:00", tz_offset=5):
        generate_fineos_extract_files(test_dataset.scenario_dataset)

    # ===============================================================================
    # [Day 7 - 9:00 PM] Run the FINEOS ECS task - Process Claim and Payment Extract
    # ===============================================================================

    with freeze_time("2021-05-07 21:30:00", tz_offset=5):
        process_fineos_extracts(
            test_dataset, mock_experian_client, test_db_session, test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_RETURN,],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # validate other scenarios that have reached an end state are erroring out
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=stage_1_happy_path_scenarios,
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=test_db_session,
        )

        # assert prenote states
        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.PRENOTE_WITH_EXISTING_EFT_ACCOUNT,
                ScenarioName.EFT_ACCOUNT_NOT_PRENOTED,
                ScenarioName.PUB_ACH_PRENOTE_INVALID_PAYMENT_ID_FORMAT,
                ScenarioName.PUB_ACH_PRENOTE_PAYMENT_ID_NOT_FOUND,
                ScenarioName.PUB_ACH_PRENOTE_NOTIFICATION,
            ],
            expected_prenote_state=PrenoteState.APPROVED,
        )

        assert_prenote_state(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.PUB_ACH_PRENOTE_RETURN,],
            expected_prenote_state=PrenoteState.REJECTED,
        )

        # Writeback
        stage_4_legacy_writeback_scenario_names = []

        stage_4_generic_flow_writeback_scenarios = [ScenarioName.PUB_ACH_PRENOTE_RETURN]

        assert_writeback_for_stage(
            test_dataset,
            stage_4_legacy_writeback_scenario_names,
            stage_4_generic_flow_writeback_scenarios,
            test_db_session,
        )

        # Metrics
        assert_metrics(
            test_db_other_session,
            "FineosPeiWritebackStep",
            {
                "eft_account_information_error_writeback_transaction_status_count": len(
                    [ScenarioName.PUB_ACH_PRENOTE_RETURN]
                ),
            },
        )


def test_e2e_pub_payments_delayed_scenarios(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    caplog,
    local_create_triggers,
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

    test_dataset = generate_test_dataset(DELAYED_SCENARIO_DESCRIPTORS, local_test_db_session)
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
            test_dataset, mock_experian_client, local_test_db_session, local_test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP,
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,],
            end_state=State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.INVALID_ADDRESS_FIXED,],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=local_test_db_session,
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
        process_pub_payments(local_test_db_session, local_test_db_other_session)

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=local_test_db_session,
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
            db_session=local_test_db_session,
        )

        # == Validate FINEOS status writeback states
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
            ],
            end_state=State.DELEGATED_FINEOS_WRITEBACK_SENT,
            flow=Flow.DELEGATED_PEI_WRITEBACK,
            db_session=local_test_db_session,
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
            test_dataset, mock_experian_client, local_test_db_session, local_test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.CHECK_PAYMENT_ADDRESS_NO_MATCHES_FROM_EXPERIAN_FIXED,
                ScenarioName.INVALID_ADDRESS_FIXED,
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
                ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP,
            ],
            end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            db_session=local_test_db_session,
            check_additional_payment=True,
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
    #     process_pub_responses(test_db_session, test_db_other_session)

    # ===============================================================================
    # [Day 3 - Before 5:00 PM] Payment Integrity Team returns Payment Rejects File
    # ===============================================================================

    with freeze_time("2021-05-03 14:00:00", tz_offset=5):
        generate_rejects_file(test_dataset, round=2)

    # ============================================================================================================
    # [Day 3 - Between 5:00 - 7:00 PM] Run the PUB Processing ECS task - Rejects, PUB Transaction Files, Writeback
    # ============================================================================================================

    with freeze_time("2021-05-03 18:00:00", tz_offset=5):
        process_pub_payments(local_test_db_session, local_test_db_other_session)

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[
                ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,
                ScenarioName.AUDIT_SKIPPED_THEN_ACCEPTED,
                ScenarioName.HAPPY_PATH_TWO_PAYMENTS_UNDER_WEEKLY_CAP,
                ScenarioName.HAPPY_PATH_TWO_ADHOC_PAYMENTS_OVER_CAP,
            ],
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            db_session=local_test_db_session,
            check_additional_payment=True,
        )

        # We set these to be rejected in the file we sent
        # and the file comes back unmodified, so they will be rejected.
        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.SECOND_PAYMENT_FOR_PERIOD_OVER_CAP],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            db_session=local_test_db_session,
            check_additional_payment=True,
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
            test_dataset, mock_experian_client, local_test_db_session, local_test_db_other_session
        )

        assert_payment_state_for_scenarios(
            test_dataset=test_dataset,
            scenario_names=[ScenarioName.AUDIT_REJECTED_THEN_ACCEPTED,],
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            db_session=local_test_db_session,
        )

    # TODO Scenario: Day 6 Prenote Rejection
    # TODO Scenario: Fix for invalid ach return
    # TODO Scenario: Fix for invalid check return


def test_e2e_pub_payments_fails(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    monkeypatch,
    set_exporter_env_vars,
    mock_s3_bucket,
):
    test_db_session = local_test_db_session
    test_db_other_session = local_test_db_other_session
    setup_common_env_variables(monkeypatch)

    # Make it error when the first step in the task runs
    with mock.patch(
        "massgov.pfml.delegated_payments.step.Step.set_metrics", side_effect=Exception("Error msg"),
    ):

        # Run and error all 3 ECS tasks
        with pytest.raises(Exception, match="Error msg"):
            run_fineos_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=FineosTaskConfiguration(["--steps", "ALL"]),
            )

        with pytest.raises(Exception, match="Error msg"):
            run_process_pub_payments_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
            )

        with pytest.raises(Exception, match="Error msg"):
            run_process_pub_responses_ecs_task(
                db_session=test_db_session,
                log_entry_db_session=test_db_other_session,
                config=ProcessPubResponsesTaskConfiguration(["--steps", "ALL"]),
            )

        # Despite the failure, the metrics are still written to S3
        # although the only "metric" is the error message as it failed
        # to initialize the metrics with how it errors above
        # The PickupResponseFilesStep appears twice as it's the first
        # step in the 2nd & 3rd ECS task
        expected_metrics = {"message": "Exception: Error msg"}
        assert_metrics(test_db_other_session, "StateCleanupStep", expected_metrics)
        assert_metrics(test_db_other_session, "PickupResponseFilesStep", expected_metrics)
        assert_metrics(
            test_db_other_session, "PickupResponseFilesStep", expected_metrics, log_report_index=1
        )

        # Nothing should have been written to s3
        all_files = file_util.list_files(f"s3://{mock_s3_bucket}", recursive=True)
        assert len(all_files) == 0


# == Common E2E Workflow Segments ==


def generate_test_dataset(
    scenario_descriptors: List[ScenarioDescriptor], db_session: db.Session
) -> TestDataSet:
    config = ScenarioDataConfig(
        scenarios_with_count=[
            ScenarioNameWithCount(scenario_name=scenario_descriptor.scenario_name, count=1)
            for scenario_descriptor in scenario_descriptors
        ]
    )
    scenario_dataset = generate_scenario_dataset(config=config, db_session=db_session)
    return TestDataSet(scenario_dataset)


def generate_fineos_extract_files(scenario_dataset: List[ScenarioData], round: int = 1):
    s3_config = payments_config.get_s3_config()

    fineos_data_export_path = s3_config.fineos_data_export_path
    fineos_extract_date_prefix = get_current_timestamp_prefix()

    # claimant extract
    generate_claimant_data_files(
        scenario_dataset, fineos_data_export_path, payments_util.get_now(), round=round
    )
    # Confirm expected claimant files were generated
    assert_files(
        fineos_data_export_path,
        payments_util.CLAIMANT_EXTRACT_FILE_NAMES,
        fineos_extract_date_prefix,
    )

    # payment extract
    generate_payment_extract_files(
        scenario_dataset, fineos_data_export_path, payments_util.get_now(), round=round
    )
    # Confirm expected payment files were generated
    assert_files(
        fineos_data_export_path,
        payments_util.PAYMENT_EXTRACT_FILE_NAMES,
        fineos_extract_date_prefix,
    )


def generate_rejects_file(test_dataset: TestDataSet, round: int = 1):
    s3_config = payments_config.get_s3_config()

    rejects_file_received_path = os.path.join(
        s3_config.dfml_response_inbound_path, "Payment-Audit-Report-Response.csv",
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

        scenario_descriptor = scenario_data.scenario_descriptor
        if scenario_descriptor.is_audit_rejected and scenario_descriptor.is_audit_skipped:
            raise Exception(
                "Invalid scenario with both audit rejected and audit skipped set to true"
            )

        if scenario_descriptor.is_audit_rejected:
            rejected_value = "Y"
            if scenario_descriptor.is_audit_approved_delayed and round > 1:
                rejected_value = "N"
            parsed_audit_row[
                PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity
            ] = rejected_value

        if scenario_descriptor.is_audit_skipped:
            skipped_value = "Y"
            if scenario_descriptor.is_audit_approved_delayed and round > 1:
                skipped_value = "N"
            parsed_audit_row[PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity] = skipped_value

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
    mock_experian_client: soap_api.Client,
    db_session: db.Session,
    log_entry_db_session: db.Session,
):
    with mock.patch(
        "massgov.pfml.delegated_payments.address_validation._get_experian_soap_client",
        return_value=mock_experian_client,
    ):
        run_fineos_ecs_task(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            config=FineosTaskConfiguration(["--steps", "ALL"]),
        )

    assert_success_file("pub-payments-process-fineos")
    test_dataset.populate_scenario_data_payments(db_session)
    test_dataset.populate_scenario_dataset_claims(db_session)


def process_pub_payments(db_session: db.Session, log_entry_db_session: db.Session):
    run_process_pub_payments_ecs_task(
        db_session=db_session,
        log_entry_db_session=log_entry_db_session,
        config=ProcessPubPaymentsTaskConfiguration(["--steps", "ALL"]),
    )
    assert_success_file("pub-payments-create-pub-files")


def process_pub_responses(db_session: db.Session, log_entry_db_session: db.Session):
    run_process_pub_responses_ecs_task(
        db_session=db_session,
        log_entry_db_session=log_entry_db_session,
        config=ProcessPubResponsesTaskConfiguration(["--steps", "ALL"]),
    )
    assert_success_file("pub-payments-process-pub-returns")


def setup_common_env_variables(monkeypatch):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")
    monkeypatch.setenv("FINEOS_PAYMENT_EXTRACT_MAX_HISTORY_DATE", "2021-04-30")

    monkeypatch.setenv("DFML_PUB_ACCOUNT_NUMBER", "123456789")
    monkeypatch.setenv("DFML_PUB_ROUTING_NUMBER", "234567890")
    monkeypatch.setenv("PUB_PAYMENT_STARTING_CHECK_NUMBER", "100")
    monkeypatch.setenv("USE_AUDIT_REJECT_TRANSACTION_STATUS", "1")


# == Assertion Helpers ==


def assert_files(folder_path, expected_files, file_prefix=""):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert (
            f"{file_prefix}{expected_file}" in files_in_folder
        ), f"Can not find {file_prefix}{expected_file} under path: {folder_path}, found files: {files_in_folder}"


def assert_claim_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: LkState,
    db_session: db.Session,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            claim = scenario_data.claim
            state_log = state_log_util.get_latest_state_log_in_flow(
                claim, Flow.DELEGATED_CLAIM_VALIDATION, db_session
            )

            assert (
                state_log is not None
            ), f"No state found for scenario: {scenario_name}, {claim.state_logs}"
            assert (
                state_log.end_state_id == end_state.state_id
            ), f"Unexpected claim state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}"


def assert_payment_state_for_scenarios(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    end_state: LkState,
    db_session: db.Session,
    flow: LkFlow = Flow.DELEGATED_PAYMENT,
    check_additional_payment: bool = False,
):
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            if check_additional_payment:
                payment = scenario_data.additional_payment
            else:
                payment = scenario_data.payment

            assert payment is not None

            state_log = state_log_util.get_latest_state_log_in_flow(payment, flow, db_session)

            assert state_log is not None
            assert (
                state_log.end_state_id == end_state.state_id
            ), f"Unexpected payment state for scenario: {scenario_name}, expected: {end_state.state_description}, found: {state_log.end_state.state_description}, validation: {state_log.outcome}"


def assert_prenote_state(
    test_dataset: TestDataSet,
    scenario_names: List[ScenarioName],
    expected_prenote_state: PrenoteState,
):
    assertion_errors = []
    for scenario_name in scenario_names:
        scenario_data_items = test_dataset.get_scenario_data_by_name(scenario_name)

        assert scenario_data_items is not None, f"No data found for scenario: {scenario_name}"

        for scenario_data in scenario_data_items:
            payment = scenario_data.payment

            assert payment is not None, f"No Payment found: {scenario_name}"

            pub_eft = payment.pub_eft

            assert pub_eft is not None, f"No PubEft found: {scenario_name}"

            if pub_eft.prenote_state_id != expected_prenote_state.prenote_state_id:
                assertion_errors.append(
                    f"Scenario: {scenario_name}, found state: {pub_eft.prenote_state.prenote_state_description}\n"
                )

    errors = "".join(assertion_errors)
    assert (
        len(assertion_errors) == 0
    ), f"Unexpected prenote state for scenario(s) - expected state: {expected_prenote_state.prenote_state_description}\n{errors}"


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


def assert_csv_content(rows: Dict[str, str], rows_expected_values: List[Dict[str, str]]):
    def is_row_match(row_expected_values):
        for row in rows:
            match = False
            for column, value in row_expected_values.items():
                match = row.get(column, None) == value
                if not match:
                    break

            if match:
                return True

        return False

    for row_expected_values in rows_expected_values:
        assert is_row_match(
            row_expected_values
        ), f"Expected csv row not found - expected row values: {row_expected_values}"


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


def assert_success_file(process_name):
    s3_config = payments_config.get_s3_config()

    processed_folder = os.path.join(
        s3_config.pfml_error_reports_archive_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        get_current_date_folder(),
    )
    expected_file_name = f"{process_name}.SUCCESS"
    assert_files(processed_folder, [expected_file_name], get_current_timestamp_prefix())


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


def assert_writeback_for_stage(
    test_dataset: TestDataSet,
    legacy_writeback_scenario_names: List[ScenarioName],
    generic_writeback_scenario_names: List[ScenarioName],
    db_session: db.Session,
):

    # Validate file creation
    s3_config = payments_config.get_s3_config()
    date_folder = get_current_date_folder()
    timestamp_prefix = get_current_timestamp_prefix()

    writeback_folder_path = os.path.join(s3_config.fineos_data_import_path)
    assert_files(writeback_folder_path, ["pei_writeback.csv"], timestamp_prefix)

    writeback_file_path = f"{s3_config.pfml_fineos_writeback_archive_path}sent/{date_folder}/{timestamp_prefix}pei_writeback.csv"
    assert_ref_file(
        writeback_file_path, ReferenceFileType.PEI_WRITEBACK, db_session,
    )

    # Validate FINEOS status writeback states
    assert_payment_state_for_scenarios(
        test_dataset=test_dataset,
        scenario_names=generic_writeback_scenario_names,
        end_state=State.DELEGATED_FINEOS_WRITEBACK_SENT,
        flow=Flow.DELEGATED_PEI_WRITEBACK,
        db_session=db_session,
    )

    # Validate counts
    writeback_scenario_names = []
    writeback_scenario_names.extend(legacy_writeback_scenario_names)
    writeback_scenario_names.extend(generic_writeback_scenario_names)

    writeback_scenario_payments = []
    for writeback_scenario_name in writeback_scenario_names:
        scenario_payments = test_dataset.get_scenario_payments_by_name(writeback_scenario_name)
        writeback_scenario_payments.extend(scenario_payments)

    assert len(writeback_scenario_names) == len(writeback_scenario_payments)

    generic_flow_scenario_payments = []
    for writeback_scenario_name in generic_writeback_scenario_names:
        scenario_payments = test_dataset.get_scenario_payments_by_name(writeback_scenario_name)
        generic_flow_scenario_payments.extend(scenario_payments)

    generic_flow_scenario_payment_ids = set([p.payment_id for p in generic_flow_scenario_payments])

    writeback_details = (
        db_session.query(FineosWritebackDetails)
        .filter(
            FineosWritebackDetails.payment_id.in_(generic_flow_scenario_payment_ids),
            FineosWritebackDetails.created_at
            >= payments_util.get_now(),  # get writeback items created during current time freeze
        )
        .all()
    )

    assert len(writeback_details) == len(generic_writeback_scenario_names)

    # Validate csv content
    expected_csv_rows = []
    for p in writeback_scenario_payments:
        expected_csv_row = {
            "pei_C_Value": p.fineos_pei_c_value,
            "pei_I_Value": p.fineos_pei_i_value,
        }

        # TODO remove condition when we are fully transitioned to using generic flow
        if p.payment_id in generic_flow_scenario_payment_ids:
            transaction_status = get_writeback_transaction_status_for_payment(db_session, p)
            expected_csv_row[
                "transactionStatus"
            ] = transaction_status.transaction_status_description
            expected_csv_row["status"] = transaction_status.writeback_record_status

            transaction_status_date = payments_util.get_transaction_status_date(p)
            expected_csv_row["transStatusDate"] = transaction_status_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        else:
            expected_csv_row["status"] = "Active"

        expected_csv_rows.append(expected_csv_row)

    writeback_csv_rows = parse_csv(writeback_file_path)
    assert_csv_content(writeback_csv_rows, expected_csv_rows)


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


def get_writeback_transaction_status_for_payment(
    db_session: db.Session, payment: Payment
) -> LkFineosWritebackTransactionStatus:
    writeback_details = (
        db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .order_by(FineosWritebackDetails.created_at.desc())
        .first()
    )

    assert writeback_details is not None

    return writeback_details.transaction_status


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
