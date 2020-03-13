import flask

import massgov.pfml.api.generate_fake_data as fake

wages_dict = fake.wages


def wages_get(employee_id, period_id=None):
    try:
        wages = wages_dict[employee_id]
    except KeyError:
        not_found_status_code = flask.Response(status=404)
        return not_found_status_code

    if period_id and wages:
        # filter wages by quarter
        filtered_wages = []

        for w in wages:
            if w.get("period_id") == str(period_id):
                filtered_wages.append(w)
        return filtered_wages

    if wages:
        return wages
