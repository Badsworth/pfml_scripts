import flask

import massgov.pfml.api.generate_fake_data as fake

employers_dict = fake.employers


def employers_get(employer_id):
    employer = employers_dict.get(employer_id)

    if employer:
        return employer

    not_found_error = flask.Response(status=404)
    return not_found_error
