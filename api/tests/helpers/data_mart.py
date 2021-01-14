import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.db.models.employees import Employee, State, StateLog
from massgov.pfml.db.models.factories import CtrAddressPairFactory, EftFactory


def create_complete_valid_matching_vendor_info_for_employee(
    employee: Employee,
) -> data_mart.VendorInfoResult:
    addr = employee.ctr_address_pair.fineos_address

    return data_mart.VendorInfoResult(
        vendor_customer_code=employee.ctr_vendor_customer_code,
        vendor_active_status=data_mart.VendorActiveStatus.ACTIVE,
        eft_status=data_mart.EFTStatus.ELIGIBILE_FOR_EFT,
        generate_eft_payment=True,
        aba_no=employee.eft.routing_nbr if employee.eft else None,
        address_id=payments_util.Constants.COMPTROLLER_AD_ID,
        street_1=addr.address_line_one,
        street_2=addr.address_line_two,
        city=addr.city,
        zip_code=addr.zip_code,
        state=addr.geo_state.geo_state_description,
        country_code=addr.country.country_description if addr.country else None,
    )


def run_test_process_success_no_pending_payment(
    test_db_session, mock_data_mart_client, mocker, state_log, process_func
):
    employee = state_log.employee

    if employee.ctr_vendor_customer_code is None:
        employee.ctr_vendor_customer_code = "foo"

    if employee.eft is None:
        employee.eft = EftFactory.create()

    if employee.ctr_address_pair is None:
        employee.ctr_address_pair = CtrAddressPairFactory.create()

    mock_data_mart_client.get_vendor_info.return_value = create_complete_valid_matching_vendor_info_for_employee(
        employee
    )

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    process_func(test_db_session, mock_data_mart_client)

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee,
        end_state=State.MMARS_STATUS_CONFIRMED,
        db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id
    assert new_state_log.start_state_id == state_log.end_state.state_id
