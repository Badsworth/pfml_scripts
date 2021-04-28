import logging  # noqa: B1

import pytest
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.payments.ctr_vendor_customer_code_cleanup as vc_cleanup
import massgov.pfml.payments.data_mart as data_mart
from massgov.pfml.db.models.factories import EmployeeFactory


class MockLogEntry:
    def set_metrics(self, metrics):
        pass

    def increment(self, metric):
        pass


def test_cleanup_single_employee(caplog, initialize_factories_session, mocker):
    """Test successful match."""
    caplog.set_level(logging.INFO)  # noqa: B1
    config = vc_cleanup.Configuration([])
    employee = EmployeeFactory.create(ctr_vendor_customer_code="foo")
    vendor_info = data_mart.VendorInfoResult(vendor_customer_code="foo",)
    mocker.patch.object(vc_cleanup, "get_vendor_info", return_value=vendor_info)

    update_required = vc_cleanup.cleanup_single_employee(config, employee)

    assert update_required is False
    assert len(caplog.records) == 1
    assert "Success" in caplog.records[0].msg


def test_cleanup_single_employee_update_required(caplog, initialize_factories_session, mocker):
    """Test update required in default mode: dry run is on."""
    caplog.set_level(logging.INFO)  # noqa: B1
    config = vc_cleanup.Configuration([])
    employee = EmployeeFactory.create(ctr_vendor_customer_code="foo")
    vendor_info = data_mart.VendorInfoResult(vendor_customer_code="bar",)
    mocker.patch.object(vc_cleanup, "get_vendor_info", return_value=vendor_info)

    update_required = vc_cleanup.cleanup_single_employee(config, employee)

    assert update_required is True
    assert len(caplog.records) == 1
    assert caplog.records[0].msg == "Warning: VC code in PFML API db does not match Data Mart"
    # Confirm the employee record is unchanged.
    assert employee.ctr_vendor_customer_code == "foo"


def test_cleanup_single_employee_update_required_no_dry_run(
    caplog, initialize_factories_session, mocker
):
    """Test update required with dry run off."""
    caplog.set_level(logging.INFO)  # noqa: B1
    config = vc_cleanup.Configuration(["--commit"])
    employee = EmployeeFactory.create(ctr_vendor_customer_code="foo")
    vendor_info = data_mart.VendorInfoResult(vendor_customer_code="bar",)
    mocker.patch.object(vc_cleanup, "get_vendor_info", return_value=vendor_info)

    update_required = vc_cleanup.cleanup_single_employee(config, employee)

    assert update_required is True
    assert len(caplog.records) == 2
    # Confirm the employee record has changed.
    assert employee.ctr_vendor_customer_code == "bar"


def test_cleanup_single_employee_delete(caplog, initialize_factories_session, mocker):
    """Test delete employee.ctr_vendor_customer_code in default mode: dry run is on."""
    caplog.set_level(logging.INFO)  # noqa: B1
    config = vc_cleanup.Configuration([])
    employee = EmployeeFactory.create(ctr_vendor_customer_code="foo")
    mocker.patch.object(vc_cleanup, "get_vendor_info", return_value=None)

    update_required = vc_cleanup.cleanup_single_employee(config, employee)

    assert update_required is True
    assert len(caplog.records) == 1
    assert caplog.records[0].msg == "Warning: No match found in Data Mart"
    # Confirm the employee record is unchanged.
    assert employee.ctr_vendor_customer_code == "foo"


def test_cleanup_single_employee_delete_no_dry_run(caplog, initialize_factories_session, mocker):
    """Test delete employee.ctr_vendor_customer_code with dry run off."""
    caplog.set_level(logging.INFO)  # noqa: B1
    config = vc_cleanup.Configuration(["--commit"])
    employee = EmployeeFactory.create(ctr_vendor_customer_code="foo")
    mocker.patch.object(vc_cleanup, "get_vendor_info", return_value=None)

    update_required = vc_cleanup.cleanup_single_employee(config, employee)

    assert update_required is True
    assert len(caplog.records) == 2
    assert caplog.records[0].msg == "Warning: No match found in Data Mart"
    # Confirm the employee record has changed.
    assert employee.ctr_vendor_customer_code is None


def test_cleanup_single_employee_multiple_results(caplog, initialize_factories_session, mocker):
    """Test catching exception: multiple results found"""
    config = vc_cleanup.Configuration([])
    employee = EmployeeFactory.create()
    mocker.patch.object(vc_cleanup, "get_vendor_info", side_effect=MultipleResultsFound)

    with pytest.raises(MultipleResultsFound):
        vc_cleanup.cleanup_single_employee(config, employee)

    assert len(caplog.records) == 1
    assert (
        caplog.records[0].msg == "Data Mart query returned more than one result; something is wrong"
    )


def test_cleanup_single_employee_no_tin(initialize_factories_session):
    """Test catching exception: multiple results found"""
    config = vc_cleanup.Configuration([])
    employee = EmployeeFactory.create()
    employee.tax_identifier = None

    with pytest.raises(Exception):
        vc_cleanup.cleanup_single_employee(config, employee)


def test_cleanup_ctr_vendor_customer_codes(
    caplog, initialize_factories_session, mocker, test_db_session
):
    """Test the process doesn't run if there are no employees with vendor customer codes."""
    caplog.set_level(logging.INFO)  # noqa: B1
    config = vc_cleanup.Configuration([])
    # Make one employee without a vendor customer code.
    EmployeeFactory.create(ctr_vendor_customer_code=None)
    vc_cleanup_spy = mocker.spy(vc_cleanup, "cleanup_single_employee")

    vc_cleanup.cleanup_ctr_vendor_customer_codes(config, test_db_session, MockLogEntry())

    assert "No employees have MMARS vendor customer codes" in [
        record.msg for record in caplog.records
    ]
    # Confirm that vc_cleanup.cleanup_single_employee() does not get called.
    assert vc_cleanup_spy.call_count == 0
