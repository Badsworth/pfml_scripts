import pydantic
import pytest
import sqlalchemy.orm.exc

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.common as common
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import (
    Country,
    GeoState,
    LatestStateLog,
    PaymentMethod,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import CtrAddressPairFactory, EftFactory, EmployeeFactory
from tests.helpers.data_mart import create_complete_valid_matching_vendor_info_for_employee
from tests.helpers.state_log import setup_state_log

# tests in here require real resources
pytestmark = pytest.mark.integration


# Helpers


def create_identify_mmars_status_state_log(test_db_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.VENDOR_CHECK_INITIATED_BY_VENDOR_EXPORT],
        end_states=[State.IDENTIFY_MMARS_STATUS],
        test_db_session=test_db_session,
    )

    return state_log_setup.state_logs[0]


@pytest.fixture
def complete_vendor_info_address():
    return data_mart.VendorInfoResult(
        street_1="123 MAIN ST",
        street_2="APT 4",
        city="Boston",
        state="MA",
        zip_code="12345-6789",
        country_code="USA",
    )


# Tests


def test_query_data_mart_for_issues_and_updates_no_vendor(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create()
    mocker.patch.object(data_mart, "get_vendor_info", return_value=None)

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.vendor_exists is False
    assert issues_and_updates.employee_updates is False
    assert issues_and_updates.issues.has_validation_issues() is False


def test_query_data_mart_for_issues_and_updates_parse_error(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create()

    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        side_effect=pydantic.ValidationError([], data_mart.VendorInfoResult),
    )

    with pytest.raises(pydantic.ValidationError):
        common.query_data_mart_for_issues_and_updates(
            mock_data_mart_engine, employee, employee.tax_identifier
        )


def test_query_data_mart_for_issues_and_updates_multiple_vendor_entries(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create()

    mocker.patch.object(
        data_mart, "get_vendor_info", side_effect=sqlalchemy.orm.exc.MultipleResultsFound(),
    )

    with pytest.raises(sqlalchemy.orm.exc.MultipleResultsFound):
        common.query_data_mart_for_issues_and_updates(
            mock_data_mart_engine, employee, employee.tax_identifier
        )


def test_query_data_mart_for_issues_and_updates_no_vendor_info(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    # Have Data Mart return empty info for the Vendor
    mocker.patch.object(
        data_mart, "get_vendor_info", return_value=data_mart.VendorInfoResult(),
    )

    # If employee doesn't have a ctr_vendor_customer_code, then it still
    # shouldn't if we don't get one from Data Mart
    employee_without_vendor_code = EmployeeFactory.create(ctr_vendor_customer_code=None)

    assert employee_without_vendor_code.ctr_vendor_customer_code is None

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine,
        employee_without_vendor_code,
        employee_without_vendor_code.tax_identifier,
    )

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is False
    assert issues_and_updates.issues.validation_issues == [
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD, "vendor_customer_code"
        ),
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD, "vendor_active_status"
        ),
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD, "Vendor address does not exist"
        ),
    ]

    assert employee_without_vendor_code.ctr_vendor_customer_code is None

    # For an employee that has an existing ctr_vendor_customer_code set, don't
    # erase if we get back nothing from Data Mart
    employee_with_vendor_code = EmployeeFactory.create(ctr_vendor_customer_code="BAR")

    assert employee_with_vendor_code.ctr_vendor_customer_code == "BAR"

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee_with_vendor_code, employee_with_vendor_code.tax_identifier
    )

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is False
    assert issues_and_updates.issues.validation_issues == [
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD, "vendor_customer_code"
        ),
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD, "vendor_active_status"
        ),
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD, "Vendor address does not exist"
        ),
    ]

    assert employee_with_vendor_code.ctr_vendor_customer_code == "BAR"


