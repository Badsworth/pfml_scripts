import json
from dataclasses import asdict

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    Country,
    Employee,
    Employer,
    EmployerAddress,
    GeoState,
    ImportLog,
    WagesAndContributions,
)

logger = logging.get_logger(__name__)


def create_employer(db_session, employer_info, import_log_entry_id):
    emp = Employer(
        account_key=employer_info["account_key"],
        employer_fein=employer_info["fein"],
        employer_name=employer_info["employer_name"],
        employer_dba=employer_info["employer_dba"],
        family_exemption=employer_info["family_exemption"],
        medical_exemption=employer_info["medical_exemption"],
        exemption_commence_date=employer_info["exemption_commence_date"],
        exemption_cease_date=employer_info["exemption_cease_date"],
        dor_updated_date=employer_info["updated_date"],
        latest_import_log_id=import_log_entry_id,
    )
    db_session.add(emp)

    try:
        state = find_state(db_session, employer_info["employer_address_state"])
        country = find_country(db_session, "US")
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error("Error trying to find address lookup values", extra={"error": e})
        raise ValueError("Error trying to find address lookup values")

    address = Address(
        address_type_id=AddressType.BUSINESS.address_type_id,
        address_line_one=employer_info["employer_address_street"],
        city=employer_info["employer_address_city"],
        geo_state_id=state.geo_state_id,
        zip_code=employer_info["employer_address_zip"],
        country_id=country.country_id,
    )
    db_session.add(address)

    db_session.flush()
    db_session.refresh(emp)
    db_session.refresh(address)

    emp_address = EmployerAddress(employer_id=emp.employer_id, address_id=address.address_id)
    db_session.add(emp_address)

    return emp


def update_employer(db_session, existing_employer, employer_info, import_log_entry_id):
    existing_employer.employer_name = employer_info["employer_name"]
    existing_employer.employer_dba = employer_info["employer_dba"]
    existing_employer.family_exemption = employer_info["family_exemption"]
    existing_employer.medical_exemption = employer_info["medical_exemption"]
    existing_employer.exemption_commence_date = employer_info["exemption_commence_date"]
    existing_employer.exemption_cease_date = employer_info["exemption_cease_date"]
    existing_employer.dor_updated_date = employer_info["updated_date"]
    existing_employer.latest_import_log_id = import_log_entry_id

    try:
        existing_employer_address = get_employer_address(db_session, existing_employer.employer_id)
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error(
            "Expected a single matching employer address row to be found",
            extra={"employer_id": existing_employer.employer_id, "error": e},
        )
        raise ValueError("Expected a single employer address row to be found")

    try:
        existing_address = get_address(db_session, existing_employer_address.address_id)
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error(
            "Address row not found by id",
            extra={"address_id": existing_employer_address.address_id, "error": e},
        )
        raise ValueError("Address row not found by id")

    try:
        state = find_state(db_session, employer_info["employer_address_state"])
        country = find_country(db_session, "US")
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error("Error trying to find address lookup values", extra={"error": e})
        raise ValueError("Error trying to find address lookup values")

    existing_address.address_line_one = employer_info["employer_address_street"]
    existing_address.city = employer_info["employer_address_city"]
    existing_address.geo_state_id = state.geo_state_id
    existing_address.zip_code = employer_info["employer_address_zip"]
    existing_address.country_id = country.country_id

    return existing_employer


def create_employee(db_session, employee_info, import_log_entry_id):
    employee = Employee(
        tax_identifier=employee_info["employee_ssn"],
        first_name=employee_info["employee_first_name"],
        last_name=employee_info["employee_last_name"],
        latest_import_log_id=import_log_entry_id,
    )
    db_session.add(employee)

    db_session.flush()
    db_session.refresh(employee)

    return employee


def update_employee(db_session, existing_employee, employee_info, import_log_entry_id):
    existing_employee.first_name = employee_info["employee_first_name"]
    existing_employee.last_name = employee_info["employee_last_name"]
    existing_employee.latest_import_log_id = import_log_entry_id

    return existing_employee


