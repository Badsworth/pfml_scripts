from werkzeug.exceptions import NotFound

import massgov.pfml.api.generate_fake_data as fake

wages_dict = fake.wages


def wages_get(employee_id, period_id=None):
    try:
        wages = wages_dict[employee_id]
    except KeyError:
        raise NotFound()

    if period_id:
        # filter wages by quarter
        return [w for w in wages if w.period_id == str(period_id)]

    return wages
