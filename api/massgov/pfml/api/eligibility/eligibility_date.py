from datetime import date


def eligibility_date(benefit_year_start_date: date, application_submitted_date: date) -> date:
    if date.today() < benefit_year_start_date:
        return application_submitted_date
    return benefit_year_start_date
