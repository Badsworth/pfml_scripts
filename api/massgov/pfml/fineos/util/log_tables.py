import massgov.pfml.db as db
from massgov.pfml.db.models.employees import Employee, EmployeeLog, Employer, EmployerLog


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
