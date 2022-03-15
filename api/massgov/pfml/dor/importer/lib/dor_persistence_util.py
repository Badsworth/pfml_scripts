import datetime
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov.pfml.db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.base import uuid_gen
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    Employee,
    Employer,
    EmployerAddress,
    EmployerQuarterlyContribution,
    TaxIdentifier,
    WagesAndContributions,
    WagesAndContributionsHistory,
)
from massgov.pfml.db.models.geo import Country, GeoState
from massgov.pfml.dor.importer.dor_file_formats import (
    EmployerQuarterlyKey,
    ParsedEmployeeLine,
    ParsedEmployeeWageLine,
    ParsedEmployerLine,
)
from massgov.pfml.util.datetime import to_datetime
from massgov.pfml.util.pydantic.types import TaxIdUnformattedStr

logger = logging.get_logger(__name__)


def employer_id_address_id_to_model(
    employer_id: uuid.UUID, address_id: uuid.UUID
) -> EmployerAddress:
    return EmployerAddress(employer_id=employer_id, address_id=address_id)


def dict_to_employee(
    employee_info: ParsedEmployeeLine,
    import_log_entry_id: int,
    employee_id: Optional[uuid.UUID],
    tax_identifier_id: Optional[uuid.UUID] = None,
) -> Employee:

    if employee_id is None:
        employee_id = uuid_gen()

    employee = Employee(
        employee_id=employee_id,
        first_name=employee_info["employee_first_name"].replace("_", " ").strip(),
        last_name=employee_info["employee_last_name"].replace("_", " ").strip(),
        latest_import_log_id=import_log_entry_id,
        tax_identifier_id=tax_identifier_id,
    )

    return employee


def dict_to_wages_and_contributions(
    employee_wage_info: ParsedEmployeeWageLine,
    employee_id: uuid.UUID,
    employer_id: uuid.UUID,
    import_log_entry_id: int,
) -> WagesAndContributions:
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

    return wage


def dict_to_employer_quarter_contribution(
    employer_info: ParsedEmployerLine, employer_id: uuid.UUID, import_log_entry_id: int
) -> EmployerQuarterlyContribution:
    return EmployerQuarterlyContribution(
        employer_id=employer_id,
        filing_period=employer_info["filing_period"],
        employer_total_pfml_contribution=employer_info["total_pfml_contribution"],
        pfm_account_id=employer_info["pfm_account_id"],
        dor_received_date=employer_info["received_date"],
        dor_updated_date=employer_info["updated_date"],
        latest_import_log_id=import_log_entry_id,
    )


def dict_to_employer(
    employer_info: ParsedEmployerLine, import_log_entry_id: int, employer_id: Optional[uuid.UUID]
) -> Employer:
    if employer_id is None:
        employer_id = uuid_gen()

    return Employer(
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
        employer_id=employer_id,
    )