def test_query_data_mart_for_issues_and_updates_sets_vendor_customer_code_only_if_different(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    # If the employee has no customer code...
    employee = EmployeeFactory.create(ctr_vendor_customer_code=None)
    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(vendor_customer_code="FOO"),
    )

    assert employee.ctr_vendor_customer_code is None

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    # ...we should pick it up
    assert issues_and_updates.employee_updates is True
    assert employee.ctr_vendor_customer_code == "FOO"

    # If we run through it again...
    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    # ...should indicate no updates and value is unchanged
    assert issues_and_updates.employee_updates is False
    assert employee.ctr_vendor_customer_code == "FOO"

    # But if new value shows up...
    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(vendor_customer_code="BAR"),
    )

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    # ...we should see the update
    assert issues_and_updates.employee_updates is True
    assert employee.ctr_vendor_customer_code == "BAR"


def test_query_data_mart_for_issues_and_updates_sets_ctr_address_only_if_none_and_matching(
    test_db_session,
    initialize_factories_session,
    mock_data_mart_engine,
    mocker,
    complete_vendor_info_address,
):
    address_mismatch_issue = payments_util.ValidationIssue(
        payments_util.ValidationReason.MISMATCHED_DATA, "Vendor address does not match",
    )

    employee = EmployeeFactory.create(ctr_address_pair=CtrAddressPairFactory.create())

    # If we get address info that does not match the FINEOS address, it should
    # not be saved.
    mismatching_vendor_info = complete_vendor_info_address
    mismatching_vendor_info.address_id = "FOO"
    mismatching_vendor_info.vendor_customer_code = employee.ctr_vendor_customer_code

    mocker.patch.object(data_mart, "get_vendor_info", return_value=mismatching_vendor_info)

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.employee_updates is False
    assert employee.ctr_address_pair.ctr_address is None
    assert address_mismatch_issue in issues_and_updates.issues.validation_issues

    # If we wipe that out and try from None with an address that matches the existing,
    # we should save the address and see no validation issue
    employee.ctr_address_pair.ctr_address = None
    test_db_session.commit()
    assert employee.ctr_address_pair.ctr_address is None

    matching_vendor_info = create_complete_valid_matching_vendor_info_for_employee(employee)

    mocker.patch.object(data_mart, "get_vendor_info", return_value=matching_vendor_info)

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.employee_updates is True
    assert employee.ctr_address_pair.ctr_address is not None
    assert address_mismatch_issue not in issues_and_updates.issues.validation_issues

    # If we run through the process again...
    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    # ...should indicate no updates and value is unchanged
    assert issues_and_updates.employee_updates is False
    assert employee.ctr_address_pair.ctr_address is not None
    assert address_mismatch_issue not in issues_and_updates.issues.validation_issues

    # Even if new value shows up...
    mocker.patch.object(data_mart, "get_vendor_info", return_value=mismatching_vendor_info)

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    # ...we should not see any update
    assert issues_and_updates.employee_updates is False
    assert employee.ctr_address_pair.ctr_address is not None
    # but there should be a mismatch error
    assert address_mismatch_issue in issues_and_updates.issues.validation_issues


def test_query_data_mart_for_issues_and_updates_not_active(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create()

    for not_active_status in [
        data_mart.VendorActiveStatus.INACTIVE,
        data_mart.VendorActiveStatus.NULL,
        data_mart.VendorActiveStatus.NOT_APPLICABLE,
        data_mart.VendorActiveStatus.DELETE,
    ]:
        mocker.patch.object(
            data_mart,
            "get_vendor_info",
            return_value=data_mart.VendorInfoResult(
                vendor_customer_code="FOO", vendor_active_status=not_active_status,
            ),
        )

        issues_and_updates = common.query_data_mart_for_issues_and_updates(
            mock_data_mart_engine, employee, employee.tax_identifier
        )

        status_issue = payments_util.ValidationIssue(
            payments_util.ValidationReason.UNUSABLE_STATE,
            f"vendor_active_status is {not_active_status.name}",
        )

        assert issues_and_updates.vendor_exists is True
        assert status_issue in issues_and_updates.issues.validation_issues


def test_query_data_mart_for_issues_and_updates_ach_set_but_no_info_in_API(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)
    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(
            vendor_customer_code="FOO",
            vendor_active_status=data_mart.VendorActiveStatus.ACTIVE,
            eft_status=None,
        ),
    )

    with pytest.raises(ValueError) as e:
        common.query_data_mart_for_issues_and_updates(
            mock_data_mart_engine, employee, employee.tax_identifier
        )

    assert (
        str(e.value)
        == f"No EFT information for Employee with ACH payment method in API DB. Employee ID: {employee.employee_id}"
    )


