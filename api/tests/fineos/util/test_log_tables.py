from contextlib import contextmanager

import pytest

import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
from massgov.pfml.db.models.employees import EmployeeLog, EmployerLog
from massgov.pfml.db.models.factories import (
    CtrAddressPairFactory,
    EmployeeFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)


@contextmanager
def assert_log_before_after(test_db_session, log_class, before_counts=(1, 0), after_counts=(1, 0)):
    emp_log_count_before = test_db_session.query(log_class).count()
    assert emp_log_count_before == before_counts[0]

    emp_log_update_count_before = (
        test_db_session.query(log_class).filter(log_class.action == "UPDATE").count()
    )
    assert emp_log_update_count_before == before_counts[1]

    yield

    emp_log_count_after = test_db_session.query(log_class).count()
    assert emp_log_count_after == after_counts[0]

    emp_log_update_count_after = (
        test_db_session.query(log_class).filter(log_class.action == "UPDATE").count()
    )
    assert emp_log_update_count_after == after_counts[1]


@pytest.mark.parametrize("commit", [True, False])
def test_update_entity_and_remove_log_entry_employee(
    test_db_session, initialize_factories_session, create_triggers, mocker, commit
):
    employee = EmployeeFactory.create()

    with assert_log_before_after(test_db_session, EmployeeLog):
        delete_employee_log_spy = mocker.spy(
            fineos_log_tables_util, "delete_most_recent_update_entry_for_employee"
        )

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            test_db_session, employee, commit=commit
        ):
            employee.first_name = employee.first_name + "_FOO"
            employee.last_name = employee.last_name + "_FOO"

        delete_employee_log_spy.assert_called_once()


@pytest.mark.parametrize("commit", [True, False])
def test_update_entity_and_remove_log_entry_employee_foreign_keys(
    test_db_session, initialize_factories_session, create_triggers, mocker, commit
):
    employee = EmployeeFactory.create()

    with assert_log_before_after(test_db_session, EmployeeLog):
        delete_employee_log_spy = mocker.spy(
            fineos_log_tables_util, "delete_most_recent_update_entry_for_employee"
        )

        assert employee.ctr_address_pair_id is None

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            test_db_session, employee, commit=commit
        ):
            employee.ctr_address_pair = CtrAddressPairFactory.build()

        assert employee.ctr_address_pair_id is not None

        delete_employee_log_spy.assert_called_once()


@pytest.mark.parametrize("commit", [True, False])
def test_update_entity_and_remove_log_entry_employer(
    test_db_session, initialize_factories_session, create_triggers, mocker, commit
):
    employer = EmployerFactory.create()

    with assert_log_before_after(test_db_session, EmployerLog):
        delete_employer_log_spy = mocker.spy(
            fineos_log_tables_util, "delete_most_recent_update_entry_for_employer"
        )

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            test_db_session, employer, commit=commit
        ):
            employer.employer_name = employer.employer_name + "_FOO"

        delete_employer_log_spy.assert_called_once()


@pytest.mark.parametrize("commit", [True, False])
def test_update_entity_and_remove_log_entry_non_columns_dont_matter(
    test_db_session, initialize_factories_session, create_triggers, mocker, commit
):
    employee = EmployeeFactory.create()

    with assert_log_before_after(test_db_session, EmployeeLog):
        delete_employee_log_spy = mocker.spy(
            fineos_log_tables_util, "delete_most_recent_update_entry_for_employee"
        )

        wages_count_before = employee.wages_and_contributions.count()
        assert wages_count_before == 0

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            test_db_session, employee, commit=commit
        ):
            employee.wages_and_contributions.append(
                WagesAndContributionsFactory.build(employee=employee)
            )

        delete_employee_log_spy.assert_not_called()

        wages_count_after = employee.wages_and_contributions.count()
        assert wages_count_after == 1


def test_update_entity_and_remove_log_entry_manual_extra_flush_not_handled(
    test_db_session, initialize_factories_session, create_triggers, mocker
):
    employee = EmployeeFactory.create()

    with assert_log_before_after(test_db_session, EmployeeLog, after_counts=(2, 1)):
        delete_employee_log_spy = mocker.spy(
            fineos_log_tables_util, "delete_most_recent_update_entry_for_employee"
        )

        with fineos_log_tables_util.update_entity_and_remove_log_entry(
            test_db_session, employee, commit=True
        ):
            employee.first_name = employee.first_name + "_FOO"
            test_db_session.flush()
            employee.last_name = employee.last_name + "_FOO"

        delete_employee_log_spy.assert_called_once()


def test_delete_most_recent_update_entry_for_employee_no_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employee = EmployeeFactory.create()

    with assert_log_before_after(test_db_session, EmployeeLog):
        fineos_log_tables_util.delete_most_recent_update_entry_for_employee(
            test_db_session, employee
        )


def test_delete_most_recent_update_entry_for_employee_single_update(
    test_db_session, initialize_factories_session, create_triggers
):
    employee = EmployeeFactory.create()

    employee.first_name = employee.first_name + "FOO"
    test_db_session.commit()

    with assert_log_before_after(
        test_db_session, EmployeeLog, before_counts=(2, 1), after_counts=(1, 0)
    ):
        fineos_log_tables_util.delete_most_recent_update_entry_for_employee(
            test_db_session, employee
        )

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == 1

    employee_log_update_count_after = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE").count()
    )
    assert employee_log_update_count_after == 0


def test_delete_most_recent_update_entry_for_employee_multiple_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employee = EmployeeFactory.create()

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    employee.first_name = employee.first_name + "FOO"
    test_db_session.commit()

    employee.first_name = employee.first_name + "BAR"
    test_db_session.commit()

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 3

    employee_log_update_count_before = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE").count()
    )
    assert employee_log_update_count_before == 2

    with assert_log_before_after(
        test_db_session, EmployeeLog, before_counts=(3, 2), after_counts=(2, 1)
    ):
        fineos_log_tables_util.delete_most_recent_update_entry_for_employee(
            test_db_session, employee
        )


def test_delete_most_recent_update_entry_for_employer_no_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employer = EmployerFactory.create()

    with assert_log_before_after(test_db_session, EmployerLog):
        fineos_log_tables_util.delete_most_recent_update_entry_for_employer(
            test_db_session, employer
        )


def test_delete_most_recent_update_entry_for_employer_single_update(
    test_db_session, initialize_factories_session, create_triggers
):
    employer = EmployerFactory.create()

    employer.employer_name = employer.employer_name + "FOO"
    test_db_session.commit()

    with assert_log_before_after(
        test_db_session, EmployerLog, before_counts=(2, 1), after_counts=(1, 0)
    ):
        fineos_log_tables_util.delete_most_recent_update_entry_for_employer(
            test_db_session, employer
        )


def test_delete_most_recent_update_entry_for_employer_multiple_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employer = EmployerFactory.create()

    employer.employer_name = employer.employer_name + "FOO"
    test_db_session.commit()

    employer.employer_name = employer.employer_name + "BAR"
    test_db_session.commit()

    with assert_log_before_after(
        test_db_session, EmployerLog, before_counts=(3, 2), after_counts=(2, 1)
    ):
        fineos_log_tables_util.delete_most_recent_update_entry_for_employer(
            test_db_session, employer
        )
