import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import Country, Employee, GeoState, State, StateLog
from massgov.pfml.db.models.factories import AddressFactory, CtrAddressPairFactory, EftFactory


def create_complete_valid_matching_vendor_info_for_employee(
    employee: Employee,
) -> data_mart.VendorInfoResult:
    addr = employee.ctr_address_pair.ctr_address

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
        state=GeoState.get_description(addr.geo_state_id) if addr.geo_state_id else None,
        country_code=Country.get_description(addr.country_id) if addr.country_id else None,
    )


def run_test_process_success_no_pending_payment(
    test_db_session, mock_data_mart_client, mocker, state_log, process_func
):
    employee = state_log.employee
    previous_end_state_id = state_log.end_state.state_id

    if employee.ctr_vendor_customer_code is None:
        employee.ctr_vendor_customer_code = "foo"

    if employee.eft is None:
        employee.eft = EftFactory.create()

    if employee.ctr_address_pair is None:
        employee.ctr_address_pair = CtrAddressPairFactory.create()
        employee.ctr_address_pair.ctr_address = AddressFactory.create()

    mock_data_mart_client.get_vendor_info.return_value = create_complete_valid_matching_vendor_info_for_employee(
        employee
    )

    # just be sure all the setup is written to the DB
    test_db_session.commit()

    state_log_count_before = test_db_session.query(StateLog).count()
    assert state_log_count_before == 1

    # run process
    process_func(test_db_session, mock_data_mart_client)

    # we do not want to test things that are not committed, so close the session
    # so the asserts below are against only the data that exists in the DB
    test_db_session.close()

    state_log_count_after = test_db_session.query(StateLog).count()
    assert state_log_count_after == 2

    new_state_log = state_log_util.get_latest_state_log_in_end_state(
        associated_model=employee,
        end_state=State.MMARS_STATUS_CONFIRMED,
        db_session=test_db_session,
    )

    assert new_state_log
    assert new_state_log.state_log_id != state_log.state_log_id
    assert new_state_log.end_state_id != previous_end_state_id