def test_query_data_mart_for_issues_and_updates_ach_set_but_no_info_in_MMARS(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create(
        payment_method_id=PaymentMethod.ACH.payment_method_id, eft=EftFactory.create()
    )
    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(
            vendor_customer_code="FOO",
            vendor_active_status=data_mart.VendorActiveStatus.ACTIVE,
            eft_status=None,
        ),
    )

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    eft_related_issues = [
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISSING_FIELD,
            "No EFT information for Employee with ACH payment method in MMARS",
        ),
        payments_util.ValidationIssue(
            payments_util.ValidationReason.MISMATCHED_DATA,
            "Routing number in EFT information for Employee differs",
        ),
    ]

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is True
    for eft_related_issue in eft_related_issues:
        assert eft_related_issue in issues_and_updates.issues.validation_issues


def test_query_data_mart_for_issues_and_updates_ach_set_mismatched_routing_number(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create(
        payment_method_id=PaymentMethod.ACH.payment_method_id, eft=EftFactory.create()
    )

    mismatched_routing_number_issue = payments_util.ValidationIssue(
        payments_util.ValidationReason.MISMATCHED_DATA,
        "Routing number in EFT information for Employee differs",
    )

    # If aba_no is None but Employee has info recorded
    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(
            vendor_customer_code="FOO",
            vendor_active_status=data_mart.VendorActiveStatus.ACTIVE,
            eft_status=data_mart.EFTStatus.PRENOTE_REQUESTED,
            aba_no=None,
        ),
    )

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is True
    assert mismatched_routing_number_issue in issues_and_updates.issues.validation_issues

    # If aba_no is not None, but still different from info Employee has recorded
    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=data_mart.VendorInfoResult(
            vendor_customer_code="FOO",
            vendor_active_status=data_mart.VendorActiveStatus.ACTIVE,
            eft_status=data_mart.EFTStatus.PRENOTE_REQUESTED,
            aba_no="junk",
        ),
    )

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is False
    assert mismatched_routing_number_issue in issues_and_updates.issues.validation_issues


