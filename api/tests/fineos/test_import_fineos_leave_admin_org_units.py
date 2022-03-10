import pytest

import massgov.pfml.fineos.import_fineos_leave_admin_org_units as fineos_la_org_units
from massgov.pfml.db.models.employees import OrganizationUnit, UserLeaveAdministratorOrgUnit
from massgov.pfml.db.models.factories import (
    EmployerFactory,
    UserLeaveAdministratorFactory,
    VerificationFactory,
)
from massgov.pfml.types import Fein

content_line_one = '"ORGUNIT_CLASSID","ORGUNIT_INDEXID","ORGUNIT_NAME","FEIN","WORKSITE","POC","EMAIL","USERENABLED"'


@pytest.fixture
def test_verification():
    return VerificationFactory.create()


@pytest.fixture()
def setup_leave_admins(test_verification):
    leave_admin_one = UserLeaveAdministratorFactory.create(
        employer=EmployerFactory.create(employer_fein=Fein("999999998")), verification=test_verification
    )
    leave_admin_two = UserLeaveAdministratorFactory.create(
        employer=EmployerFactory.create(employer_fein=Fein("999999997")), verification=test_verification
    )

    return leave_admin_one, leave_admin_two


def get_test_folder(tmp_path, file_name, content):
    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    # Additional file to test file filter
    file_name_two = "OrgUnitExtract.csv"
    test_file_two = test_folder / file_name_two
    test_file_two.write_text("Just another file\nto Filter out.")

    return test_folder


@pytest.fixture
def la_org_units_happy_path(tmp_path, setup_leave_admins):
    [leave_admin_one, leave_admin_two] = setup_leave_admins

    # The organization unit names used in this data
    # are hard coded in the mock fineos client read employer response
    content_line_two = f'"","","OrgUnitOne","{leave_admin_one.employer.employer_fein}","","","{leave_admin_one.user.email_address}","1"'
    content_line_three = f'"","","OrgUnitThree","{leave_admin_two.employer.employer_fein}","","","{leave_admin_two.user.email_address}","1"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    file_name = "happy_path-VBI_ORGUNIT_DETAILS_SOM.csv"
    return get_test_folder(tmp_path, file_name, content)


@pytest.fixture
def la_org_units_missing_required_fields(tmp_path, setup_leave_admins):
    [leave_admin_one, leave_admin_two] = setup_leave_admins

    content_line_two = f'"","","OrgUnitOne","{leave_admin_one.employer.employer_fein}","","","{leave_admin_one.user.email_address}",""'
    content_line_three = f'"","","OrgUnitThree","","","","{leave_admin_two.user.email_address}","1"'

    content_line_four = (
        f'"","","OrgUnitTwo","{leave_admin_one.employer.employer_fein}","","","","1"'
    )
    content_line_five = f'"","","","{leave_admin_two.employer.employer_fein}","","","{leave_admin_two.user.email_address}","1"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}\n{content_line_four}\n{content_line_five}"

    file_name = "missing_required_fields-VBI_ORGUNIT_DETAILS_SOM.csv"
    return get_test_folder(tmp_path, file_name, content)


@pytest.fixture
def la_org_units_missing_employer(tmp_path, setup_leave_admins):
    [leave_admin_one, leave_admin_two] = setup_leave_admins

    content_line_two = f'"","","OrgUnitOne","{leave_admin_one.employer.employer_fein}","","","{leave_admin_one.user.email_address}","1"'
    content_line_three = (
        f'"","","OrgUnitThree","123456789","","","{leave_admin_two.user.email_address}","1"'
    )
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    file_name = "missing_employer-VBI_ORGUNIT_DETAILS_SOM.csv"
    return get_test_folder(tmp_path, file_name, content)


@pytest.fixture
def la_org_units_missing_employer_org_unit(tmp_path, setup_leave_admins):
    [leave_admin_one, leave_admin_two] = setup_leave_admins

    content_line_two = f'"","","OrgUnitOne","{leave_admin_one.employer.employer_fein}","","","{leave_admin_one.user.email_address}","1"'
    content_line_three = f'"","","OrgUnitTwo","{leave_admin_two.employer.employer_fein}","","","{leave_admin_two.user.email_address}","1"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    file_name = "missing_employer_org_unit-VBI_ORGUNIT_DETAILS_SOM.csv"
    return get_test_folder(tmp_path, file_name, content)


