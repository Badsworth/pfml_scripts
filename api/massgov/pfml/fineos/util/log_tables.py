from contextlib import contextmanager
from typing import Generator, Union

import massgov.pfml.db as db
from massgov.pfml.db.models.employees import Employee, EmployeeLog, Employer, EmployerLog


@contextmanager
def update_entity_and_remove_log_entry(
    db_session: db.Session, emp: Union[Employee, Employer], commit: bool
) -> Generator[None, None, None]:
    """Collect DB updates into a single flush/commit and clean up resulting log entry

    Currently any DB write to the employee or employer tables result in entries
    in the employee_log and employer_log tables (respectively), which end up
    driving exports to FINEOS.

    In many places we are updating our employee/employer tables with information
    *from* FINEOS, so we do not need to export it back to that system.

    Inside this context, SQLAlchemy's autoflush behavior is disabled, so updates
    to an Employee/Employer model can be built up iteratively, upon exiting the
    context updates will be pushed to the DB all at once, ensuring only one log
    entry is created for the update, that is then removed.

    Args:
        db_session: SQLAlchemy Session the entity belongs to
        emp: The Employee or Employer model that will be updated in the context block
        commit: Before leaving the context, if True, DB session will be
            committed, otherwise it is flushed.
    """
    # no_autoflush here so we do not push partial changes to DB, to ensure only
    # one Employe{e,r}Log entry is created and is therefore easy to clean up at
    # the end
    with db_session.no_autoflush:

        yield

        is_emp_modified = db_session.is_modified(emp, include_collections=False)

    if commit:
        db_session.commit()
    else:
        db_session.flush()

    # Remove row from Employe{e,r}Log table due to update trigger if there were
    # changes to the Employe{e,r} in the DB.
    if is_emp_modified:
        if isinstance(emp, Employee):
            delete_most_recent_update_entry_for_employee(db_session, emp)
        else:
            delete_most_recent_update_entry_for_employer(db_session, emp)

        if commit:
            db_session.commit()
        else:
            db_session.flush()


def delete_most_recent_update_entry_for_employee(
    db_session: db.Session, employee: Employee
) -> None:
    db_session.query(EmployeeLog).filter(
        EmployeeLog.employee_log_id
        == (
            db_session.query(EmployeeLog.employee_log_id)
            .filter(
                EmployeeLog.employee_id == employee.employee_id, EmployeeLog.action == "UPDATE",
            )
            .order_by(EmployeeLog.modified_at.desc())
            .limit(1)
        )
    ).delete(synchronize_session=False)


def delete_created_entry_for_employee(db_session: db.Session, employee: Employee) -> None:
    db_session.query(EmployeeLog).filter(
        EmployeeLog.employee_log_id
        == (
            db_session.query(EmployeeLog.employee_log_id)
            .filter(
                EmployeeLog.employee_id == employee.employee_id, EmployeeLog.action == "INSERT",
            )
            .order_by(EmployeeLog.modified_at.desc())
            .limit(1)
        )
    ).delete(synchronize_session=False)


def delete_most_recent_update_entry_for_employer(
    db_session: db.Session, employer: Employer
) -> None:
    db_session.query(EmployerLog).filter(
        EmployerLog.employer_log_id
        == (
            db_session.query(EmployerLog.employer_log_id)
            .filter(
                EmployerLog.employer_id == employer.employer_id, EmployerLog.action == "UPDATE",
            )
            .order_by(EmployerLog.modified_at.desc())
            .limit(1)
        )
    ).delete(synchronize_session=False)
