import decimal

import pytest

import massgov.pfml.delegated_payments.delegated_fineos_iaww_extract as extractor
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.api.eligibility.benefit_year import get_benefit_year_by_employee_id
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import ReferenceFileType
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ClaimFactory,
    EmployerFactory,
    ImportLogFactory,
    ReferenceFileFactory,
)
from massgov.pfml.db.models.payments import (
    FineosExtractVbiLeavePlanRequestedAbsence,
    FineosExtractVPaidLeaveInstruction,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import FineosIAWWData


@pytest.fixture
def local_iaww_extract_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return extractor.IAWWExtractStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def stage_data(records, db_session, reference_file=None, import_log=None):
    if not reference_file:
        reference_file = ReferenceFileFactory.create(
            reference_file_type_id=ReferenceFileType.FINEOS_IAWW_EXTRACT.reference_file_type_id
        )
    if not import_log:
        import_log = ImportLogFactory.create()

    for record in records:
        instance = payments_util.create_staging_table_instance(
            record.get_leave_plan_request_absence_record(),
            FineosExtractVbiLeavePlanRequestedAbsence,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)
        instance = payments_util.create_staging_table_instance(
            record.get_vpaid_leave_instruction_record(),
            FineosExtractVPaidLeaveInstruction,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)

    db_session.commit()


def test_run_step_happy_path(local_iaww_extract_step, local_test_db_session):
    # create absence cases and get the leave request ID so we can generate FINEOS IAWW data
    absence_case_1 = AbsencePeriodFactory.create()
    leave_request_1 = absence_case_1.fineos_leave_request_id
    absence_case_2 = AbsencePeriodFactory.create()
    leave_request_2 = absence_case_2.fineos_leave_request_id

    # this absence case will have the same leave request id, and should also have it's IAWW populated
    absence_case_3 = AbsencePeriodFactory.create(fineos_leave_request_id=leave_request_1)

    # this absence case will not have corresponding IAWW data from FINEOS and should not get updated
    absence_case_4 = AbsencePeriodFactory.create()

    iaww_data_1 = FineosIAWWData(leave_request_id_value=leave_request_1)
    iaww_data_2 = FineosIAWWData(leave_request_id_value=leave_request_2)

    stage_data([iaww_data_1, iaww_data_2], local_test_db_session)

    local_iaww_extract_step.run()

    assert absence_case_1.fineos_average_weekly_wage == decimal.Decimal(iaww_data_1.aww_value)
    assert absence_case_2.fineos_average_weekly_wage == decimal.Decimal(iaww_data_2.aww_value)
    assert absence_case_3.fineos_average_weekly_wage == decimal.Decimal(iaww_data_1.aww_value)
    assert absence_case_4.fineos_average_weekly_wage is None


def test_run_overwrite_existing_iaww_data(local_iaww_extract_step, local_test_db_session):
    employer = EmployerFactory.create()
    claim = ClaimFactory.create(employer_id=employer.employer_id)
    # create absence cases and get the leave request ID so we can generate FINEOS IAWW data
    absence_case_1 = AbsencePeriodFactory.create(claim_id=claim.claim_id)
    leave_request_1 = absence_case_1.fineos_leave_request_id
    absence_case_2 = AbsencePeriodFactory.create()
    leave_request_2 = absence_case_2.fineos_leave_request_id

    claim.fineos_absence_status_id = AbsenceStatus.APPROVED.absence_status_id
    claim.absence_period_start_date = absence_case_1.absence_period_start_date

    iaww_data_1 = FineosIAWWData(leave_request_id_value=leave_request_1, aww_value="1000")
    iaww_data_2 = FineosIAWWData(leave_request_id_value=leave_request_2, aww_value="1200")

    stage_data([iaww_data_1, iaww_data_2], local_test_db_session)

    local_iaww_extract_step.run()

    assert absence_case_1.fineos_average_weekly_wage == decimal.Decimal("1000")
    assert absence_case_2.fineos_average_weekly_wage == decimal.Decimal("1200")

    benefit_year = get_benefit_year_by_employee_id(
        local_test_db_session, claim.employee_id, claim.absence_period_start_date
    )

    for contribution in benefit_year.contributions:
        if contribution.employer_id == claim.employer_id:
            assert contribution.average_weekly_wage == decimal.Decimal("1000")

    # change the IAWW for the first absence case and ensure it gets updated with the new value
    iaww_data_1 = FineosIAWWData(leave_request_id_value=leave_request_1, aww_value="1100")
    stage_data([iaww_data_1, iaww_data_2], local_test_db_session)

    local_iaww_extract_step.run()

    assert absence_case_1.fineos_average_weekly_wage == decimal.Decimal("1100")
    assert absence_case_2.fineos_average_weekly_wage == decimal.Decimal("1200")

    for contribution in benefit_year.contributions:
        if contribution.employer_id == claim.employer_id:
            assert contribution.average_weekly_wage == decimal.Decimal("1100")