@pytest.fixture
def la_org_units_missing_leave_admin(tmp_path, setup_leave_admins):
    [leave_admin_one, leave_admin_two] = setup_leave_admins

    content_line_two = f'"","","OrgUnitOne","{leave_admin_one.employer.employer_fein}","","","{leave_admin_one.user.email_address}","1"'
    content_line_three = (
        f'"","","OrgUnitThree","{leave_admin_two.employer.employer_fein}","","","a@test.com","1"'
    )
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    file_name = "missing_leave_admin-VBI_ORGUNIT_DETAILS_SOM.csv"
    return get_test_folder(tmp_path, file_name, content)


@pytest.fixture
def la_org_units_leave_admin_disabled(tmp_path, setup_leave_admins):
    [leave_admin_one, leave_admin_two] = setup_leave_admins

    content_line_two = f'"","","OrgUnitOne","{leave_admin_one.employer.employer_fein}","","","{leave_admin_one.user.email_address}","1"'
    content_line_three = f'"","","OrgUnitThree","{leave_admin_two.employer.employer_fein}","","","{leave_admin_two.user.email_address}","0"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    file_name = "leave_admin_disabled-VBI_ORGUNIT_DETAILS_SOM.csv"
    return get_test_folder(tmp_path, file_name, content)


def determine_current_status(test_db_session, leave_admins):
    [leave_admin_one, leave_admin_two] = leave_admins

    employer_one_org_units = (
        test_db_session.query(OrganizationUnit)
        .filter(OrganizationUnit.employer_id == leave_admin_one.employer.employer_id)
        .all()
    )

    employer_two_org_units = (
        test_db_session.query(OrganizationUnit)
        .filter(OrganizationUnit.employer_id == leave_admin_two.employer.employer_id)
        .all()
    )

    leave_admin_one_org_units = (
        test_db_session.query(UserLeaveAdministratorOrgUnit)
        .filter(
            UserLeaveAdministratorOrgUnit.user_leave_administrator_id
            == leave_admin_one.user_leave_administrator_id
        )
        .all()
    )

    leave_admin_two_org_units = (
        test_db_session.query(UserLeaveAdministratorOrgUnit)
        .filter(
            UserLeaveAdministratorOrgUnit.user_leave_administrator_id
            == leave_admin_two.user_leave_administrator_id
        )
        .all()
    )

    return (
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    )


def test_fineos_la_org_units_happy_path(
    test_db_session, initialize_factories_session, setup_leave_admins, la_org_units_happy_path
):
    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    report = fineos_la_org_units.process_fineos_updates(test_db_session, la_org_units_happy_path)

    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 2
    assert len(employer_two_org_units) == 2
    assert len(leave_admin_one_org_units) == 1
    assert len(leave_admin_two_org_units) == 1

    assert report.total_rows_received_count == 2
    assert report.created_employer_org_units_count == 4
    assert report.created_leave_admin_org_units_count == 2

    assert report.missing_required_fields_count == 0
    assert report.errored_employer_org_units_count == 0
    assert report.employer_org_unit_discrepancy_count == 0
    assert report.missing_employer_count == 0
    assert report.missing_leave_admins_count == 0
    assert report.errored_leave_admin_org_units_count == 0
    assert report.missing_fineos_employer_count == 0
    assert report.missing_fineos_org_units_count == 0
    assert report.duplicate_leave_admins_count == 0
    assert report.duplicate_employer_count == 0
    assert report.disabled_leave_admins_count == 0
    assert report.updated_employer_org_units_count == 0


def test_fineos_la_org_units_missing_required_fields(
    test_db_session,
    initialize_factories_session,
    setup_leave_admins,
    la_org_units_missing_required_fields,
):
    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    report = fineos_la_org_units.process_fineos_updates(
        test_db_session, la_org_units_missing_required_fields
    )

    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    assert report.total_rows_received_count == 4
    assert report.missing_required_fields_count == 4

    assert report.created_employer_org_units_count == 0
    assert report.errored_employer_org_units_count == 0
    assert report.employer_org_unit_discrepancy_count == 0
    assert report.missing_employer_count == 0
    assert report.missing_leave_admins_count == 0
    assert report.created_leave_admin_org_units_count == 0
    assert report.errored_leave_admin_org_units_count == 0
    assert report.missing_fineos_employer_count == 0
    assert report.missing_fineos_org_units_count == 0
    assert report.duplicate_leave_admins_count == 0
    assert report.duplicate_employer_count == 0
    assert report.disabled_leave_admins_count == 0
    assert report.updated_employer_org_units_count == 0


