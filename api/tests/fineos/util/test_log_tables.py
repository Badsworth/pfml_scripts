import massgov.pfml.fineos.util.log_tables as fineos_log_tables_util
from massgov.pfml.db.models.employees import EmployeeLog, EmployerLog
from massgov.pfml.db.models.factories import EmployeeFactory, EmployerFactory


def test_delete_most_recent_update_entry_for_employee_no_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employee = EmployeeFactory.create()

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    employee_log_update_count_before = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE").count()
    )
    assert employee_log_update_count_before == 0

    fineos_log_tables_util.delete_most_recent_update_entry_for_employee(test_db_session, employee)

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == 1

    employee_log_update_count_after = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE").count()
    )
    assert employee_log_update_count_after == 0


def test_delete_most_recent_update_entry_for_employee_single_update(
    test_db_session, initialize_factories_session, create_triggers
):
    employee = EmployeeFactory.create()

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    employee.first_name = employee.first_name + "FOO"
    test_db_session.commit()

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 2

    employee_log_update_count_before = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE").count()
    )
    assert employee_log_update_count_before == 1

    fineos_log_tables_util.delete_most_recent_update_entry_for_employee(test_db_session, employee)

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

    fineos_log_tables_util.delete_most_recent_update_entry_for_employee(test_db_session, employee)

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == 2

    employee_log_update_count_after = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE").count()
    )
    assert employee_log_update_count_after == 1


def test_delete_most_recent_update_entry_for_employer_no_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employer = EmployerFactory.create()

    employer_log_count_before = test_db_session.query(EmployerLog).count()
    assert employer_log_count_before == 1

    employer_log_update_count_before = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "UPDATE").count()
    )
    assert employer_log_update_count_before == 0

    fineos_log_tables_util.delete_most_recent_update_entry_for_employer(test_db_session, employer)

    employer_log_count_after = test_db_session.query(EmployerLog).count()
    assert employer_log_count_after == 1

    employer_log_update_count_after = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "UPDATE").count()
    )
    assert employer_log_update_count_after == 0


def test_delete_most_recent_update_entry_for_employer_single_update(
    test_db_session, initialize_factories_session, create_triggers
):
    employer = EmployerFactory.create()

    employer_log_count_before = test_db_session.query(EmployerLog).count()
    assert employer_log_count_before == 1

    employer.employer_name = employer.employer_name + "FOO"
    test_db_session.commit()

    employer_log_count_before = test_db_session.query(EmployerLog).count()
    assert employer_log_count_before == 2

    employer_log_update_count_before = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "UPDATE").count()
    )
    assert employer_log_update_count_before == 1

    fineos_log_tables_util.delete_most_recent_update_entry_for_employer(test_db_session, employer)

    employer_log_count_after = test_db_session.query(EmployerLog).count()
    assert employer_log_count_after == 1

    employer_log_update_count_after = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "UPDATE").count()
    )
    assert employer_log_update_count_after == 0


def test_delete_most_recent_update_entry_for_employer_multiple_updates(
    test_db_session, initialize_factories_session, create_triggers
):
    employer = EmployerFactory.create()

    employer_log_count_before = test_db_session.query(EmployerLog).count()
    assert employer_log_count_before == 1

    employer.employer_name = employer.employer_name + "FOO"
    test_db_session.commit()

    employer.employer_name = employer.employer_name + "BAR"
    test_db_session.commit()

    employer_log_count_before = test_db_session.query(EmployerLog).count()
    assert employer_log_count_before == 3

    employer_log_update_count_before = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "UPDATE").count()
    )
    assert employer_log_update_count_before == 2

    fineos_log_tables_util.delete_most_recent_update_entry_for_employer(test_db_session, employer)

    employer_log_count_after = test_db_session.query(EmployerLog).count()
    assert employer_log_count_after == 2

    employer_log_update_count_after = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "UPDATE").count()
    )
    assert employer_log_update_count_after == 1