def test_query_data_mart_for_issues_and_updates_no_issues_all_updates_saved(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create(
        ctr_vendor_customer_code=None,
        payment_method_id=PaymentMethod.ACH.payment_method_id,
        eft=EftFactory.create(),
        ctr_address_pair=CtrAddressPairFactory.create(),
    )

    # ensure there's no address for the comptroller representation
    employee.ctr_address_pair.ctr_address = None
    test_db_session.commit()

    vendor_info = create_complete_valid_matching_vendor_info_for_employee(employee)
    vendor_info.vendor_customer_code = "FOO"

    mocker.patch.object(data_mart, "get_vendor_info", return_value=vendor_info)

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is True
    assert issues_and_updates.issues.has_validation_issues() is False

    assert employee.ctr_vendor_customer_code == vendor_info.vendor_customer_code
    assert employee.ctr_address_pair.ctr_address is not None
    assert payments_util.is_same_address(
        employee.ctr_address_pair.fineos_address, employee.ctr_address_pair.ctr_address
    )


def test_query_data_mart_for_issues_and_updates_no_issues_no_updates(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker
):
    employee = EmployeeFactory.create(
        payment_method_id=PaymentMethod.ACH.payment_method_id,
        eft=EftFactory.create(),
        ctr_address_pair=CtrAddressPairFactory.create(),
    )

    employee.ctr_address_pair.ctr_address = employee.ctr_address_pair.fineos_address
    test_db_session.commit()

    mocker.patch.object(
        data_mart,
        "get_vendor_info",
        return_value=create_complete_valid_matching_vendor_info_for_employee(employee),
    )

    issues_and_updates = common.query_data_mart_for_issues_and_updates(
        mock_data_mart_engine, employee, employee.tax_identifier
    )

    assert issues_and_updates.vendor_exists is True
    assert issues_and_updates.employee_updates is False
    assert issues_and_updates.issues.has_validation_issues() is False


def simple_address_asserts(mmars_data, db_address):
    assert db_address.address_type is None
    assert db_address.address_line_one == mmars_data.street_1
    assert db_address.address_line_two == mmars_data.street_2
    assert db_address.city == mmars_data.city
    assert db_address.zip_code == mmars_data.zip_code


def test_make_db_address_from_mmars_data(test_db_session, complete_vendor_info_address):
    # Happy path
    mmars_data = complete_vendor_info_address.copy()

    db_address = common.make_db_address_from_mmars_data(mmars_data)

    simple_address_asserts(mmars_data, db_address)
    assert db_address.geo_state_id == GeoState.MA.geo_state_id
    assert db_address.geo_state_text is None
    assert db_address.country_id == Country.USA.country_id

    # Unknown (to PFML) country code
    mmars_data = complete_vendor_info_address.copy()
    mmars_data.country_code = "YUG"

    db_address = common.make_db_address_from_mmars_data(mmars_data)

    simple_address_asserts(mmars_data, db_address)
    assert db_address.geo_state_id == GeoState.MA.geo_state_id
    assert db_address.geo_state_text is None
    assert db_address.country_id is None

    # Unknown (to PFML) state
    mmars_data = complete_vendor_info_address.copy()
    mmars_data.state = "FO"

    db_address = common.make_db_address_from_mmars_data(mmars_data)

    simple_address_asserts(mmars_data, db_address)
    assert db_address.geo_state_id is None
    assert db_address.geo_state_text == mmars_data.state
    assert db_address.country_id == Country.USA.country_id

    # Empty info
    mmars_data = data_mart.VendorInfoResult()

    db_address = common.make_db_address_from_mmars_data(mmars_data)

    simple_address_asserts(mmars_data, db_address)
    assert db_address.geo_state_id is None
    assert db_address.geo_state_text is None
    assert db_address.country_id is None


def test_process_data_mart_issues_no_vendor(test_db_session, initialize_factories_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.IDENTIFY_MMARS_STATUS],
        end_states=[None],
        test_db_session=test_db_session,
    )

    state_log = state_log_setup.state_logs[0]
    employee = state_log.employee

    # signal couldn't find vendor
    issues = common.DataMartIssuesAndUpdates(vendor_exists=False)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    common.process_data_mart_issues(
        test_db_session,
        state_log,
        employee,
        issues,
        missing_vendor_state=State.ADD_TO_VCC,
        mismatched_data_state=State.ADD_TO_VCM_REPORT,
    )

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 1

    test_db_session.refresh(state_log)
    assert state_log.end_state_id == State.ADD_TO_VCC.state_id
    assert state_log.outcome == state_log_util.build_outcome(
        "Queried Data Mart: Vendor does not exist yet"
    )


def test_process_data_mart_issues_mismatched_data(test_db_session, initialize_factories_session):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.IDENTIFY_MMARS_STATUS],
        end_states=[None],
        test_db_session=test_db_session,
    )

    state_log = state_log_setup.state_logs[0]
    employee = state_log.employee

    # signal some issue
    issues = common.DataMartIssuesAndUpdates(
        vendor_exists=True,
        issues=payments_util.ValidationContainer(
            record_key="foo",
            validation_issues=[
                payments_util.ValidationIssue(
                    payments_util.ValidationReason.UNUSABLE_STATE,
                    "vendor_active_status is INACTIVE",
                ),
            ],
        ),
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    common.process_data_mart_issues(
        test_db_session,
        state_log,
        employee,
        issues,
        missing_vendor_state=State.ADD_TO_VCC,
        mismatched_data_state=State.ADD_TO_VCM_REPORT,
    )

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 1

    test_db_session.refresh(state_log)
    assert state_log.end_state_id == State.ADD_TO_VCM_REPORT.state_id
    assert state_log.outcome == state_log_util.build_outcome(
        "Queried Data Mart: Vendor does not match", issues.issues
    )


def test_process_data_mart_issues_no_issues_no_pending_payment(
    test_db_session, initialize_factories_session
):
    state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.IDENTIFY_MMARS_STATUS],
        end_states=[None],
        test_db_session=test_db_session,
    )

    state_log = state_log_setup.state_logs[0]
    employee = state_log.employee

    # signal no issues
    issues = common.DataMartIssuesAndUpdates(vendor_exists=True)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    common.process_data_mart_issues(
        test_db_session,
        state_log,
        employee,
        issues,
        missing_vendor_state=State.ADD_TO_VCC,
        mismatched_data_state=State.ADD_TO_VCM_REPORT,
    )

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 1

    test_db_session.refresh(state_log)
    assert state_log.end_state_id == State.MMARS_STATUS_CONFIRMED.state_id
    assert state_log.outcome == state_log_util.build_outcome("Vendor confirmed in MMARS.")