def test_fineos_la_org_units_missing_employer(
    test_db_session, initialize_factories_session, setup_leave_admins, la_org_units_missing_employer
):
    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    report = fineos_la_org_units.process_fineos_updates(
        test_db_session, la_org_units_missing_employer
    )

    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 2
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 1
    assert len(leave_admin_two_org_units) == 0

    assert report.total_rows_received_count == 2
    assert report.created_employer_org_units_count == 2
    assert report.created_leave_admin_org_units_count == 1
    assert report.missing_employer_count == 1

    assert report.errored_employer_org_units_count == 0
    assert report.missing_required_fields_count == 0
    assert report.missing_leave_admins_count == 0
    assert report.errored_leave_admin_org_units_count == 0
    assert report.employer_org_unit_discrepancy_count == 0
    assert report.missing_fineos_employer_count == 0
    assert report.missing_fineos_org_units_count == 0
    assert report.duplicate_leave_admins_count == 0
    assert report.duplicate_employer_count == 0
    assert report.disabled_leave_admins_count == 0
    assert report.updated_employer_org_units_count == 0


def test_fineos_la_org_units_missing_employer_org_unit(
    test_db_session,
    initialize_factories_session,
    setup_leave_admins,
    la_org_units_missing_employer_org_unit,
):
    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    report = fineos_la_org_units.process_fineos_updates(
        test_db_session, la_org_units_missing_employer_org_unit
    )

    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 2
    assert len(employer_two_org_units) == 2
    assert len(leave_admin_one_org_units) == 1
    assert len(leave_admin_two_org_units) == 0

    assert report.total_rows_received_count == 2
    assert report.created_employer_org_units_count == 4
    assert report.created_leave_admin_org_units_count == 1
    assert report.employer_org_unit_discrepancy_count == 1

    assert report.missing_required_fields_count == 0
    assert report.errored_employer_org_units_count == 0
    assert report.missing_employer_count == 0
    assert report.missing_leave_admins_count == 0
    assert report.errored_leave_admin_org_units_count == 0
    assert report.missing_fineos_employer_count == 0
    assert report.missing_fineos_org_units_count == 0
    assert report.duplicate_leave_admins_count == 0
    assert report.duplicate_employer_count == 0
    assert report.disabled_leave_admins_count == 0
    assert report.updated_employer_org_units_count == 0


def test_fineos_la_org_units_missing_leave_admin(
    test_db_session,
    initialize_factories_session,
    setup_leave_admins,
    la_org_units_missing_leave_admin,
):
    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    report = fineos_la_org_units.process_fineos_updates(
        test_db_session, la_org_units_missing_leave_admin
    )

    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 2
    assert len(employer_two_org_units) == 2
    assert len(leave_admin_one_org_units) == 1
    assert len(leave_admin_two_org_units) == 0

    assert report.total_rows_received_count == 2
    assert report.created_employer_org_units_count == 4
    assert report.created_leave_admin_org_units_count == 1
    assert report.missing_leave_admins_count == 1

    assert report.missing_required_fields_count == 0
    assert report.errored_employer_org_units_count == 0
    assert report.employer_org_unit_discrepancy_count == 0
    assert report.missing_employer_count == 0
    assert report.errored_leave_admin_org_units_count == 0
    assert report.missing_fineos_employer_count == 0
    assert report.missing_fineos_org_units_count == 0
    assert report.duplicate_leave_admins_count == 0
    assert report.duplicate_employer_count == 0
    assert report.disabled_leave_admins_count == 0
    assert report.updated_employer_org_units_count == 0


def test_fineos_la_org_units_leave_admin_disabled(
    test_db_session,
    initialize_factories_session,
    setup_leave_admins,
    la_org_units_leave_admin_disabled,
):
    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 0
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 0
    assert len(leave_admin_two_org_units) == 0

    report = fineos_la_org_units.process_fineos_updates(
        test_db_session, la_org_units_leave_admin_disabled
    )

    [
        employer_one_org_units,
        employer_two_org_units,
        leave_admin_one_org_units,
        leave_admin_two_org_units,
    ] = determine_current_status(test_db_session, setup_leave_admins)

    assert len(employer_one_org_units) == 2
    assert len(employer_two_org_units) == 0
    assert len(leave_admin_one_org_units) == 1
    assert len(leave_admin_two_org_units) == 0

    assert report.total_rows_received_count == 2
    assert report.created_employer_org_units_count == 2
    assert report.created_leave_admin_org_units_count == 1
    assert report.disabled_leave_admins_count == 1

    assert report.missing_leave_admins_count == 0
    assert report.missing_required_fields_count == 0
    assert report.errored_employer_org_units_count == 0
    assert report.employer_org_unit_discrepancy_count == 0
    assert report.missing_employer_count == 0
    assert report.errored_leave_admin_org_units_count == 0
    assert report.missing_fineos_employer_count == 0
    assert report.missing_fineos_org_units_count == 0
    assert report.duplicate_leave_admins_count == 0
    assert report.duplicate_employer_count == 0
    assert report.updated_employer_org_units_count == 0