def create_wages_and_contributions(
    db_session, employee_wage_info, employee_id, employer_id, import_log_entry_id
):
    wage = WagesAndContributions(
        account_key=employee_wage_info["account_key"],
        filing_period=employee_wage_info["filing_period"],
        employee_id=employee_id,
        employer_id=employer_id,
        is_independent_contractor=employee_wage_info["independent_contractor"],
        is_opted_in=employee_wage_info["opt_in"],
        employee_ytd_wages=employee_wage_info["employee_ytd_wages"],
        employee_qtr_wages=employee_wage_info["employee_qtr_wages"],
        employee_med_contribution=employee_wage_info["employee_medical"],
        employer_med_contribution=employee_wage_info["employer_medical"],
        employee_fam_contribution=employee_wage_info["employee_family"],
        employer_fam_contribution=employee_wage_info["employer_family"],
        latest_import_log_id=import_log_entry_id,
    )
    db_session.add(wage)

    return wage


def update_wages_and_contributions(
    db_session, existing_wages_and_contributions, employee_wage_info, import_log_entry_id
):
    existing_wages_and_contributions.is_independent_contractor = employee_wage_info[
        "independent_contractor"
    ]
    existing_wages_and_contributions.is_opted_in = employee_wage_info["opt_in"]
    existing_wages_and_contributions.employee_ytd_wages = employee_wage_info["employee_ytd_wages"]
    existing_wages_and_contributions.employee_qtr_wages = employee_wage_info["employee_qtr_wages"]
    existing_wages_and_contributions.employee_med_contribution = employee_wage_info[
        "employee_medical"
    ]
    existing_wages_and_contributions.employer_med_contribution = employee_wage_info[
        "employer_medical"
    ]
    existing_wages_and_contributions.employee_fam_contribution = employee_wage_info[
        "employee_family"
    ]
    existing_wages_and_contributions.employer_fam_contribution = employee_wage_info[
        "employer_family"
    ]
    existing_wages_and_contributions.latest_import_log_id = import_log_entry_id

    return existing_wages_and_contributions


def create_import_log_entry(db_session, report):
    """Creating a a report log entry in the database"""
    logger.info("Adding report to import log")
    import_log = ImportLog(
        source="DOR",
        import_type="Initial",
        status=report.status,
        report=json.dumps(asdict(report), indent=2),
        start=report.start,
        end=report.end,
    )
    db_session.add(import_log)
    db_session.flush()
    db_session.refresh(import_log)
    logger.info("Added report to import log")
    return import_log


def update_import_log_entry(db_session, existing_import_log, report):
    """Updating an existing import log entry with the supplied report"""
    logger.info("Updating report in import log")
    existing_import_log.status = report.status
    existing_import_log.report = json.dumps(asdict(report), indent=2)
    existing_import_log.start = report.start
    existing_import_log.end = report.end
    db_session.add(existing_import_log)
    db_session.flush()
    db_session.refresh(existing_import_log)
    logger.info("Finished saving import report in log")
    return existing_import_log


# == Query Helpers ==


def get_employee_by_ssn(db_session, ssn):
    employee_row = db_session.query(Employee).filter(Employee.tax_identifier == ssn).one_or_none()
    return employee_row


def get_wages_and_contributions_by_employee_id_and_filling_period(
    db_session, employee_id, employer_id, filing_period
):
    wage_row = (
        db_session.query(WagesAndContributions)
        .filter(
            WagesAndContributions.employee_id == employee_id,
            WagesAndContributions.employer_id == employer_id,
            WagesAndContributions.filing_period == filing_period,
        )
        .one_or_none()
    )
    return wage_row


def get_employer_by_fein(db_session, fein):
    employer_row = db_session.query(Employer).filter(Employer.employer_fein == fein).one_or_none()
    return employer_row


def get_employer_address(db_session, employer_id):
    employer_address_row = (
        db_session.query(EmployerAddress).filter(EmployerAddress.employer_id == employer_id).one()
    )
    return employer_address_row


def get_address(db_session, address_id):
    address_row = db_session.query(Address).filter(Address.address_id == address_id).one()
    return address_row


# TODO find the state by state_name after lookup is fully populated
def find_state(db_session, state_name):
    state = db_session.query(GeoState).filter(GeoState.geo_state_description == "MA").one()
    return state


# TODO find the country by country_name after lookup is fully populated
def find_country(db_session, country_name):
    country = db_session.query(Country).filter(Country.country_description == "US").one()
    return country
