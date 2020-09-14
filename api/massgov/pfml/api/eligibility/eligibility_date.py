from datetime import date


def eligibility_date(leave_start_date: date, application_submitted_date: date) -> date:
    if date.today() < leave_start_date:
        return application_submitted_date
    return leave_start_date