def employer_dict_to_country_and_state_values(
    employer_info: ParsedEmployerLine,
) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Get employer country and state values for persistence.
    Will throw a KeyError if state is invalid for a USA country code.
    """
    state_id = None
    state_text = None

    country_id = None
    try:
        country_id = Country.get_id(employer_info["employer_address_country"])
    except KeyError:
        logger.info("Country not found %s", employer_info["employer_address_country"])

    if Country.USA.country_id == country_id:
        state_id = GeoState.get_id(employer_info["employer_address_state"])
    else:
        state_text = employer_info["employer_address_state"]

    return country_id, state_id, state_text


def dict_to_address(employer_info: ParsedEmployerLine, address_id: Optional[uuid.UUID]) -> Address:
    country_id, state_id, state_text = employer_dict_to_country_and_state_values(employer_info)

    if address_id is None:
        address_id = uuid_gen()

    return Address(
        address_type_id=AddressType.BUSINESS.address_type_id,
        address_line_one=employer_info["employer_address_street"],
        city=employer_info["employer_address_city"],
        geo_state_id=state_id,
        geo_state_text=state_text,
        zip_code=employer_info["employer_address_zip"],
        country_id=country_id,
        address_id=address_id,
    )


def update_employer(
    db_session: massgov.pfml.db.Session,
    existing_employer: Employer,
    employer_info: ParsedEmployerLine,
    import_log_entry_id: int,
) -> Employer:
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

    country_id, state_id, state_text = employer_dict_to_country_and_state_values(employer_info)

    existing_address.address_line_one = employer_info["employer_address_street"]
    existing_address.city = employer_info["employer_address_city"]
    existing_address.geo_state_id = state_id
    existing_address.geo_state_text = state_text
    existing_address.zip_code = employer_info["employer_address_zip"]
    existing_address.country_id = country_id

    return existing_employer


def tax_id_from_dict(employee_id: uuid.UUID, tax_id: str) -> TaxIdentifier:
    formatted_tax_id = TaxIdUnformattedStr.validate_type(tax_id)
    tax_identifier = TaxIdentifier(tax_identifier_id=employee_id, tax_identifier=formatted_tax_id)

    return tax_identifier


def create_tax_id(db_session: massgov.pfml.db.Session, tax_id: str) -> TaxIdentifier:
    formatted_tax_id = TaxIdUnformattedStr.validate_type(tax_id)
    tax_identifier = TaxIdentifier(tax_identifier=formatted_tax_id)
    db_session.add(tax_identifier)
    db_session.flush()
    db_session.refresh(tax_identifier)
    return tax_identifier


def create_employee(
    db_session: massgov.pfml.db.Session, employee_info: ParsedEmployeeLine, import_log_entry_id: int
) -> Employee:
    employee = Employee(
        first_name=employee_info["employee_first_name"],
        last_name=employee_info["employee_last_name"],
        latest_import_log_id=import_log_entry_id,
    )

    tax_id = get_tax_id(db_session, employee_info["employee_ssn"])
    if tax_id is None:
        tax_id = create_tax_id(db_session, employee_info["employee_ssn"])

    employee.tax_identifier = tax_id

    db_session.add(employee)
    db_session.flush()
    db_session.refresh(employee)

    return employee


def check_and_update_employee(
    existing_employee: Employee, employee_info: ParsedEmployeeLine, import_log_entry_id: int
) -> bool:
    do_update = (
        existing_employee.first_name != employee_info["employee_first_name"]
        or existing_employee.last_name != employee_info["employee_last_name"]
    )

    if not do_update:
        return False

    update_employee(existing_employee, employee_info, import_log_entry_id)
    return True


def update_employee(
    existing_employee: Employee, employee_info: ParsedEmployeeLine, import_log_entry_id: int
) -> Employee:
    existing_employee.first_name = employee_info["employee_first_name"]
    existing_employee.last_name = employee_info["employee_last_name"]
    existing_employee.latest_import_log_id = import_log_entry_id

    return existing_employee


def check_and_update_employer_quarterly_contribution(
    existing_employer_quarterly_contribution: EmployerQuarterlyContribution,
    employer_info: ParsedEmployeeLine,
    import_log_entry_id: int,
) -> bool:
    do_update = (
        existing_employer_quarterly_contribution.employer_total_pfml_contribution
        != employer_info["total_pfml_contribution"]
        or existing_employer_quarterly_contribution.dor_received_date is None
        or existing_employer_quarterly_contribution.dor_received_date.date()
        != employer_info["received_date"]
        or existing_employer_quarterly_contribution.dor_updated_date is None
        or existing_employer_quarterly_contribution.dor_updated_date.date()
        != employer_info["updated_date"].date()
        or existing_employer_quarterly_contribution.pfm_account_id
        != employer_info["pfm_account_id"]
    )

    if not do_update:
        return False

    existing_employer_quarterly_contribution.employer_total_pfml_contribution = employer_info[
        "total_pfml_contribution"
    ]
    existing_employer_quarterly_contribution.pfm_account_id = employer_info["pfm_account_id"]
    existing_employer_quarterly_contribution.dor_received_date = to_datetime(
        employer_info["received_date"]
    )
    existing_employer_quarterly_contribution.dor_updated_date = employer_info["updated_date"]
    existing_employer_quarterly_contribution.latest_import_log_id = import_log_entry_id

    return True


def create_wages_and_contributions(
    db_session: massgov.pfml.db.Session,
    employee_wage_info: ParsedEmployeeWageLine,
    employee_id: uuid.UUID,
    employer_id: uuid.UUID,
    import_log_entry_id: int,
) -> WagesAndContributions:
    wage = dict_to_wages_and_contributions(
        employee_wage_info, employee_id, employer_id, import_log_entry_id
    )
    db_session.add(wage)

    return wage


def _capture_current_wage_and_contribution_state(
    wage_and_contribution_record: WagesAndContributions,
) -> WagesAndContributionsHistory:
    return WagesAndContributionsHistory(
        wage_and_contribution_id=wage_and_contribution_record.wage_and_contribution_id,
        is_independent_contractor=wage_and_contribution_record.is_independent_contractor,
        is_opted_in=wage_and_contribution_record.is_opted_in,
        employee_ytd_wages=wage_and_contribution_record.employee_ytd_wages,
        employee_qtr_wages=wage_and_contribution_record.employee_qtr_wages,
        employee_med_contribution=wage_and_contribution_record.employee_med_contribution,
        employer_med_contribution=wage_and_contribution_record.employer_med_contribution,
        employee_fam_contribution=wage_and_contribution_record.employee_fam_contribution,
        employer_fam_contribution=wage_and_contribution_record.employer_fam_contribution,
        import_log_id=wage_and_contribution_record.latest_import_log_id,
    )


def check_and_update_wages_and_contributions(
    existing_wages_and_contributions: WagesAndContributions,
    employee_wage_info: ParsedEmployeeWageLine,
    import_log_entry_id: int,
    wage_history_records: List[WagesAndContributionsHistory],
) -> bool:
    do_update = (
        existing_wages_and_contributions.is_independent_contractor
        != employee_wage_info["independent_contractor"]
        or existing_wages_and_contributions.is_opted_in != employee_wage_info["opt_in"]
        or existing_wages_and_contributions.employee_ytd_wages
        != employee_wage_info["employee_ytd_wages"]
        or existing_wages_and_contributions.employee_qtr_wages
        != employee_wage_info["employee_qtr_wages"]
        or existing_wages_and_contributions.employee_med_contribution
        != employee_wage_info["employee_medical"]
        or existing_wages_and_contributions.employer_med_contribution
        != employee_wage_info["employer_medical"]
        or existing_wages_and_contributions.employee_fam_contribution
        != employee_wage_info["employee_family"]
        or existing_wages_and_contributions.employer_fam_contribution
        != employee_wage_info["employer_family"]
    )

    if not do_update:
        return False

    wage_and_contribution_history = _capture_current_wage_and_contribution_state(
        existing_wages_and_contributions
    )

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

    wage_history_records.append(wage_and_contribution_history)

    return True


# == Query Helpers ==


def get_employer_quarterly_info_by_employer_id(
    db_session: massgov.pfml.db.Session, employer_ids: Iterable[uuid.UUID]
) -> Dict[EmployerQuarterlyKey, EmployerQuarterlyContribution]:
    """Return a map from (employer id, period date) to EmployerQuarterlyContribution object."""
    employer_contributions = db_session.query(EmployerQuarterlyContribution).filter(
        EmployerQuarterlyContribution.employer_id.in_(employer_ids)
    )
    return {(c.employer_id, c.filing_period): c for c in employer_contributions}


def get_tax_ids(db_session: massgov.pfml.db.Session, ssns: List[str]) -> List[TaxIdentifier]:
    tax_id_rows = (
        db_session.query(TaxIdentifier).filter(TaxIdentifier.tax_identifier.in_(ssns)).all()
    )
    return tax_id_rows


def get_employees_by_ssn(db_session: massgov.pfml.db.Session, ssns: List[str]) -> List[Employee]:
    employee_rows = (
        db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier.in_(ssns))
        .all()
    )
    return employee_rows


def get_wages_and_contributions_by_employee_ids(
    db_session: massgov.pfml.db.Session, employee_ids: List[uuid.UUID]
) -> List[WagesAndContributions]:
    return list(
        db_session.query(WagesAndContributions).filter(
            WagesAndContributions.employee_id.in_(employee_ids)
        )
    )


def get_wages_and_contributions_by_employee_id_and_filling_period(
    db_session: massgov.pfml.db.Session,
    employee_id: uuid.UUID,
    employer_id: uuid.UUID,
    filing_period: datetime.date,
) -> Optional[WagesAndContributions]:
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


def get_tax_id(db_session: massgov.pfml.db.Session, tax_id: str) -> Optional[TaxIdentifier]:
    unformatted_tax_id = TaxIdUnformattedStr.validate_type(tax_id)
    tax_id_row = (
        db_session.query(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == unformatted_tax_id)
        .one_or_none()
    )
    return tax_id_row


def get_all_employers_fein(db_session: massgov.pfml.db.Session) -> List[Employer]:
    employer_rows = (
        db_session.query(Employer)
        .with_entities(Employer.employer_id, Employer.employer_fein, Employer.dor_updated_date)
        .all()
    )
    return employer_rows


def get_employers_by_account_key(
    db_session: massgov.pfml.db.Session, account_keys: Iterable[str]
) -> Dict[str, uuid.UUID]:
    """Return a map from account key to employer id for the given account keys."""
    employer_rows = db_session.query(Employer.account_key, Employer.employer_id).filter(
        Employer.account_key.in_(account_keys)
    )
    return dict(employer_rows)


def get_employer_by_fein(db_session: massgov.pfml.db.Session, fein: str) -> Optional[Employer]:
    employer_row = db_session.query(Employer).filter(Employer.employer_fein == fein).one_or_none()
    return employer_row


def get_employer_address(
    db_session: massgov.pfml.db.Session, employer_id: uuid.UUID
) -> EmployerAddress:
    employer_address_row = (
        db_session.query(EmployerAddress).filter(EmployerAddress.employer_id == employer_id).one()
    )
    return employer_address_row


def get_address(db_session: massgov.pfml.db.Session, address_id: uuid.UUID) -> Address:
    address_row = db_session.query(Address).filter(Address.address_id == address_id).one()
    return address_row