def test_process_data_mart_issues_no_issues_pending_payment_updated(
    test_db_session, initialize_factories_session
):
    employee_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.IDENTIFY_MMARS_STATUS],
        end_states=[None],
        test_db_session=test_db_session,
    )

    vendor_check_state_log = employee_state_log_setup.state_logs[0]
    employee = vendor_check_state_log.employee

    payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        test_db_session=test_db_session,
    )

    payment_state_log = payment_state_log_setup.state_logs[0]
    payment = payment_state_log.payment

    # Update claim to be for the test employee
    payment.claim.employee = employee

    test_db_session.commit()

    # signal no issues
    issues = common.DataMartIssuesAndUpdates(vendor_exists=True)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 2

    common.process_data_mart_issues(
        test_db_session,
        vendor_check_state_log,
        employee,
        issues,
        missing_vendor_state=State.ADD_TO_VCC,
        mismatched_data_state=State.ADD_TO_VCM_REPORT,
    )

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 3

    test_db_session.refresh(vendor_check_state_log)
    assert vendor_check_state_log.end_state_id == State.MMARS_STATUS_CONFIRMED.state_id

    new_payment_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=payment, end_state=State.ADD_TO_GAX, db_session=test_db_session,
    )

    assert new_payment_state_log
    assert new_payment_state_log.start_state_id == State.CONFIRM_VENDOR_STATUS_IN_MMARS.state_id


def test_process_data_mart_issues_no_issues_multiple_pending_payment_updated(
    test_db_session, initialize_factories_session
):
    employee_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.IDENTIFY_MMARS_STATUS],
        end_states=[None],
        test_db_session=test_db_session,
    )

    vendor_check_state_log = employee_state_log_setup.state_logs[0]
    employee = vendor_check_state_log.employee

    first_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        test_db_session=test_db_session,
    )

    first_payment_state_log = first_payment_state_log_setup.state_logs[0]
    first_payment = first_payment_state_log.payment
    # Update claim to be for the test employee
    first_payment.claim.employee = employee

    second_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        test_db_session=test_db_session,
    )

    second_payment_state_log = second_payment_state_log_setup.state_logs[0]
    second_payment = second_payment_state_log.payment
    # Make second payment a part of the same claim as the first one
    second_payment.claim = first_payment.claim

    third_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        test_db_session=test_db_session,
    )
    third_payment_state_log = third_payment_state_log_setup.state_logs[0]
    third_payment = third_payment_state_log.payment
    # Same Employee, different Claim
    third_payment.claim.employee = employee

    different_employee_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        test_db_session=test_db_session,
    )
    different_employee_payment_state_log = different_employee_payment_state_log_setup.state_logs[0]
    different_employee_payment = different_employee_payment_state_log.payment

    test_db_session.commit()

    # signal no issues
    issues = common.DataMartIssuesAndUpdates(vendor_exists=True)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 5

    latest_state_log_count_before = test_db_session.query(LatestStateLog).count()
    assert latest_state_log_count_before == 5

    common.process_data_mart_issues(
        test_db_session,
        vendor_check_state_log,
        employee,
        issues,
        missing_vendor_state=State.ADD_TO_VCC,
        mismatched_data_state=State.ADD_TO_VCM_REPORT,
    )

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 8

    latest_state_log_count_after = test_db_session.query(LatestStateLog).count()
    assert latest_state_log_count_after == 5

    test_db_session.refresh(vendor_check_state_log)
    assert vendor_check_state_log.end_state_id == State.MMARS_STATUS_CONFIRMED.state_id

    # all payments for our confirmed employee should be moved along
    for payment in [first_payment, second_payment, third_payment]:
        new_payment_state_log = state_log_util.get_latest_state_log_in_end_state(
            associated_model=payment, end_state=State.ADD_TO_GAX, db_session=test_db_session,
        )

        assert new_payment_state_log
        assert new_payment_state_log.start_state_id == State.CONFIRM_VENDOR_STATUS_IN_MMARS.state_id

    # *should not* have a `ADD_TO_GAX` state for the payment for the employee we have not confirmed
    new_different_employee_payment_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=different_employee_payment,
        end_state=State.ADD_TO_GAX,
        db_session=test_db_session,
    )

    assert new_different_employee_payment_state_log is None


def test_process_data_mart_issues_no_issues_only_new_pending_payment_updated(
    test_db_session, initialize_factories_session
):
    employee_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        start_states=[State.IDENTIFY_MMARS_STATUS],
        end_states=[None],
        test_db_session=test_db_session,
    )

    vendor_check_state_log = employee_state_log_setup.state_logs[0]
    employee = vendor_check_state_log.employee

    first_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        test_db_session=test_db_session,
    )

    first_payment_state_log = first_payment_state_log_setup.state_logs[0]
    first_payment = first_payment_state_log.payment
    # Update claim to be for the test employee
    first_payment.claim.employee = employee

    # Add some payments that have already moved along to ADD_TO_GAX for this
    # claim and employee
    second_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS, State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS, State.ADD_TO_GAX],
        test_db_session=test_db_session,
    )

    for second_payment_state_log in second_payment_state_log_setup.state_logs:
        second_payment_state_log = second_payment_state_log_setup.state_logs[0]
        second_payment = second_payment_state_log.payment
        # Make second payment a part of the same claim as the first one
        second_payment.claim = first_payment.claim

    third_payment_state_log_setup = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        start_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS, State.CONFIRM_VENDOR_STATUS_IN_MMARS],
        end_states=[State.CONFIRM_VENDOR_STATUS_IN_MMARS, State.ADD_TO_GAX],
        test_db_session=test_db_session,
    )
    for third_payment_state_log in third_payment_state_log_setup.state_logs:
        third_payment_state_log = third_payment_state_log_setup.state_logs[0]
        third_payment = third_payment_state_log.payment
        # Same Employee, different Claim
        third_payment.claim.employee = employee

    test_db_session.commit()

    # signal no issues
    issues = common.DataMartIssuesAndUpdates(vendor_exists=True)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 6

    latest_state_log_count_before = test_db_session.query(LatestStateLog).count()
    assert latest_state_log_count_before == 4

    common.process_data_mart_issues(
        test_db_session,
        vendor_check_state_log,
        employee,
        issues,
        missing_vendor_state=State.ADD_TO_VCC,
        mismatched_data_state=State.ADD_TO_VCM_REPORT,
    )

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 7

    latest_state_log_count_after = test_db_session.query(LatestStateLog).count()
    assert latest_state_log_count_after == 4

    test_db_session.refresh(vendor_check_state_log)
    assert vendor_check_state_log.end_state_id == State.MMARS_STATUS_CONFIRMED.state_id

    # the first (new) payment should be moved along
    new_payment_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=first_payment, end_state=State.ADD_TO_GAX, db_session=test_db_session,
    )

    assert new_payment_state_log
    assert new_payment_state_log.start_state_id == State.CONFIRM_VENDOR_STATUS_IN_MMARS.state_id

    # the other payments should not have any state change
    for unchanged_payment_state_log in [
        second_payment_state_log_setup.state_logs[1],
        third_payment_state_log_setup.state_logs[1],
    ]:
        new_payment_state_log = state_log_util.get_latest_state_log_in_end_state(
            associated_model=unchanged_payment_state_log.payment,
            end_state=State.ADD_TO_GAX,
            db_session=test_db_session,
        )

        assert new_payment_state_log.state_log_id == unchanged_payment_state_log.state_log_id


def test_process_catches_exceptions_and_continues(
    test_db_session, initialize_factories_session, mock_data_mart_engine, mocker, caplog
):
    state_logs = [create_identify_mmars_status_state_log(test_db_session) for _ in range(2)]

    employee_to_fail_processing = state_logs[0].employee

    def mock_process_state_log_func(pfml_db_session, data_mart_conn, state_log, employee, tax_id):
        if employee.employee_id == employee_to_fail_processing.employee_id:
            raise Exception
        else:
            state_log_util.finish_state_log(
                state_log=state_log,
                end_state=State.ADD_TO_VCC,
                outcome=state_log_util.build_outcome(
                    "Queried Data Mart: Vendor does not exist yet"
                ),
                db_session=pfml_db_session,
            )
            return None

    mock_process_state_log = mocker.Mock(side_effect=mock_process_state_log_func)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 2

    common.process_employees_in_state(
        test_db_session, mock_data_mart_engine, State.IDENTIFY_MMARS_STATUS, mock_process_state_log
    )

    assert mock_process_state_log.call_count == 2

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 4

    # check that the processing error was logged, there was only one such
    # message and it was tagged with the correct extra info
    assert len(caplog.records) > 0
    failed_log_records = list(
        filter(lambda lr: lr.msg == "Hit error processing record", caplog.records)
    )
    assert len(failed_log_records) == 1
    failed_log_record_dict = failed_log_records[0].__dict__
    assert failed_log_record_dict["employee_id"] == employee_to_fail_processing.employee_id
    assert failed_log_record_dict["start_state"] == State.IDENTIFY_MMARS_STATUS.state_description

    # first employee should be in same state as start due to exception
    new_state_log_for_failed = state_log_util.get_latest_state_log_in_end_state(
        associated_model=state_logs[0].employee,
        end_state=State.IDENTIFY_MMARS_STATUS,
        db_session=test_db_session,
    )

    assert new_state_log_for_failed
    assert new_state_log_for_failed.state_log_id != state_logs[0].state_log_id
    assert new_state_log_for_failed.start_state_id == State.IDENTIFY_MMARS_STATUS.state_id
    assert new_state_log_for_failed.end_state_id == State.IDENTIFY_MMARS_STATUS.state_id
    assert new_state_log_for_failed.outcome["message"] == "Hit exception: Exception"
    # and the related log message should have the correct info
    assert failed_log_record_dict["state_log_id"] == new_state_log_for_failed.state_log_id

    # second employee should be in next state
    new_state_log_for_success = state_log_util.get_latest_state_log_in_end_state(
        associated_model=state_logs[1].employee,
        end_state=State.ADD_TO_VCC,
        db_session=test_db_session,
    )

    assert new_state_log_for_success
    assert new_state_log_for_success.state_log_id != state_logs[1].state_log_id
    assert new_state_log_for_success.start_state_id == State.IDENTIFY_MMARS_STATUS.state_id
    assert new_state_log_for_success.end_state_id == State.ADD_TO_VCC.state_id


def test_process_data_mart_connection_issue_kills_everything(
    test_db_session, initialize_factories_session, mocker, mock_data_mart_engine
):
    mock_process_state_log = mocker.Mock()

    failing_data_mart_engine = mock_data_mart_engine
    failing_data_mart_engine.connect = mocker.Mock(side_effect=Exception)

    for _ in range(2):
        create_identify_mmars_status_state_log(test_db_session)

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 2

    with pytest.raises(Exception):
        common.process_employees_in_state(
            test_db_session,
            failing_data_mart_engine,
            State.IDENTIFY_MMARS_STATUS,
            mock_process_state_log,
        )

    mock_process_state_log.assert_not_called()

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2
